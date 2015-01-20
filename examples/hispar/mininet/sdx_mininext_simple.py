# Author: Waqar Ahmed

import inspect
import os
import sys
import atexit
# Import topo from Mininext
from mininext.topo import Topo
# Other Mininext specific imports
from mininext.net import MiniNExT as Mininext
from mininext.cli import CLI
import mininext.util
# Imports from Mininet
import mininet.util
mininet.util.isShellBuiltin = mininext.util.isShellBuiltin
sys.modules['mininet.util'] = mininet.util

from mininet.node import RemoteController
from mininet.log import setLogLevel, info
from collections import namedtuple
from pyretic.hispar.pending.snmpd import SnmpdService

HostTuple = namedtuple("HostTuple", "name ip mac port")
net = None


class SnmpTopo(Topo):
    """ SNMP topology example. """

    def __init__(self):

        """Initialize topology"""
        Topo.__init__(self)

#         # Directory where this file / script is located
#         scriptdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
#         snmpd_svc = SnmpdService(autoStop=False)
# 
#         # List of host configs"
#         hosts = [
#             (HostTuple(name='a1', ip='172.0.0.1/16', mac='08:00:27:89:3b:9f', port=1)),
#             (HostTuple(name='b1', ip='172.0.0.11/16', mac='08:00:27:92:18:1f', port=2)),
#             (HostTuple(name='x1', ip='172.0.0.21/16', mac='08:00:27:54:56:eb', port=3)),
#             (HostTuple(name='y1', ip='172.0.0.31/16', mac='08:00:27:54:56:ec', port=4)),
#             (HostTuple(name='azure', ip='10.0.0.1/16', mac='08:00:27:54:56:ed', port=None))]
# 
#         # Add switch for IXP fabric"
#         ixpfabric = self.addSwitch('s1')
# 
#         # Setup each legacy router, add a link between it and the IXP fabric"
#         snmp_nodes = {}
#         for host in hosts:
#             # Set snmp service configuration for this node"
#             snmpd_svc_config = {'snmpd_config_path': scriptdir + '/snmpdcfgs/' + host.name}
# 
#             snmp_container = self.addHost(name=host.name,
#                                             ip=host.ip,
#                                             mac=host.mac,
#                                             privateLogDir=True,
#                                             privateRunDir=True,
#                                             inMountNamespace=True,
#                                             inPIDNamespace=True)
#             snmp_nodes[host.name] = snmp_container
# 
#             self.addNodeService(node=host.name, service=snmpd_svc,
#                                 nodeConfig=snmpd_svc_config)
# 
#             # Attach the Container to the IXP Fabric Switch"
# #             if host.name != 'azure':
# #                 self.addLink(snmp_container, ixpfabric, port2=host.port)
# 
# 

        # Add routers
        x1 = self.addHost('x1', ip='172.0.0.21')

        # Add other intermediary hosts
        ahost = self.addHost('ahost', ip='110.0.0.1')
        self.addLink(x1, ahost);

        # Add cloud server to upload files links
        azure = self.addHost('azure', ip='10.0.0.1')
        self.addLink(azure, x1)

        bhost1 = self.addHost('bhost1', ip='120.0.0.1')
        bhost2 = self.addHost('bhost2', ip='130.0.0.1')
        self.addLink(x1, bhost1);
        self.addLink(x1, bhost2);


def configure_hosts(net_sim):
    hosts = net_sim.hosts
    print "Configuring participating ASs\n\n"
    for host in hosts:
        print "Host name: ", host.name
        if host.name == "x1":
            host.cmd('sysctl -w net.ipv4.ip_forward=1')
            host.cmd('/sbin/ip route flush table main')
            host.cmd('route add -net 110.0.0.0 netmask 255.255.0.0 x1-eth0')
            host.cmd('route add -net 120.0.0.0 netmask 255.255.0.0 x1-eth2')
            host.cmd('route add -net 130.0.0.0 netmask 255.255.0.0 x1-eth3')
            host.cmd('route add -net 10.0.0.0 netmask 255.255.0.0 x1-eth1')
            host.cmd('ifconfig x1-eth2 172.0.0.22 up')
            host.cmd('ifconfig x1-eth3 172.0.0.23 up')
            host.cmd('echo 1 > /proc/sys/net/ipv4/conf/x1-eth0/proxy_arp')
            host.cmd('echo 1 > /proc/sys/net/ipv4/conf/x1-eth1/proxy_arp')
            host.cmd('echo 1 > /proc/sys/net/ipv4/conf/x1-eth2/proxy_arp')
            host.cmd('echo 1 > /proc/sys/net/ipv4/conf/x1-eth3/proxy_arp')

            # Rate limiting traffic
            host.cmd('tc qdisc add dev x1-eth1 root netem rate 10mbit')

        elif host.name == "y1":
            host.cmd('sysctl -w net.ipv4.ip_forward=1')
            host.cmd('/sbin/ip route flush table main')
            host.cmd('route add default y1-eth0')
            host.cmd('route add -net 10.0.0.0 netmask 255.255.0.0 y1-eth1')
            host.cmd('echo 1 > /proc/sys/net/ipv4/conf/y1-eth0/proxy_arp')
            host.cmd('echo 1 > /proc/sys/net/ipv4/conf/y1-eth1/proxy_arp')

        elif host.name == "azure":
            host.cmd('route add default dev azure-eth0')

        elif host.name == "ahost":
            host.cmd('route add -net 172.0.0.0 netmask 255.255.0.0 ahost-eth0')
            host.cmd('route add default gw 172.0.0.21 dev ahost-eth0')

            # Rate limiting traffic
            host.cmd('tc qdisc add dev ahost-eth0 root netem rate 5mbit')

        elif host.name == "bhost1":
            host.cmd('route add -net 172.0.0.0 netmask 255.255.0.0 bhost1-eth0')
            host.cmd('route add default gw 172.0.0.22 dev bhost1-eth0')

            # Rate limiting traffic
            host.cmd('tc qdisc add dev bhost1-eth0 root netem rate 3mbit')

        elif host.name == "bhost2":
            host.cmd('route add -net 172.0.0.0 netmask 255.255.0.0 bhost2-eth0')
            host.cmd('route add default gw 172.0.0.23 dev bhost2-eth0')

            # Rate limiting traffic
            host.cmd('tc qdisc add dev bhost2-eth0 root netem rate 7mbit')


def start_network():
    info('** Creating Snmp network topology\n')
    topo = SnmpTopo()
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
    configure_hosts(net)
    
    info('** Running CLI\n')
    CLI(net)


def stop_network():
    if net is not None:
        info('** Tearing down Snmp network\n')
        net.stop()

if __name__ == '__main__':
    # Clear input stream
    # termios.tcflush(sys.stdin, termios.TCIOFLUSH)
    # Force cleanup on exit by registering a cleanup function
    atexit.register(stop_network)

    # Tell mininet to print useful information
    setLogLevel('info')
    start_network()
