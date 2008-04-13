import logmodule
import time

#Configuration
print 'Loading the logmodule module'
logger = logmodule.LogModule();
logger.setDataDirectory("O:\\yakalope\\logging\\data\\")
logger.setIndexDirectory("O:\\yakalope\\logging\\index\\")

#Get a list of messages
print ' '
results = logger.searchMessages("torhelge@localhost","friend_chat:janke*")
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