# encoding: utf-8
"""
operational/__init__.py

Created by Thomas Mangin on 2013-09-01.
Copyright (c) 2009-2013 Exa Networks. All rights reserved.
"""

from struct import pack,unpack

from exabgp.protocol.family import AFI,SAFI
from exabgp.bgp.message.open.routerid import RouterID
from exabgp.bgp.message import Message

# =================================================================== Operational

MAX_ADVISORY = 2048  # 2K

class Type (int):
	def pack (self):
		return pack('!H',self)

	def extract (self):
		return [pack('!H',self)]

	def __len__ (self):
		return 2

	def __str__ (self):
		pass

class OperationalType:
	# ADVISE
	ADM  = 0x01  # 01: Advisory Demand Message
	ASM  = 0x02  # 02: Advisory Static Message
	# STATE
	RPCQ = 0x03  # 03: Reachable Prefix Count Request
	RPCP = 0x04  # 04: Reachable Prefix Count Reply
	APCQ = 0x05  # 05: Adj-Rib-Out Prefix Count Request
	APCP = 0x06  # 06: Adj-Rib-Out Prefix Count Reply
	LPCQ = 0x07  # 07: BGP Loc-Rib Prefix Count Request
	LPCP = 0x08  # 08: BGP Loc-Rib Prefix Count Reply
	SSQ  = 0x09  # 09: Simple State Request
	# DUMP
	DUP  = 0x0A  # 10: Dropped Update Prefixes
	MUP  = 0x0B  # 11: Malformed Update Prefixes
	MUD  = 0x0C  # 12: Malformed Update Dump
	SSP  = 0x0D  # 13: Simple State Response
	# CONTROL
	MP   = 0xFFFE  # 65534: Max Permitted
	NS   = 0xFFFF  # 65535: Not Satisfied

class Operational (Message):
	TYPE = chr(0x06)  # next free Message Type, as IANA did not assign one yet.
	has_family = False
	has_routerid = False
	is_fault = False

	def __init__ (self,what):
		Message.__init__(self)
		self.what = Type(what)

	def _message (self,data):
		return Message._message(self,"%s%s%s" % (
			self.what.pack(),
			pack('!H',len(data)),
			data
		))

	def __str__ (self):
		return self.extensive()

	def extensive (self):
		return 'operational %s' % self.name

class OperationalFamily (Operational):
	has_family = True

	def __init__ (self,what,afi,safi,data=''):
		Operational.__init__(self,what)
		self.afi = AFI(afi)
		self.safi = SAFI(afi)
		self.data = data

	def family (self):
		return (self.afi,self.safi)

	def _message (self,data):
		return Operational._message(self,"%s%s%s" % (
			self.afi.pack(),
			self.safi.pack(),
			data
		))

	def message (self,negotiated):
		return self._message(self.data)


class SequencedOperationalFamily (OperationalFamily):
	__sequence_number = {}
	has_routerid = True

	def __init__ (self,what,afi,safi,routerid,sequence,data=''):
		OperationalFamily.__init__(self,what,afi,safi,data)
		self.routerid = routerid if routerid else None
		self.sequence = sequence if sequence else None
		self._sequence = self.sequence
		self._routerid = self.routerid

	def message (self,negotiated):
		self.sent_routerid = self.routerid if self.routerid else negotiated.sent_open.router_id
		if self.sequence is None:
			self.sent_sequence = (self.__sequence_number.setdefault(self.routerid,0) + 1) % 0xFFFFFFFF
			self.__sequence_number[self.sent_routerid] = self.sent_sequence
		else:
			self.sent_sequence = self.sequence

		return self._message("%s%s%s" % (
			self.sent_routerid.pack(),pack('!L',self.sent_sequence),
			self.data
		))


class NS:
	MALFORMED   = 0x01  # Request TLV Malformed
	UNSUPPORTED = 0x02  # TLV Unsupported for this neighbor
	MAXIMUM     = 0x03  # Max query frequency exceeded
	PROHIBITED  = 0x04  # Administratively prohibited
	BUSY        = 0x05  # Busy
	NOTFOUND    = 0x06  # Not Found

	class _NS (OperationalFamily):
		is_fault = True

		def __init__ (self,afi,safi,sequence):
			OperationalFamily.__init__(
				self,
				OperationalType.NS,
				afi,safi,
				'%s%s' % (sequence,self.ERROR_SUBCODE)
			)

		def extensive (self):
			return 'operational NS %s %s/%s' % (self.name,self.afi,self.safi)


	class Malformed (_NS):
		name = 'NS malformed'
		ERROR_SUBCODE = '\x00\x01'  # pack('!H',MALFORMED)

	class Unsupported (_NS):
		name = 'NS unsupported'
		ERROR_SUBCODE = '\x00\x02'  # pack('!H',UNSUPPORTED)

	class Maximum (_NS):
		name = 'NS maximum'
		ERROR_SUBCODE = '\x00\x03'  # pack('!H',MAXIMUM)

	class Prohibited (_NS):
		name = 'NS prohibited'
		ERROR_SUBCODE = '\x00\x04'  # pack('!H',PROHIBITED)

	class Busy (_NS):
		name = 'NS busy'
		ERROR_SUBCODE = '\x00\x05'  # pack('!H',BUSY)

	class NotFound (_NS):
		name = 'NS notfound'
		ERROR_SUBCODE = '\x00\x06'  # pack('!H',NOTFOUND)


class Advisory:
	class _Advisory (OperationalFamily):
		def extensive (self):
			return 'operational %s afi %s safi %s "%s"' % (self.name,self.afi,self.safi,self.data)

	class ADM (_Advisory):
		name = 'ADM'

		def __init__ (self,afi,safi,advisory,routerid=None):
			utf8 = advisory.encode('utf-8')
			if len(utf8) > MAX_ADVISORY:
				utf8 = utf8[:MAX_ADVISORY-3] + '...'.encode('utf-8')
			OperationalFamily.__init__(
				self,OperationalType.ADM,
				afi,safi,
				utf8
			)

	class ASM (_Advisory):
		name = 'ASM'

		def __init__ (self,afi,safi,advisory,routerid=None):
			utf8 = advisory.encode('utf-8')
			if len(utf8) > MAX_ADVISORY:
				utf8 = utf8[:MAX_ADVISORY-3] + '...'.encode('utf-8')
			OperationalFamily.__init__(
				self,OperationalType.ASM,
				afi,safi,
				utf8
			)

# a = Advisory.ADM(1,1,'string 1')
# print a.extensive()
# b = Advisory.ASM(1,1,'string 2')
# print b.extensive()


class Query:
	class _Query (SequencedOperationalFamily):
		name = None
		code = None

		def __init__ (self,afi,safi,routerid,sequence):
			SequencedOperationalFamily.__init__(
				self,self.code,
				afi,safi,
				routerid,sequence
			)

		def extensive (self):
			if self._routerid and self._sequence:
				return 'operational %s afi %s safi %s router-id %s sequence %d' % (
					self.name,
					self.afi,self.safi,
					self._routerid,self._sequence,
				)
			return 'operational %s afi %s safi %s' % (self.name,self.afi,self.safi)

	class RPCQ (_Query):
		name = 'RPCQ'
		code = OperationalType.RPCQ

	class APCQ (_Query):
		name = 'APCQ'
		code = OperationalType.APCQ

	class LPCQ (_Query):
		name = 'LPCQ'
		code = OperationalType.LPCQ

class Response:
	class RPCP (SequencedOperationalFamily):
		name = 'RPCP'
		code = OperationalType.RPCP

		def __init__ (self,afi,safi,routerid,sequence,rxc,txc):
			self.rxc = rxc
			self.txc = txc
			SequencedOperationalFamily.__init__(
				self,self.code,
				afi,safi,
				routerid,sequence,
				'%s%s' % (pack('!L',rxc),pack('!L',txc))
			)

		def extensive (self):
			return 'operational %s afi %s safi %s router-id %s sequence %d rxc %d txc %d' % (
				self.name,
				self.afi,self.safi,
				self.routerid,self.sequence,
				self.rxc,self.txc
			)

	class _Counter (SequencedOperationalFamily):
		def __init__ (self,afi,safi,routerid,sequence,counter):
			self.counter = counter
			SequencedOperationalFamily.__init__(
				self,self.code,
				afi,safi,
				routerid,sequence,
				pack('!L',counter)
			)

		def extensive (self):
			if self._routerid and self._sequence:
				return 'operational %s afi %s safi %s router-id %s sequence %d counter %d' % (
					self.name,
					self.afi,self.safi,
					self._routerid,self._sequence,
					self.counter
				)
			return 'operational %s afi %s safi %s counter %d' % (self.name,self.afi,self.safi,self.counter)

	class APCP (_Counter):
		name = 'RPCP'
		code = OperationalType.APCP

	class LPCP (_Counter):
		name = 'RPCP'
		code = OperationalType.LPCP

# c = State.RPCQ(1,1,'82.219.0.1',10)
# print c.extensive()
# d = State.RPCP(1,1,'82.219.0.1',10,10000)
# print d.extensive()

class Dump:
	pass

OperationalGroup = {
	OperationalType.ADM: ('advisory', Advisory.ADM),
	OperationalType.ASM: ('advisory', Advisory.ASM),

	OperationalType.RPCQ: ('query', Query.RPCQ),
	OperationalType.RPCP: ('interface', Response.RPCP),

	OperationalType.APCQ: ('query', Query.APCQ),
	OperationalType.APCP: ('counter', Response.APCP),

	OperationalType.LPCQ: ('query', Query.LPCQ),
	OperationalType.LPCP: ('counter', Response.LPCP),
}

def OperationalFactory (data):
	what = Type(unpack('!H',data[0:2])[0])
	length = unpack('!H',data[2:4])[0]

	decode,klass = OperationalGroup.get(what,('unknown',None))

	if decode == 'advisory':
		afi = unpack('!H',data[4:6])[0]
		safi = ord(data[6])
		data = data[7:length+4]
		return klass(afi,safi,data)
	elif decode == 'query':
		afi = unpack('!H',data[4:6])[0]
		safi = ord(data[6])
		routerid = RouterID('.'.join(str(ord(_)) for _ in data[7:11]))
		sequence = unpack('!L',data[11:15])[0]
		return klass(afi,safi,routerid,sequence)
	elif decode == 'counter':
		afi = unpack('!H',data[4:6])[0]
		safi = ord(data[6])
		routerid = RouterID('.'.join(str(ord(_)) for _ in data[7:11]))
		sequence = unpack('!L',data[11:15])[0]
		counter = unpack('!L',data[15:19])[0]
		return klass(afi,safi,routerid,sequence,counter)
	elif decode == 'interface':
		afi = unpack('!H',data[4:6])[0]
		safi = ord(data[6])
		routerid = RouterID('.'.join(str(ord(_)) for _ in data[7:11]))
		sequence = unpack('!L',data[11:15])[0]
		rxc = unpack('!L',data[15:19])[0]
		txc = unpack('!L',data[19:23])[0]
		return klass(afi,safi,routerid,sequence,rxc,txc)
	else:
		print 'ignoring ATM this kind of message'
