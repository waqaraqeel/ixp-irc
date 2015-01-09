################################################################################
#
#  <website link>
#
#  File:
#        core.py
#
#  Project:
#        Software Defined Exchange (SDX)
#
#  Author:
#        Arpit Gupta
#        Laurent Vanbever
#        Muhammad Shahbaz
#
#  Copyright notice:
#        Copyright (C) 2012, 2013 Georgia Institute of Technology
#              Network Operations and Internet Security Lab
#
#  Licence:
#        This file is part of the SDX development base package.
#
#        This file is free code: you can redistribute it and/or modify it under
#        the terms of the GNU Lesser General Public License version 2.1 as
#        published by the Free Software Foundation.
#
#        This package is distributed in the hope that it will be useful, but
#        WITHOUT ANY WARRANTY; without even the implied warranty of
#        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#        Lesser General Public License for more details.
#
#        You should have received a copy of the GNU Lesser General Public
#        License along with the SDX source package.  If not, see
#        http://www.gnu.org/licenses/.
#

## General imports
from pyretic.hispar.lib.corelib import *
from importlib import import_module

## Pyretic-specific imports
from pyretic.lib.corelib import *
from pyretic.lib.std import *

## SDX-specific imports
from pyretic.hispar.lib.common import *
from pyretic.hispar.lib.bgp_interface import *
from pyretic.hispar.lib.set_operations import *
from pyretic.hispar.lib.language import *
from pyretic.hispar.lib.vnh_assignment import *
from pyretic.hispar.lib.composition import simple_compose

# TODO: these should be added in the config file --AG
VNH_2_IP = {
            'VNH':list(IPNetwork('172.0.1.1/28'))
           }
VNH_2_MAC= {
            'VNH':'aa:00:00:00:00:00'
           }


class SDX(object):
    """Represent a SDX platform configuration"""
    def __init__(self):
        self.server = None
        self.compose_mode = 0       # 0:sdx_platform
        
        self.participants = {}
        
        self.sdx_ports={}
        self.participant_id_to_in_var = {}
        self.out_var_to_port = {}
        self.port_id_to_out_var = {}
        
        self.participant_2_port={}
        
        
        self.VNH_2_pfx = {}
        self.VNH_2_IP=VNH_2_IP
        self.VNH_2_MAC = VNH_2_MAC
        self.part_2_VNH={}
        
        #self.prefixes=prefixes
        
        self.port_2_participant={}
        self.part_2_prefix_old={}
        self.part_2_prefix_lcs={}
        self.lcs_old=[]
        
    ''' Get the name of the participant belonging to the IP address '''
    def get_participant_name(self,ip):
        
        for participant_name in self.sdx_ports:
            for port in self.sdx_ports[participant_name]:  
                if ip is str(port.ip):
                    return participant_name
    
    def get_neighborList(self,sname):
        #print type(sname)
        neighbor_list=[]
        for participant in self.participants:
            #print participant.peers.keys()
            if sname in self.participants[participant].peers.keys():
                #print "Neighbor found",participant.id_
                neighbor_list.append(self.participants[participant].id_) 
        return neighbor_list
    
    def add_participant(self, participant, name):
        self.participants[name] = participant
        self.participant_id_to_in_var[participant.id_] = "in" + participant.id_.upper()
        i = 0
        for port in participant.phys_ports:
            self.port_id_to_out_var[port.id_] = "out" + participant.id_.upper() + "_" + str(i)
            self.out_var_to_port["out" + participant.id_.upper() + "_" + str(i)] = port
            i += 1
    
    def fwd(self, port):
        if isinstance(port, PhysicalPort):
            return modify(state=self.port_id_to_out_var[port.id_], dstmac=port.mac)
        else:
            return modify(state=self.participant_id_to_in_var[port.participant.id_])
        
    def compose_policies(self):
        # Compose participant's policies using various composition approaches
        if self.compose_mode == 0:
            return simple_compose(self)
        
            
        

###
### SDX primary functions
###

def sdx_parse_config(config_file):
    sdx = SDX()
    
    sdx_config = json.load(open(config_file, 'r'))
    #print sdx_config
    sdx_ports = {}
    sdx_vports = {}
    
    
    ''' 
        Create SDX environment ...
    '''
    print "Creating SDX environment from the config files"
    for participant_name in sdx_config:
        
        ''' Adding physical ports '''
        print "Adding Physical ports for ", participant_name
        participant = sdx_config[participant_name]
        sdx_ports[participant_name] = [PhysicalPort(id_=participant["Ports"][i]['Id'],
                                       mac=MAC(participant["Ports"][i]["MAC"]),
                                       ip=IP(participant["Ports"][i]["IP"])) 
                                       for i in range(0, len(participant["Ports"]))]     
        sdx.participant_2_port[participant_name] = {participant_name:[]}
        for i in range(0, len(participant["Ports"])):
            sdx.port_2_participant[participant["Ports"][i]['Id']] = participant_name  
            sdx.participant_2_port[participant_name][participant_name].append(participant["Ports"][i]['Id'])
        #print sdx_ports[participant_name]
        ''' Adding virtual port '''
        print "Adding virtual ports for ", participant_name
        sdx_vports[participant_name] = VirtualPort(participant=participant_name, id_ = participant["Ports"][0]['Id']) #Check if we need to add a MAC here
    
    sdx.sdx_ports=sdx_ports   
    for participant_name in sdx_config:
        peers = {}
        
        ''' Assign peers to each participant '''
        for peer_name in sdx_config[participant_name]["Peers"]:
            peers[peer_name] = sdx_vports[peer_name]
            sdx.participant_2_port[participant_name][peer_name] = [sdx_vports[peer_name].id_]
        print sdx.participant_2_port
            
        ''' Creating a participant object '''
        sdx_participant = SDXParticipant(id_=participant_name,vport=sdx_vports[participant_name],
                                         phys_ports=sdx_ports[participant_name],peers=peers)
        
        ''' Adding the participant in the SDX '''
        sdx.add_participant(sdx_participant,participant_name)
    
    return sdx
                
def sdx_parse_policies(policy_file,sdx):
        
    sdx_policies = json.load(open(policy_file,'r'))  
    ''' 
        Get participants policies
    '''
    print "Parsing participant's policies"
    for participant_name in sdx_policies:
        participant = sdx.participants[participant_name]
        policy_modules = [import_module(sdx_policies[participant_name][i]) 
                          for i in range(0, len(sdx_policies[participant_name]))]
        
        participant.policies = parallel([
             policy_modules[i].policy(participant, sdx) 
             for i in range(0, len(sdx_policies[participant_name]))])  
#        print "Before pre",participant.policies
        # translate these policies for VNH Assignment
#         participant.original_policies=participant.policies
#         participant.policies=pre_VNH(participant.policies,sdx,participant_name,participant)
#         
#         print "After pre: ",participant.policies
    #print sdx.out_var_to_port[u'outB_1'].id_  
       
    # Virtual Next Hop Assignment
#     print "Starting VNH Assignment"
#     vnh_assignment(sdx) 
#     print "Completed VNH Assignment"
    # translate these policies post VNH Assignment
    
    classifier=[]
    for participant_name in sdx.participants:
#         sdx.participants[participant_name].policies=post_VNH(sdx.participants[participant_name].policies,
#                                                          sdx,participant_name)        
#         print "After Post VNH: ",sdx.participants[participant_name].policies
        start_comp=time.time()
        classifier.append(sdx.participants[participant_name].policies.compile())
        #print participant_name, time.time() - start_comp, "seconds"
    
def sdx_parse_announcements(announcement_file,sdx):
        
    sdx_announcements = json.load(open(announcement_file,'r'))  
    ''' 
        Get participants custom routes
    '''
    for participant_name in sdx_announcements:
        participant = sdx.participants[participant_name]
        announcement_modules = [import_module(sdx_announcements[participant_name][i]) 
                          for i in range(0, len(sdx_announcements[participant_name]))]
        
        participant.custom_routes = []
        for announcement_module in announcement_modules:
            participant.custom_routes.extend(announcement_module.custom_routes(participant,sdx))
        
def sdx_annouce_custom_routes(sdx):
    ''' 
        Announce participants custom routes
    '''
    
    for participant_name in sdx.participants:
        for route in sdx.participants[participant_name].custom_routes:
            bgp_announce_route(sdx,route)
