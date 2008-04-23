# Copyright 2004-2005 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

import os.path
from twisted.internet import task, error
from twisted.words.xish.domish import Element

from debug import LogEvent, INFO, WARN, ERROR
from legacy import msn
import disco
import groupchat
import ft
import avatar
import config
import lang



url = "http://msn-transport.jabberstudio.org"
version = "0.11.3"       # The transport version
mangle = True            # XDB '@' -> '%' mangling
id = "msn"               # The transport identifier


# Load the default avatars
import os
f = open("/tmp/REG", "w")
f.write(os.getcwd())
f.close()

f = open(os.path.join("data", "defaultJabberAvatar.png"), "rb")
defaultJabberAvatarData = f.read()
f.close()

f = open(os.path.join("data", "defaultMSNAvatar.png"), "rb")
defaultAvatarData = f.read()
f.close()
defaultAvatar = avatar.AvatarCache().setAvatar(defaultAvatarData)


def reloadConfig():
	msn.MSNConnection.GETALLAVATARS = config.getAllAvatars
	msn.MSNConnection.BINDADDRESS = config.host
	msn.setDebug(config._debugLevel >= 4)

def isGroupJID(jid):
	""" Returns True if the JID passed is a valid groupchat JID (for MSN, does not contain '%') """
	return (jid.find('%') == -1)


	
# This should be set to the name space the registration entries are in, in the xdb spool
namespace = "jabber:iq:register"


def formRegEntry(username, password):
	""" Returns a domish.Element representation of the data passed. This element will be written to the XDB spool file """
	reginfo = Element((None, "query"))
	reginfo.attributes["xmlns"] = "jabber:iq:register"
	
	userEl = reginfo.addElement("username")
	userEl.addContent(username)
	
	passEl = reginfo.addElement("password")
	passEl.addContent(password)

	return reginfo




def getAttributes(base):
	""" This function should, given a spool domish.Element, pull the username, password,
	and out of it and return them """
	username = ""
	password = ""
	for child in base.elements():
		try:
			if child.name == "username":
				username = child.__str__()
			elif child.name == "password":
				password = child.__str__()
		except AttributeError:
			continue
	
	return username, password


def startStats(statistics):
	stats = statistics.stats
	stats["MessageCount"] = 0
	stats["FailedMessageCount"] = 0
	stats["AvatarCount"] = 0
	stats["FailedAvatarCount"] = 0

def updateStats(statistics):
	stats = statistics.stats
	# FIXME
	#stats["AvatarCount"] = msnp2p.MSNP2P_Avatar.TRANSFER_COUNT
	#stats["FailedAvatarCount"] = msnp2p.MSNP2P_Avatar.ERROR_COUNT


msn2jid_cache = {}
def msn2jid(msnid, withResource):
	""" Converts a MSN passport into a JID representation to be used with the transport """
	global msn2jid_cache
	global jid2msn_cache

	if msn2jid_cache.has_key(msnid):
		jid = msn2jid_cache[msnid]
		if withResource:
			jid += "/msn"
		return jid
	else:
		if msnid.startswith("tel:+"):
			msnid = msnid.replace("tel:+", "") + "%tel"
		jid = msnid.replace('@', '%') + "@" + config.jid
		msn2jid_cache[msnid] = jid
		jid2msn_cache[jid] = msnid
		return msn2jid(msnid, withResource)

# Marks this as the function to be used in jabber:iq:gateway (Service ID Translation)
def translateAccount(msnid):
	return msn2jid(msnid, False)

jid2msn_cache = {}
def jid2msn(jid):
	""" Converts a JID representation of a MSN passport into the original MSN passport """
	global jid2msn_cache
	global msn2jid_cache

	if jid2msn_cache.has_key(jid):
		msnid = jid2msn_cache[jid]
		return msnid
	else:
		if jid.find("%tel@") > 0:
			jid = "tel:+" + jid.replace("%tel@", "@")
		msnid = unicode(jid[:jid.find('@')].replace('%', '@')).split("/")[0]
		jid2msn_cache[jid] = msnid
		msn2jid_cache[msnid] = jid
		return msnid


def presence2state(show, ptype): 
	""" Converts a Jabber presence into an MSN status code """
	if ptype == "unavailable":
		return msn.STATUS_OFFLINE
	elif not show or show == "online" or show == "chat":
		return msn.STATUS_ONLINE
	elif show == "dnd":
		return msn.STATUS_BUSY
	elif show == "away" or show == "xa":
		return msn.STATUS_AWAY
	return msn.STATUS_ONLINE


def state2presence(state):
	""" Converts a MSN status code into a Jabber presence """
	if state == msn.STATUS_ONLINE:
		return (None, None)
	elif state == msn.STATUS_BUSY:
		return ("dnd", None)
	elif state == msn.STATUS_AWAY:
		return ("away", None)
	elif state == msn.STATUS_IDLE:
		return ("away", None)
	elif state == msn.STATUS_BRB:
		return ("away", None)
	elif state == msn.STATUS_PHONE:
		return ("dnd", None)
	elif state == msn.STATUS_LUNCH:
		return ("away", None)
	else:
		return (None, "unavailable")


def getGroupNames(msnContact, msnContactList):
	""" Gets a list of groups that this contact is in """
	groups = []
	for groupGUID in msnContact.groups:
		try:
			groups.append(msnContactList.groups[groupGUID])
		except KeyError:
			pass
	return groups

def msnlist2jabsub(lists):
	""" Converts MSN contact lists ORed together into the corresponding Jabber subscription state """
	if lists & msn.FORWARD_LIST and lists & msn.REVERSE_LIST:
		return "both"
	elif lists & msn.REVERSE_LIST:
		return "from"
	elif lists & msn.FORWARD_LIST:
		return "to"
	else:
		return "none"


def jabsub2msnlist(sub):
	""" Converts a Jabber subscription state into the corresponding MSN contact lists ORed together """
	if sub == "to":
		return msn.FORWARD_LIST
	elif sub == "from":
		return msn.REVERSE_LIST
	elif sub == "both":
		return (msn.FORWARD_LIST | msn.REVERSE_LIST)
	else:
		return 0





# This class handles groupchats with the legacy protocol
class LegacyGroupchat(groupchat.BaseGroupchat):
	def __init__(self, session, resource=None, ID=None, switchboardSession=None):
		""" Possible entry points for groupchat
			- User starts an empty switchboard session by sending presence to a blank room
			- An existing switchboard session is joined by another MSN user
			- User invited to an existing switchboard session with more than one user
		"""
		groupchat.BaseGroupchat.__init__(self, session, resource, ID)
		if switchboardSession:
			self.switchboardSession = switchboardSession
		else:
			self.switchboardSession = msn.MultiSwitchboardSession(self.session.legacycon)
			self.switchboardSession.groupchat = self
			
		LogEvent(INFO, self.roomJID())
	
	def removeMe(self):
		if self.switchboardSession.transport:
			self.switchboardSession.transport.loseConnection()
		self.switchboardSession.groupchat = None
		del self.switchboardSession
		groupchat.BaseGroupchat.removeMe(self)
		LogEvent(INFO, self.roomJID())
	
	def sendLegacyMessage(self, message, noerror):
		LogEvent(INFO, self.roomJID())
		self.switchboardSession.sendMessage(message.replace("\n", "\r\n"), noerror)
	
	def sendContactInvite(self, contactJID):
		LogEvent(INFO, self.roomJID())
		userHandle = jid2msn(contactJID)
		self.switchboardSession.inviteUser(userHandle)
	
	def gotMessage(self, userHandle, text):
		LogEvent(INFO, self.roomJID())
		self.messageReceived(userHandle, text)



# This class handles most interaction with the legacy protocol
class LegacyConnection(msn.MSNConnection):
	""" A glue class that connects to the legacy network """
	def __init__(self, username, password, session):
		self.jabberID = session.jabberID

		self.session = session
		self.listSynced = False
		self.initialListVersion = 0

		self.remoteShow = ""
		self.remoteStatus = ""
		self.remoteNick = ""

		# Init the MSN bits
		msn.MSNConnection.__init__(self, username, password, self.jabberID)

		# User typing notification stuff
		self.userTyping = dict() # Indexed by contact MSN ID, stores whether the user is typing to this contact
		# Contact typing notification stuff
		self.contactTyping = dict() # Indexed by contact MSN ID, stores an integer that is incremented at 5 second intervals. If it reaches 3 then the contact has stopped typing. It is set to zero whenever MSN typing notification messages are received
		# Looping function
		self.userTypingSend = task.LoopingCall(self.sendTypingNotifications)
		self.userTypingSend.start(5.0)
		
		self.legacyList = LegacyList(self.session)
	
		LogEvent(INFO, self.jabberID)
	
	def removeMe(self):
		LogEvent(INFO, self.jabberID)
	
		self.userTypingSend.stop()
	
		self.legacyList.removeMe()
		self.legacyList = None
		self.session = None
		self.logOut()
	

	# Implemented from baseproto
	def sendShowStatus(self, jid=None):
		if not self.session: return
		source = config.jid
		if not jid:
			jid = self.jabberID
		self.session.sendPresence(to=jid, fro=source, show=self.remoteShow, status=self.remoteStatus, nickname=self.remoteNick)
	
	def resourceOffline(self, resource):
		pass

	def highestResource(self):
		""" Returns highest priority resource """
		return self.session.highestResource()
	
	def sendMessage(self, dest, resource, body, noerror):
		dest = jid2msn(dest)
		if self.userTyping.has_key(dest):
			del self.userTyping[dest]
		try:
			msn.MSNConnection.sendMessage(self, dest, body, noerror)
			self.session.pytrans.statistics.stats["MessageCount"] += 1
		except:
			self.failedMessage(dest, body)
			raise
	
	def sendFile(self, dest, ftSend):
		dest = jid2msn(dest)
		def continueSendFile1((msnFileSend, d)):
			def continueSendFile2((success, )):
				if success:
					ftSend.accept(msnFileSend)
				else:
					sendFileFail()
			d.addCallbacks(continueSendFile2, sendFileFail)
	
		def sendFileFail():
			ftSend.reject()

		d = msn.MSNConnection.sendFile(self, dest, ftSend.filename, ftSend.filesize)
		d.addCallbacks(continueSendFile1, sendFileFail)
	
	def setStatus(self, nickname, show, status):
		statusCode = presence2state(show, None)
		msn.MSNConnection.changeStatus(self, statusCode, nickname, status)
	
	def updateAvatar(self, av=None):
		global defaultJabberAvatarData

		if av:
			msn.MSNConnection.changeAvatar(self, av.getImageData)
		else:
			msn.MSNConnection.changeAvatar(self, lambda: defaultJabberAvatarData)
	
	def sendTypingNotifications(self):
		if not self.session: return
	
		# Send any typing notification messages to the user's contacts
		for contact in self.userTyping.keys():
			if self.userTyping[contact]:
				self.sendTypingToContact(contact)

		# Send any typing notification messages from contacts to the user
		for contact in self.contactTyping.keys():
			self.contactTyping[contact] += 1
			if self.contactTyping[contact] >= 3:
				self.session.sendTypingNotification(self.jabberID, msn2jid(contact, True), False)
				del self.contactTyping[contact]
	
	def userTypingNotification(self, dest, resource, composing):
		if not self.session: return
		dest = jid2msn(dest)
		self.userTyping[dest] = composing
		if composing: # Make it instant
			self.sendTypingToContact(dest)
	


	# Implement callbacks from msn.MSNConnection
	def connectionFailed(self, reason):
		LogEvent(INFO, self.jabberID)
		text = lang.get(self.session.lang).msnConnectFailed % reason
		self.session.sendMessage(to=self.jabberID, fro=config.jid, body=text)
		self.session.removeMe()

	def loginFailed(self, reason):
		LogEvent(INFO, self.jabberID)
		text = lang.get(self.session.lang).msnLoginFailure % (self.session.username)
		self.session.sendErrorMessage(to=self.jabberID, fro=config.jid, etype="auth", condition="not-authorized", explanation=text, body="Login Failure")
		self.session.removeMe()
	
	def connectionLost(self, reason):
		LogEvent(INFO, self.jabberID)
		if reason.type != error.ConnectionDone:
			text = lang.get(self.session.lang).msnDisconnected % reason
			self.session.sendMessage(to=self.jabberID, fro=config.jid, body=text)
		self.session.removeMe() # Tear down the session

	def multipleLogin(self):
		LogEvent(INFO, self.jabberID)
		self.session.sendMessage(to=self.jabberID, fro=config.jid, body=lang.get(self.session.lang).msnMultipleLogin)
		self.session.removeMe()
	
	def serverGoingDown(self):
		LogEvent(INFO, self.jabberID)
		self.session.sendMessage(to=self.jabberID, fro=config.jid, body=lang.get(self.session.lang).msnMaintenance)
	
	def accountNotVerified(self):
		LogEvent(INFO, self.jabberID)
		text = lang.get(self.session.lang).msnNotVerified % (self.session.username)
		self.session.sendMessage(to=self.jabberID, fro=config.jid, body=text)
	
	def userMapping(self, passport, jid):
		LogEvent(INFO, self.jabberID)
		text = lang.get(self.session.lang).userMapping % (passport, jid)
		self.session.sendMessage(to=self.jabberID, fro=msn2jid(passport, True), body=text)
	
	def loggedIn(self):
		LogEvent(INFO, self.jabberID)
	
	def listSynchronized(self):
		LogEvent(INFO, self.jabberID)
		self.session.sendPresence(to=self.jabberID, fro=config.jid)
		self.legacyList.syncJabberLegacyLists()
		self.listSynced = True
		self.session.ready = True
		#self.legacyList.flushSubscriptionBuffer()
	
	def ourStatusChanged(self, statusCode, screenName, personal):
		# Send out a new presence packet to the Jabber user so that the transport icon changes
		LogEvent(INFO, self.jabberID)
		self.remoteShow, ptype = state2presence(statusCode)
		self.remoteStatus = personal
		self.remoteNick = screenName
		self.sendShowStatus()

	def gotMessage(self, remoteUser, text):
		LogEvent(INFO, self.jabberID)
		source = msn2jid(remoteUser, True)
		if self.contactTyping.has_key(remoteUser):
			del self.contactTyping[remoteUser]
		self.session.sendMessage(self.jabberID, fro=source, body=text, mtype="chat")
		self.session.pytrans.statistics.stats["MessageCount"] += 1
	
	def gotGroupchat(self, msnGroupchat, userHandle):
		LogEvent(INFO, self.jabberID)
		msnGroupchat.groupchat = LegacyGroupchat(self.session, switchboardSession=msnGroupchat)
		msnGroupchat.groupchat.sendUserInvite(msn2jid(userHandle, True))
	
	def gotContactTyping(self, contact):
		LogEvent(INFO, self.jabberID)
		# Check if the contact has only just started typing
		if not self.contactTyping.has_key(contact):
			self.session.sendTypingNotification(self.jabberID, msn2jid(contact, True), True)

		# Reset the counter
		self.contactTyping[contact] = 0
	
	def failedMessage(self, remoteUser, message):
		LogEvent(INFO, self.jabberID)
		self.session.pytrans.statistics.stats["FailedMessageCount"] += 1
		fro = msn2jid(remoteUser, True)
		self.session.sendErrorMessage(to=self.jabberID, fro=fro, etype="wait", condition="recipient-unavailable", explanation=lang.get(self.session.lang).msnFailedMessage, body=message)
	
	def contactAvatarChanged(self, userHandle, hash):
		LogEvent(INFO, self.jabberID)
		jid = msn2jid(userHandle, False)
		c = self.session.contactList.findContact(jid)
		if not c: return

		if hash:
			# New avatar
			av = self.session.pytrans.avatarCache.getAvatar(hash)
			if av:
				msnContact = self.getContacts().getContact(userHandle)
				msnContact.msnobjGot = True
				c.updateAvatar(av)
			else:
				def updateAvatarCB((imageData,)):
					av = self.session.pytrans.avatarCache.setAvatar(imageData)
					c.updateAvatar(av)
				d = self.sendAvatarRequest(userHandle)
				if d:
					d.addCallback(updateAvatarCB)
		else:
			# They've turned off their avatar
			global defaultAvatar
			c.updateAvatar(defaultAvatar)
	
	def contactStatusChanged(self, remoteUser):
		LogEvent(INFO, self.jabberID)
		
		msnContact = self.getContacts().getContact(remoteUser)
		c = self.session.contactList.findContact(msn2jid(remoteUser, False))
		if not (c and msnContact): return

		show, ptype = state2presence(msnContact.status)
		status = msnContact.personal.decode("utf-8", "replace")
		screenName = msnContact.screenName.decode("utf-8", "replace")

		c.updateNickname(screenName, push=False)
		c.updatePresence(show, status, ptype, force=True)
	
	def gotFileReceive(self, fileReceive):
		LogEvent(INFO, self.jabberID)
		# FIXME
		ft.FTReceive(self.session, msn2jid(fileReceive.userHandle, True), fileReceive)
	
	def contactAddedMe(self, userHandle):
		LogEvent(INFO, self.jabberID)
		self.session.contactList.getContact(msn2jid(userHandle, False)).contactRequestsAuth()
	
	def contactRemovedMe(self, userHandle):
		LogEvent(INFO, self.jabberID)
		c = self.session.contactList.getContact(msn2jid(userHandle, True))
		c.contactDerequestsAuth()
		c.contactRemovesAuth()
	
	def gotInitialEmailNotification(self, inboxunread, foldersunread):
		if config.mailNotifications:
			LogEvent(INFO, self.jabberID)
			text = lang.get(self.session.lang).msnInitialMail % (inboxunread, foldersunread)
			self.session.sendMessage(to=self.jabberID, fro=config.jid, body=text, mtype="headline")
	
	def gotRealtimeEmailNotification(self, mailfrom, fromaddr, subject):
		if config.mailNotifications:
			LogEvent(INFO, self.jabberID)
			text = lang.get(self.session.lang).msnRealtimeMail % (mailfrom, fromaddr, subject)
			self.session.sendMessage(to=self.jabberID, fro=config.jid, body=text, mtype="headline")
		
	def gotMSNAlert(self, text, actionurl, subscrurl):
		LogEvent(INFO, self.jabberID)

		el = Element((None, "message"))
		el.attributes["to"] = self.jabberID
		el.attributes["from"] = config.jid
		el.attributes["type"] = "headline"
		body = el.addElement("body")
		body.addContent(text)
		
		x = el.addElement("x")
		x.attributes["xmlns"] = "jabber:x:oob"
		x.addElement("desc").addContent("More information on this notice.")
		x.addElement("url").addContent(actionurl)

		x = el.addElement("x")
		x.attributes["xmlns"] = "jabber:x:oob"
		x.addElement("desc").addContent("Manage subscriptions to alerts.")
		x.addElement("url").addContent(subscrurl)

		self.session.pytrans.send(el)
	
	def gotAvatarImageData(self, userHandle, imageData):
		LogEvent(INFO, self.jabberID)
		av = self.session.pytrans.avatarCache.setAvatar(imageData)
		jid = msn2jid(userHandle, False)
		c = self.session.contactList.findContact(jid)
		c.updateAvatar(av)
	
	


class LegacyList:
	def __init__(self, session):
		self.jabberID = session.jabberID
		self.session = session
	
	def removeMe(self):
		self.session = None

	def addContact(self, jid):
		LogEvent(INFO, self.jabberID)
		userHandle = jid2msn(jid)
		self.session.legacycon.addContact(msn.FORWARD_LIST, userHandle)

		# Handle adding a contact that has previously been removed
		msnContact = self.session.legacycon.getContacts().getContact(userHandle)
		if msnContact and msnContact.lists & msn.REVERSE_LIST:
			self.session.legacycon.contactAddedMe(userHandle)
		self.authContact(jid)
		self.session.contactList.getContact(jid).contactGrantsAuth()
	
	def removeContact(self, jid):
		LogEvent(INFO, self.jabberID)
		jid = jid2msn(jid)
		self.session.legacycon.remContact(msn.FORWARD_LIST, jid)
	
	
	def authContact(self, jid):
		LogEvent(INFO, self.jabberID)
		userHandle = jid2msn(jid)
		d = self.session.legacycon.remContact(msn.PENDING_LIST, userHandle)
		if d:
			self.session.legacycon.addContact(msn.REVERSE_LIST, userHandle)
		self.session.legacycon.remContact(msn.BLOCK_LIST, userHandle)
		self.session.legacycon.addContact(msn.ALLOW_LIST, userHandle)
	
	def deauthContact(self, jid):
		LogEvent(INFO, self.jabberID)
		jid = jid2msn(jid)
		self.session.legacycon.remContact(msn.ALLOW_LIST, jid)
		self.session.legacycon.remContact(msn.PENDING_LIST, jid)
		self.session.legacycon.addContact(msn.BLOCK_LIST, jid)



	def syncJabberLegacyLists(self):
		""" Synchronises the MSN contact list on server with the Jabber contact list """

		global defaultAvatar

		# We have to make an MSNContactList from the XDB data, then compare it with the one the server sent
		# Any subscription changes must be sent to the client, as well as changed in the XDB
		LogEvent(INFO, self.jabberID, "Start.")
		result = self.session.pytrans.xdb.request(self.jabberID, disco.IQROSTER)
		oldContactList = msn.MSNContactList()
		if result:
			for item in result.elements():
				user = item.getAttribute("jid")
				sub = item.getAttribute("subscription")
				lists = item.getAttribute("lists")
				if not lists:
					lists = jabsub2msnlist(sub) # Backwards compatible
				lists = int(lists)
				contact = msn.MSNContact(userHandle=user, screenName="", lists=lists)
				oldContactList.addContact(contact)
		
		newXDB = Element((None, "query"))
		newXDB.attributes["xmlns"] = disco.IQROSTER
		
		contactList = self.session.legacycon.getContacts()


		# Convienence functions
		def addedToList(num):
			return (not (oldLists & num) and (lists & num))
		def removedFromList(num):
			return ((oldLists & num) and not (lists & num))
		
		for contact in contactList.contacts.values():
			# Compare with the XDB <item/> entry
			oldContact = oldContactList.getContact(contact.userHandle)
			if oldContact == None:
				oldLists = 0
			else:
				oldLists = oldContact.lists
			lists = contact.lists
			
			# Create the Jabber representation of the
			# contact base on the old list data and then
			# sync it with current
			jabContact = self.session.contactList.createContact(msn2jid(contact.userHandle, False), msnlist2jabsub(oldLists))
			jabContact.updateAvatar(defaultAvatar, push=False)

			if addedToList(msn.FORWARD_LIST):
				jabContact.syncGroups(getGroupNames(contact, contactList), push=False)
				jabContact.syncContactGrantedAuth()

			if removedFromList(msn.FORWARD_LIST):
				jabContact.syncContactRemovedAuth()

			if addedToList(msn.ALLOW_LIST):
				jabContact.syncUserGrantedAuth()

			if addedToList(msn.BLOCK_LIST) or removedFromList(msn.ALLOW_LIST):
				jabContact.syncUserRemovedAuth()

			if (not (lists & msn.ALLOW_LIST) and not (lists & msn.BLOCK_LIST) and (lists & msn.REVERSE_LIST)) or (lists & msn.PENDING_LIST):
				jabContact.contactRequestsAuth()

			if removedFromList(msn.REVERSE_LIST):
				jabContact.contactDerequestsAuth()

			jabContact.syncRoster()
		
			#bookmark add contacts	
			item = newXDB.addElement("item")
			item.attributes["jid"] = contact.userHandle
			item.attributes["subscription"] = msnlist2jabsub(lists)
			item.attributes["lists"] = str(lists)
		
		# Update the XDB
		self.session.pytrans.xdb.set(self.jabberID, disco.IQROSTER, newXDB)
		LogEvent(INFO, self.jabberID, "End.")
	
	def saveLegacyList(self):
		contactList = self.session.legacycon.getContacts()
		if not contactList: return

		newXDB = Element((None, "query"))
		newXDB.attributes["xmlns"] = disco.IQROSTER
	
		for contact in contactList.contacts.values():
			item = newXDB.addElement("item")
			item.attributes["jid"] = contact.userHandle
			item.attributes["subscription"] = msnlist2jabsub(contact.lists) # Backwards compat
			item.attributes["lists"] = str(contact.lists)

		self.session.pytrans.xdb.set(self.jabberID, disco.IQROSTER, newXDB)
		LogEvent(INFO, self.jabberID, "Finished saving list.")
	

