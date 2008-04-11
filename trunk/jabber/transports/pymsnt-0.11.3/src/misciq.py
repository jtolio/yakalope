# Copyright 2004-2005 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
from twisted.internet import reactor, task, protocol, error
from twisted.words.xish.domish import Element
from twisted.words.protocols.jabber.jid import internJID
from debug import LogEvent, INFO, WARN, ERROR
import jabw
import legacy
import disco
import config
import lang
import ft
import base64
import sys, urllib


class ConnectUsers:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.adHocCommands.addCommand("connectusers", self.incomingIq, "command_ConnectUsers")
	
	def sendProbes(self):
		for jid in self.pytrans.xdb.files():
			jabw.sendPresence(self.pytrans, jid, config.jid, ptype="probe")
	
	def incomingIq(self, el):
		to = el.getAttribute("from")
		ID = el.getAttribute("id")
		ulang = utils.getLang(el)

		if config.admins.count(internJID(to).userhost()) == 0:
			self.pytrans.discovery.sendIqError(to=to, fro=config.jid, ID=ID, xmlns=disco.COMMANDS, etype="cancel", condition="not-authorized")
			return


		self.sendProbes()
	
		iq = Element((None, "iq"))
		iq.attributes["to"] = to
		iq.attributes["from"] = config.jid
		if(ID):
			iq.attributes["id"] = ID
		iq.attributes["type"] = "result"

		command = iq.addElement("command")
		command.attributes["sessionid"] = self.pytrans.makeMessageID()
		command.attributes["xmlns"] = disco.COMMANDS
		command.attributes["status"] = "completed"

		x = command.addElement("x")
		x.attributes["xmlns"] = disco.XDATA
		x.attributes["type"] = "result"

		title = x.addElement("title")
		title.addContent(lang.get(ulang).command_ConnectUsers)

		field = x.addElement("field")
		field.attributes["type"] = "fixed"
		field.addElement("value").addContent(lang.get(ulang).command_Done)

		self.pytrans.send(iq)


class Statistics:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.adHocCommands.addCommand("stats", self.incomingIq, "command_Statistics")

		# self.stats is indexed by a unique ID, with value being the value for that statistic
		self.stats = {}
		self.stats["Uptime"] = 0
		self.stats["OnlineUsers"] = 0
		self.stats["TotalUsers"] = 0

		legacy.startStats(self)

	def incomingIq(self, el):
		to = el.getAttribute("from")
		ID = el.getAttribute("id")
		ulang = utils.getLang(el)

		iq = Element((None, "iq"))
		iq.attributes["to"] = to
		iq.attributes["from"] = config.jid
		if(ID):
			iq.attributes["id"] = ID
		iq.attributes["type"] = "result"

		command = iq.addElement("command")
		command.attributes["sessionid"] = self.pytrans.makeMessageID()
		command.attributes["xmlns"] = disco.COMMANDS
		command.attributes["status"] = "completed"

		x = command.addElement("x")
		x.attributes["xmlns"] = disco.XDATA
		x.attributes["type"] = "result"

		title = x.addElement("title")
		title.addContent(lang.get(ulang).command_Statistics)

		for key in self.stats:
			label = getattr(lang.get(ulang), "command_%s" % key)
			description = getattr(lang.get(ulang), "command_%s_Desc" % key)
			field = x.addElement("field")
			field.attributes["var"] = key
			field.attributes["label"] = label
			field.attributes["type"] = "text-single"
			field.addElement("value").addContent(str(self.stats[key]))
			field.addElement("desc").addContent(description)

		self.pytrans.send(iq)
		
		

class AdHocCommands:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.discovery.addFeature(disco.COMMANDS, self.incomingIq, config.jid)
		self.pytrans.discovery.addNode(disco.COMMANDS, self.sendCommandList, "command_CommandList", config.jid, True)

		self.commands = {} # Dict of handlers indexed by node
		self.commandNames = {} # Dict of names indexed by node
	
	def addCommand(self, command, handler, name):
		self.commands[command] = handler
		self.commandNames[command] = name
		self.pytrans.discovery.addNode(command, self.incomingIq, name, config.jid, False)
	
	def incomingIq(self, el):
		itype = el.getAttribute("type")
		fro = el.getAttribute("from")
		froj = internJID(fro)
		to = el.getAttribute("to")
		ID = el.getAttribute("id")

		LogEvent(INFO, "", "Looking for handler")

		node = None
		for child in el.elements():
			xmlns = child.uri
			node = child.getAttribute("node")

			handled = False
			if(child.name == "query" and xmlns == disco.DISCO_INFO):
				if(node and self.commands.has_key(node) and (itype == "get")):
					self.sendCommandInfoResponse(to=fro, ID=ID)
					handled = True
			elif(child.name == "query" and xmlns == disco.DISCO_ITEMS):
				if(node and self.commands.has_key(node) and (itype == "get")):
					self.sendCommandItemsResponse(to=fro, ID=ID)
					handled = True
			elif(child.name == "command" and xmlns == disco.COMMANDS):
				if((node and self.commands.has_key(node)) and (itype == "set" or itype == "error")):
					self.commands[node](el)
					handled = True
			if(not handled):
				LogEvent(WARN, "", "Unknown Ad-Hoc command received.")
				self.pytrans.discovery.sendIqError(to=fro, fro=config.jid, ID=ID, xmlns=xmlns, etype="cancel", condition="feature-not-implemented")
		
	
	def sendCommandList(self, el):
		to = el.getAttribute("from")
		ID = el.getAttribute("id")
		ulang = utils.getLang(el)

		iq = Element((None, "iq"))
		iq.attributes["to"] = to
		iq.attributes["from"] = config.jid
		if ID:
			iq.attributes["id"] = ID
		iq.attributes["type"] = "result"

		query = iq.addElement("query")
		query.attributes["xmlns"] = disco.DISCO_ITEMS
		query.attributes["node"] = disco.COMMANDS

		for command in self.commands:
			item = query.addElement("item")
			item.attributes["jid"] = config.jid
			item.attributes["node"] = command
			item.attributes["name"] = getattr(lang.get(ulang), self.commandNames[command])

		self.pytrans.send(iq)

	def sendCommandInfoResponse(self, to, ID):
		LogEvent(INFO, "", "Replying to disco#info")
		iq = Element((None, "iq"))
		iq.attributes["type"] = "result"
		iq.attributes["from"] = config.jid
		iq.attributes["to"] = to
		if(ID): iq.attributes["id"] = ID
		query = iq.addElement("query")
		query.attributes["xmlns"] = disco.DISCO_INFO

		feature = query.addElement("feature")
		feature.attributes["var"] = disco.COMMANDS
		self.pytrans.send(iq)

	def sendCommandItemsResponse(self, to, ID):
		LogEvent(INFO, "", "Replying to disco#items")
		iq = Element((None, "iq"))
		iq.attributes["type"] = "result"
		iq.attributes["from"] = config.jid
		iq.attributes["to"] = to
		if(ID): iq.attributes["id"] = ID
		query = iq.addElement("query")
		query.attributes["xmlns"] = disco.DISCO_ITEMS
		self.pytrans.send(iq)


class VCardFactory:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.discovery.addFeature("vcard-temp", self.incomingIq, "USER")
		self.pytrans.discovery.addFeature("vcard-temp", self.incomingIq, config.jid)
	
	def incomingIq(self, el):
		itype = el.getAttribute("type")
		fro = el.getAttribute("from")
		froj = internJID(fro)
		to = el.getAttribute("to")
		toj = internJID(to)
		ID = el.getAttribute("id")
		if itype != "get" and itype != "error":
			self.pytrans.discovery.sendIqError(to=fro, fro=config.jid, ID=ID, xmlns="vcard-temp", etype="cancel", condition="feature-not-implemented")
			return

		LogEvent(INFO, "", "Sending vCard")

		toGateway = not (to.find('@') > 0)

		if not toGateway:
			if not self.pytrans.sessions.has_key(froj.userhost()):
				self.pytrans.discovery.sendIqError(to=fro, fro=config.jid, ID=ID, xmlns="vcard-temp", etype="auth", condition="not-authorized")
				return
			s = self.pytrans.sessions[froj.userhost()]
			if not s.ready:
				self.pytrans.discovery.sendIqError(to=fro, fro=config.jid, ID=ID, xmlns="vcard-temp", etype="auth", condition="not-authorized")
				return
		
			c = s.contactList.findContact(toj.userhost())
			if not c:
				self.pytrans.discovery.sendIqError(to=fro, fro=config.jid, ID=ID, xmlns="vcard-temp", etype="cancel", condition="recipient-unavailable")
				return


		iq = Element((None, "iq"))
		iq.attributes["to"] = fro
		iq.attributes["from"] = to
		if ID:
			iq.attributes["id"] = ID
		iq.attributes["type"] = "result"
		vCard = iq.addElement("vCard")
		vCard.attributes["xmlns"] = "vcard-temp"
		if toGateway:
			FN = vCard.addElement("FN")
			FN.addContent(config.discoName)
			DESC = vCard.addElement("DESC")
			DESC.addContent(config.discoName)
			URL = vCard.addElement("URL")
			URL.addContent(legacy.url)
		else:
			if c.nickname:
				NICKNAME = vCard.addElement("NICKNAME")
				NICKNAME.addContent(c.nickname)
			if c.avatar:
				PHOTO = c.avatar.makePhotoElement()
				vCard.addChild(PHOTO)

		self.pytrans.send(iq)
		
class IqAvatarFactory:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.discovery.addFeature(disco.IQAVATAR, self.incomingIq, "USER")
		self.pytrans.discovery.addFeature(disco.STORAGEAVATAR, self.incomingIq, "USER")

	def incomingIq(self, el):
		itype = el.getAttribute("type")
		fro = el.getAttribute("from")
		froj = internJID(fro)
		to = el.getAttribute("to")
		toj = internJID(to)
		ID = el.getAttribute("id")

		if(itype != "get" and itype != "error"):
			self.pytrans.discovery.sendIqError(to=fro, fro=config.jid, ID=ID, xmlns=disco.IQAVATAR, etype="cancel", condition="feature-not-implemented")
			return

		LogEvent(INFO, "", "Retrieving avatar")

		if(not self.pytrans.sessions.has_key(froj.userhost())):
			self.pytrans.discovery.sendIqError(to=fro, fro=config.jid, ID=ID, xmlns=disco.IQAVATAR, etype="auth", condition="not-authorized")
			return
		s = self.pytrans.sessions[froj.userhost()]
		if(not s.ready):
			self.pytrans.discovery.sendIqError(to=fro, fro=config.jid, ID=ID, xmlns=disco.IQAVATAR, etype="auth", condition="not-authorized")
			return

		c = s.contactList.findContact(toj.userhost())
		if(not c):
			self.pytrans.discovery.sendIqError(to=fro, fro=config.jid, ID=ID, xmlns=disco.IQAVATAR, etype="cancel", condition="recipient-unavailable")
			return

		iq = Element((None, "iq"))
		iq.attributes["to"] = fro
		iq.attributes["from"] = to
		if ID:
			iq.attributes["id"] = ID
		iq.attributes["type"] = "result"
		query = iq.addElement("query")
		query.attributes["xmlns"] = disco.IQAVATAR
		if(c.avatar):
			DATA = c.avatar.makeDataElement()
			query.addChild(DATA)

		self.pytrans.send(iq)



class PingService:
	def __init__(self, pytrans):
		self.pytrans = pytrans
#		self.pingCounter = 0
#		self.pingTask = task.LoopingCall(self.pingCheck)
		self.pingTask = task.LoopingCall(self.whitespace)
#		reactor.callLater(10.0, self.start)
	
#	def start(self):
#		self.pingTask.start(120.0)
	
	def whitespace(self):
		self.pytrans.send(" ")

#	def pingCheck(self):
#		if(self.pingCounter >= 2 and self.pytrans.xmlstream): # Two minutes of no response from the main server
#			LogEvent(WARN, "", "Disconnecting because the main server has ignored our pings for too long.")
#			self.pytrans.xmlstream.transport.loseConnection()
#		elif(config.mainServerJID):
#			d = self.pytrans.discovery.sendIq(self.makePingPacket())
#			d.addCallback(self.pongReceived)
#			d.addErrback(self.pongFailed)
#			self.pingCounter += 1
	
#	def pongReceived(self, el):
#		self.pingCounter = 0
	
#	def pongFailed(self, el):
#		pass
	
#	def makePingPacket(self):
#		iq = Element((None, "iq"))
#		iq.attributes["from"] = config.jid
#		iq.attributes["to"] = config.mainServerJID
#		iq.attributes["type"] = "get"
#		query = iq.addElement("query")
#		query.attributes["xmlns"] = disco.IQVERSION
#		return iq

class GatewayTranslator:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.discovery.addFeature(disco.IQGATEWAY, self.incomingIq, config.jid)
	
	def incomingIq(self, el):
		fro = el.getAttribute("from")
		ID = el.getAttribute("id")
		itype = el.getAttribute("type")
		if(itype == "get"):
			self.sendPrompt(fro, ID, utils.getLang(el))
		elif(itype == "set"):
			self.sendTranslation(fro, ID, el)
	
	
	def sendPrompt(self, to, ID, ulang):
		LogEvent(INFO)
		
		iq = Element((None, "iq"))
		
		iq.attributes["type"] = "result"
		iq.attributes["from"] = config.jid
		iq.attributes["to"] = to
		if ID:
			iq.attributes["id"] = ID
		query = iq.addElement("query")
		query.attributes["xmlns"] = disco.IQGATEWAY
		desc = query.addElement("desc")
		desc.addContent(lang.get(ulang).gatewayTranslator)
		prompt = query.addElement("prompt")
		
		self.pytrans.send(iq)
	
	def sendTranslation(self, to, ID, el):
		LogEvent(INFO)
		
		# Find the user's legacy account
		legacyaccount = None
		for query in el.elements():
			if(query.name == "query"):
				for child in query.elements():
					if(child.name == "prompt"):
						legacyaccount = str(child)
						break
				break
		
		
		if(legacyaccount and len(legacyaccount) > 0):
			LogEvent(INFO, "", "Sending translated account.")
			iq = Element((None, "iq"))
			iq.attributes["type"] = "result"
			iq.attributes["from"] = config.jid
			iq.attributes["to"] = to
			if ID:
				iq.attributes["id"] = ID
			query = iq.addElement("query")
			query.attributes["xmlns"] = disco.IQGATEWAY
			prompt = query.addElement("prompt")
			prompt.addContent(legacy.translateAccount(legacyaccount))
			
			self.pytrans.send(iq)
		
		else:
			self.pytrans.discovery.sendIqError(to, ID, disco.IQGATEWAY)
			self.pytrans.discovery.sendIqError(to=to, fro=config.jid, ID=ID, xmlns=disco.IQGATEWAY, etype="retry", condition="bad-request")



class VersionTeller:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.discovery.addFeature(disco.IQVERSION, self.incomingIq, config.jid)
		self.pytrans.discovery.addFeature(disco.IQVERSION, self.incomingIq, "USER")
		self.version = legacy.version
		self.os = "Python" + ".".join([str(x) for x in sys.version_info[0:3]]) + " - " + sys.platform
	
	def incomingIq(self, el):
		eltype = el.getAttribute("type")
		if(eltype != "get"): return # Only answer "get" stanzas
		
		self.sendVersion(el)
	
	def sendVersion(self, el):
		LogEvent(INFO)
		iq = Element((None, "iq"))
		iq.attributes["type"] = "result"
		iq.attributes["from"] = el.getAttribute("to")
		iq.attributes["to"] = el.getAttribute("from")
		if(el.getAttribute("id")):
			iq.attributes["id"] = el.getAttribute("id")
		query = iq.addElement("query")
		query.attributes["xmlns"] = disco.IQVERSION
		name = query.addElement("name")
		name.addContent(config.discoName)
		version = query.addElement("version")
		version.addContent(self.version)
		os = query.addElement("os")
		os.addContent(self.os)
		
		self.pytrans.send(iq)


class FileTransferOOBSend:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.discovery.addFeature(disco.IQOOB, self.incomingOOB, "USER")
	
	def incomingOOB(self, el):
		ID = el.getAttribute("id")
		def errOut():
			self.pytrans.discovery.sendIqError(to=el.getAttribute("from"), fro=el.getAttribute("to"), ID=ID, xmlns=disco.IQOOB, etype="cancel", condition="feature-not-implemented")

		if el.attributes["type"] != "set":
			return errOut()
		for child in el.elements():
			if child.name == "query":
				query = child
				break
		else:
			return errOut()
		for child in query.elements():
			if child.name == "url":
				url = child.__str__()
				break
		else:
			return errOut()

		froj = internJID(el.getAttribute("from"))
		toj = internJID(el.getAttribute("to"))
		session = self.pytrans.sessions.get(froj.userhost(), None)
		if not session:
			return errOut()
		
		res = utils.getURLBits(url, "http")
		if not res:
			return errOut()
		host, port, path, filename = res
		

		def sendResult():
			iq = Element((None, "iq"))
			iq.attributes["to"] = froj.full()
			iq.attributes["from"] = toj.full()
			iq.attributes["type"] = "result"
			if ID:
				iq.attributes["id"] = ID
			iq.addElement("query").attributes["xmlns"] = "jabber:iq:oob"
			self.pytrans.send(iq)

		def startTransfer(consumer):
			factory = protocol.ClientFactory()
			factory.protocol = ft.OOBSendConnector
			factory.path = path
			factory.host = host
			factory.port = port
			factory.consumer = consumer
			factory.finished = sendResult
			reactor.connectTCP(host, port, factory)

		def doSendFile(length):
			ft.FTSend(session, toj.userhost(), startTransfer, errOut, filename, length)

		# Make a HEAD request to grab the length of data first
		factory = protocol.ClientFactory()
		factory.protocol = ft.OOBHeaderHelper
		factory.path = path
		factory.host = host
		factory.port = port
		factory.gotLength = doSendFile
		reactor.connectTCP(host, port, factory)



class Socks5FileTransfer:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.discovery.addFeature(disco.SI, self.incomingSI, "USER")
		self.pytrans.discovery.addFeature(disco.FT, lambda: None, "USER")
		self.pytrans.discovery.addFeature(disco.S5B, self.incomingS5B, "USER")
		self.sessions = {}
	
	def incomingSI(self, el):
		ID = el.getAttribute("id")
		def errOut():
			self.pytrans.discovery.sendIqError(to=el.getAttribute("from"), fro=el.getAttribute("to"), ID=ID, xmlns=disco.SI, etype="cancel", condition="bad-request")

		toj = internJID(el.getAttribute("to"))
		froj = internJID(el.getAttribute("from"))
		session = self.pytrans.sessions.get(froj.userhost(), None)
		if not session:
			return errOut()

		si = el.si
		if not (si and si.getAttribute("profile") == disco.FT):
			return errOut()
		file = si.file
		if not (file and file.uri == disco.FT):
			return errOut()
		try:
			sid = si["id"]
			filename = file["name"]
			filesize = int(file["size"])
		except KeyError:
			return errOut()
		except ValueError:
			return errOut()

		# Check that we can use socks5 bytestreams
		feature = si.feature
		if not (feature and feature.uri == disco.FEATURE_NEG):
			return errOut()
		x = feature.x
		if not (x and x.uri == disco.XDATA):
			return errOut()
		field = x.field
		if not (field and field.getAttribute("var") == "stream-method"):
			return errOut()
		for option in field.elements():
			value = option.value
			if not value:
				continue
			value = value.__str__()
			if value == disco.S5B:
				break
		else:
			return errOut() # Socks5 bytestreams not supported :(


		def startTransfer(consumer):
			iq = Element((None, "iq"))
			iq["type"] = "result"
			iq["to"] = froj.full()
			iq["from"] = toj.full()
			iq["id"] = ID
			si = iq.addElement("si")
			si["xmlns"] = disco.SI
			feature = si.addElement("feature")
			feature["xmlns"] = disco.FEATURE_NEG
			x = feature.addElement("x")
			x["xmlns"] = disco.XDATA
			x["type"] = "submit"
			field = x.addElement("field")
			field["var"] = "stream-method"
			value = field.addElement("value")
			value.addContent(disco.S5B)
			self.pytrans.send(iq)
			self.sessions[(froj.full(), sid)] = consumer

		ft.FTSend(session, toj.userhost(), startTransfer, errOut, filename, filesize)
	
	def incomingS5B(self, el):
		ID = el.getAttribute("id")
		def errOut():
			self.pytrans.discovery.sendIqError(to=el.getAttribute("from"), fro=el.getAttribute("to"), ID=ID, xmlns=disco.S5B, etype="cancel", condition="item-not-found")

		if el.getAttribute("type") != "set":
			return errOut()

		toj = internJID(el.getAttribute("to"))
		froj = internJID(el.getAttribute("from"))

		query = el.query
		if not (query and query.getAttribute("mode", "tcp") == "tcp"):
			return errOut()
		sid = query.getAttribute("sid")
		consumer = self.sessions.pop((froj.full(), sid), None)
		if not consumer:
			return errOut()
		streamhosts = []
		for streamhost in query.elements():
			if streamhost.name == "streamhost":
				try:
					JID = streamhost["jid"]
					host = streamhost["host"]
					port = int(streamhost["port"])
				except ValueError:
					return errOut()
				except KeyError:
					continue
				streamhosts.append((JID, host, port))


		def gotStreamhost(host):
			for streamhost in streamhosts:
				if streamhost[1] == host:
					jid = streamhost[0]
					break
			else:
				LogEvent(WARN)
				return errOut()

			for connector in factory.connectors:
				# Stop any other connections
				try:
					connector.stopConnecting()
				except error.NotConnectingError:
					pass

			if factory.streamHostTimeout:
				factory.streamHostTimeout.cancel()
				factory.streamHostTimeout = None

			iq = Element((None, "iq"))
			iq["type"] = "result"
			iq["from"] = toj.full()
			iq["to"] = froj.full()
			iq["id"] = ID
			query = iq.addElement("query")
			query["xmlns"] = disco.S5B
			streamhost = query.addElement("streamhost-used")
			streamhost["jid"] = jid
			self.pytrans.send(iq)


		# Try the streamhosts
		LogEvent(INFO)
		factory = protocol.ClientFactory()
		factory.protocol = ft.JEP65ConnectionSend
		factory.consumer = consumer
		factory.hash = utils.socks5Hash(sid, froj.full(), toj.full())
		factory.madeConnection = gotStreamhost
		factory.connectors = []
		factory.streamHostTimeout = reactor.callLater(120, consumer.error)

		for streamhost in streamhosts:
			factory.connectors.append(reactor.connectTCP(streamhost[1], streamhost[2], factory))


