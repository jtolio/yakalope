import logmodule
import time


#Setup Index
print 'Loading the logmodule module'
logger = logmodule.LogModule();
logger.setDataDirectory("O:\\yakalope\\logmodule\\data\\")
logger.setIndexDirectory("O:\\yakalope\\logmodule\\index\\")

curtime = int(time.time())
#Add 2 messages 1 per minute after "now" (not including now)
print 'Adding 2 post-now messages'
starttime = curtime + 60
endtime = curtime + (60 * 2)
while starttime <= endtime:
    logger.addMessage("username", "protocol", "friend_chat", "who_sent", starttime, "testing: " + str(curtime))
    starttime += 60


#Add 2 messages 1 per minute before of "now" (including now)
print 'Adding 2 pre-now messages'
starttime = curtime - (60 * 32)
endtime = curtime - (30*60)
while starttime <= endtime:
    logger.addMessage("username", "protocol", "friend_chat", "who_sent", starttime, "testing: " + str(curtime))
    starttime += 60


#Get a list of recent messages
results = logger.getRecentConversations("username")
print len(results), ' results found'
print ' '

for i in range(len(results)):
    print "===New Conversation==="
    print results[i].getFriendChat(),",",
    print results[i].getProtocol()
    for j in range(len(results[i].messages)):
        print results[i].messages[j].getTimestamp(),",",
        print results[i].messages[j].getWhoSent(),",",
        print results[i].messages[j].getMessageText()
