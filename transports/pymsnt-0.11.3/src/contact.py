# Copyright 2005-2006 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

from debug import LogEvent, INFO, WARN, ERROR

from twisted.internet import reactor
from twisted.words.xish.domish import Element

import disco
import legacy


class Contact:
	""" Represents a Jabber contact """
	def __init__(self, jid, sub, contactList):
		self.jid = jid
		self.contactList = contactList
		self.groups = []
		self.origsub = sub
		self.sub = sub
		self.nickname = ""
		self.avatar = None
		self.show = ""
		self.status = ""
		self.ptype = "unavailable"
	
	def removeMe(self):
		""" Destroys this object. Does not remove the contact from the server's list. """
		self.contactList = None
		self.avatar = None
	
	def syncContactGrantedAuth(self):
		""" Since last using the transport the user has been granted authorisation by this contact.
		Call this to synchronise the user's Jabber list with their legacy list after logon. """
		if self.sub == "none":
			self.sub = "to"
		elif self.sub == "from":
			self.sub = "both"
		else:
			return

	def syncContactRemovedAuth(self):
		""" Since last using the transport the user has been blocked by this contact.
		Call this to synchronise the user's Jabber list with their legacy list after logon. """
		if self.sub == "to":
			self.sub = "none"
		elif self.sub == "both":
			self.sub = "from"
		else:
			return
	
	def syncUserGrantedAuth(self):
		""" Since last using the transport the user has granted authorisation to this contact.
		Call this to synchronise the user's Jabber list with their legacy list after logon. """
		if self.sub == "none":
			self.sub = "from"
		elif self.sub == "to":
			self.sub = "both"
		else:
			return
	
	def syncUserRemovedAuth(self):
		""" Since last using the transport the user has removed this contact's authorisation.
		Call this to synchronise the user's Jabber list with their legacy list after logon. """
		if self.sub == "from":
			self.sub = "none"
		elif self.sub == "both":
			self.sub = "to"
		else:
			return
	
	def syncGroups(self, groups, push=True):
		""" Set the groups that this contact is in on the legacy service.
		By default this pushes the groups out with a presence subscribed packet. """
		self.groups = groups
		if push: self.syncRoster(ptype="subscribed");
	
	syncChoice = {
	   ("none", "none") : "",              #
	   ("none", "to"  ) : "subscribe",     # User+ Contact
	   ("none", "from") : "subscribe",     # User  Contact+
	   ("none", "both") : "subscribe",     # User+ Contact+
	   ("to"  , "none") : "unsubscribed",  # User- Contact
	   ("to"  , "to"  ) : "",              #
	   ("to"  , "from") : "unsubscribe",   # User- Contact+      **
	   ("to"  , "both") : "subscribe",     # User  Contact+
	   ("from", "none") : "unsubscribe",   # User  Contact-
	   ("from", "to"  ) : "subscribe",     # User+ Contact-      *
	   ("from", "from") : "",              #
	   ("from", "both") : "subscribe",     # User+ Contact
	   ("both", "none") : "unsubscribed",  # User- Contact-      *
	   ("both", "to"  ) : "unsubscribe",   # User  Contact-
	   ("both", "from") : "unsubscribed",  # User- Contact
	   ("both", "both") : ""               #
	}
	   
	def syncRoster(self, ptype=""):
		if not ptype:
			ptype = self.syncChoice.get((self.origsub, self.sub))
		if ptype:
			self.contactList.session.sendRosterImport(jid=self.jid, ptype=ptype, sub=self.sub, groups=self.groups, name=self.nickname)

	def contactGrantsAuth(self):
		""" Live roster event """
		if self.sub == "none":
			self.sub = "to"
		elif self.sub == "from":
			self.sub = "both"
		self.sendSub("subscribed")
		self.sendPresence()
	
	def contactRemovesAuth(self):
		""" Live roster event """
		if self.sub == "to":
			self.sub = "none"
		elif self.sub == "both":
			self.sub = "from"
		self.sendSub("unsubscribed")
	
	def contactRequestsAuth(self):
		""" Live roster event """
		self.sendSub("subscribe")
	
	def contactDerequestsAuth(self):
		""" Live roster event """
		self.sendSub("unsubscribe")
	
	def jabberSubscriptionReceived(self, subtype):
		""" Updates the subscription state internally and pushes the update to the legacy server """
		if subtype == "subscribe":
			if self.sub == "to" or self.sub == "both":
				self.sendSub("subscribed")
			else:
				self.contactList.legacyList.addContact(self.jid)

		elif subtype == "subscribed":
			if self.sub == "none":
				self.sub = "from"
			if self.sub == "to":
				self.sub = "both"
			self.contactList.legacyList.authContact(self.jid)

		elif subtype == "unsubscribe":
			if self.sub == "none" or self.sub == "from":
				self.sendSub("unsubscribed")
			if self.sub == "both":
				self.sub = "from"
			if self.sub == "to":
				self.sub = "none"
			self.contactList.legacyList.removeContact(self.jid)

		elif subtype == "unsubscribed":
			if self.sub == "both":
				self.sub = "to"
			if self.sub == "from":
				self.sub = "none"
			self.contactList.legacyList.deauthContact(self.jid)

	def updateNickname(self, nickname, push=True):
		if self.nickname != nickname:
			self.nickname = nickname
			if push: self.sendPresence()
	
	def updatePresence(self, show, status, ptype, force=False):
		updateFlag = (self.show != show or self.status != status or self.ptype != ptype or force)
		self.show = show
		self.status = status
		self.ptype = ptype
		if updateFlag:
			self.sendPresence()
	
	def updateAvatar(self, avatar=None, push=True):
		if self.avatar == avatar:
			return
		self.avatar = avatar
		if push:
			self.sendPresence()
	
	def sendSub(self, ptype):
		self.contactList.session.sendPresence(to=self.contactList.session.jabberID, fro=self.jid + "/" + legacy.id, ptype=ptype)
	
	def sendPresence(self, tojid=""):
		avatarHash = ""
		if self.avatar:
			avatarHash = self.avatar.getImageHash()
		caps = Element((None, "c"))
		caps.attributes["xmlns"] = disco.CAPS
		caps.attributes["node"] = legacy.url + "/protocol/caps"
		caps.attributes["ver"] = legacy.version
		if not tojid:
			tojid=self.contactList.session.jabberID
		self.contactList.session.sendPresence(to=tojid, fro=self.jid + "/" + legacy.id, ptype=self.ptype, show=self.show, status=self.status, avatarHash=avatarHash, nickname=self.nickname, payload=[caps])
	


class ContactList:
	""" Represents the Jabber contact list """
	def __init__(self, session):
		LogEvent(INFO, session.jabberID)
		self.session = session
		self.contacts = {}
	
	def removeMe(self):
		""" Cleanly removes the object """
		LogEvent(INFO, self.session.jabberID)
		for jid in self.contacts:
			self.contacts[jid].updatePresence("", "", "unavailable")
			self.contacts[jid].removeMe()
		self.contacts = {}
		self.session = None
		self.legacyList = None
	
	def resendLists(self, tojid=""):
		for jid in self.contacts:
			if self.contacts[jid].ptype != "unavailable" :
				self.contacts[jid].sendPresence(tojid)
		LogEvent(INFO, self.session.jabberID)
	
	def createContact(self, jid, sub):
		""" Creates a contact object. Use this to initialise the contact list
		Returns a Contact object which you can call sync* methods on to synchronise
		the user's legacy contact list with their Jabber list """
		LogEvent(INFO, self.session.jabberID)
		c = Contact(jid, sub, self)
		self.contacts[jid] = c
		return c
	
	def getContact(self, jid):
		""" Finds the contact. If one doesn't exist then a new one is created, with sub set to "none" """
		if not self.contacts.has_key(jid):
			self.contacts[jid] = Contact(jid, "none", self)
		return self.contacts[jid]
	
	def findContact(self, jid):
		if self.contacts.has_key(jid):
			return self.contacts[jid]
		return None
	
	def jabberSubscriptionReceived(self, jid, subtype):
		self.getContact(jid).jabberSubscriptionReceived(subtype)
	

