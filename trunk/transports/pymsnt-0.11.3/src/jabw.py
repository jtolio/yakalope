# Copyright 2004-2005 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
from twisted.words.xish.domish import Element
from twisted.words.protocols.jabber.jid import internJID
from debug import LogEvent, INFO, WARN, ERROR
import disco


def sendMessage(pytrans, to, fro, body, mtype=None, delay=None):
	""" Sends a Jabber message """
	LogEvent(INFO)
	el = Element((None, "message"))
	el.attributes["to"] = to
	el.attributes["from"] = fro
	el.attributes["id"] = pytrans.makeMessageID()
	if(mtype):
		el.attributes["type"] = mtype
	
	if(delay):
		x = el.addElement("x")
		x.attributes["xmlns"] = disco.XDELAY
		x.attributes["from"] = fro
		x.attributes["stamp"] = delay
	
	b = el.addElement("body")
	b.addContent(body)
	x = el.addElement("x")
	x.attributes["xmlns"] = disco.XEVENT
	composing = x.addElement("composing")
	pytrans.send(el)

def sendPresence(pytrans, to, fro, show=None, status=None, priority=None, ptype=None, avatarHash=None, nickname=None, payload=[]):
	# Strip the resource off any presence subscribes (as per XMPP RFC 3921 Section 5.1.6)
	# Makes eJabberd behave :)
	if ptype in ("subscribe", "subscribed", "unsubscribe", "unsubscribed"):
		to = internJID(to).userhost()
		fro = internJID(fro).userhost()
	
	el = Element((None, "presence"))
	el.attributes["to"] = to
	el.attributes["from"] = fro
	if(ptype):
		el.attributes["type"] = ptype
	if(show):
		s = el.addElement("show")
		s.addContent(show)
	if(status):
		s = el.addElement("status")
		s.addContent(status)
	if(priority):
		s = el.addElement("priority")
		s.addContent(priority)

	if(not ptype):
		x = el.addElement("x")
		x.attributes["xmlns"] = disco.XVCARDUPDATE
		if(avatarHash):
			xx = el.addElement("x")
			xx.attributes["xmlns"] = disco.XAVATAR
			h = xx.addElement("hash")
			h.addContent(avatarHash)
			h = x.addElement("photo")
			h.addContent(avatarHash)
		if(nickname):
			n = x.addElement("nickname")
			n.addContent(nickname)
	
	if(payload):
		for p in payload:
			el.addChild(p)

	pytrans.send(el)


def sendErrorMessage(pytrans, to, fro, etype, condition, explanation, body=None):
	el = Element((None, "message"))
	el.attributes["to"] = to
	el.attributes["from"] = fro
	el.attributes["type"] = "error"
	error = el.addElement("error")
	error.attributes["type"] = etype
	error.attributes["code"] = str(utils.errorCodeMap[condition])
	desc = error.addElement(condition)
	desc.attributes["xmlns"] = disco.XMPP_STANZAS
	text = error.addElement("text")
	text.attributes["xmlns"] = disco.XMPP_STANZAS
	text.addContent(explanation)
	if(body and len(body) > 0):
		b = el.addElement("body")
		b.addContent(body)
	pytrans.send(el)




class JabberConnection:
	""" A class to handle a Jabber "Connection", ie, the Jabber side of the gateway.
	If you want to send a Jabber event, this is the place, and this is where incoming
	Jabber events for a session come to. """
	
	def __init__(self, pytrans, jabberID):
		self.pytrans = pytrans
		self.jabberID = jabberID

		self.typingUser = False # Whether this user can accept typing notifications
		self.messageIDs = dict() # The ID of the last message the user sent to a particular contact. Indexed by contact JID
		
		LogEvent(INFO, self.jabberID)
	
	def removeMe(self):
		""" Cleanly deletes the object """
		LogEvent(INFO, self.jabberID)
	
	def sendMessage(self, to, fro, body, mtype=None, delay=None):
		""" Sends a Jabber message 
		For this message to have a <x xmlns="jabber:x:delay"/> you must pass a correctly formatted timestamp (See JEP0091)
		"""
		LogEvent(INFO, self.jabberID)
		sendMessage(self.pytrans, to, fro, body, mtype, delay)
	
	def sendTypingNotification(self, to, fro, typing):
		""" Sends the user the contact's current typing notification status """
		if(self.typingUser):
			LogEvent(INFO, self.jabberID)
			el = Element((None, "message"))
			el.attributes["to"] = to
			el.attributes["from"] = fro
			x = el.addElement("x")
			x.attributes["xmlns"] = disco.XEVENT
			if(typing):
				composing = x.addElement("composing") 
			id = x.addElement("id")
			if(self.messageIDs.has_key(fro) and self.messageIDs[fro]):
				id.addContent(self.messageIDs[fro])
			self.pytrans.send(el)
	
	def sendVCardRequest(self, to, fro):
		""" Requests the the vCard of 'to'
		Returns a Deferred which fires when the vCard has been received.
		First argument an Element object of the vCard
		"""
		el = Element((None, "iq"))
		el.attributes["to"] = to
		el.attributes["from"] = fro
		el.attributes["type"] = "get"
		el.attributes["id"] = self.pytrans.makeMessageID()
		vCard = el.addElement("vCard")
		vCard.attributes["xmlns"] = "vcard-temp"
		return self.pytrans.discovery.sendIq(el)
	
	def sendErrorMessage(self, to, fro, etype, condition, explanation, body=None):
		LogEvent(INFO, self.jabberID)
		sendErrorMessage(self.pytrans, to, fro, etype, condition, explanation, body)
	
	def sendPresence(self, to, fro, show=None, status=None, priority=None, ptype=None, avatarHash=None, nickname=None, payload=[]):
		""" Sends a Jabber presence packet """
		LogEvent(INFO, self.jabberID)
		sendPresence(self.pytrans, to, fro, show, status, priority, ptype, avatarHash, nickname, payload)
	
	def sendRosterImport(self, jid, ptype, sub, name="", groups=[]):
		""" Sends a special presence packet. This will work with all clients, but clients that support roster-import will give a better user experience
		IMPORTANT - Only ever use this for contacts that have already been authorised on the legacy service """
		x = Element((None, "x"))
		x.attributes["xmlns"] = disco.SUBSYNC
		item = x.addElement("item")
		item.attributes["subscription"] = sub
		if name:
			item.attributes["name"] = unicode(name)
		for group in groups:
			g = item.addElement("group")
			g.addContent(group)
		
		self.sendPresence(to=self.jabberID, fro=jid, ptype=ptype, payload=[x])
	
	def onMessage(self, el):
		""" Handles incoming message packets """
		#LogEvent(INFO, self.jabberID)
		fro = el.getAttribute("from")
		to = el.getAttribute("to")
		try:
			froj = internJID(fro)
			toj = internJID(to)
		except Exception, e:
			LogEvent(WARN, self.jabberID)
			return

		mID = el.getAttribute("id")
		mtype = el.getAttribute("type")
		body = ""
		inviteTo = ""
		inviteRoom = ""
		messageEvent = False
		noerror = False
		composing = None
		for child in el.elements():
			if(child.name == "body"):
				body = child.__str__()
			elif(child.name == "noerror" and child.uri == "sapo:noerror"):
				noerror = True
			elif(child.name == "x"):
				if(child.uri == disco.XCONFERENCE):
					inviteTo = to
					inviteRoom = child.getAttribute("jid") # The room the contact is being invited to
				elif(child.uri == disco.MUC_USER):
					for child2 in child.elements():
						if(child2.name == "invite"):
							inviteTo = child2.getAttribute("to")
							break
					inviteRoom = to
				elif(child.uri == disco.XEVENT):
					messageEvent = True
					composing = False
					for child2 in child.elements():
						if(child2.name == "composing"):
							composing = True
							break
		
		if(inviteTo and inviteRoom):
			LogEvent(INFO, self.jabberID, "Message groupchat invite packet")
			self.inviteReceived(source=froj.userhost(), resource=froj.resource, dest=inviteTo, destr="", roomjid=inviteRoom)
			return

		# Check message event stuff
		if(body and messageEvent):
			self.typingUser = True
		elif(body and not messageEvent):
			self.typingUser = False
		elif(not body and messageEvent):
			LogEvent(INFO, self.jabberID, "Message typing notification packet")
			self.typingNotificationReceived(toj.userhost(), toj.resource, composing)
			
			
		if(body):
			# Save the message ID for later
			self.messageIDs[to] = mID
			LogEvent(INFO, self.jabberID, "Message packet")
			self.messageReceived(froj.userhost(), froj.resource, toj.userhost(), toj.resource, mtype, body, noerror)
	
	def onPresence(self, el):
		""" Handles incoming presence packets """
		#LogEvent(INFO, self.jabberID)
		fro = el.getAttribute("from")
		froj = internJID(fro)
		to = el.getAttribute("to")
		toj = internJID(to)
		
		# Grab the contents of the <presence/> packet
		ptype = el.getAttribute("type")
		if ptype and (ptype.startswith("subscribe") or ptype.startswith("unsubscribe")):
			LogEvent(INFO, self.jabberID, "Parsed subscription presence packet")
			self.subscriptionReceived(fro, toj.userhost(), ptype)
		else:
			status = None
			show = None
			priority = None
			avatarHash = ""
			nickname = ""
			for child in el.elements():
				if(child.name == "status"):
					status = child.__str__()
				elif(child.name == "show"):
					show = child.__str__()
				elif(child.name == "priority"):
					priority = child.__str__()
				elif(child.uri == disco.XVCARDUPDATE):
					avatarHash = " "
					for child2 in child.elements():
						if(child2.name == "photo"):
							avatarHash = child2.__str__()
						elif(child2.name == "nickname"):
							nickname = child2.__str__()

			if not ptype:
				# available presence
				if(avatarHash):
					self.avatarHashReceived(froj.userhost(), toj.userhost(), avatarHash)
				if(nickname):
					self.nicknameReceived(froj.userhost(), toj.userhost(), nickname)
			
			LogEvent(INFO, self.jabberID, "Parsed presence packet")
			self.presenceReceived(froj.userhost(), froj.resource, toj.userhost(), toj.resource, priority, ptype, show, status)
	
	
	
	def messageReceived(self, source, resource, dest, destr, mtype, body, noerror):
		""" Override this method to be notified when a message is received """
		pass
	
	def inviteReceived(self, source, resource, dest, destr, roomjid):
		""" Override this method to be notified when an invitation is received """
		pass
	
	def presenceReceived(self, source, resource, to, tor, priority, ptype, show, status):
		""" Override this method to be notified when presence is received """
		pass
	
	def subscriptionReceived(self, source, dest, subtype):
		""" Override this method to be notified when a subscription packet is received """
		pass
	
	def nicknameReceived(self, source, dest, nickname):
		""" Override this method to be notified when a nickname has been received """
		pass
	
	def avatarHashReceieved(self, source, dest, avatarHash):
		""" Override this method to be notified when an avatar hash is received """
		pass


