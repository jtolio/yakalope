# Copyright 2004-2006 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

from twisted.words.protocols.jabber.jid import internJID

import utils
import legacy
import jabw
import contact
import avatar
import config
import lang
import disco
from debug import LogEvent, INFO, WARN, ERROR



def makeSession(pytrans, jabberID, ulang):
	""" Tries to create a session object for the corresponding JabberID. Retrieves information
	from XDB to create the session. If it fails, then the user is most likely not registered with
	the transport """
	LogEvent(INFO, jabberID)
	if pytrans.sessions.has_key(jabberID):
		LogEvent(INFO, jabberID, "Removing existing session.")
		pytrans.sessions[jabberID].removeMe()
	result = pytrans.registermanager.getRegInfo(jabberID)
	if result:
		username, password = result
		return Session(pytrans, jabberID, username, password, ulang)
	else:
		return None



class Session(jabw.JabberConnection):
	""" A class to represent each registered user's session with the legacy network. Exists as long as there
	is a Jabber resource for the user available """
	
	def __init__(self, pytrans, jabberID, username, password, ulang):
		""" Initialises the session object and connects to the legacy network """
		jabw.JabberConnection.__init__(self, pytrans, jabberID)
		LogEvent(INFO, jabberID)
		
		self.pytrans = pytrans
		self.alive = True
		self.ready = False # Only ready when we're logged into the legacy service
		self.jabberID = jabberID # the JabberID of the Session's user
		self.username = username # the legacy network ID of the Session's user
		self.password = password
		self.nickname = ""
		self.avatar = None
		self.lang = ulang
		
		self.show = None
		self.status = None
		
		self.resourceList = {}
		self.groupchats = []
		
		self.legacycon = legacy.LegacyConnection(self.username, self.password, self)
		self.contactList = contact.ContactList(self)
		self.contactList.legacyList = self.legacycon.legacyList
		
		if config.sessionGreeting:
			self.sendMessage(to=self.jabberID, fro=config.jid, body=config.sessionGreeting)

		self.updateNickname("")
		self.doVCardUpdate()
		LogEvent(INFO, self.jabberID, "Created!")
	
	def removeMe(self):
		""" Safely removes the session object, including sending <presence type="unavailable"/> messages for each legacy related item on the user's contact list """
		# Send offline presence to Jabber ID
		# Delete all objects cleanly
		# Remove this Session object from the pytrans
		
		LogEvent(INFO, self.jabberID)
		
		# Mark as dead
		self.alive = False
		self.ready = False
		
		# Send offline presence to the user
		if self.pytrans:
			self.sendPresence(to=self.jabberID, fro=config.jid, ptype="unavailable")

		# Clean up stuff on the legacy service end (including sending offline presences for all contacts)
		if self.legacycon:
			self.legacycon.removeMe()
			self.legacycon = None

		if self.contactList:
			self.contactList.removeMe()
			self.contactList = None

		# Remove any groupchats we may be in
		for groupchat in self.groupchats[:]:
			groupchat.removeMe()
		
		if self.pytrans:
			# Remove us from the session list
			del self.pytrans.sessions[self.jabberID]
			# Clean up the no longer needed reference
			self.pytrans = None
		
		LogEvent(INFO, self.jabberID, "Removed!")
	
	def doVCardUpdate(self):
		def vCardReceived(el):
			if not self.alive: return
			LogEvent(INFO, self.jabberID)
			vCard = None
			for e in el.elements():
				if e.name == "vCard" and e.uri == disco.VCARDTEMP:
					vCard = e
					break
			else:
				self.legacycon.updateAvatar() # Default avatar
				return
			avatarSet = False
			name = ""
			for e in vCard.elements():
				if e.name == "NICKNAME" and e.__str__():
					name = e.__str__()
				if not name and e.name == "FN" and e.__str__():
					# Give priority to nickname
					name = e.__str__()
				if e.name == "PHOTO":
					imageData = avatar.parsePhotoEl(e)
					if not imageData:
						errback() # Possibly it wasn't in a supported format?
					self.avatar = self.pytrans.avatarCache.setAvatar(imageData)
					self.legacycon.updateAvatar(self.avatar)
					avatarSet = True
			if name:
				self.updateNickname(name)
			if not avatarSet:
				self.legacycon.updateAvatar() # Default avatar

		def errback(args=None):
			LogEvent(INFO, self.jabberID, "Error fetching avatar.")
			if self.alive:
				self.legacycon.updateAvatar()

		LogEvent(INFO, self.jabberID, "Fetching avatar.")
		d = self.sendVCardRequest(to=self.jabberID, fro=config.jid + "/msn")
		d.addCallback(vCardReceived)
		d.addErrback(errback)
	
	def updateNickname(self, nickname):
		self.nickname = nickname
		if not self.nickname:
			j = internJID(self.jabberID)
			self.nickname = j.user
		self.setStatus(self.show, self.status)
	
	def setStatus(self, show, status):
		self.show = show
		self.status = status
		self.legacycon.setStatus(self.nickname, show, status)
	
	def sendNotReadyError(self, source, resource, dest, body):
		self.sendErrorMessage(source + '/' + resource, dest, "wait", "not-allowed", lang.get(self.lang).waitForLogin, body)
	
	def findGroupchat(self, to):
		pos = to.find('@')
		if pos > 0:
			roomID = to[:pos]
		else:
			roomID = to
		
		for groupchat in self.groupchats:
			if groupchat.ID == roomID:
				return groupchat
		
		return None
	
	def nicknameReceived(self, source, dest, nickname):
		if dest.find('@') > 0: return # Ignore presence packets sent to users
		
		self.updateNickname(nickname)
	
	def avatarHashReceived(self, source, dest, avatarHash):
		if dest.find('@') > 0: return # Ignore presence packets sent to users

		if avatarHash == " ": # Setting no avatar
			self.legacycon.updateAvatar() # Default
		elif (not self.avatar) or (self.avatar and self.avatar.getImageHash() != avatarHash):
			av = self.pytrans.avatarCache.getAvatar(avatarHash)
			if av:
				self.avatar = av # Stuff in the cache is always PNG
				self.legacycon.updateAvatar(self.avatar)
			else:
				self.doVCardUpdate()
		
	def messageReceived(self, source, resource, dest, destr, mtype, body, noerror):
		if dest == config.jid:
			if body.lower().startswith("end"):
				LogEvent(INFO, self.jabberID, "Received 'end' request.")
				self.removeMe()
			return
		
		if not self.ready:
			self.sendNotReadyError(source, resource, dest, body)
			return
		
		# Sends the message to the legacy translator
		groupchat = self.findGroupchat(dest)
		if groupchat:
			# It's for a groupchat
			if destr and len(destr) > 0 and not noerror:
				self.sendErrorMessage(to=(source + "/" + resource), fro=dest, etype="cancel", condition="not-allowed", explanation=lang.get(self.lang).groupchatPrivateError, body=body)
			else:
				LogEvent(INFO, self.jabberID, "Groupchat.")
				groupchat.sendMessage(body, noerror)
		else:
			LogEvent(INFO, self.jabberID, "Message.")
			self.legacycon.sendMessage(dest, resource, body, noerror)
	
	def inviteReceived(self, source, resource, dest, destr, roomjid):
		if not self.ready:
			self.sendNotReadyError(source, resource, dest, roomjid)
			return

		if not roomjid.endswith('@' + config.jid): # Inviting a MSN user to a Jabber chatroom
			message = lang.get(self.lang).groupchatAdvocacy % (self.jabberID, config.website)
			self.legacycon.sendMessage(dest, resource, message, True)
			return

		groupchat = self.findGroupchat(roomjid)
		if groupchat:
			LogEvent(INFO, self.jabberID, "Groupchat invitation.")
			groupchat.sendContactInvite(dest)
	
	def typingNotificationReceived(self, dest, resource, composing):
		""" The user has sent typing notification to a contact on the legacy service """
		self.legacycon.userTypingNotification(dest, resource, composing)
	
	def presenceReceived(self, source, resource, to, tor, priority, ptype, show, status):
		# Checks resources and priorities so that the highest priority resource always appears as the
		# legacy services status. If there are no more resources then the session is deleted
		# Additionally checks if the presence is to a groupchat room
		groupchat = self.findGroupchat(to)
		if groupchat:
			# It's for an existing groupchat
			if ptype == "unavailable":
				# Kill the groupchat
				LogEvent(INFO, self.jabberID, "Killing groupchat.")
				groupchat.removeMe()
			else:
				if source == self.jabberID:
					LogEvent(INFO, self.jabberID, "Groupchat presence.")
					if ptype == "error":
						groupchat.removeMe()
					else:
						groupchat.userJoined(tor)
				else:
					LogEvent(INFO, self.jabberID, "Sending groupchat error presence.")
					self.sendPresence(to=(source + "/" + resource), fro=to, ptype="error")
		
		elif legacy.isGroupJID(to) and to != config.jid and not ptype:
			# Its to a groupchat JID, and the presence type is available
			if not self.ready:
				self.sendNotReadyError(source, resource, to, to)
				return

			# It's a new groupchat
			gcID = to[:to.find('@')] # Grab the room name
			LogEvent(INFO, self.jabberID, "Creating a new groupchat.")
			groupchat = legacy.LegacyGroupchat(self, resource, gcID) # Creates an empty groupchat
			groupchat.userJoined(tor)
		
		elif ptype == "probe":
			LogEvent(INFO, self.jabberID, "Responding to presence probe")
			if to == config.jid:
				self.legacycon.sendShowStatus(source)
			else:
				self.contactList.getContact(to).sendPresence(source)
		else:
			# Not for groupchat
			self.handleResourcePresence(source, resource, to, tor, priority, ptype, show, status)

		
	def handleResourcePresence(self, source, resource, to, tor, priority, ptype, show, status):
		if ptype and ptype != "unavailable": return # Ignore presence errors, probes, etc
		if to.find('@') > 0: return # Ignore presence packets sent to users
		
		existing = self.resourceList.has_key(resource)
		if ptype == "unavailable":
			if existing:
				LogEvent(INFO, self.jabberID, "Resource gone offline.")
				self.resourceOffline(resource)
			else:
				return # I don't know the resource, and they're leaving, so it's all good
		else:
			if not existing:
				LogEvent(INFO, self.jabberID, "Resource came online.")
				self.contactList.resendLists(source + "/" + resource)
			LogEvent(INFO, self.jabberID, "Setting status.")
			self.resourceList[resource] = SessionResource(show, status, priority)

		highestActive = self.highestResource()

		if highestActive:
			# If we're the highest active resource, we should update the legacy service
			LogEvent(INFO, self.jabberID, "Updating status on legacy service.")
			r = self.resourceList[highestActive]
			self.setStatus(r.show, r.status)
		else:
			LogEvent(INFO, self.jabberID, "Last resource died. Calling removeMe in 0 seconds.")
			#reactor.callLater(0, self.removeMe)
			self.removeMe()
			#FIXME Which of the above?
	
	def highestResource(self):
		""" Returns the highest priority resource """
		highestActive = None
		for checkR in self.resourceList.keys():
			if highestActive == None or self.resourceList[checkR].priority > self.resourceList[highestActive].priority: 
				highestActive = checkR
		
#		if highestActive:
#			debug.log("Session %s - highest active resource is \"%s\" at %d" % (self.jabberID, highestActive, self.resourceList[highestActive].priority))

		return highestActive
		
	
	def resourceOffline(self, resource):
		del self.resourceList[resource]
		self.legacycon.resourceOffline(resource)
	
	def subscriptionReceived(self, fro, to, subtype):
		""" Sends the subscription request to the legacy services handler """
		if to.find('@') > 0:
			if self.ready:
				LogEvent(INFO, self.jabberID, "Passing subscription to legacy service.")
				self.contactList.jabberSubscriptionReceived(to, subtype)
			else:
				self.sendPresence(fro, to, ptype="error")
		else:
			if subtype == "subscribe":
				self.sendPresence(to=self.jabberID, fro=config.jid, ptype="subscribed")
			elif subtype.startswith("unsubscribe"):
				# They want to unregister.
				jid = self.jabberID
				LogEvent(INFO, jid, "About to unregister.")
				self.pytrans.registermanager.removeRegInfo(jid)
				LogEvent(INFO, jid, "Just unregistered.")

	





class SessionResource:
	""" A convienence class to allow comparisons of Jabber resources """
	def __init__(self, show=None, status=None, priority=None):
		self.show = show
		self.status = status
		self.priority = 0
		try:
			self.priority = int(priority) 
		except TypeError: pass
		except ValueError: pass


