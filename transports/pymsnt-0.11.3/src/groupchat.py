# Copyright 2004-2005 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
from twisted.internet import reactor
from twisted.words.xish.domish import Element

from debug import LogEvent, INFO, WARN, ERROR
import disco
import jabw
import config
import lang
import string
import time


class BaseGroupchat:
	""" A class to map a groupchat from a legacy service back to the Jabber user """
	def __init__(self, session, resource, ID=None):
		self.session = session
		self.session.groupchats.append(self)
		self.nick = resource
		if(ID):
			self.ID = ID
			self.session.pytrans.reserveID(self.ID)
		else:
			self.ID = self.session.pytrans.makeID()
		
		self.ready = False # Is True only after the user has joined
		self.messageBuffer = []
		self.contacts = []
		
		self.checkTimer = reactor.callLater(float(config.groupchatTimeout), self.checkUserJoined, None)
		
		LogEvent(INFO, self.roomJID())
	
	def removeMe(self):
		""" Cleanly removes the object """
		self.session.groupchats.remove(self)
		if(self.ready):
			self.session.sendPresence(to=self.user(), fro=self.roomJID() + "/" + self.nick, ptype="unavailable")
		self.ready = False
		self.session = None
		
		if(self.checkTimer and not self.checkTimer.called):
			self.checkTimer.cancel()
		self.checkTimer = None

		LogEvent(INFO, self.roomJID())

	def roomJID(self):
		""" Returns the room JID """
		return self.ID + "@" + config.jid
	
	def user(self):
		""" Returns the full JID of the Jabber user in this groupchat """
		jid = self.session.jabberID
		# FIXME, this probably won't work with multiple resources (unless you're using the highest resource)
#		if(self.resource):
#			jid += "/" + self.resource
		return jid
	
	def checkUserJoined(self, ignored=None):
		self.checkTimer = None
		if(not self.ready):
			LogEvent(INFO, self.roomJID(), "User hasn't joined after two minutes. Removing them from the room.")
			
			text = []
			text.append(lang.get(self.session.lang).groupchatFailJoin1 % (self.roomJID()))
			for contact in self.contacts:
				text.append("\t%s" % (contact))
			text.append("")
			text.append(lang.get(self.session.lang).groupchatFailJoin2)
			text.append("")
			for (source, message, timestamp) in self.messageBuffer:
				if(source):
					text.append("%s says: %s" % (source, message))
				else:
					text.append(message)
			
			body = string.join(text, "\n")
			
			self.session.sendMessage(to=self.user(), fro=config.jid, body=body)
			
			self.removeMe()
	
	def sendUserInvite(self, fro):
		""" Sends the invitation out to the Jabber user to join this room """
		LogEvent(INFO, self.roomJID(), "Sending invitation to user")
		el = Element((None, "message"))
		el.attributes["from"] = fro
		el.attributes["to"] = self.user()
		body = el.addElement("body")
		text = lang.get(self.session.lang).groupchatInvite % (self.roomJID())
		body.addContent(text)
		x = el.addElement("x")
		x.attributes["jid"] = self.roomJID()
		x.attributes["xmlns"] = disco.XCONFERENCE
		self.session.pytrans.send(el)
	
	def userJoined(self, nick):
		# Send any buffered messages
		self.nick = nick
		if(not self.nick):
			self.nick = self.session.username
		self.session.sendPresence(to=self.user(), fro=self.roomJID() + "/" + self.nick)
		if(not self.ready):
			LogEvent(INFO, self.roomJID())
			self.ready = True
			for (source, text, timestamp) in self.messageBuffer:
				self.messageReceived(source, text, timestamp)
			self.messageBuffer = None
			for contact in self.contacts:
				self.contactPresenceChanged(contact)
	
	def contactJoined(self, contact):
		if(self.contacts.count(contact) == 0):
			self.contacts.append(contact)
			LogEvent(INFO, self.roomJID())
		self.contactPresenceChanged(contact)
		self.messageReceived(None, "%s has joined the conference." % (contact))
	
	def contactLeft(self, contact):
		if(self.contacts.count(contact) > 0):
			self.contacts.remove(contact)
			LogEvent(INFO, self.roomJID())
		self.contactPresenceChanged(contact, ptype="unavailable")
		self.messageReceived(None, "%s has left the conference." % (contact))
	
	def messageReceived(self, source, message, timestamp=None):
		if(not self.ready):
			timestamp = time.strftime("%Y%m%dT%H:%M:%S")
			self.messageBuffer.append((source, message, timestamp))
		else:
			self.session.pytrans.statistics.stats["MessageCount"] += 1
			fro = self.roomJID()
			if(source):
				fro += "/" + source
			LogEvent(INFO, self.roomJID())
			self.session.sendMessage(to=self.user(), fro=fro, body=message, mtype="groupchat", delay=timestamp)
	
	def contactPresenceChanged(self, contact, ptype=None):
		if(self.session):
			fro = self.roomJID() + "/" + contact
			self.session.sendPresence(to=self.user(), fro=fro, ptype=ptype)
	
	def sendMessage(self, text, noerror):
		LogEvent(INFO, self.roomJID())
		self.messageReceived(self.nick, text)
		self.sendLegacyMessage(text, noerror)
	
	def sendLegacyMessage(self, text):
		""" Reimplement this to send the packet to the legacy service """
		pass
	
	def sendContactInvite(self, contact):
		""" Reimplement this to send the packet to the legacy service """
		pass


