# Copyright 2004-2006 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
from twisted.words.xish.domish import Element
from twisted.words.protocols.jabber.jid import internJID
from debug import LogEvent, INFO, WARN, ERROR
import disco
import session
import config
import lang
import jabw
import legacy
import re

class RegisterManager:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		if config.allowRegister:
			self.pytrans.discovery.addFeature(disco.IQREGISTER, self.incomingRegisterIq, config.jid)
		LogEvent(INFO)
	
	def removeRegInfo(self, jabberID):
		LogEvent(INFO)
		try:
			# If the session is active then send offline presences
			session = self.pytrans.sessions[jabberID]
			session.removeMe()
		except KeyError:
			pass
		
		self.pytrans.xdb.remove(jabberID)
		LogEvent(INFO, "", "done")
	
	
	def setRegInfo(self, jabberID, username, password):
		LogEvent(INFO)
		if(len(password) == 0):
			(blah1, password, blah3) = self.getRegInfo(jabberID)
		
		reginfo = legacy.formRegEntry(username, password)
		self.pytrans.xdb.set(internJID(jabberID).userhost(), legacy.namespace, reginfo)
	
	def getRegInfo(self, jabberID):
		LogEvent(INFO)
		result = self.pytrans.xdb.request(internJID(jabberID).userhost(), legacy.namespace)
		if(result == None):
			LogEvent(INFO, "", "Not registered!")
			return None
		
		username, password = legacy.getAttributes(result)
		
		if(username and password and len(username) > 0 and len(password) > 0):
			LogEvent(INFO, "", "Returning reg info.")
			return (username, password)
		else:
			LogEvent(WARN, "", "Registration data corrupted!")
			return None
	
	def incomingRegisterIq(self, incoming):
		# Check what type the Iq is..
		itype = incoming.getAttribute("type")
		LogEvent(INFO)
		if(itype == "get"):
			self.sendRegistrationFields(incoming)
		elif(itype == "set"):
			self.updateRegistration(incoming)
		
	def sendRegistrationFields(self, incoming):
		# Construct a reply with the fields they must fill out
		ID = incoming.getAttribute("id")
		fro = incoming.getAttribute("from")
		LogEvent(INFO)
		reply = Element((None, "iq"))
		reply.attributes["from"] = config.jid
		reply.attributes["to"] = fro
		if ID:
			reply.attributes["id"] = ID
		reply.attributes["type"] = "result"
		query = reply.addElement("query")
		query.attributes["xmlns"] = "jabber:iq:register"
		instructions = query.addElement("instructions")
		ulang = utils.getLang(incoming)
		instructions.addContent(lang.get(ulang).registerText)
		userEl = query.addElement("username")
		passEl = query.addElement("password")
		
		# Check to see if they're registered
		result = self.getRegInfo(incoming.getAttribute("from"))
		if(result):
			username, password = result
			userEl.addContent(username)
			query.addElement("registered")
		
		self.pytrans.send(reply)
	
	def updateRegistration(self, incoming):
		# Grab the username, password
		ID = incoming.getAttribute("id")
		fro = incoming.getAttribute("from")
		LogEvent(INFO)
		source = internJID(fro).userhost()
		ulang = utils.getLang(incoming)
		username = None
		password = None
		
		for queryFind in incoming.elements():
			if(queryFind.name == "query"):
				for child in queryFind.elements():
					try:
						if(child.name == "username"):
							username = child.__str__()
						elif(child.name == "password"):
							password = child.__str__()
						elif(child.name == "remove"):
							# The user wants to unregister the transport! Gasp!
							LogEvent(INFO, "", "Unregistering.")
							try:
								self.removeRegInfo(source)
								self.successReply(incoming)
							except:
								self.xdbErrorReply(incoming)
								return
							LogEvent(INFO, "", "Unregistered!")
							return
					except AttributeError, TypeError:
						continue # Ignore any errors, we'll check everything below
		
		if(self.isValid(username) and password and len(username) > 0 and len(password) > 0):
			# Valid registration data
			LogEvent(INFO, "", "Updating XDB")
			try:
				self.setRegInfo(source, username, password)
				LogEvent(INFO, "", "Updated XDB")
				self.successReply(incoming)
				LogEvent(INFO, "", "Sent a result Iq")
				to = internJID(incoming.getAttribute("from")).userhost()
				jabw.sendPresence(self.pytrans, to=to, fro=config.jid, ptype="subscribe")
				if(config.registerMessage):
					jabw.sendMessage(self.pytrans, to=incoming.getAttribute("from"), fro=config.jid, body=config.registerMessage)
			except:
				self.xdbErrorReply(incoming)
				raise
		
		else:
			self.badRequestReply(incoming)

	def isValid(self, string):
		f = open('/tmp/REGUSER', "a")
		f.write(string)
		f.close()

		pattern = '([a-zA-Z0-9])*@(([a-zA-Z0-9])*(\.)*)*\Z'
		if re.match(pattern, string):
			return True
		else:
			return False		

	def badRequestReply(self, incoming):
		LogEvent(INFO)
		# Invalid registration data was sent to us. Or the removal failed
		# Send an error Iq
		reply = incoming
		reply.swapAttributeValues("to", "from")
		reply.attributes["type"] = "error"
		error = reply.addElement("error")
		error.attributes["type"] = "modify"
		interror = error.addElement("bad-request")
		interror["xmlns"] = disco.XMPP_STANZAS
		self.pytrans.send(reply)
	
	def xdbErrorReply(self, incoming):
		LogEvent(INFO)
		# Failure in updating XDB or sending result Iq
		# send an error Iq
		reply = incoming
		reply.swapAttributeValues("to", "from")
		reply.attributes["type"] = "error"
		error = reply.addElement("error")
		error.attributes["type"] = "wait"
		interror = error.addElement("internal-server-error")
		interror["xmlns"] = disco.XMPP_STANZAS
		self.pytrans.send(reply)
	
	def successReply(self, incoming):
		reply = Element((None, "iq"))
		reply.attributes["type"] = "result"
		ID = incoming.getAttribute("id")
		if(ID): reply.attributes["id"] = ID
		reply.attributes["from"] = config.jid
		reply.attributes["to"] = incoming.getAttribute("from")
		self.pytrans.send(reply)

