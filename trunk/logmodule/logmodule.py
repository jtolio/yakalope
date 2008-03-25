"""
    File Header
"""
import lucene
import time
import os.path
lucene.initVM(lucene.CLASSPATH)

"""
    Constants
"""
PATH_SEP = os.path.sep
SECONDS_IN_20_MINUTES = 1200 #(20 * 60)
MAX_TIMESTAMP = "999999999999"
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
        return True


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
        return True

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
                   timestamp, text):
        #Determine index and data paths
        index_dir = self.indexdir + username
        data_dir = self.datadir + username + PATH_SEP + protocol + PATH_SEP
        data_file = data_dir + friend_chat

        #if the index doesn't exist, we use a sepcial constructor to create it
        if os.path.isdir(index_dir) == False:
            os.makedirs(index_dir)
            luc_index = lucene.FSDirectory.getDirectory(index_dir,True)
            luc_writer = lucene.IndexWriter(luc_index,
                                            lucene.StandardAnalyzer(),True)
        else:
            luc_index = lucene.FSDirectory.getDirectory(index_dir)
            luc_writer = lucene.IndexWriter(luc_index,
                                            lucene.StandardAnalyzer())
        #Opening the index before writing to the file gives us a lock
        #on the index. As long as writing to data files occurs only
        #through this function, this is guaranteed to be an atomic
        #operation. Closing the writer releases the lock.

        if os.path.isdir(data_dir) == False:
            os.makedirs(data_dir)
        #filesize is used to determine the file offset
        if os.path.isfile(data_file) == False:
            filesize = 0
        else:
            filesize = os.path.getsize(data_file)

        datahandle = open(data_file, 'a')
        datahandle.write(str(who_sent))
        datahandle.write("\n")
        datahandle.write(str(timestamp))
        datahandle.write("\n")
        datahandle.write(str(text))
        datahandle.write("\n")

        doc = lucene.Document()
        doc.add(self._makeKeywordField('protocol',str(protocol)))
        doc.add(self._makeKeywordField('friend_chat',str(friend_chat)))
        doc.add(self._makeKeywordField('timestamp',str(timestamp)))
        doc.add(self._makeKeywordField('who_sent',str(who_sent)))
        doc.add(self._makeUnIndexedField('file_offset',str(filesize)))
        doc.add(self._makeUnStoredField('text',str(text)))

        luc_writer.addDocument(doc)
        luc_writer.close()

    """
    METHOD: LogModule::getRecentMessages

    ACCESS: public

    PARAMETERS:
        username -- Jabber user

    DESCRIPTION:
        Returns a list of messages that occurred recently based on some
        criteria.
        Current criteria is: occurred in the last 20 minutes.

    RETURNS:
        List of LogConversation objects on success
        False on failure
    """
    def getRecentConversations(self,username):
        #Determine index and data paths
        index_dir = self.indexdir + username
        data_dir = self.datadir + username

        #Load the index
        if os.path.isdir(index_dir) == True:
            luc_index = lucene.FSDirectory.getDirectory(index_dir)

            #Get the current time in UTC seconds
            curtime = int(time.time())

            #Convert to a search range
            searchstart = str(curtime - SECONDS_IN_20_MINUTES)
            searchend = str(MAX_TIMESTAMP)

            #Build and perform the query
            qtext = "timestamp:[" + searchstart + " TO " + searchend + "]"
            searcher = lucene.IndexSearcher(luc_index)
            qparser = lucene.QueryParser("text", lucene.StandardAnalyzer())
            query = qparser.parse(qtext)
            sortmethod = lucene.Sort(["protocol","friend_chat","timestamp"])
            qresults = searcher.search(query,sortmethod)

            #Fetch the results
            conversationlist = []
            for i in range(qresults.length()):
                mprotocol = qresults.doc(i).get("protocol")
                mfriend_chat = qresults.doc(i).get("friend_chat")
                mtimestamp = qresults.doc(i).get("timestamp")
                mwho_sent = qresults.doc(i).get("who_sent")
                mfileoffset = qresults.doc(i).get("file_offset")
                mrank = qresults.score(i)

                #For now just be an idiot and create a conversation for
                #each new message found
                #Revise this so it groups by conversation
                message = LogMessage('text',mtimestamp,mwho_sent)
                message.setRank(mrank)
                conversation = LogConversation(mprotocol,mfriend_chat)
                conversation.addMessage(message)

                conversationlist.append(conversation)

            return conversationlist
        else:
            #Index does not exist
            return False;




    # Functions to make Lucene document fields
    def _makeKeywordField(self,fieldname,fielddata):
        return lucene.Field(fieldname,
                            fielddata,
                            lucene.Field.Store.YES,
                            lucene.Field.Index.UN_TOKENIZED)

    def _makeUnIndexedField(self,fieldname,fielddata):
        return lucene.Field(fieldname,
                            fielddata,
                            lucene.Field.Store.YES,
                            lucene.Field.Index.NO)

    def _makeUnStoredField(self,fieldname,fielddata):
        return lucene.Field(fieldname,
                            fielddata,
                            lucene.Field.Store.NO,
                            lucene.Field.Index.TOKENIZED)





    """
    METHOD: LogModule::searchMessages

    ACCESS: public

    PARAMETERS:
        username -- Jabber user
        query -- Lucene query for searching the user's index

    DESCRIPTION:
        Returns a list of messages that matched the query.

    RETURNS:
        List of LogConversation objects on success. Certain LogMessages (1 or
        more) in each conversation will contain a rank.
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

    def addMessage(self,msg):
        self.messages.append(msg)

    def getFriendChat(self):
        return self.friend_chat

    def getProtocol(self):
        return self.protocol


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
        self.timestamp = 0
        self.whosent = ""
        self.rank = 0

    def setRank(self,newrank):
        self.rank = newrank

    def getMessageText(self):
        return self.message_text

    def getTimestamp(self):
        return self.timestamp

    def getWhoSent(self):
        return self.whosent

    def getRank(self):
        return self.rank