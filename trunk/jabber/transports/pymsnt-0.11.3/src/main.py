# Copyright 2004-2006 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

import os, os.path, time, sys, codecs, getopt
reload(sys)
sys.setdefaultencoding("utf-8")
sys.stdout = codecs.lookup('utf-8')[-1](sys.stdout)


# Find the best reactor
selectWarning = "Unable to install any good reactors (kqueue, epoll, poll).\nWe fell back to using select. You may have scalability problems.\nThis reactor will not support more than 1024 connections at a time."
reactors = [("epollreactor", True), ("pollreactor", True), ("selectreactor", False), ("default", False)]
for tryReactor, good in reactors:
	try:
		bestReactor = __import__("twisted.internet." + tryReactor)
		if not good:
			print >> sys.stderr, selectWarning
		break
	except ImportError:
		pass
else:
	print >> sys.stderr, "Unable to find a reactor. Please make sure you have Twisted properly installed.\nExiting..."
	sys.exit(1)


import twistfix
twistfix.main()


# Must load config before everything else
import config
import xmlconfig
configFile = "config.xml"
configOptions = {}
opts, args = getopt.getopt(sys.argv[1:], "bc:o:dDgtlp:h", ["background", "config=", "option=", "debug", "Debug", "garbage", "traceback", "log=", "pid=", "help"])
for o, v in opts:
	if o in ("-c", "--config"):
		configFile = v
	elif o in ("-b", "--background"):
		config.background = True
	elif o in ("-d", "--debug"):
		config.debugLevel = "2"
	elif o in ("-D", "--Debug"):
		config.debugLevel = "3"
	elif o in ("-g", "--garbage"):
		import gc
		gc.set_debug(gc.DEBUG_LEAK|gc.DEBUG_STATS)
	elif o in ("-t", "--traceback"):
		config.debugLevel = "1"
	elif o in ("-l", "--log"):
		config.debugFile = v
	elif o in ("-p", "--pid"):
		config.pid = v
	elif o in ("-o", "--option"):
		var, setting = v.split("=", 2)
		configOptions[var] = setting
	elif o in ("-h", "--help"):
		print "%s [options]" % sys.argv[0]
		print "   -h                  print this help"
		print "   -b                  daemonize/background transport"
		print "   -c <file>           read configuration from this file"
		print "   -d                  print debugging output"
		print "   -D                  print extended debugging output"
		print "   -g                  print garbage collection output"
		print "   -t                  print debugging only on traceback"
		print "   -l <file>           write debugging output to file"
		print "   -p <file>           write process ID to file"
		print "   -o <var>=<setting>  set config var to setting"
		sys.exit(0)

xmlconfig.reloadConfig(configFile, configOptions)

if config.reactor:
	# They picked their own reactor. Lets install it.
	del sys.modules["twisted.internet.reactor"]
	if config.reactor == "epoll":
		from twisted.internet import epollreactor
		epollreactor.install()
	elif config.reactor == "poll":
		from twisted.internet import pollreactor
		pollreactor.install()
	elif config.reactor == "kqueue":
		from twisted.internet import kqreactor
		kqreactor.install()
	elif len(config.reactor) > 0:
		print >> sys.stderr, "Unknown reactor: ", config.reactor, ". Using best available reactor."


from twisted.internet import reactor, task
from twisted.internet.defer import Deferred
from twisted.words.xish.domish import Element
from twisted.words.protocols.jabber import component
from twisted.words.protocols.jabber.jid import internJID

from debug import LogEvent, INFO, WARN, ERROR

import debug
import utils
import xdb
import avatar
import session
import jabw
import disco
import register
import misciq
import ft
import lang
import legacy
import housekeep



class PyTransport(component.Service):
	def __init__(self):
		LogEvent(INFO)
		LogEvent(INFO, msg="Reactor: " + str(reactor))

		# Discovery, as well as some builtin features
		self.discovery = disco.ServerDiscovery(self)
		self.discovery.addIdentity("gateway", legacy.id, config.discoName, config.jid)
		self.discovery.addIdentity("conference", "text", config.discoName + " Chatrooms", config.jid)
		self.discovery.addFeature(disco.XCONFERENCE, None, config.jid) # So that clients know you can create groupchat rooms on the server
		self.discovery.addFeature("jabber:iq:conference", None, config.jid) # We don't actually support this, but Psi has a bug where it looks for this instead of the above
		self.discovery.addIdentity("client", "pc", "MSN Messenger", "USER")
		self.discovery.addIdentity("conference", "text", "MSN Groupchat", "ROOM")
		
		self.xdb = xdb.XDB(config.jid, legacy.mangle)
		self.avatarCache = avatar.AvatarCache()
		self.registermanager = register.RegisterManager(self)
		self.gatewayTranslator = misciq.GatewayTranslator(self)
		self.versionTeller = misciq.VersionTeller(self)
		self.pingService = misciq.PingService(self)
		self.adHocCommands = misciq.AdHocCommands(self)
		self.vCardFactory = misciq.VCardFactory(self)
		self.iqAvatarFactor = misciq.IqAvatarFactory(self)
		self.connectUsers = misciq.ConnectUsers(self)
		if config.ftJabberPort:
			self.ftSOCKS5Receive = ft.Proxy65(int(config.ftJabberPort))
			self.ftSOCKS5Send = misciq.Socks5FileTransfer(self)
		if config.ftOOBPort:
			self.ftOOBReceive = ft.FileTransferOOBReceive(int(config.ftOOBPort))
			self.ftOOBSend = misciq.FileTransferOOBSend(self)
		self.statistics = misciq.Statistics(self)
		self.startTime = int(time.time())

		self.xmlstream = None
		self.sessions = {}
		
		# Groupchat ID handling
		self.lastID = 0
		self.reservedIDs = []

		# Message IDs
		self.messageID = 0
		
		self.loopTask = task.LoopingCall(self.loopFunc)
		self.loopTask.start(60.0)

	def removeMe(self):
		LogEvent(INFO)
		for session in self.sessions.copy():
			self.sessions[session].removeMe()
	
	def makeMessageID(self):
		self.messageID += 1
		return str(self.messageID)
	
	def makeID(self):
		newID = "r" + str(self.lastID)
		self.lastID += 1
		if self.reservedIDs.count(newID) > 0:
			# Ack, it's already used.. Try again
			return self.makeID()
		else:
			return newID
	
	def reserveID(self, ID):
		self.reservedIDs.append(ID)
	
	def loopFunc(self):
		numsessions = len(self.sessions)

		#if config.debugOn and numsessions > 0:
		#	print "Sessions:"
		#	for key in self.sessions:
		#		print "\t" + self.sessions[key].jabberID
	
		self.statistics.stats["Uptime"] = int(time.time()) - self.startTime
		self.statistics.stats["OnlineUsers"] = numsessions
		legacy.updateStats(self.statistics)
		if numsessions > 0:
			oldDict = self.sessions.copy()
			self.sessions = {}
			for key in oldDict:
				s = oldDict[key]
				if not s.alive:
					LogEvent(WARN, "", "Ghost session found.")
					# Don't add it to the new dictionary. Effectively removing it
				else:
					self.sessions[key] = s
	
	def componentConnected(self, xmlstream):
		LogEvent(INFO)
		self.xmlstream = xmlstream
		self.xmlstream.addObserver("/iq", self.discovery.onIq)
		self.xmlstream.addObserver("/presence", self.onPresence)
		self.xmlstream.addObserver("/message", self.onMessage)
		self.xmlstream.addObserver("/route", self.onRouteMessage)
		if config.useXCP:
			pres = Element((None, "presence"))
			pres.attributes["to"] = "presence@-internal"
			pres.attributes["from"] = config.compjid
			x = pres.addElement("x")
			x.attributes["xmlns"] = "http://www.jabber.com/schemas/component-presence.xsd"
			x.attributes["xmlns:config"] = "http://www.jabber.com/config"
			x.attributes["config:version"] = "1"
			x.attributes["protocol-version"] = "1.0"
			x.attributes["config-ns"] = legacy.url + "/component"
			self.send(pres)
	
	def componentDisconnected(self):
		LogEvent(INFO)
		self.xmlstream = None
	
	def onRouteMessage(self, el):
		for child in el.elements():
			if child.name == "message":
				self.onMessage(child)
			elif child.name == "presence":
				# Ignore any presence broadcasts about other XCP components
				if child.getAttribute("to") and child.getAttribute("to").find("@-internal") > 0: return
				self.onPresence(child)
			elif child.name == "iq":
				self.discovery.onIq(child)
	
	def onMessage(self, el):
		fro = el.getAttribute("from")
		try:
			froj = internJID(fro)
		except Exception, e:
			LogEvent(WARN, "", "Failed stringprep.")
			return
		mtype = el.getAttribute("type")
		s = self.sessions.get(froj.userhost(), None)
		if mtype == "error" and s:
			LogEvent(INFO, s.jabberID, "Removing session because of message type=error")
			s.removeMe()
		elif s:
			s.onMessage(el)
		elif mtype != "error":
			to = el.getAttribute("to")
			ulang = utils.getLang(el)
			body = None
			for child in el.elements():
				if child.name == "body":
					body = child.__str__()
			LogEvent(INFO, "", "Sending error response to a message outside of session.")
			jabw.sendErrorMessage(self, fro, to, "auth", "not-authorized", lang.get(ulang).notLoggedIn, body)
			jabw.sendPresence(self, fro, to, ptype="unavailable")
	
	def onPresence(self, el):
		fro = el.getAttribute("from")
		to = el.getAttribute("to")
		try:
			froj = internJID(fro)
			toj = internJID(to)
		except Exception, e:
			LogEvent(WARN, "", "Failed stringprep.")
			return

		ptype = el.getAttribute("type")
		s = self.sessions.get(froj.userhost())
		if ptype == "error" and s:
			LogEvent(INFO, s.jabberID, "Removing session because of message type=error")
			s.removeMe()
		elif s:
			s.onPresence(el)
		else:
			ulang = utils.getLang(el)
			ptype = el.getAttribute("type")
			if to.find('@') < 0:
				# If the presence packet is to the transport (not a user) and there isn't already a session
				if not el.getAttribute("type"): # Don't create a session unless they're sending available presence
					LogEvent(INFO, "", "Attempting to create a new session.")
					s = session.makeSession(self, froj.userhost(), ulang)
					if s:
						self.statistics.stats["TotalUsers"] += 1
						self.sessions[froj.userhost()] = s
						LogEvent(INFO, "", "New session created.")
						# Send the first presence
						s.onPresence(el)
					else:
						LogEvent(INFO, "", "Failed to create session")
						jabw.sendMessage(self, to=froj.userhost(), fro=config.jid, body=lang.get(ulang).notRegistered)
				
				elif el.getAttribute("type") != "error":
					LogEvent(INFO, "", "Sending unavailable presence to non-logged in user.")
					jabw.sendPresence(self, fro, to, ptype="unavailable")
					return
			
			elif ptype and (ptype.startswith("subscribe") or ptype.startswith("unsubscribe")):
				# They haven't logged in, and are trying to change subscription to a user
				# No, lets not log them in. Lets send an error :)
				jabw.sendPresence(self, fro, to, ptype="error")
				
				# Lets log them in and then do it
				#LogEvent(INFO, "", "Attempting to create a session to do subscription stuff.")
				#s = session.makeSession(self, froj.userhost(), ulang)
				#if s:
				#	self.sessions[froj.userhost()] = s
				#	LogEvent(INFO, "", "New session created.")
				#	# Tell the session there's a new resource
				#	s.handleResourcePresence(froj.userhost(), froj.resource, toj.userhost(), toj.resource, 0, None, None, None)
				#	# Send this subscription
				#	s.onPresence(el)


class App:
	def __init__(self):
		# Check for any other instances
		if config.pid and os.name != "posix":
			config.pid = ""
		if config.pid:
			twistd.checkPID(config.pid)

		# Do any auto-update stuff
		housekeep.init()
		
		# Daemonise the process and write the PID file
		if config.background and os.name == "posix":
			twistd.daemonize()
		if config.pid:
			self.writePID()

		# Initialise debugging, and do the other half of SIGHUPstuff
		debug.reloadConfig()
		legacy.reloadConfig()

		# Start the service
		jid = config.jid
		if config.useXCP and config.compjid:
			jid = config.compjid
		self.c = component.buildServiceManager(jid, config.secret, "tcp:%s:%s" % (config.mainServer, config.port))
		self.transportSvc = PyTransport()
		self.transportSvc.setServiceParent(self.c)
		self.c.startService()
		reactor.addSystemEventTrigger('before', 'shutdown', self.shuttingDown)
	
	def writePID(self):
		# Create a PID file
		pid = str(os.getpid())
		pf = open(config.pid, "w")
		pf.write("%s\n" % pid)
		pf.close()

	def shuttingDown(self):
		self.transportSvc.removeMe()
		# Keep the transport running for another 3 seconds
		def cb(ignored=None):
			if config.pid:
				twistd.removePID(config.pid)
		d = Deferred()
		d.addCallback(cb)
		reactor.callLater(3.0, d.callback, None)
		return d



def SIGHUPstuff(*args):
	global configFile, configOptions
	xmlconfig.reloadConfig(configFile, configOptions)
	if config.pid and os.name != "posix":
		config.pid = ""
	debug.reloadConfig()
	legacy.reloadConfig()

if os.name == "posix":
	import signal
	# Set SIGHUP to reload the config file & close & open debug file
	signal.signal(signal.SIGHUP, SIGHUPstuff)
	# Load some scripts for PID and daemonising
	from twisted.scripts import _twistd_unix as twistd


def main():
	# Create the application
	app = App()
	reactor.run()

if __name__ == "__main__":
	main()

