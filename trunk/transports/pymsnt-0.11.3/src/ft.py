# Copyright 2005-2006 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

from throttle import Throttler
from twisted.internet import protocol
from twisted.words.xish.domish import Element

import disco
import lang
from debug import LogEvent, INFO, WARN, ERROR
import config
import utils

import random
import sys


def doRateLimit(setConsumer, consumer):
	try:
		rateLimit = int(config.ftRateLimit)
	except ValueError:
		rateLimit = 0
	if rateLimit > 0:
		throttler = Throttler(consumer, rateLimit)
		setConsumer(throttler)
	else:
		setConsumer(consumer)

def checkSizeOk(size):
	try:
		size = int(size)
		limit = int(config.ftSizeLimit)
	except ValueError:
		return False
	if limit == 0:
		return True
	return limit > size

###########
# Sending #
###########

class FTSend:
	""" For file transfers going from Jabber to MSN. """
	def __init__(self, session, to, startTransfer, cancelTransfer, filename, filesize):
		self.startTransfer = startTransfer
		self.cancelTransfer = cancelTransfer
		self.filename = filename
		self.filesize = filesize
		if not checkSizeOk(self.filesize):
			LogEvent(INFO, session.jabberID, "File too large.")
			text = lang.get(session.lang).msnFtSizeRejected % (self.filename, config.ftSizeLimit, config.website)
			session.legacycon.sendMessage(to, "", text, True)
			session.sendMessage(to=session.jabberID, fro=to, body=text)
			self.reject()
			return

		session.legacycon.sendFile(to, self)
	
	def accept(self, legacyFileSend):
		doRateLimit(self.startTransfer, legacyFileSend)
		self.cleanup()
	
	def reject(self):
		self.cancelTransfer()
		self.cleanup()
	
	def cleanup(self):
		del self.startTransfer, self.cancelTransfer


try:
	from twisted.web import http
except ImportError:
	try:
		from twisted.protocols import http
	except ImportError:
		print "Couldn't find http.HTTPClient. If you're using Twisted 2.0, make sure that you've installed twisted.web"
		raise


class OOBHeaderHelper(http.HTTPClient):
	""" Makes a HEAD request and grabs the length """
	def connectionMade(self):
		self.sendCommand("HEAD", self.factory.path.encode("utf-8"))
		self.sendHeader("Host", (self.factory.host + ":" + str(self.factory.port)).encode("utf-8"))
		self.endHeaders()
	
	def handleEndHeaders(self):
		self.factory.gotLength(self.length)
	
	def handleResponse(self, data):
		pass


class OOBSendConnector(http.HTTPClient):
	def connectionMade(self):
		self.sendCommand("GET", self.factory.path.encode("utf-8"))
		self.sendHeader("Host", (self.factory.host + ":" + str(self.factory.port)).encode("utf-8"))
		self.endHeaders()
		self.first = True
	
	def handleResponsePart(self, data):
		self.factory.consumer.write(data)
	
	def handleResponseEnd(self):
		# This is called once before writing is finished, and once when the
		# connection closes. We only consumer.close() on the second.
		if self.first:
			self.first = False
		else:
			self.factory.consumer.close()
			self.factory.consumer = None
			self.factory.finished()





#############
# Receiving #
#############

class FTReceive:
	""" For file transfers going from MSN to Jabber. """

	"""
	Plan of action for this class:
	* Determine the FT support of the Jabber client.
	* If we find a common protocol, then send the invitation.
	* Tell the legacyftp object the result of the invitation.
	* If it was accepted, then start the transfer.

	"""

	def __init__(self, session, senderJID, legacyftp):
		if not checkSizeOk(legacyftp.filesize):
			LogEvent(INFO, session.jabberID, "File too large.")
			legacyftp.reject()
			text = lang.get(session.lang).msnFtSizeRejected % (legacyftp.filename, config.ftSizeLimit, config.website)
			session.legacycon.sendMessage(senderJID, "", text, False)
			session.sendMessage(to=session.jabberID, fro=senderJID, body=text)
			return
		self.session = session
		self.toJID = self.session.jabberID + "/" + self.session.highestResource()
		self.senderJID = senderJID
		self.ident = (self.toJID, self.senderJID)
		self.legacyftp = legacyftp
		LogEvent(INFO, session.jabberID)
		self.checkSupport()
	
	def checkSupport(self):
		def discoDone(features):
			LogEvent(INFO, self.ident)
			enabledS5B = hasattr(self.session.pytrans, "ftSOCKS5Receive")
			enabledOOB = hasattr(self.session.pytrans, "ftOOBReceive")
			hasFT  = features.count(disco.FT)
			hasS5B = features.count(disco.S5B)
			hasOOB = features.count(disco.IQOOB)
			LogEvent(INFO, self.ident, "Choosing transfer mode.")
			if hasFT > 0 and hasS5B > 0 and enabledS5B:
				self.socksMode()
			elif hasOOB > 0 and enabledOOB:
				self.oobMode()
			elif enabledOOB:
				self.messageOobMode()
			else:
				# No support
				self.legacyftp.reject()
				del self.legacyftp

		def discoFail(err=None):
			LogEvent(INFO, self.ident, str(err))
			if hasattr(self.session.pytrans, "ftOOBReceive"):
				self.messageOobMode()
			else:
				# No support
				self.legacyftp.reject()
				del self.legacyftp
		
		d = disco.DiscoRequest(self.session.pytrans, self.toJID).doDisco()
		d.addCallbacks(discoDone, discoFail)
	
	def socksMode(self):
		def ftReply(el):
			if el.getAttribute("type") != "result":
				ftDeclined()
				return
			self.session.pytrans.ftSOCKS5Receive.addConnection(utils.socks5Hash(self.sid, self.senderJID, self.toJID), self.legacyftp)
			LogEvent(INFO, self.ident)
			iq = Element((None, "iq"))
			iq.attributes["type"] = "set"
			iq.attributes["to"] = self.toJID
			iq.attributes["from"] = self.senderJID
			query = iq.addElement("query")
			query.attributes["xmlns"] = disco.S5B
			query.attributes["sid"] = self.sid
			query.attributes["mode"] = "tcp"
			streamhost = query.addElement("streamhost")
			streamhost.attributes["jid"] = self.senderJID
			streamhost.attributes["host"] = config.host
			streamhost.attributes["port"] = config.ftJabberPort
			d = self.session.pytrans.discovery.sendIq(iq)
			d.addErrback(ftDeclined) # Timeout

		def ftDeclined(el):
			self.legacyftp.reject()
			del self.legacyftp
	
		LogEvent(INFO, self.ident)
		self.sid = str(random.randint(1000, sys.maxint))
		iq = Element((None, "iq"))
		iq.attributes["type"] = "set"
		iq.attributes["to"] = self.toJID
		iq.attributes["from"] = self.senderJID
		si = iq.addElement("si")
		si.attributes["xmlns"] = disco.SI
		si.attributes["profile"] = disco.FT
		si.attributes["id"] = self.sid
		file = si.addElement("file")
		file.attributes["xmlns"] = disco.FT
		file.attributes["size"] = str(self.legacyftp.filesize)
		file.attributes["name"] = self.legacyftp.filename
		# Feature negotiation
		feature = si.addElement("feature")
		feature.attributes["xmlns"] = disco.FEATURE_NEG
		x = feature.addElement("x")
		x.attributes["xmlns"] = disco.XDATA
		x.attributes["type"] = "form"
		field = x.addElement("field")
		field.attributes["type"] = "list-single"
		field.attributes["var"] = "stream-method"
		option = field.addElement("option")
		value = option.addElement("value")
		value.addContent(disco.S5B)
		d = self.session.pytrans.discovery.sendIq(iq, 60*3)
		d.addCallback(ftReply)
		d.addErrback(ftDeclined)

	def oobMode(self):
		def cb(el):
			if el.getAttribute("type") != "result":
				self.legacyftp.reject()
			del self.legacyftp
			self.session.pytrans.ftOOBReceive.remFile(filename)

		def ecb(ignored=None):
			self.legacyftp.reject()
			del self.legacyftp
	
		LogEvent(INFO, self.ident)
		filename = self.session.pytrans.ftOOBReceive.putFile(self, self.legacyftp.filename)
		iq = Element((None, "iq"))
		iq.attributes["to"] = self.toJID
		iq.attributes["from"] = self.senderJID
		query = m.addElement("query")
		query.attributes["xmlns"] = disco.IQOOB
		query.addElement("url").addContent(config.ftOOBRoot + "/" + filename)
		d = self.session.send(iq)
		d.addCallbacks(cb, ecb)

	def messageOobMode(self):
		LogEvent(INFO, self.ident)
		filename = self.session.pytrans.ftOOBReceive.putFile(self, self.legacyftp.filename)
		m = Element((None, "message"))
		m.attributes["to"] = self.session.jabberID
		m.attributes["from"] = self.senderJID
		m.addElement("body").addContent(config.ftOOBRoot + "/" + filename)
		x = m.addElement("x")
		x.attributes["xmlns"] = disco.XOOB
		x.addElement("url").addContent(config.ftOOBRoot + "/" + filename)
		self.session.pytrans.send(m)

	def error(self, ignored=None):
		# FIXME
		LogEvent(WARN)
		


# SOCKS5

import socks5
import struct

class JEP65ConnectionSend(protocol.Protocol):
# TODO, clean up and move this to socks5
	STATE_INITIAL = 1
	STATE_WAIT_AUTHOK = 2
	STATE_WAIT_CONNECTOK = 3
	STATE_READY = 4

	def __init__(self):
		self.state = self.STATE_INITIAL
		self.buf = ""
	
	def connectionMade(self):
		self.transport.write(struct.pack("!BBB", 5, 1, 0))
		self.state = self.STATE_WAIT_AUTHOK
	
	def connectionLost(self, reason):
		if self.state == self.STATE_READY:
			self.factory.consumer.close()
		else:
			self.factory.consumer.error()
	
	def _waitAuthOk(self):
		ver, method = struct.unpack("!BB", self.buf[:2])
		if ver != 5 or method != 0:
			self.transport.loseConnection()
			return
		self.buf = self.buf[2:] # chop
		
		# Send CONNECT request
		length = len(self.factory.hash)
		self.transport.write(struct.pack("!BBBBB", 5, 1, 0, 3, length))
		self.transport.write("".join([struct.pack("!B" , ord(x))[0] for x in self.factory.hash]))
		self.transport.write(struct.pack("!H", 0))
		self.state = self.STATE_WAIT_CONNECTOK
	
	def _waitConnectOk(self):
		ver, rep, rsv, atyp = struct.unpack("!BBBB", self.buf[:4])
		if not (ver == 5 and rep == 0):
			self.transport.loseConnection()
			return
		
		self.state = self.STATE_READY
		self.factory.madeConnection(self.transport.addr[0])
	
	def dataReceived(self, buf):
		if self.state == self.STATE_READY:
			self.factory.consumer.write(buf)

		self.buf += buf
		if self.state == self.STATE_WAIT_AUTHOK:
			self._waitAuthOk()
		elif self.state == self.STATE_WAIT_CONNECTOK:
			self._waitConnectOk()
		

class JEP65ConnectionReceive(socks5.SOCKSv5):
	def __init__(self, listener):
		socks5.SOCKSv5.__init__(self)
		self.listener = listener
		self.supportedAuthMechs = [socks5.AUTHMECH_ANON]
		self.supportedAddrs = [socks5.ADDR_DOMAINNAME]
		self.enabledCommands = [socks5.CMD_CONNECT]
		self.addr = ""
	
	def connectRequested(self, addr, port):
		# So that the legacyftp can close the connection
		self.transport.close = self.transport.loseConnection
	
		# Check for special connect to the namespace -- this signifies that
		# the client is just checking that it can connect to the streamhost
		if addr == disco.S5B:
			self.connectCompleted(addr, 0)
			self.transport.loseConnection()
			return

		self.addr = addr

		if self.listener.isActive(addr):
			self.sendErrorReply(socks5.REPLY_CONN_NOT_ALLOWED)
			return

		if self.listener.addConnection(addr, self):
			self.connectCompleted(addr, 0)
		else:
			self.sendErrorReply(socks5.REPLY_CONN_REFUSED)

	def connectionLost(self, reason):
		if self.state == socks5.STATE_CONNECT_PENDING:
			self.listener.removePendingConnection(self.addr, self)
		else:
			self.transport.unregisterProducer()
			if self.peersock != None:
				self.peersock.peersock = None
				self.peersock.transport.unregisterProducer()
				self.peersock = None
				self.listener.removeActiveConnection(self.addr)

class Proxy65(protocol.Factory):
	def __init__(self, port):
		LogEvent(INFO)
		reactor.listenTCP(port, self)
		self.pendingConns = {}
		self.activeConns = {}
	
	def buildProtocol(self, addr):
		return JEP65ConnectionReceive(self)
	
	def isActive(self, address):
		return address in self.activeConns
	
	def activateStream(self, address):
		if address in self.pendingConns:
			olist = self.pendingConns[address]
			if len(olist) != 2:
				LogEvent(WARN, '', "Not exactly two!")
				return

			assert address not in self.activeConns
			self.activeConns[address] = None
			
			if not isinstance(olist[0], JEP65ConnectionReceive):
				legacyftp = olist[0]
				connection = olist[1]
			elif not isinstance(olist[1], JEP65ConnectionReceive):
				legacyftp = olist[1]
				connection = olist[0]
			else:
				LogEvent(WARN, '', "No JEP65Connection")
				return

			doRateLimit(legacyftp.accept, connection.transport)
		else:
			LogEvent(WARN, '', "No pending connection.")
	
	def addConnection(self, address, connection):
		olist = self.pendingConns.get(address, [])
		if len(olist) <= 1:
			olist.append(connection)
			self.pendingConns[address] = olist
			if len(olist) == 2:
				self.activateStream(address)
			return True
		else:
			return False
	
	def removePendingConnection(self, address, connection):
		olist = self.pendingConns[address]
		if len(olist) == 1:
			del self.pendingConns[address]
		else:
			olist.remove(connection)
	
	def removeActiveConnection(self, address):
		del self.activeConns[address]


# OOB download server

from twisted.web import server, resource, error
from twisted.internet import reactor

from debug import LogEvent, INFO, WARN, ERROR

class OOBReceiveConnector:
	def __init__(self, ftReceive, ftHttpPush):
		self.ftReceive, self.ftHttpPush = ftReceive, ftHttpPush
		doRateLimit(self.ftReceive.legacyftp.accept, self)
	
	def write(self, data):
		self.ftHttpPush.write(data)
	
	def close(self):
		self.ftHttpPush.finish()
	
	def error(self):
		self.ftHttpPush.finish()
		self.ftReceive.error()

class FileTransferOOBReceive(resource.Resource):
	def __init__(self, port):
		LogEvent(INFO)
		self.isLeaf = True
		self.files = {}
		self.oobSite = server.Site(self)
		reactor.listenTCP(port, self.oobSite)

	def putFile(self, file, filename):
		path = str(random.randint(100000000, 999999999))
		filename = (path + "/" + filename).replace("//", "/")
		self.files[filename] = file
		return filename
	
	def remFile(self, filename):
		if self.files.has_key(filename):
			del self.files[filename]
	
	def render_GET(self, request):
		filename = request.path[1:] # Remove the leading /
		if self.files.has_key(filename):
			file = self.files[filename]
			request.setHeader("Content-Length", str(file.legacyftp.filesize))
			request.setHeader("Content-Disposition", "attachment; filename=\"%s\"" % file.legacyftp.filename.encode("utf-8"))
			OOBReceiveConnector(file, request)
			del self.files[filename]
			return server.NOT_DONE_YET
		else:
			page = error.NoResource(message="404 File Not Found")
			return page.render(request)
	
	def render_HEAD(self, request):
		filename = request.path[1:] # Remove the leading /
		if self.files.has_key(filename):
			file = self.files[filename]
			request.setHeader("Content-Length", str(file.legacyftp.filesize))
			request.setHeader("Content-Disposition", "attachment; filename=\"%s\"" % file.legacyftp.filename.encode("utf-8"))
			return ""
		else:
			page = error.NoResource(message="404 File Not Found")
			return page.render(request)


