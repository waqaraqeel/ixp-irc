from pyretic.lib.query import count_bytes
from threading import RLock as lock, Lock as slock
import sqlite3
import os

cwd = os.getcwd()
INTERVAL = 2

class ByteCounter():

    def __init__(self, sdx):
        # Create a database in RAM
        self.db = sqlite3.connect(cwd+'/pyretic/hispar/ribs/rib.db',check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.sdx = sdx
        self.count_lock = slock()
        self.util_lock = slock()

        # Get a cursor object
        cursor = self.db.cursor()
        cursor.execute(''' create table if not exists traffic_count (ip text, from_AS text, bps integer, total integer) ''')
        cursor.execute(''' create table if not exists utilization (port integer, to_AS text, util real, total integer) ''')

        self.capacities = {}
        self.capacities[1] = 10485760
        self.capacities[2] = 10485760
        self.capacities[3] = 10485760
        self.capacities[4] = 10485760

        self.db.commit()

    def __del__(self, ):
        with lock():
            self.db.close()

    def add_or_update_count(self, key, total, interval):
        with slock():
            old_record = self.get_count_record(key)
            
            if old_record is None:
                self.add_count_record(key, 0, total)
            else:
                old_total = old_record['total']
                if old_total is None:
                    old_total = 0
                bps = (total - old_total) / interval * 8
                self.update_count_record(key, bps, total)
                print str(bps/1000) + " Kbps received from " + key[0]
                    
    def add_or_update_util(self, port, to_AS, byte_count, interval):
        with slock():
            if to_AS is not None:
                old_record = self.get_util_record(to_AS)
            
            if old_record is None:
                util = byte_count * 8 / interval / float(self.capacities[port]) * 100
                self.add_util_record(port, to_AS, util, byte_count)
            else:
                old_total = old_record['total']
                if old_total is None:
                    old_total = 0
                delta_bytes = byte_count - old_total
                util = delta_bytes * 8 / interval / float(self.capacities[port]) * 100
                self.update_util_record(port, to_AS, util, byte_count)

            print str(delta_bytes * 8 / interval / 1000) + " Kbps sent on port " + str(port) + ": "+ str(self.capacities[port]/1000) + " Kbps: " + str(util) + "%"
                
    def add_count_record(self, key, bps, total):

        with lock():
            cursor = self.db.cursor()

            cursor.execute('''insert into traffic_count (ip, from_AS, bps, total) values(?,?,?,?)''', 
                        (key[0], key[1], bps, total))
            self.commit()

    def add_util_record(self, port, to_AS, util, total):

        with lock():
            cursor = self.db.cursor()

            cursor.execute('''insert into utilization (port, to_AS, util, total) values(?,?,?,?)''', 
                        (port, to_AS, util, total))
            self.commit()


    def get_count_record(self,key): 
        with lock():
            cursor = self.db.cursor()
            cursor.execute('''select * from traffic_count where ip = ? and from_AS = ?''', (key[0], key[1]))

            return cursor.fetchone()

    def get_util_record(self, to_AS): 
        with lock():
            cursor = self.db.cursor()
            cursor.execute('''select * from utilization where to_AS = ?''', to_AS)

            return cursor.fetchone()


    def update_count_record(self,key,bps,total):

        with lock():
            cursor = self.db.cursor()

            script = "update traffic_count set bps = " + str(bps) + ", total = " + str(total) + " where ip = '" + key[0] + "' and from_AS = '" + key[1] + "'"

            cursor.execute(script)
            self.commit()

    def update_util_record(self, port, to_AS, util, total):

        with lock():
            cursor = self.db.cursor()

            script = "update utilization set util = " + str(util) + ", to_AS = '" + str(to_AS) + "', total = " + str(total) + " where port = " + str(port)

            cursor.execute(script)
            self.commit()


    def commit(self):

        with lock():
            self.db.commit()

    def rollback(self):

        with lock():
            self.db.rollback()

    def __get_AS(self, inport):
        for participant in self.sdx.participants:
            for port in self.sdx.participants[participant].phys_ports:
                if inport == port.id_:
                    return participant


    def get_count_policy(self):
        count_policy = count_bytes(interval=INTERVAL, group_by=["dstip", "inport", "outport"])
        count_policy.register_callback(self.__count_callback)
        return count_policy


    def get_util_policy(self):
        monitor_policy = count_bytes(interval=INTERVAL, group_by=['outport'])
        monitor_policy.register_callback(self.__util_callback)
        return monitor_policy


    def __util_callback(self, pkt):
        with self.util_lock:
            for match, byte_count in pkt.iteritems():
                if 'outport' in match.map:
                    if match.map['outport'] is not None:
                        port = int(match.map['outport'])
                        if port == 3 or port == 4:
                            print pkt
#                             to_AS = self.__get_AS(match.map['outport'])
#                             self.add_or_update_util(port, str(to_AS), byte_count, INTERVAL)


    def __count_callback(self, pkt):
        with self.count_lock:
            for match, byte_count in pkt.iteritems():
                if 'inport' in match.map and 'dstip' in match.map:
                    if match.map['inport'] is not None and match.map['dstip'] is not None:
                        ip = str(match.map['dstip'])
			if not ip.startswith('172.0.0.'):
			    from_AS = self.__get_AS(match.map['inport'])
			    self.add_or_update_count( (ip, str(from_AS)), int(byte_count), INTERVAL)
