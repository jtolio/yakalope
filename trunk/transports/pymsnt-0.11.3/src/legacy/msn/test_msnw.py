# Copyright 2005-2006 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

"""
Test cases for msnw (MSN Wrapper)
"""

# Settings
TIMEOUT = 30.0 # Connection timeout in seconds
LOGGING = True
TWOFILES = False
FTSENDTEST = False
FTRECEIVETEST = False
USER1 = "messengertest1@hotmail.com"
PASS1 = "hellohello"
USER2 = "messengertest2@hotmail.com"
PASS2 = "hellohello"



# Twisted imports
from twisted.internet.defer import Deferred
from twisted.internet import reactor, error
from twisted.trial import unittest
from twisted.python import log

# System imports
import sys, random

# Local imports
import msnw
import msn


if LOGGING:
	log.startLogging(sys.stdout)


def clearAccount(msncon):
	""" Clears the contact list of the given MSNConnection. Returns a
	Deferred which fires when the task is complete.
	"""
	d = Deferred()
	count = 0
	checkCount = [0]
	def cb(ignored=None):
		checkCount[0] += 1
		if checkCount[0] == count:
			d.callback(None)

	for msnContact in msncon.getContacts().contacts.values():
		for list in [msn.FORWARD_LIST, msn.BLOCK_LIST, msn.ALLOW_LIST, msn.PENDING_LIST]:
			if msnContact.lists & list:
				msncon.remContact(list, msnContact.userHandle).addCallback(cb)
				count += 1

	if count == 0:
		reactor.callLater(0, d.callback, None)
	return d


####################
# Basic connection #
####################

class MSNConnection(msnw.MSNConnection):
	def __init__(self, username, password, ident, testCase):
		msnw.MSNConnection.__init__(self, username, password, ident)
		self.testCase = testCase
		self.message = None
		self.contactAdded = None

	def listSynchronized(self):
		# Now we're fully connected
		self.testCase.done = "SYNCED"
	
	def gotMessage(self, userHandle, text):
		self.testCase.done = "GOTMESSAGE"
		self.message = (userHandle, text)
	
	def contactAddedMe(self, userHandle):
		self.contactAdded = userHandle
	

class TestsUtil:
	def setUp(self):
		self.failure = None
		self.timeout = None
		self.done = False
		self.user1 = None
		self.user2 = None

	def tearDown(self):
		if self.user1:
			self.user1.logOut()
			reactor.iterate(0.1)
		if self.user2:
			self.user2.logOut()
			reactor.iterate(0.1)
	
	def doLogins(self, both=True):
		# Connect two accounts
		self.user1 = MSNConnection(USER1, PASS1, "user1", self)
		self.loop("Logging in user1.", cond="SYNCED")
		if both:
			self.user2 = MSNConnection(USER2, PASS2, "user2", self)
			self.loop("Logging in user2.", cond="SYNCED")

	def doPurgeContacts(self, both=True):
		# Purge both contact lists
		clearAccount(self.user1).addCallback(self.cb)
		self.loop("Purging user1 contact list.")
		if both:
			clearAccount(self.user2).addCallback(self.cb)
			self.loop("Purging user2 contact list.")

	def doAddContacts(self, both=True):
		# Adding users to each other's lists
		self.user1.addContact(msn.FORWARD_LIST, USER2).addCallback(self.cb)
		self.loop("Adding user2 to user1's forward list.")
		self.user1.addContact(msn.ALLOW_LIST, USER2).addCallback(self.cb)
		self.loop("Adding user2 to user1's allow list.")
		if both:
			self.user2.addContact(msn.FORWARD_LIST, USER1).addCallback(self.cb)
			self.loop("Adding user1 to user2's forward list.")
			self.user2.addContact(msn.ALLOW_LIST, USER1).addCallback(self.cb)
			self.loop("Adding user1 to user2's allow list.")

			# Check the contacts have seen each other
			reactor.iterate(0.5) # One last chance to notice each other
			self.failUnless((self.user1.contactAdded == USER2 and self.user2.contactAdded == USER1), "Contacts can't see each other.")

	def cb(self, ignored=None):
		self.done = True

	def loop(self, failMsg, cond=True, timeout=TIMEOUT):
		# Loops with a timeout
		self.done = False
		self.timeout = reactor.callLater(timeout, self.failed, "Timeout: " + failMsg)
		if cond == True:
			while not self.done:
				reactor.iterate(0.1)
		else:
			while self.done != cond:
				reactor.iterate(0.1)
		try:
			self.timeout.cancel()
		except (error.AlreadyCancelled, error.AlreadyCalled):
			pass
		if self.failure:
			self.fail(self.failure)
		if cond:
			self.failUnless((self.done == cond), "Failed: " + failMsg)
	
	def failed(self, why):
		self.failure = why
		self.done = True

# The tests!

class BasicTests(unittest.TestCase, TestsUtil):
	def setUp(self):
		TestsUtil.setUp(self)

	def tearDown(self):
		TestsUtil.tearDown(self)

	def testReconnect(self):
		self.user1 = MSNConnection(USER1, PASS1, "user1", self)
		self.loop("Looping user1.", cond="SYNCED")
		self.user1.notificationClient.transport.loseConnection()
		self.done = False
		self.loop("Looping user1.", cond="SYNCED")
	testReconnect.skip = FTRECEIVETEST or FTSENDTEST

	def testConnect(self):
		self.doLogins(both=False)
	testConnect.skip = FTRECEIVETEST or FTSENDTEST
	
	def testPurgeContacts(self):
		self.doLogins()
		self.doPurgeContacts()
	testPurgeContacts.skip = FTRECEIVETEST or FTSENDTEST
	
	def testAddContacts(self):
		self.doLogins()
		self.doPurgeContacts()
		self.doAddContacts()
	testAddContacts.skip = FTRECEIVETEST or FTSENDTEST

	def testMessageExchange(self):
		self.doLogins()
		self.doPurgeContacts()
		self.doAddContacts()
		self.user1.sendMessage(USER2, "Hi user2")
		self.loop("Timeout exchanging message.", cond="GOTMESSAGE")
		self.failUnless((self.user2.message == (USER1, "Hi user2")), "Failed to transfer message.")
	testMessageExchange.skip = FTRECEIVETEST or FTSENDTEST

	def testFileSend(self):
		if raw_input("\n\nALERT!!!\n\nPlease connect to account %s and accept the file transfer from %s. When you have received the complete file, send a message back to the client to signal success.\nType ok when you are ready: " % (USER2, USER1)).lower() != "ok":
			raise unittest.SkipTest("User didn't type 'ok'")

		data = "Testing 123\r\n" * 5000
		def accepted((yes,)):
			if yes:
				self.fileSend.write(data)
				self.fileSend.close()
			else:
				self.fail("File was not accepted.")
		def failed():
			self.fail("Transfer failed in invitation.")
		def gotFileSend((fileSend, d)):
			self.fileSend = fileSend
			d.addCallbacks(accepted, failed)

		self.doLogins(both=False)
		self.doPurgeContacts(both=False)
		self.doAddContacts(both=False)
		d = self.user1.sendFile(USER2, "myfile.txt", len(data))
		d.addCallback(gotFileSend)
		self.loop("Sending file.", cond="GOTMESSAGE", timeout=60*60)
		global TWOFILES
		if TWOFILES:
			d = self.user1.sendFile(USER2, "myfile2.txt", len(data))
			d.addCallback(gotFileSend)
			self.loop("Sending file.", cond="GOTMESSAGE", timeout=60*60)
	testFileSend.skip = not FTSENDTEST

	def testFileReceive(self):
		if raw_input("\n\nALERT!!!\n\nPlease connect to account %s and send a file transfer to %s.\nType ok when you are ready: " % (USER2, USER1)).lower() != "ok":
			raise unittest.SkipTest("User didn't type 'ok'")

		def fileFinished(data):
			#filename = "/tmp/msn" + str(random.randint(1000, 9999)) + ".dat"
			filename = "/tmp/MSNFILE_" + self.fileReceive.filename
			f = open(filename, "w")
			f.write(data)
			f.close()
			print "Got file!", filename
			# Terminate the loop in a little, let them send the BYE before
			# we drop the connection
			def wait():
				self.done = "GOTFILE"
			reactor.callLater(5, wait)

		def gotFileReceive(fileReceive):
			buffer = msn.StringBuffer(fileFinished)
			self.fileReceive = fileReceive
			self.fileReceive.accept(buffer)

		self.doLogins(both=False)
		self.user1.gotFileReceive = gotFileReceive
		self.doPurgeContacts(both=False)
		self.doAddContacts(both=False)
		self.loop("Receiving file.", cond="GOTFILE", timeout=60*60)
		global TWOFILES
		if TWOFILES:
			self.loop("Receiving file.", cond="GOTFILE", timeout=60*60)
	testFileReceive.skip = not FTRECEIVETEST

