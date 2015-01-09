from pyretic.lib.query import count_bytes
from threading import RLock as lock
import sqlite3
import os

cwd = os.getcwd()
INTERVAL = 10

class ByteCounter():

    def __init__(self, sdx):
        # Create a database in RAM
        self.db = sqlite3.connect(cwd+'/pyretic/hispar/ribs/rib.db',check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.sdx = sdx

        # Get a cursor object
        cursor = self.db.cursor()
        cursor.execute(''' create table if not exists traffic_count (ip text, from_AS text, bps integer, total integer) ''')

        self.db.commit()

    def __del__(self, ):
        with lock():
            self.db.close()

    def add_or_update(self, key, total, interval):
        old_record = self.get(key)
        
        if old_record is None:
            self.add(key, 0, total)
        else:
            #FIXME: The total field might soon overflow.

            old_total = old_record['total']
            bps = (old_total - total) / interval
            self.update(key, bps, total)
            

    def add(self, key, bps, total):

        with lock():
            cursor = self.db.cursor()

            cursor.execute('''insert into traffic_count (ip, from_AS, bps, total) values(?,?,?,?)''', 
                        (key[0], key[1], bps, total))
            self.commit()

    def add_many(self,items):
        with lock():
            cursor = self.db.cursor()

            if (isinstance(items,list)):
                cursor.execute('''insert into traffic_count (ip, from_AS, bps, total) values(?,?,?,?)''', items)
                self.commit()

    def get(self,key): 
        with lock():
            cursor = self.db.cursor()
            cursor.execute('''select * from traffic_count where ip = ? and from_AS = ?''', (key[0], key[1]))

            return cursor.fetchone()

    def get_all(self): 

        with lock():    
            cursor = self.db.cursor()

            cursor.execute('''select * from traffic_count''')

            return cursor.fetchall()

    def update(self,key,bps,total):

        with lock():
            cursor = self.db.cursor()

            script = "update traffic_count set bps = " + str(bps) + ", total = " + str(total) + " where ip = '" + key[0] + "' and from_AS = '" + key[1] + "'"

            cursor.execute(script)
            self.commit()

    def delete(self,key):

        with lock():
            cursor = self.db.cursor()

            cursor.execute('''delete from traffic_count where ip = ? and from_AS = ?''', (key[0],key[1]))

    def delete_all(self):

        with lock():
            cursor = self.db.cursor()

            cursor.execute('''delete from traffic_count''')

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
        count_policy = count_bytes(interval=INTERVAL, group_by=["dstip", "inport"])
        count_policy.register_callback(self.pkt_callback)
        return count_policy


    def pkt_callback(self, pkt):
        for match, byte_count in pkt.iteritems():
            ip = match.map['dstip']
            from_AS = self.__get_AS(match.map['inport'])
            self.add_or_update( (str(ip), str(from_AS)), int(byte_count), INTERVAL)
