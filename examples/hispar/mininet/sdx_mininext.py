#!/usr/bin/python

# Author: Waqar Ahmed

import inspect
import os
import sys
import atexit
# Import topo from Mininext
from mininext.topo import Topo
# Import quagga service from examples
from mininext.services.quagga import QuaggaService
# Other Mininext specific imports
from mininext.net import MiniNExT as Mininext
from mininext.cli import CLI
import mininext.util
# Imports from Mininet
import mininet.util
mininet.util.isShellBuiltin = mininext.util.isShellBuiltin
sys.modules['mininet.util'] = mininet.util

from mininet.util import dumpNodeConnections
from mininet.node import RemoteController
from mininet.log import setLogLevel, info
from collections import namedtuple
from pyretic.hispar.tempScripts.snmpd import SnmpdService

QuaggaHost = namedtuple("QuaggaHost", "name ip mac port")
net = None


class QuaggaTopo(Topo):
    """ Quagga topology example. """

    def __init__(self):

        """Initialize topology"""
        Topo.__init__(self)

        "Directory where this file / script is located"
        scriptdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))  # script directory
        "Initialize a service helper for Quagga with default options"
        quagga_svc = QuaggaService(autoStop=False)
        # snmpd_svc = SnmpdService(autoStop=False)

        "List of Quagga host configs"
        quagga_hosts = [
            (QuaggaHost(name='a1', ip='172.0.0.1/16', mac='08:00:27:89:3b:9f', port=1)),
            (QuaggaHost(name='b1', ip='172.0.0.11/16', mac='08:00:27:92:18:1f', port=2)),
            (QuaggaHost(name='c1', ip='172.0.0.21/16', mac='08:00:27:54:56:ea', port=3)),
            (QuaggaHost(name='x1', ip='172.0.0.31/16', mac='08:00:27:54:56:eb', port=4)),
            (QuaggaHost(name='y1', ip='172.0.0.41/16', mac='08:00:27:54:56:ec', port=5))]

        "Add switch for IXP fabric"
        ixpfabric = self.addSwitch('s1')

        "Setup each legacy router, add a link between it and the IXP fabric"
        quagga_nodes = {}
        for host in quagga_hosts:
            "Set Quagga service configuration for this node"
            quagga_svc_config = {'quaggaConfigPath': scriptdir + '/quaggacfgs/' + host.name}
            snmpd_svc_config = {'snmpd_config_path': scriptdir + '/snmpdcfgs/' + host.name}

            quagga_container = self.addHost(name=host.name,
                                            ip=host.ip,
                                            mac=host.mac,
                                            privateLogDir=True,
                                            privateRunDir=True,
                                            inMountNamespace=True,
                                            inPIDNamespace=True)
            quagga_nodes[host.name] = quagga_container

            self.addNodeService(node=host.name, service=quagga_svc,
                                nodeConfig=quagga_svc_config)

            # self.addNodeService(node=host.name, service=snmpd_svc,
            #                     nodeConfig=snmpd_svc_config)

            "Attach the quaggaContainer to the IXP Fabric Switch"
            self.addLink(quagga_container, ixpfabric, port2=host.port)
        
        " Add root node for ExaBGP. ExaBGP acts as route server for SDX. "
        root = self.addHost('exabgp', ip='172.0.255.254/16', inNamespace=False)
        self.addLink(root, ixpfabric, port2=6)

        # " Add cloud server to upload files "
        # azure = self.addHost('azure', ip='10.0.0.1', inNamspace=False)
        # self.addLink(azure, quagga_nodes['x1'])
        # self.addLink(azure, quagga_nodes['y1'])


def add_interfaces_for_sdx_network(net_sim):
    hosts = net_sim.hosts
    print "Configuring participating ASs\n\n"
    for host in hosts:
        print "Host name: ", host.name
        if host.name == 'a1':
            host.cmd('sudo ifconfig lo:1 100.0.0.1 netmask 255.255.255.0 up')
            host.cmd('sudo ifconfig lo:2 100.0.0.2 netmask 255.255.255.0 up')
            host.cmd('sudo ifconfig lo:110 110.0.0.1 netmask 255.255.255.0 up')
        if host.name == 'b1':
            host.cmd('sudo ifconfig lo:140 140.0.0.1 netmask 255.255.255.0 up')
            host.cmd('sudo ifconfig lo:150 150.0.0.1 netmask 255.255.255.0 up')
        if host.name == 'c1':
            host.cmd('sudo ifconfig lo:140 140.0.0.1 netmask 255.255.255.0 up')
            host.cmd('sudo ifconfig lo:150 150.0.0.1 netmask 255.255.255.0 up')
        if host.name == 'c2':
            host.cmd('sudo ifconfig lo:140 140.0.0.1 netmask 255.255.255.0 up')
            host.cmd('sudo ifconfig lo:150 150.0.0.1 netmask 255.255.255.0 up')
        if host.name == "exabgp":
            host.cmd('route add -net 172.0.0.0/16 dev exabgp-eth0')


def start_network():
    info('** Creating Quagga network topology\n')
    topo = QuaggaTopo()
    global net
    net = Mininext(topo=topo, 
                   controller=lambda name: RemoteController(name, ip='127.0.0.1'), listenPort=6633)
    
    info('** Starting the network\n')
    net.start()
    
    info('** psaux dumps on all hosts\n')
    for lr in net.hosts:
        if lr.name != 'exabgp':
            lr.cmdPrint("ps aux")
    
    info('**Adding Network Interfaces for SDX Setup\n')
    add_interfaces_for_sdx_network(net)
    
    info('** Running CLI\n')
    CLI(net)


def stop_network():
    if net is not None:
        info('** Tearing down Quagga network\n')
        net.stop()

if __name__ == '__main__':
    # Force cleanup on exit by registering a cleanup function
    atexit.register(stop_network)

    # Tell mininet to print useful information
    setLogLevel('info')
    start_network()
