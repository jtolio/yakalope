import logmodule
import time

#Configuration
print 'Loading the logmodule module'
logger = logmodule.LogModule();
logger.setDataDirectory("/home/janke/yakdata/data/")
logger.setIndexDirectory("/home/janke/yakdata/index/")


#Some constants to make things easier
print ' '
print 'Setting constants'
T_MIN = 60
T_HOUR = 60*60
T_DAY = 60*60


#Enter in some messages, relative to now
now = int(time.time())
print ' '
print 'Entering some messages'
logger.addMessage("Skidmark@localhost",
                  "aim",
                  "SoAndSo",
                  "Skidmark@localhost",
                  (now - (15 * T_MIN)),
                  "<span style='font-weight: bold;'>1</span>")
logger.addMessage("Skidmark@localhost",
                  "aim",
                  "SoAndSo",
                  "Skidmark@localhost",
                  (now - (14 * T_MIN)),
                  "<span style='font-weight: bold;'>2</span>")
logger.addMessage("Skidmark@localhost",
                  "aim",
                  "SoAndSo",
                  "Skidmark@localhost",
                  (now - (13 * T_MIN)),
                  "<span style='font-weight: bold;'>3</span>")
logger.addMessage("Skidmark@localhost",
                  "aim",
                  "SoAndSo",
                  "Skidmark@localhost",
                  (now - (12 * T_MIN)),
                  "<span style='font-weight: bold;'>4</span>")
logger.addMessage("Skidmark@localhost",
                  "aim",
                  "SoAndSo",
                  "Skidmark@localhost",
                  (now - (11 * T_MIN)),
                  "<span style='font-weight: bold;'>5</span>")
logger.addMessage("Skidmark@localhost",
                  "aim",
                  "SoAndSo",
                  "Skidmark@localhost",
                  (now - (10 * T_MIN)),
                  "<span style='font-weight: bold;'>6</span>")
logger.addMessage("Skidmark@localhost",
                  "aim",
                  "SoAndSo",
                  "Skidmark@localhost",
                  (now - (9 * T_MIN)),
                  "<span style='font-weight: bold;'>7</span>")
logger.addMessage("Skidmark@localhost",
                  "aim",
                  "SoAndSo",
                  "Skidmark@localhost",
                  (now - (8 * T_MIN)),
                  "<span style='font-weight: bold;'>8 - wombat</span>")
logger.addMessage("Skidmark@localhost",
                  "aim",
                  "SoAndSo",
                  "Skidmark@localhost",
                  (now - (7 * T_MIN)),
                  "<span style='font-weight: bold;'>9</span>")
logger.addMessage("Skidmark@localhost",
                  "aim",
                  "SoAndSo",
                  "Skidmark@localhost",
                  (now - (6 * T_MIN)),
                  "<span style='font-weight: bold;'>10 - wombat</span>")
logger.addMessage("Skidmark@localhost",
                  "aim",
                  "SoAndSo",
                  "Skidmark@localhost",
                  (now - (5 * T_MIN)),
                  "<span style='font-weight: bold;'>11</span>")
logger.addMessage("Skidmark@localhost",
                  "aim",
                  "SoAndSo",
                  "Skidmark@localhost",
                  (now - (4 * T_MIN)),
                  "<span style='font-weight: bold;'>12</span>")
logger.addMessage("Skidmark@localhost",
                  "aim",
                  "SoAndSo",
                  "Skidmark@localhost",
                  (now - (3 * T_MIN)),
                  "<span style='font-weight: bold;'>13</span>")
logger.addMessage("Skidmark@localhost",
                  "aim",
                  "SoAndSo",
                  "Skidmark@localhost",
                  (now - (2 * T_MIN)),
                  "<span style='font-weight: bold;'>14 - wombat</span>")
logger.addMessage("Skidmark@localhost",
                  "aim",
                  "Other",
                  "Skidmark@localhost",
                  (now - (10 * T_MIN)),
                  "<span style='font-weight: bold;'>nooooo</span>")

time.sleep(1)


#Get a list of recent messages
print ' '
print 'Getting recent conversations for Skidmark@localhost'
results = logger.getRecentConversations("Skidmark@localhost")
print len(results), ' results found'
for i in range(len(results)):
    print "===New Conversation==="
    print results[i].getFriendChat(),",",
    print results[i].getProtocol()
    for j in range(len(results[i].messages)):
        print results[i].messages[j].getTimestamp(),",",
        print results[i].messages[j].getWhoSent(),",",
        print results[i].messages[j].getMessageText()

print ' '
print 'Performing a search for "wombat"'
results = logger.searchMessages("Skidmark@localhost","wombat")
print len(results), ' results found'
for result in results:
    print "===New Conversation================================"
    print "Rank: ", result.getRank()
    print "Friend: ", result.getFriendChat()
    print "Protocol: ", result.getProtocol()
    print "---------------------------------------------------"
    for m in result.messages:
        print m.getID(),",",
        print m.getRank(),",",
        print m.getTimestamp(),",",
        print m.getWhoSent(),",",
        print m.getMessageText()
