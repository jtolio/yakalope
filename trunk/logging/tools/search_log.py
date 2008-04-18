import logmodule
import sys

if len(sys.argv) != 5:
    print "Usage:",sys.argv[0],"[data directory] [index directory] [username] [query]"
else:
    #Prepare the logger module
    logmod = logmodule.LogModule();
    logmod.setDataDirectory(sys.argv[1])
    logmod.setIndexDirectory(sys.argv[2])
    
    #Get a list of messages    print ' '
    results = logmod.searchMessages(sys.argv[3],sys.argv[4])
    print len(results), ' results found'
    for con in results:
        print ""
        print "==========================================================="
        print "=    New Conversation                                     ="
        print "==========================================================="
        print "  Friend / Chat:", con.getFriendChat()
        print "  Protocol:", con.getProtocol()
        print "  Rank:", con.getRank()
        print "-----------------------------------------------------------"
        print "ID \t RANK \t TIME \t WHO SENT \t TEXT"
        for msg in con.messages:
            print msg.getID(),"\t",
            print msg.getRank(),"\t",
            print msg.getTimestamp(),"\t",
            print msg.getWhoSent(),"\t",
            print msg.getMessageText()
