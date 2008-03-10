"""
    File Header
"""
import lucene


"""
    CLASS: LogModule
"""
class LogModule:
    def __init__(self):
        self.datadir = "data"
        self.indexdir = "index"

    """
    METHOD: LogModule::setDataDirectory

    ACCESS: public

    PARAMETERS:
        location -- Full path of the data directory. Be sure to include a
                    slash at the end of the path.

    DESCRIPTION:
        Sets the directory in which it can find the data files. Data files
        store the actual formatted text of the messages. If the directory
        does not exist, one will be created.

    RETURNS:
        True on success
        False on failure
    """
    def setDataDirectory(self,location):
        if os.path.isdir(location) == False:
            try:
                os.makedirs(location)
            except OSError:
                return False #Could not make the directory
        self.datadir = location


    """
    METHOD: LogModule::setIndexDirectory

    ACCESS: public

    PARAMETERS:
        location -- Full path of the index directory. Be sure to include
                    a slash at the end of the path.

    DESCRIPTION:
        Sets the directory in which it can find the index files. Index
        files are a collection of files used to store the Lucene index for
        the messages.

    RETURNS:
        True on success
        False on failure
    """
    def setIndexDirectory(self,location):
        if os.path.isdir(location) == False:
            try:
                os.makedirs(location)
            except OSError:
                return False #Could not make the directory
        self.indexdir = location

    """
    METHOD: LogModule::addMessage

    ACCESS: public

    PARAMETERS:
        username -- Jabber user
        protocol -- Service protocol used (i.e. AIM, MSN, etc.)
        friend_chat -- Friend or chat the conversation is with. Do not include
                       the protocol in this parameter.
        who_sent -- Username who sent the message. Outside of group chats,
                    this will typically be either our user's username or the
                    friend name. Do not include the protocol in this
                    parameter.
        timestamp -- Unix timestamp in GMT that the message was sent/received

    DESCRIPTION:
        This function is the basis of the logging module. Every message coming
        into and leaving the system should be added via this module.

    RETURNS:
        True on success
        False on failure
    """
    def addMessage(self, username, protocol, friend_chat, who_sent,
                   timestamp):
        path_sep = os.path.sep
        print 'Not yet written'


    """
    METHOD: LogModule::getRecentMessages

    ACCESS: public

    PARAMETERS:
        username -- Jabber user
        protocol -- Service protocol used (i.e. AIM, MSN, etc.)
        friend_chat -- Friend or chat the conversation is with. Do not include
                       the protocol in this parameter.

    DESCRIPTION:
        Returns a list of messages that occurred recently with a friend or
        in a chat room based on some criteria.
        Current criteria is: occurred in the last 20 minutes.

    RETURNS:
        List of LogConversation objects on success
        False on failure
    """
    def getRecentConversations(self,username, protocol, friend_chat):
        print 'Not yet written'


    """
    METHOD: LogModule::searchMessages

    ACCESS: public

    PARAMETERS:
        username -- Jabber user
        query -- Lucene query for searching the user's index

    DESCRIPTION:
        Returns a list of messages that matched the query

    RETURNS:
        List of LogConversation objects on success
        False on failure
    """
    def searchMessages(self,username, query):
        print 'Not yet written'


"""
    CLASS: LogConversation

    DESCRIPTION:
        This class represents a conversation between a user of our service and
        another user. Each conversation consists of a protocol, the friend or
        chatroom in which the conversation was taking place, and a series of
        messages.
        Note: A conversation may not necessarily contain an entire
        conversation. Instead, it will usually be a subset of the conversation
        over a short range of time.
"""
class LogConversation:
    def __init__(self,protocol,friend_chat):
        self.protocol = ""
        self.friend_chat = ""
        self.messages = []


"""
    CLASS: LogMessage

    ACCESS: public

    DESCRIPTION:
        This class represents a message inside of a conversation. Each message
        consists of the formatted message text, the username of who sent the
        message, and the GMT timestamp in which the message was sent or
        received by our server.
"""
class LogMessage:
    def __init__(self,message_text,timestamp,whosent):
        self.message_text = ""
        self.timestamp = ""
        self.whosent = ""

    def getMessageText(self):
        #NOTE FOR THE FUTURE: we could wait to fetch from the data files until
        # this function gets called, but we would lose any optimizations we
        # get from loading all the messages from the same file at once.
        print 'Not yet written'

    def getTimestamp(self):
        print 'Not yet written'

    def getWhoSent(self):
        print 'Not yet written'

