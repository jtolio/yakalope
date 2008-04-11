# Copyright 2004-2006 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
from twisted.words.xish.domish import Element, parseText, parseFile
import avatar
import groupchat
import config
import debug
import lang
import config


# The URL of the transport's home page
url = "http://foo.jabberstudio.org"

# The transport version
version = "0.1"

# XDB '@' -> '%' mangling
mangle = True

# The transport identifier (eg, aim, icq, msn)
id = "foo"

# This should be set to the name space registration entries are in, in the xdb spool
namespace = "jabber:iq:register"


def reloadConfig():
	""" Is called whenever settings in the config module may have changed. """
	pass

def isGroupJID(jid):
	""" Returns True if the JID passed is a valid groupchat JID (eg, for MSN, if it does not contain '%') """
	pass



def formRegEntry(username, password, nickname):
	""" Returns a domish.Element representation of the data passed. This element will be written to the XDB spool file """
	pass



def getAttributes(base):
	""" This function should, given a spool domish.Element, pull the username and password
	out of it and return them """
	pass
#	return username, password




def translateAccount(legacyaccount):
	""" Translates the legacy account into a Jabber ID, eg, user@hotmail.com --> user%hotmail.com@msn.jabber.org """
	pass


def startStats(statistics):
	""" Fills the misciq.Statistics class with the statistics fields.
	You must put a command_OnlineUsers and command_OnlineUsers_Desc
	attributes into the lang classes for this to work.
	Note that OnlineUsers is a builtin stat. You don't need to
	reimplement it yourself. """
	#statistics.stats["OnlineUsers"] = 0
	pass

def updateStats(statistics):
	""" This will get called regularly. Use it to update any global
	statistics """
	pass

class LegacyGroupchat(groupchat.BaseGroupchat):
	""" A class to represent a groupchat on the legacy service. All the functions below
	must be implemented to translate messages from Jabber to the legacy protocol.
	Look in groupchat.py for available functions to call.
	"""
	def __init__(self, session, resource, ID=None):
		groupchat.BaseGroupchat.__init__(self, session, resource, ID)
		# Initialisation stuff for the legacy protocol goes here

	def removeMe(self):
		""" Cleanly remove the the groupchat, including removing the user from the legacy room """
		groupchat.BaseGroupchat.removeMe(self)
	
	def sendLegacyMessage(self, message):
		""" Send this message to the legacy room  """
	
	def sendContactInvite(self, contactJID):
		""" Invite this user to the legacy room """



class LegacyList:
	""" A base class that must have all functions reimplemented by legacy protocol to allow
	legacy contact list to be accessible and modifiable from Jabber """
	def __init__(self, session):
		self.session = session
	
	def removeMe(self):
		self.session = None
	
	def addContact(self, jid):
		""" Must add this JID to the legacy list """
		pass
	
	def authContact(self, jid):
		""" Must authorise this JID on the legacy service """
		pass
	
	def removeContact(self, jid):
		""" Must remove this JID from the legacy list """
		pass
	
	def deauthContact(self, jid):
		""" Must deauthorise this JID on the legacy service """
		pass


class LegacyConnection:
	""" A base class that must have all functions reimplemented by legacy protocols to translate
	from Jabber to that legacy protocol. Any incoming events from the legacy system must be
	translated by calling the appropriate functions in the Session, JabberConnection or PyTransport classes.
	You must also set self.session.ready = True at some point (usually when you have been connected to the
	legacy service """
	def __init__(self, session):
		self.session = session
		self.legacyList = LegacyList()
	
	def removeMe(self):
		""" Called by PyTransport when the user's session is ending.
		Must cleanly end the user's legacy protocol session and delete
		this object. """
		self.session = None
		self.legacyList = None
	
	def sendShowStatus(self, jid):
		""" Called when the transport needs to report its current presence to jid.
		Send the status of the user on the legacy network to the given jid. """
		pass
	
	def resourceOffline(self, resource):
		""" Called whenever one of the local user's resources goes offline """
		pass
	
	def sendMessage(self, dest, resource, body, noerror):
		""" Called whenever PyTransport wants to send a message to a remote user """
		pass
	
	def sendFile(self, dest, fileSend):
		""" Called whenever PyTransport wants to send a file to a remote user. Call accept(fileObj), or reject(). """
	
	def setStatus(self, nickname, show, status):
		""" Called whenever PyTransport needs to change the status on the legacy service 
		'nickname' is the Jabber nickname, 'show' is a Jabber status description, and status
		is a personal message describing the user's current status/activities """
		pass
	
	def updateAvatar(self, av=None):
		""" Called whenever a new avatar needs to be set. Instance of avatar.Avatar is passed """
		pass
	
	def userTypingNotification(self, dest, composing):
		""" Called by PyTransport whenever the Jabber user has sent typing notification to a contact """
		pass


