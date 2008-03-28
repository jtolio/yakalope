# Copyright 2004-2006 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

# -- DO NOT EDIT THIS FILE --
# This file is -not- to be edited by hand.  It is simply defaults.
# Actual configuration should be done in config.xml in the root directory.
# -- DO NOT EDIT THIS FILE --

if type(True) != bool: from bool import bool

class DeprecatedVariable:
	def __init__(self, msg):
		self.msg = msg

	def __call__(self):
		print "WARNING: %s" % self.msg

jid = "aim.localhost"
confjid = "conference.aim.localhost"
compjid = ""
spooldir = ".."
pid = ""
mainServer = "127.0.0.1"
mainServerJID = ""
website = ""
reactor = ""
port = 5347
webport = 0
secret = "secret"
websecret = DeprecatedVariable("websecret is no longer used as web interface auths against JID now.")
lang = "en"
aimServer = "login.oscar.aol.com"
aimPort = 5190
sessionGreeting = ""
registerMessage = ""
crossChat = bool(False)
debugLevel = 0 # 0->None, 1->Traceback, 2->WARN,ERROR, 3->INFO,WARN,ERROR
debugFile = ""
disableRegister = bool(False)
disableXHTML = bool(False)
enableAutoInvite = bool(False)
tracebackDebug = bool(False)
socksProxyServer = ""
socksProxyPort = 0
admins = []
xdbDriver = "xmlfiles"
xdbDriver_mysql = {}
xdbDriver_xmlfiles = {}
useXCP = bool(False)
useComponentBinding = bool(False)
useRouteWrap = bool(False)
useJ2Component = DeprecatedVariable("useJ2Component has been split up into useComponentBinding and useRouteWrap.")
saslUsername = ""
avatarsOnlyOnChat = bool(False)
disableDefaultAvatar = bool(False)
disableAvatars = bool(False)
disableMailNotifications = bool(False)
messageArchiveJID = ""
authRegister = ""
authRegister_LDAP = {}
disableIQAvatars = bool(False)
disableVCardAvatars = bool(False)
#disablePEPAvatars = bool(False)
disableAwayMessage = bool(False)
