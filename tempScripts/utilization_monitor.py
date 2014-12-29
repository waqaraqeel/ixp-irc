__author__ = 'wirate'
# This script takes the interface number as argument and computes utilization
# percentage using the rule given at cisco link in the Links file. Interval is 5 seconds

from pysnmp.entity.rfc3413.oneliner import cmdgen
import sys
from time import sleep

# constants for numerical OIDs
IFNAME = '.1.3.6.1.2.1.31.1.1.1.1'
IFINOCTETS = '.1.3.6.1.2.1.2.2.1.10'
IFOUTOCTETS = '.1.3.6.1.2.1.2.2.1.16'
IFSPEED = '.1.3.6.1.2.1.2.2.1.5'

# other constants
INTERVAL = 5


def fetch_value(cmd_generator, variable):
    error_indication, error_status, error_index, var_binds = cmd_generator.getCmd(
        cmdgen.CommunityData('public'),
        cmdgen.UdpTransportTarget(('localhost', 161)),
        variable
    )

    return var_binds[0][1]


def get_if_id(cmd_generator, if_name):
    error_indication, error_status, error_index, var_bind_table = cmd_generator.nextCmd(
        cmdgen.CommunityData('public'),
        cmdgen.UdpTransportTarget(('localhost', 161)),
        IFNAME
    )

    for varBindTableRow in var_bind_table:
        for name, val in varBindTableRow:
            if val == if_name:
                pos = str(name).rfind(".")
                return str(name)[pos+1:]


def monitor_utilization(if_id=None, if_name=None):
    cmd_gen = cmdgen.CommandGenerator()
    if if_id is None and if_name is not None:
        if_id = get_if_id(cmd_gen, if_name)

    if_id = '.' + if_id
    if_name = str(fetch_value(cmd_gen, IFNAME + if_id))
    if_speed = long(fetch_value(cmd_gen, IFSPEED + if_id))

    if if_speed <= 0:
        sys.exit("interface speed is 0")

    prev_inoctets = long(fetch_value(cmd_gen, IFINOCTETS + if_id))
    prev_outoctets = long(fetch_value(cmd_gen, IFOUTOCTETS + if_id))
    sleep(INTERVAL)

    while True:
        inoctets = long(fetch_value(cmd_gen, IFINOCTETS + if_id))
        outoctets = long(fetch_value(cmd_gen, IFOUTOCTETS + if_id))
        d_inoctets = inoctets - prev_inoctets
        d_outoctets = outoctets - prev_outoctets

        util = ((d_inoctets + d_outoctets) * 8 * 100) / (INTERVAL * if_speed)
        print if_name + ' utilization: ' + str(util) + '%'
        prev_inoctets = inoctets
        prev_outoctets = outoctets
        sleep(INTERVAL)
