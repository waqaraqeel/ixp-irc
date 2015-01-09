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
#        Muhammad Shahbaz
#        Laurent Vanbever
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

## Pyretic-specific imports
from pyretic.lib.corelib import *
from pyretic.lib.std import *

## SDX-specific imports
from pyretic.hispar.lib.common import *
from pyretic.hispar.lib.bgp_interface import *
from pyretic.hispar.lib.language import *

## General imports
import json
import os

cwd = os.getcwd()

def parse_config(config_file):
    participants = json.load(open(config_file, 'r'))
    
    for participant_name in participants:
        for i in range(len(participants[participant_name]["IPP"])):
            participants[participant_name]["IPP"][i] = IPPrefix(participants[participant_name]["IPP"][i])    
    return participants

def policy(participant, sdx):
    '''
        Specify participant policy
    '''
    
    prefixes_announced=bgp_get_announced_routes(sdx,'A')
    
    final_policy= (
                   (match(dstip=IPPrefix('10.0.0.0/16')) >> sdx.fwd(participant.peers['X'])) +
                   (match(dstip=IPPrefix('110.0.0.0/16')) >> sdx.fwd(participant.phys_ports[0]))
                )
    
    return final_policy
