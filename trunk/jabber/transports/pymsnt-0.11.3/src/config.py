# This file contains the default settings for various options.
# Please edit config.xml instead of this file

jid = "msn"
host = "127.0.0.1"
compjid = ""
spooldir = ""
discoName = "MSN Transport"

mainServer = "127.0.0.1"
website = ""
port = "5347"
secret = "secret"

lang = "en"

mailNotifications = False
sessionGreeting = ""
registerMessage = ""
allowRegister = False
getAllAvatars = False
groupchatTimeout = "180"
useXCP = False

ftJabberPort = ""
ftOOBPort = ""
ftOOBRoot = "http://" + host + "/"
ftSizeLimit = "0"
ftRateLimit = "0"

admins = []

reactor = ""
background = False
pid = ""

debugLevel = "0" # 0->None, 1->Traceback, 2->WARN,ERROR, 3->INFO,WARN,ERROR
_debugLevel = 0 # Maintained by debug.reloadConfig as an int
debugFile = ""
