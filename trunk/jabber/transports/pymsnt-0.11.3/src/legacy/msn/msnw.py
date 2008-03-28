# Copyright 2004-2006 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

# Twisted imports
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientFactory

# System imports
import math, base64, binascii

# Local imports
from debug import LogEvent, INFO, WARN, ERROR
import msn



"""
All interaction should be with the MSNConnection and MultiSwitchboardSession classes.
You should not directly instantiate any objects of other classes.
"""

class MSNConnection:
	""" Manages all the Twisted factories, etc """
	MAXMESSAGESIZE     = 1400
	SWITCHBOARDTIMEOUT = 30.0*60.0
	GETALLAVATARS      = False
	BINDADDRESS        = "0.0.0.0"

	def __init__(self, username, password, ident):
		""" Connects to the MSN servers.
		@param username: the MSN passport to connect with.
		@param password: the password for this account.
		@param ident: a unique identifier to use in logging.
		"""
		self.username = username
		self.password = password
		self.ident = ident
		self.timeout = None
		self.notificationFactory = None
		self.notificationClient = None
		self.connect()
		LogEvent(INFO, self.ident)
	
	def connect(self):
		""" Automatically called by the constructor """
		self.connectors = []
		self.switchboardSessions = {}
		self.savedEvents = SavedEvents() # Save any events that occur before connect
		self._getNotificationReferral()

	def _getNotificationReferral(self):
		def timeout():
			self.timeout = None
			dispatchFactory.d = None
			if not d.called:
				d.errback(Exception("Timeout"))
				self.logOut() # Clean up everything
		self.timeout = reactor.callLater(30, timeout)
		dispatchFactory = msn.DispatchFactory()
		dispatchFactory.userHandle = self.username
		dispatchFactory.protocol = DispatchClient
		d = Deferred()
		dispatchFactory.d = d
		d.addCallbacks(self._gotNotificationReferral, self.connectionFailed)
		self.connectors.append(reactor.connectTCP("messenger.hotmail.com", 1863, dispatchFactory, bindAddress=(MSNConnection.BINDADDRESS, 0)))
		LogEvent(INFO, self.ident)
	
	def _gotNotificationReferral(self, (host, port)):
		self.timeout.cancel()
		self.timeout = None
		# Create the NotificationClient
		self.notificationFactory = msn.NotificationFactory()
		self.notificationFactory.userHandle = self.username
		self.notificationFactory.password = self.password
		self.notificationFactory.msncon = self
		self.notificationFactory.protocol = NotificationClient
		self.connectors.append(reactor.connectTCP(host, port, self.notificationFactory, bindAddress=(MSNConnection.BINDADDRESS, 0)))
		LogEvent(INFO, self.ident)
	
	def _sendSavedEvents(self):
		self.savedEvents.send(self)
	
	def _notificationClientReady(self, notificationClient):
		self.notificationClient = notificationClient
	
	def _ensureSwitchboardSession(self, userHandle):
		if not self.switchboardSessions.has_key(userHandle):
			sb = OneSwitchboardSession(self, userHandle)
			sb.connect()
			self.switchboardSessions[userHandle] = sb

	

	# API calls
	def getContacts(self):
		""" Gets the contact list.

		@return an instance of MSNContactList (do not modify) if connected,
				or None if not.
		"""
		if self.notificationFactory:
			return self.notificationFactory.contacts
		else:
			return None
	
	def sendMessage(self, userHandle, text, noerror=False):
		"""
		Sends a message to a contact. Can only be called after listSynchronized().

		@param userHandle: the contact's MSN passport.
		@param text: the text to send.
		@param noerror: Set this to True if you don't want failed messages to bounce.
		"""
		LogEvent(INFO, self.ident)
		if self.notificationClient:
			self._ensureSwitchboardSession(userHandle)
			self.switchboardSessions[userHandle].sendMessage(text, noerror)
		elif not noerror:
			self.failedMessage(userHandle, text)

	def sendAvatarRequest(self, userHandle):
		"""
		Requests the avatar of a contact.

		@param userHandle: the contact to request an avatar from.
		@return: a Deferred() if the avatar can be fetched at this time.
		         This will fire with an argument of a tuple with the PNG 
				 image data as the only element.
				 Otherwise returns None
		"""

		LogEvent(INFO, self.ident)
		if not self.notificationClient: return
		if MSNConnection.GETALLAVATARS:
			self._ensureSwitchboardSession(userHandle)
		sb = self.switchboardSessions.get(userHandle)
		if sb: return sb.sendAvatarRequest()
	
	def sendFile(self, userHandle, filename, filesize):
		"""
		Used to send a file to a contact.

		@param username: the passport of the contact to send a file to.
		@param filename: the name of the file to send.
		@param filesize: the size of the file to send.
        
		@return: A Deferred, which will fire with an argument of:
		         (fileSend, d) A FileSend object and a Deferred.
		         The new Deferred will pass one argument in a tuple,
		         whether or not the transfer is accepted. If you
		         receive a True, then you can call write() on the
		         fileSend object to send your file. Call close()
		         when the file is done.
		         NOTE: You MUST write() exactly as much as you
		         declare in filesize.
		"""
		msnContact = self.getContacts().getContact(userHandle)
		if not msnContact:
			raise ValueError, "Contact not found"
		self._ensureSwitchboardSession(userHandle)
		return self.switchboardSessions[userHandle].sendFile(msnContact, filename, filesize)

	def sendTypingToContact(self, userHandle):
		"""
		Sends typing notification to a contact. Should send every 5secs.
		@param userHandle: the contact to notify of our typing.
		"""

		sb = self.switchboardSessions.get(userHandle)
		if sb: return sb.sendTypingNotification()
	
	def changeAvatar(self, imageDataFunc):
		"""
		Changes the user's avatar.
		@param imageDataFunc: a function which returns the new PNG avatar image data.
		"""
		if self.notificationClient:
			LogEvent(INFO, self.ident)
			self.notificationClient.changeAvatar(imageDataFunc, push=True)
		# Save the avatar for reuse on disconnection
		self.savedEvents.avatarImageDataFunc = imageDataFunc
	
	def changeStatus(self, statusCode, screenName, personal):
		"""
		Changes your status details. All details must be given with
		each call. This can be called before connection if you wish.

		@param statusCode: the user's new status (look in msn.statusCodes).
		@param screenName: the user's new screenName (up to 127 characters).
		@param personal: the user's new personal message.
		"""

		if not screenName: screenName = self.username
		if not statusCode: statusCode = msn.STATUS_ONLINE
		if not personal: personal = ""
		if self.notificationClient:
			changeCount = [0] # Hack for Python's limited scope :(
			def cb(ignored=None):
				changeCount[0] += 1
				if changeCount[0] == 3:
					self.ourStatusChanged(statusCode, screenName, personal)
			def errcb(ignored=None):
				pass # FIXME, should we do something here?
			LogEvent(INFO, self.ident)
			self.notificationClient.changeStatus(statusCode.encode("utf-8")).addCallbacks(cb, errcb)
			self.notificationClient.changeScreenName(screenName.encode("utf-8")).addCallbacks(cb, errcb)
			self.notificationClient.changePersonalMessage(personal.encode("utf-8")).addCallbacks(cb, errcb)
		# Remember the saved status
		self.savedEvents.statusCode = statusCode
		self.savedEvents.screenName = screenName
		self.savedEvents.personal = personal
				
	def addContact(self, listType, userHandle):
		""" See msn.NotificationClient.addContact """
		if self.notificationClient:
			return self.notificationClient.addContact(listType, str(userHandle))
		else:
			self.savedEvents.addContacts.append((listType, str(userHandle)))
			
	def remContact(self, listType, userHandle):
		""" See msn.NotificationClient.remContact """
		if self.notificationClient:
			return self.notificationClient.remContact(listType, str(userHandle))
		else:
			self.savedEvents.remContacts.append((listType, str(userHandle)))
	
	def logOut(self):
		""" Shuts down the whole connection. Don't try to call any
		other methods after this one. Except maybe connect() """
		if self.notificationClient:
			self.notificationClient.logOut()
		for c in self.connectors:
			c.disconnect()
		self.connectors = []
		if self.notificationFactory:
			self.notificationFactory.stopTrying()
			self.notificationFactory.msncon = None
			self.notificationFactory = None
		for sbs in self.switchboardSessions.values():
			if hasattr(sbs, "transport") and sbs.transport:
				sbs.transport.loseConnection()
		self.switchboardSessions = {}
		if self.timeout:
			self.timeout.cancel()
			self.timeout = None
		LogEvent(INFO, self.ident)
		
	
	# Reimplement these!
	def connectionFailed(self, reason=''):
		""" Called when the connection to the server failed. """
	
	def loginFailed(self, reason=''):
		""" Called when the account could not be logged in. """
	
	def connectionLost(self, reason=''):
		""" Called when we are disconnected. """
	
	def multipleLogin(self):
		""" Called when the server says there has been another login
		for this account. """
	
	def serverGoingDown(self):
		""" Called when the server says that it will be going down. """
	
	def accountNotVerified(self):
		""" Called if this passport has not been verified. Certain
		functions are not available. """
	
	def userMapping(self, passport, jid):
		""" Called when it is brought to our attention that one of the
		MSN contacts has a Jabber ID. You should communicate with Jabber. """
	
	def loggedIn(self):
		""" Called when we have authenticated, but before we receive
		the contact list. """
	
	def listSynchronized(self):
		""" Called when we have received the contact list. All methods
		in this class are now valid. """

	def ourStatusChanged(self, statusCode, screenName, personal):
		""" Called when the user's status has changed. """
	
	def gotMessage(self, userHandle, text):
		""" Called when a contact sends us a message """
	
	def gotGroupchat(self, msnGroupchat, userHandle):
		""" Called when a conversation with more than one contact begins.
		userHandle is the person who invited us.
		The overriding method is expected to set msnGroupchat.groupchat to an object
		that implements the following methods:
			contactJoined(userHandle)
			contactLeft(userHandle)
			gotMessage(userHandle, text)

		The object received as 'msnGroupchat' is an instance of MultiSwitchboardSession.
		"""
	
	def gotContactTyping(self, userHandle):
		""" Called when a contact sends typing notification.
		    Will be called once every 5 seconds. """
	
	def failedMessage(self, userHandle, text):
		""" Called when a message we sent has been bounced back. """

	def contactAvatarChanged(self, userHandle, hash):
		""" Called when we receive a changed avatar hash for a contact.
		You should call sendAvatarRequest(). """
	
	def contactStatusChanged(self, userHandle):
		""" Called when we receive status information for a contact. """
	
	def gotFileReceive(self, fileReceive):
		""" Called when a contact sends the user a file.
		Call accept(fileHandle) or reject() on the object. """
	
	def contactAddedMe(self, userHandle):
		""" Called when a contact adds the user to their list. """
	
	def contactRemovedMe(self, userHandle):
		""" Called when a contact removes the user from their list. """
	
	def gotInitialEmailNotification(self, inboxunread, foldersunread):
		""" Received at login to tell about the user's Hotmail status """
	
	def gotRealtimeEmailNotification(self, mailfrom, fromaddr, subject):
		""" Received in realtime whenever an email comes into the hotmail account """
	
	def gotMSNAlert(self, body, action, subscr):
		""" An MSN Alert (http://alerts.msn.com) was received. Body is the
		text of the alert. 'action' is a url for more information,
		'subscr' is a url to modify your your alerts subscriptions. """
	
	def gotAvatarImageData(self, userHandle, imageData):
		""" An contact's avatar has been received because a switchboard
		session with them was started. """


class SavedEvents:
	def __init__(self):
		self.screenName = ""
		self.statusCode = ""
		self.personal = ""
		self.avatarImageDataFunc = None
		self.addContacts = []
		self.remContacts = []
	
	def send(self, msncon):
		if self.avatarImageDataFunc:
			msncon.notificationClient.changeAvatar(self.avatarImageDataFunc, push=False)
		if self.screenName or self.statusCode or self.personal:
			msncon.changeStatus(self.statusCode, self.screenName, self.personal)
		for listType, userHandle in self.addContacts:
			msncon.addContact(listType, userHandle)
		for listType, userHandle in self.remContacts:
			msncon.remContact(listType, userHandle)



class DispatchClient(msn.DispatchClient):
	def gotNotificationReferral(self, host, port):
		d = self.factory.d
		self.factory.d = None
		if not d or d.called:
			return # Too slow! We've already timed out
		d.callback((host, port))


class NotificationClient(msn.NotificationClient):
	def doDisconnect(self, *args):
		if hasattr(self, "transport") and self.transport:
			self.transport.loseConnection()

	def loginFailure(self, message):
		self.factory.msncon.loginFailed(message)
	
	def loggedIn(self, userHandle, verified):
		LogEvent(INFO, self.factory.msncon.ident)
		msn.NotificationClient.loggedIn(self, userHandle, verified)
		self.factory.msncon._notificationClientReady(self)
		self.factory.msncon.loggedIn()
		if not verified:
			self.factory.msncon.accountNotVerified()
	
	def logOut(self):
		msn.NotificationClient.logOut(self)
		# If we explicitly log out, then all of these events
		# are now redundant
		self.loginFailure = self.doDisconnect
		self.loggedIn = self.doDisconnect
		self.connectionLost = lambda reason: msn.NotificationClient.connectionLost(self, reason)
	
	def connectionLost(self, reason):
		if not self.factory.msncon:
			# If MSNConnection.logOut is called before _notificationClientReady
			return

		def wait():
			LogEvent(INFO, self.factory.msncon.ident)
			msn.NotificationClient.connectionLost(self, reason)
			if self.factory.maxRetries > self.factory.retries:
				self.factory.stopTrying()
				self.factory.msncon.connectionLost(reason)
		# Make sure this event is handled after any others
		reactor.callLater(0, wait)
	
	def gotMSNAlert(self, body, action, subscr):
		LogEvent(INFO, self.factory.msncon.ident)
		self.factory.msncon.gotMSNAlert(body, action, subscr)

	def gotInitialEmailNotification(self, inboxunread, foldersunread):
		LogEvent(INFO, self.factory.msncon.ident)
		self.factory.msncon.gotInitialEmailNotification(inboxunread, foldersunread)

	def gotRealtimeEmailNotification(self, mailfrom, fromaddr, subject):
		LogEvent(INFO, self.factory.msncon.ident)
		self.factory.msncon.gotRealtimeEmailNotification(mailfrom, fromaddr, subject)
	
	def userAddedMe(self, userGuid, userHandle, screenName):
		LogEvent(INFO, self.factory.msncon.ident)
		self.factory.msncon.contactAddedMe(userHandle)
	
	def userRemovedMe(self, userHandle):
		LogEvent(INFO, self.factory.msncon.ident)
		self.factory.msncon.contactRemovedMe(userHandle)
	
	def listSynchronized(self, *args):
		LogEvent(INFO, self.factory.msncon.ident)
		self.factory.msncon._sendSavedEvents()
		self.factory.msncon.listSynchronized()
	
	def contactAvatarChanged(self, userHandle, hash):	
		LogEvent(INFO, self.factory.msncon.ident)
		self.factory.msncon.contactAvatarChanged(userHandle, hash)
	
	def gotContactStatus(self, userHandle, statusCode, screenName):	
		LogEvent(INFO, self.factory.msncon.ident)
		self.factory.msncon.contactStatusChanged(userHandle)
	
	def contactStatusChanged(self, userHandle, statusCode, screenName):
		LogEvent(INFO, self.factory.msncon.ident)
		self.factory.msncon.contactStatusChanged(userHandle)
	
	def contactPersonalChanged(self, userHandle, personal):
		LogEvent(INFO, self.factory.msncon.ident)
		self.factory.msncon.contactStatusChanged(userHandle)

	def contactOffline(self, userHandle):
		LogEvent(INFO, self.factory.msncon.ident)
		self.factory.msncon.contactStatusChanged(userHandle)
	
	def gotSwitchboardInvitation(self, sessionID, host, port, key, userHandle, screenName):
		LogEvent(INFO, self.factory.msncon.ident)
		sb = self.factory.msncon.switchboardSessions.get(userHandle)
		if sb and sb.transport:
			sb.transport.loseConnection()
		sb = OneSwitchboardSession(self.factory.msncon, userHandle)
		self.factory.msncon.switchboardSessions[userHandle] = sb
		sb.connectReply(host, port, key, sessionID)
	
	def multipleLogin(self):
		LogEvent(INFO, self.factory.msncon.ident)
		self.factory.msncon.multipleLogin()
	
	def serverGoingDown(self):
		LogEvent(INFO, self.factory.msncon.ident)
		self.factory.msncon.serverGoingDown()

	

class SwitchboardSessionBase(msn.SwitchboardClient):
	def __init__(self, msncon):
		msn.SwitchboardClient.__init__(self)
		self.msncon = msncon
		self.msnobj = msncon.notificationClient.msnobj
		self.userHandle = msncon.username
		self.ident = (msncon.ident, "INVALID!!")
		self.messageBuffer = []
		self.funcBuffer = []
		self.ready = False

	def connectionLost(self, reason):
		msn.SwitchboardClient.connectionLost(self, reason)
		LogEvent(INFO, self.ident)
		self.ready = False
		self.msncon = None
		self.msnobj = None
		self.ident = (self.ident[0], self.ident[1], "Disconnected!")

	def loggedIn(self):
		LogEvent(INFO, self.ident)
		self.ready = True
		self.flushBuffer()

	def connect(self):
		LogEvent(INFO, self.ident)
		self.ready = False
		def sbRequestAccepted((host, port, key)):
			LogEvent(INFO, self.ident)
			self.key = key
			self.reply = 0
			factory = ClientFactory()
			factory.buildProtocol = lambda addr: self
			self.msncon.connectors.append(reactor.connectTCP(host, port, factory, bindAddress=(MSNConnection.BINDADDRESS, 0)))
		def sbRequestFailed(ignored=None):
			LogEvent(INFO, self.ident)
			del self.msncon.switchboardSessions[self.remoteUser]
		d = self.msncon.notificationClient.requestSwitchboardServer()
		d.addCallbacks(sbRequestAccepted, sbRequestFailed)
	
	def connectReply(self, host, port, key, sessionID):
		LogEvent(INFO, self.ident)
		self.ready = False
		self.key = key
		self.sessionID = sessionID
		self.reply = 1
		factory = ClientFactory()
		factory.buildProtocol = lambda addr: self
		self.msncon.connectors.append(reactor.connectTCP(host, port, factory, bindAddress=(MSNConnection.BINDADDRESS, 0)))
	
	def flushBuffer(self):
		for message, noerror in self.messageBuffer[:]:
			self.messageBuffer.remove((message, noerror))
			self.sendMessage(message, noerror)
		for f in self.funcBuffer[:]:
			self.funcBuffer.remove(f)
			f()

	def failedMessage(self, *ignored):
		raise NotImplementedError

	def sendClientCaps(self):
		message = msn.MSNMessage()
		message.setHeader("Content-Type", "text/x-clientcaps")
		message.setHeader("Client-Name", "PyMSNt")
		if hasattr(self.msncon, "jabberID"):
			message.setHeader("JabberID", str(self.msncon.jabberID))
		self.sendMessage(message)
	
	def sendMessage(self, message, noerror=False):
		# Check to make sure that clientcaps only gets sent after
		# the first text type message.
		if isinstance(message, msn.MSNMessage) and message.getHeader("Content-Type").startswith("text"):
			self.sendMessage = self.sendMessageReal
			self.sendClientCaps()
			return self.sendMessage(message, noerror)
		else:
			return self.sendMessageReal(message, noerror)
	
	def sendMessageReal(self, text, noerror=False):
		if not isinstance(text, basestring):
			msn.SwitchboardClient.sendMessage(self, text)
			return
		if not self.ready:
			self.messageBuffer.append((text, noerror))
		else:
			LogEvent(INFO, self.ident)
			text = str(text.replace("\n", "\r\n").encode("utf-8"))
			def failedMessage(ignored):
				if not noerror:
					self.failedMessage(text)

			if len(text) < MSNConnection.MAXMESSAGESIZE:
				message = msn.MSNMessage(message=text)
				message.ack = msn.MSNMessage.MESSAGE_NACK

				d = msn.SwitchboardClient.sendMessage(self, message)
				if not noerror:
					d.addCallbacks(failedMessage, failedMessage)

			else:
				chunks = int(math.ceil(len(text) / float(MSNConnection.MAXMESSAGESIZE)))
				chunk = 0
				guid = msn.random_guid()
				while chunk < chunks:
					offset = chunk * MSNConnection.MAXMESSAGESIZE
					message = msn.MSNMessage(message=text[offset : offset + MSNConnection.MAXMESSAGESIZE])
					message.ack = msn.MSNMessage.MESSAGE_NACK
					message.setHeader("Message-ID", guid)
					if chunk == 0:
						message.setHeader("Chunks", str(chunks))
					else:
						message.delHeader("MIME-Version")
						message.delHeader("Content-Type")
						message.setHeader("Chunk", str(chunk))

					d = msn.SwitchboardClient.sendMessage(self, message)
					if not noerror:
						d.addCallbacks(failedMessage, failedMessage)

					chunk += 1


class MultiSwitchboardSession(SwitchboardSessionBase):
	""" Create one of me to chat to multiple contacts """

	def __init__(self, msncon):
		""" Automatically creates a new switchboard connection to the server """
		SwitchboardSessionBase.__init__(self, msncon)
		self.ident = (self.msncon.ident, repr(self))
		self.contactCount = 0
		self.groupchat = None
		self.connect()
	
	def failedMessage(self, text):
		self.groupchat.gotMessage("BOUNCE", text)
	
	def sendMessage(self, text, noerror=False):
		""" Used to send a mesage to the groupchat. Can be called immediately
		after instantiation. """
		if self.contactCount > 0:
			SwitchboardSessionBase.sendMessage(self, text, noerror)
		else:
			#self.messageBuffer.append((message, noerror))
			pass # They're sending messages to an empty room. Ignore.
	
	def inviteUser(self, userHandle):
		""" Used to invite a contact to the groupchat. Can be called immediately
		after instantiation. """
		userHandle = str(userHandle)
		if self.ready:
			LogEvent(INFO, self.ident, "immediate")
			msn.SwitchboardClient.inviteUser(self, userHandle)
		else:
			LogEvent(INFO, self.ident, "pending")
			self.funcBuffer.append(lambda: msn.SwitchboardClient.inviteUser(self, userHandle))
	
	def gotMessage(self, message):
		self.groupchat.gotMessage(message.userHandle, message.getMessage())

	def userJoined(self, userHandle, screenName=''):
		LogEvent(INFO, self.ident)
		self.contactCount += 1
		self.groupchat.contactJoined(userHandle)

	def userLeft(self, userHandle):
		LogEvent(INFO, self.ident)
		self.contactCount -= 1
		self.groupchat.contactLeft(userHandle)



class OneSwitchboardSession(SwitchboardSessionBase):
	def __init__(self, msncon, remoteUser):
		SwitchboardSessionBase.__init__(self, msncon)
		self.remoteUser = str(remoteUser)
		self.ident = (self.msncon.ident, self.remoteUser)
		self.chattingUsers = []
		self.timeout = None
	
	def connectionLost(self, reason):
		if self.timeout:
			self.timeout.cancel()
		self.timeout = None
		for message, noerror in self.messageBuffer:
			if not noerror:
				self.failedMessage(message)
		self.messageBuffer = []

		if self.msncon and self.msncon.switchboardSessions.has_key(self.remoteUser):
			# Unexpected disconnection. Must remove us from msncon
			self.msncon.switchboardSessions.pop(self.remoteUser)

		SwitchboardSessionBase.connectionLost(self, reason)

	def _ready(self):
		LogEvent(INFO, self.ident)
		self.ready = True
		for user in self.chattingUsers:
			self.userJoined(user)
		if self.timeout:
			self.timeout.cancel()
		self.timeout = None
		self.flushBuffer()

	def _switchToMulti(self, userHandle):
		LogEvent(INFO, self.ident)
		del self.msncon.switchboardSessions[self.remoteUser]
		self.__class__ = MultiSwitchboardSession
		del self.remoteUser
		self.contactCount = 0
		self.msncon.gotGroupchat(self, userHandle)
		assert self.groupchat
	
	def failedMessage(self, text):
		self.msncon.failedMessage(self.remoteUser, text)
	
	# Callbacks
	def loggedIn(self):
		LogEvent(INFO, self.ident)
		if not self.reply:
			def failCB(arg=None):
				self.timeout = None
				self.transport.loseConnection()
				if not (self.msncon and self.msncon.switchboardSessions.has_key(self.remoteUser)):
					return
				LogEvent(INFO, self.ident, "User has not joined after 30 seconds.")
				del self.msncon.switchboardSessions[self.remoteUser]
			d = self.inviteUser(self.remoteUser)
			d.addErrback(failCB)
			self.timeout = reactor.callLater(30.0, failCB)
		else:
			self._ready()
	
	def gotChattingUsers(self, users):
		for userHandle in users.keys():
			self.chattingUsers.append(userHandle)
	
	def userJoined(self, userHandle, screenName=''):
		LogEvent(INFO, self.ident)
		if not self.reply and not self.ready:
			self._ready()
		if userHandle != self.remoteUser:
			# Another user has joined, so we now have three participants.
			remoteUser = self.remoteUser
			self._switchToMulti(remoteUser)
			self.userJoined(remoteUser)
			self.userJoined(userHandle)
		else:
			def updateAvatarCB((imageData, )):
				if self.msncon:
					self.msncon.gotAvatarImageData(self.remoteUser, imageData)
			d = self.sendAvatarRequest()
			if d:
				d.addCallback(updateAvatarCB)

	def userLeft(self, userHandle):
		def wait():
			if userHandle == self.remoteUser:
				if self.msncon and self.msncon.switchboardSessions.has_key(self.remoteUser):
					del self.msncon.switchboardSessions[self.remoteUser]
		reactor.callLater(0, wait) # Make sure this is handled after everything else

	def gotMessage(self, message):
		LogEvent(INFO, self.ident)
		cTypes = [s.strip() for s in message.getHeader("Content-Type").split(';')]
		if "text/plain" == cTypes[0]:
			try:
				if len(cTypes) > 1 and cTypes[1].lower().find("utf-8") >= 0:
					text = message.getMessage().decode("utf-8")
				else:
					text = message.getMessage()
				self.msncon.gotMessage(self.remoteUser, text)
			except UnicodeDecodeError:
				LogEvent(WARN, self.ident, "Message lost!")
				self.msncon.gotMessage(self.remoteUser, "A message was lost.")
				raise
		elif "text/x-clientcaps" == cTypes[0]:
			if message.hasHeader("JabberID"):
				jid = message.getHeader("JabberID")
				self.msncon.userMapping(message.userHandle, jid)
		else:
			LogEvent(INFO, self.ident, "Discarding unknown message type.")
	
	def gotFileReceive(self, fileReceive):
		LogEvent(INFO, self.ident)
		self.msncon.gotFileReceive(fileReceive)
	
	def gotContactTyping(self, message):
		LogEvent(INFO, self.ident)
		self.msncon.gotContactTyping(message.userHandle)
	
	def sendTypingNotification(self):
		LogEvent(INFO, self.ident)
		if self.ready:
			msn.SwitchboardClient.sendTypingNotification(self)
	
	CAPS = msn.MSNContact.MSNC1 | msn.MSNContact.MSNC2 | msn.MSNContact.MSNC3 | msn.MSNContact.MSNC4
	def sendAvatarRequest(self):
		if not self.ready: return
		msnContacts = self.msncon.getContacts()
		if not msnContacts: return
		msnContact = msnContacts.getContact(self.remoteUser)
		if not (msnContact and msnContact.caps & self.CAPS and msnContact.msnobj): return
		if msnContact.msnobjGot: return
		msnContact.msnobjGot = True # This is deliberately set before we get the avatar. So that we don't try to reget failed avatars over & over
		return msn.SwitchboardClient.sendAvatarRequest(self, msnContact)
	
	def sendFile(self, msnContact, filename, filesize):
		def doSendFile(ignored=None):
			d.callback(msn.SwitchboardClient.sendFile(self, msnContact, filename, filesize))
		d = Deferred()
		if self.ready:
			reactor.callLater(0, doSendFile)
		else:
			self.funcBuffer.append(doSendFile)
		return d
	
