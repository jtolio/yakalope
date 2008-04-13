import logmodule
import time

#Configuration
print 'Loading the logmodule module'
logger = logmodule.LogModule();
logger.setDataDirectory("~/yakdata/data/")
logger.setIndexDirectory("~/yakdata/index/")


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
logger.addMessage("fred",
                  "aim",
                  "sassygirl85",
                  "sassygirl85",
                  (now - (20 * T_MIN)),
                  "<span style='font-weight: bold;'>Hey! This is your first message.</span>")
logger.addMessage("fred",
                  "aim",
                  "sassygirl85",
                  "fred",
                  (now - (19 * T_MIN)),
                  "What's up Rhonda?")
logger.addMessage("fred",
                  "aim",
                  "sassygirl85",
                  "fred",
                  (now - (19 * T_MIN) + 16),
                  "Oh, and your font sucks. Just use plain text. It is the win.")
logger.addMessage("fred",
                  "aim",
                  "sassygirl85",
                  "sassygirl85",
                  (now - (16 * T_MIN)),
                  "<span style='font-weight: bold;'>Shut your face noob. Sudo make me a sandwich.</span>")
logger.addMessage("fred",
                  "aim",
                  "scoobert71",
                  "fred",
                  (now - (17 * T_MIN)),
                  "Time to go Scoob.")
logger.addMessage("fred",
                  "aim",
                  "scoobert71",
                  "scoobert71",
                  (now - (17 * T_MIN) + 11),
                  "<span>Roh-Kay</span>")
logger.addMessage("shaggy",
                  "aim",
                  "scoobert71",
                  "shaggy",
                  (now - (17 * T_MIN)),
                  "<span>Zoinks Scooby! Like, free Tato Skins!</span>")
logger.addMessage("shaggy",
                  "aim",
                  "scoobert71",
                  "scoobert71",
                  (now - (17 * T_MIN) + 33),
                  "<span>Ruh-Roh</span>")

time.sleep(2)


#Get a list of recent messages
print ' '
print 'Getting recent conversations for fred'
results = logger.getRecentConversations("fred")
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
print 'Getting recent conversations for shaggy'
results = logger.getRecentConversations("shaggy")
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
print 'Performing a search for "Rhonda"'
results = logger.searchMessages("fred","Rhonda")
print len(results), ' results found'
for i in range(len(results)):
    print "===New Conversation==="
    print results[i].getFriendChat(),",",
    print results[i].getProtocol()
    for j in range(len(results[i].messages)):
        print results[i].messages[j].getID(),",",
        print results[i].messages[j].getRank(),",",
        print results[i].messages[j].getTimestamp(),",",
        print results[i].messages[j].getWhoSent(),",",
        print results[i].messages[j].getMessageText()
