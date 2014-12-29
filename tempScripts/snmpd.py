__author__ = 'wirate'


"""
service that manages snmpd routers
"""

from mininext.mount import MountProperties, ObjectPermissions, PathProperties
from mininext.moduledeps import serviceCheck
from mininext.service import Service


class SnmpdService(Service):

    """Manages SNMP Agent Service"""

    def __init__(self, name="snmpd", **params):
        """Initializes an SnmpdService instance with a set of global parameters

        Args:
            name (str): Service name (derived class may wish to override)
            params: Arbitrary length list of global properties for this service

        """

        # Verify that snmpd is installed
        serviceCheck('snmpd', moduleName='SNMP Agent Service')

        # Call service initialization (will set defaultGlobalParams)
        Service.__init__(self, name=name, **params)

        self.getDefaultGlobalMounts()

    def verifyNodeMeetsServiceRequirements(self, node):
        """Verifies that a specified node is configured to support snmpd

        Overrides the :class:`.Service` default verification method to conduct
            checks specific to snmpd. This includes checking that the node
            has a private log space, a private run space, and is in a PID
            namespace

        Args:
            node: Node to inspect
        """
        # TODO: actually verify requirements for snmpd

        # if node.inPIDNamespace is False:
        #     raise Exception("Quagga service requires PID namespace (node %s)\n"
        #                     % (node))
        #
        # if node.hasPrivateLogs is False:
        #     raise Exception("Quagga service requires private logs (node %s)\n"
        #                     % (node))
        #
        # if node.hasPrivateRun is False:
        #     raise Exception("Quagga service requires private /run (node %s)\n"
        #                     % (node))

    def setupNodeForService(self, node):
        """After mounts and other operations taken care of by Service Helper,
           we perform a few last minute tasks here"""

        # TODO
        # Initialize log directory
        # _, err, ret = node.pexec("mkdir /var/log/quagga")
        # _, err, ret = node.pexec("chown quagga:quagga /var/log/quagga")

    def getDefaultGlobalParams(self):
        """Returns the default parameters for this service"""
        defaults = {'startCmd': '/etc/init.d/snmpd start',
                    'stopCmd': '/etc/init.d/snmpd stop',
                    'autoStart': True,
                    'autoStop': True,
                    'configPath': None}
        return defaults

    def getDefaultGlobalMounts(self):
        """Service-wide default mounts for the smmpd service"""

        mounts = []
        mount_config_pairs = {}

        # snmpd configuration paths
        snmpd_config_perms = ObjectPermissions(username='snmp',
                                               groupname='snmp',
                                               mode=0o775,
                                               strictMode=False,
                                               enforceRecursive=True)
        snmpd_config_path = PathProperties(path=None,
                                           perms=snmpd_config_perms,
                                           create=True,
                                           createRecursive=True,
                                           setPerms=True,
                                           checkPerms=True)
        snmpd_config_mount = MountProperties(target='/etc/snmp',
                                             source=snmpd_config_path)
        mounts.append(snmpd_config_mount)
        mount_config_pairs['snmpd_config_path'] = snmpd_config_mount

        return mounts, mount_config_pairs