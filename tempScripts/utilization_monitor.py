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


if_id = '.' + sys.argv[1]
cmdGen = cmdgen.CommandGenerator()
if_name = str(fetch_value(cmdGen, IFNAME + if_id))
if_speed = long(fetch_value(cmdGen, IFSPEED + if_id))

if if_speed <= 0:
    sys.exit("interface speed is 0")

prev_inoctets = long(fetch_value(cmdGen, IFINOCTETS + if_id))
prev_outoctets = long(fetch_value(cmdGen, IFOUTOCTETS + if_id))
sleep(INTERVAL)

while True:
    inoctets = long(fetch_value(cmdGen, IFINOCTETS + if_id))
    outoctets = long(fetch_value(cmdGen, IFOUTOCTETS + if_id))
    d_inoctets = inoctets - prev_inoctets
    d_outoctets = outoctets - prev_outoctets

    util = ((d_inoctets + d_outoctets) * 8 * 100) / (INTERVAL * if_speed)
    print if_name + ' utilization: ' + str(util) + '%'
    prev_inoctets = inoctets
    prev_outoctets = outoctets
    sleep(INTERVAL)
