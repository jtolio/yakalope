"""
    File Header
"""
import lucene
import time
import re
import os.path
lucene.initVM(lucene.CLASSPATH)

"""
    Constants
"""
PATH_SEP = os.path.sep
SECONDS_IN_5_MINUTES = 300 #(5 * 60)
SECONDS_IN_20_MINUTES = 1200 #(20 * 60)
MAX_TIMESTAMP = "999999999999" #the end of time...
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
        #Append a PATH_SEP if it is not the last character
        if location[-1] == PATH_SEP:
            loc = location
        else:
            loc = location + PATH_SEP

        if os.path.isdir(loc) == False:
            try:
                os.makedirs(loc)
            except OSError:
                return False #Could not make the directory
        self.datadir = loc
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
        #Append a PATH_SEP if it is not the last character
        if location[-1] == PATH_SEP:
            loc = location
        else:
            loc = location + PATH_SEP

        if os.path.isdir(loc) == False:
            try:
                os.makedirs(loc)
            except OSError:
                return False #Could not make the directory
        self.indexdir = loc
        return True

    """
    METHOD: LogModule::addMessage

    ACCESS: public

    PARAMETERS:
        username -- Jabber user
        xprotocol -- Service protocol used (i.e. AIM, MSN, etc.)
        xfriend_chat -- Friend or chat the conversation is with. Do not include
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
    def addMessage(self, username, xprotocol, xfriend_chat, who_sent,
                   timestamp, text):
        #Clean up protocol and friend_chat fields
        """ For some unknown reason, PyLucene (and probably Lucene as well)
            seems to have problems searching for things like SoAndSo but
            has no problems searching for soandso. To prevent headaches in
            the future we simply set it all to lowercase since the case
            does not matter for these fields."""
        protocol = xprotocol.lower()
        friend_chat = xfriend_chat.lower()

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
        datahandle.write(str(len( str(text) ))) #what a mess
        datahandle.write("\n")
        datahandle.write(str(text))
        datahandle.write("\n")

        doc = lucene.Document()
        doc.add(self.__makeKeywordField('protocol',str(protocol)))
        doc.add(self.__makeKeywordField('friend_chat',str(friend_chat)))
        clean_timestamp = self.__padTimestamp(timestamp)
        doc.add(self.__makeKeywordField('timestamp',clean_timestamp))
        doc.add(self.__makeKeywordField('who_sent',str(who_sent)))
        doc.add(self.__makeUnIndexedField('file_offset',str(filesize)))
        clean_text = re.sub("<[^>]*>"," ",str(text))
        doc.add(self.__makeUnStoredField('text',clean_text))

        luc_writer.addDocument(doc)
        luc_writer.close()

    """
    METHOD: LogModule::getRecentConversations

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
            searchstart = self.__padTimestamp(curtime - SECONDS_IN_20_MINUTES)
            searchend = self.__padTimestamp(MAX_TIMESTAMP)

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
                mtimestamp = int(qresults.doc(i).get("timestamp"))
                mwho_sent = qresults.doc(i).get("who_sent")
                mfileoffset = int(qresults.doc(i).get("file_offset"))
                mrank = qresults.score(i)

                #This is a really bad and slow method that should
                #be optimized at a later date.
                #Simply search through all previously retrieved
                #conversations and check for a match. If match is
                #found, add it, otherwise create a new conversation.
                messagetext = self.__getMessageFromFile(username,mfriend_chat,
                                                        mprotocol,mfileoffset)
                message = LogMessage(messagetext,mtimestamp,mwho_sent)
                message.setRank(mrank)

                found = False
                for j in range(len(conversationlist)):
                    if conversationlist[j].getProtocol() == mprotocol and \
                       conversationlist[j].getFriendChat() == mfriend_chat:
                        found = True
                        conversationlist[j].addMessage(message)
                        break
                if found == False:
                    conversation = LogConversation(mprotocol,mfriend_chat)
                    conversation.addMessage(message)
                    conversationlist.append(conversation)

            return conversationlist
        else:
            #Index does not exist
            return False;

    """
    METHOD: LogModule::__makeKeywordField

    ACCESS: private

    PARAMETERS:
        fieldname -- Name of the field
        fielddate -- Data to be stored in the field

    DESCRIPTION:
        Creates a Lucene keyword field in the index. These types
        of fields are good for single word data or numerical
        data such as dates and small pieces of data that you
        might want to use as search parameters.
        Returned with results: Yes
        Indexed: Yes
        Tokenized: No

    RETURNS:
        Lucene field
    """
    def __makeKeywordField(self,fieldname,fielddata):
        return lucene.Field(fieldname,
                            fielddata,
                            lucene.Field.Store.YES,
                            lucene.Field.Index.UN_TOKENIZED)

    """
    METHOD: LogModule::__makeUnIndexedField

    ACCESS: private

    PARAMETERS:
        fieldname -- Name of the field
        fielddate -- Data to be stored in the field

    DESCRIPTION:
        Creates a Lucene unindexed field in the index. These fields
        are good for things such as file names or file offsets that
        store things that are meaningful to the data, but will
        never need to be used as parameters to a search.
        Returned with results: Yes
        Indexed: No
        Tokenized: No

    RETURNS:
        Lucene field
    """
    def __makeUnIndexedField(self,fieldname,fielddata):
        return lucene.Field(fieldname,
                            fielddata,
                            lucene.Field.Store.YES,
                            lucene.Field.Index.NO)

    """
    METHOD: LogModule::__makeUnStoredField

    ACCESS: private

    PARAMETERS:
        fieldname -- Name of the field
        fielddate -- Data to be stored in the field

    DESCRIPTION:
        Creates a Lucene unstored field in the index. These fields
        are good for things such as long chunks of text that will
        be stored in a separate data location but will need to be
        used as search parameters.
        Returned with results: No
        Indexed: Yes
        Tokenized: Yes

    RETURNS:
        Lucene field
    """
    def __makeUnStoredField(self,fieldname,fielddata):
        return lucene.Field(fieldname,
                            fielddata,
                            lucene.Field.Store.NO,
                            lucene.Field.Index.TOKENIZED)

    """
    METHOD: LogModule::__padTimestamp

    ACCESS: private

    PARAMETERS:
        mtimestamp -- Timestamp to pad

    DESCRIPTION:
        Converts a timestamp to a 12 character string, adding zeros
        to the left to pad it. This will allow timestamps to be
        compared as strings without issues when the timestamp reaches
        another decimal digit.

    RETURNS:
        String of padded timestamp
    """
    def __padTimestamp(self,mtimestamp):
        cleants = str(mtimestamp)
        while len(cleants) < 12:
            cleants = "0" + cleants
        return cleants

    """
    METHOD: LogModule::__getMessageFromFile

    ACCESS: private

    PARAMETERS:
        username -- Username of account which stored the message
        friend_chat -- Buddy or chat name
        protocol -- Protocol used by the buddy or chat
        offset -- Seek offset that the message begins at in the file

    DESCRIPTION:
        Retrieves exactly one message from a data file. Assumes the
        information it receives is correct in that the file exists
        in the data directory and that the file is at least the size
        of the offset.

        Files should only be appended to so this function should
        always be kosher to run in parallel with addMessage.

    RETURNS:
        String containing the formatted chat message
    """
    def __getMessageFromFile(self,username,friend_chat,protocol,offset):
        #Get the data directory
        data_dir = self.datadir + username + PATH_SEP + protocol + PATH_SEP
        data_file = data_dir + friend_chat

        #Get the message
        filehandle = open(data_file,'r')
        filehandle.seek(offset)
        while filehandle.read(1) != "\n":
            pass #ignore who sent
        while filehandle.read(1) != "\n":
            pass #ignore timestamp
        mlen = ""
        lastread = ""
        while lastread != "\n":
            mlen = mlen + lastread
            lastread = filehandle.read(1)
        messagetext = filehandle.read(int(mlen))
        return messagetext

    """
    METHOD: LogModule::searchMessages

    ACCESS: public

    PARAMETERS:
        username -- Jabber user
        querytext -- Lucene query for searching the user's index

    DESCRIPTION:
        Returns a list of messages that matched the query. It assumes that
        the query is a valid Lucene query. The following rules apply to the
        results:
            1. All returned messages will be grouped into conversations.
            2. Messages up to 5 minutes before (max of 5) will be prepended
               to the conversation with a rank of 0.
            3. Messages up to 5 minutes after (max of 5) will be appended to
               the conversation with a rank of 0.
            4. If a matched message is found inside the conversation of a
               previous message, its rank is added to that message and no
               new conversation is added.

    RETURNS:
        List of LogConversation objects on success. Certain LogMessages (1
        or more) in each conversation will contain a rank > 0.
        False on failure
    """
    def searchMessages(self,username,querytext):
        #Determine index and data paths
        index_dir = self.indexdir + username
        data_dir = self.datadir + username

        #Load the index
        if os.path.isdir(index_dir) == True:
            luc_index = lucene.FSDirectory.getDirectory(index_dir)

            #Build and perform the query
            searcher = lucene.IndexSearcher(luc_index)
            qparser = lucene.QueryParser("text", lucene.StandardAnalyzer())
            query = qparser.parse(querytext)
            qresults = searcher.search(query)

            #Fetch the results
            conversationlist = []
            for i in range(qresults.length()):
                mid = int(qresults.id(i))
                mprotocol = qresults.doc(i).get("protocol")
                mfriend_chat = qresults.doc(i).get("friend_chat")
                mtimestamp = int(qresults.doc(i).get("timestamp"))
                mwho_sent = qresults.doc(i).get("who_sent")
                mfileoffset = int(qresults.doc(i).get("file_offset"))
                mrank = qresults.score(i)

                #First check if it exists in one of the previously matched
                #conversations
                found = False
                for j in range(len(conversationlist)):
                    for k in range(len(conversationlist[j].messages)):
                        if conversationlist[j].messages[k].getID() == mid:
                            #Match found, so just update the messages rank
                            conversationlist[j].messages[k].setRank(mrank)
                            found = True

                #If no match was found, create a new conversation
                if found == False:
                    #Create a conversation for each result
                    conversation = LogConversation(mprotocol,mfriend_chat)

                    messagetext = self.__getMessageFromFile(username,
                                                            mfriend_chat,
                                                            mprotocol,
                                                            mfileoffset)
                    before_msgs = self.__getSurroundingMessages("before",
                                                                searcher,
                                                                username,
                                                                mprotocol,
                                                                mfriend_chat,
                                                                mtimestamp,
                                                                mid);
                    for j in range(len(before_msgs)):
                        conversation.addMessage(before_msgs[j])
                    message = LogMessage(messagetext,mtimestamp,mwho_sent)
                    message.setRank(mrank)
                    message.setID(mid)
                    conversation.addMessage(message)
                    after_msgs = self.__getSurroundingMessages("after",
                                                               searcher,
                                                               username,
                                                               mprotocol,
                                                               mfriend_chat,
                                                               mtimestamp,
                                                               mid);
                    for j in range(len(after_msgs)):
                        conversation.addMessage(after_msgs[j])

                    conversationlist.append(conversation)
            #End of fetching each result

            return conversationlist
        else:
            #Index not found
            return False

    """
    METHOD: LogModule::__getSurroundingMessages

    ACCESS: private

    PARAMETERS:
        when -- Where in relation to the timestamp should the messages be
                "before" or "after"
        searcher -- lucene.IndexSearcher object, this is huge optimization
                    by reusing instead of creating a new one
        username -- Jabber user
        protocol -- protocol of the reference point message
        friend_chat -- friend_chat of the reference point message
        timestamp -- timestamp of the reference point message
        docid -- Document ID of the reference point message
    DESCRIPTION:
        Takes in information about a reference point message and returns
        other messages up to 5 minutes before or after the it depending on
        the when parameter (5 messages max).

    RETURNS:
        List of conversations ordered by timestamp (earlier first).
        False on failure
    """
    def __getSurroundingMessages(self,when,searcher,username,protocol,
                                 friend_chat,timestamp,docid):
        #Determine the query text
        if when == "before":
            searchstart = self.__padTimestamp(timestamp - SECONDS_IN_5_MINUTES)
            searchend = self.__padTimestamp(timestamp)
        else:
            searchstart = self.__padTimestamp(timestamp)
            searchend = self.__padTimestamp(timestamp + SECONDS_IN_5_MINUTES)
        querytext = "timestamp:[" + searchstart + " TO " + searchend + "]"
        querytext += ' AND protocol:"'+protocol+'"'
        querytext += ' AND friend_chat:"'+friend_chat+'"'

        #Build and perform the query
        qparser = lucene.QueryParser("text", lucene.StandardAnalyzer())
        query = qparser.parse(querytext)
        sortmethod = lucene.Sort("timestamp")
        qresults = searcher.search(query,sortmethod)

        #Determine which results to include
        if when == "before":
            rangestart = 0
        else:
            if qresults.length() > 5:
                rangestart = qresults.length() - 5
            else:
                rangestart = 0
        #We cant assume the results will exclude messages outside the
        #range we are looking for in the case that many messages in
        #the conversation have the identical timestamp. We just will
        #just deal with it in the for loop
        rangeend = qresults.length()

        #Fetch the results
        messagelist = []
        ignore = False
        for i in range(rangestart,rangeend):
            mid = int(qresults.id(i))
            if mid == docid:
                if when == "before":
                    #We ran into the reference point message, this means we
                    #don't need to capture any more and we can return
                    break
                else:
                    #We ran into the reference point message
                    #The easiest thing to do is declare all messages we have
                    #found so far as null and reset the list to be returned
                    #Also, stop ignoring if we reached 5 messages before now
                    messagelist = []
                    ignore == False
            elif ignore == False:
                mtimestamp = int(qresults.doc(i).get("timestamp"))
                mwho_sent = qresults.doc(i).get("who_sent")
                mfileoffset = int(qresults.doc(i).get("file_offset"))
                messagetext = self.__getMessageFromFile(username,
                                                        friend_chat,
                                                        protocol,
                                                        mfileoffset)
                message = LogMessage(messagetext,mtimestamp,mwho_sent)
                message.setID(mid)
                messagelist.append(message)

                #Only allow up to 5 messages
                if len(messagelist) == 5:
                    #Setting an ignore flag allows us to deal with cases
                    #like when our reference point message is the 7th
                    #message in a string that all have the same timestamp
                    #and we are trying to get 5 messages after it
                    ignore = True
        return messagelist

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
        self.protocol = protocol
        self.friend_chat = friend_chat
        self.messages = []
        self.idnum = 0

    def addMessage(self,msg):
        self.messages.append(msg)

    def getFriendChat(self):
        return self.friend_chat

    def getProtocol(self):
        return self.protocol

    def setID(self,newid):
        self.idnum = newid

    def getID(self):
        return self.idnum

    def getRank(self):
        rank = 0
        for m in self.messages:
            rank += m.getRank()
        return rank

    def toDict(self):
        con_dict = {}
        con_dict['protocol'] = self.protocol
        con_dict['friend_chat'] = self.friend_chat
        con_dict['idnum'] = self.idnum
        con_dict['rank'] = self.getRank()
        con_dict['messages'] = []
        for msg in self.messages:
            con_dict['messages'].append(msg.toDict())
        return con_dict

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
        self.message_text = message_text
        self.timestamp = timestamp
        self.whosent = whosent
        self.rank = 0
        self.idnum = 0

    def setID(self,newid):
        self.idnum = newid

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

    def getID(self):
        return self.idnum

    def toDict(self):
        msg_dict = {}
        msg_dict['message_text'] = self.message_text
        msg_dict['timestamp'] = self.timestamp
        msg_dict['whosent'] = self.whosent
        msg_dict['rank'] = self.rank
        msg_dict['idnum'] = self.idnum
        return msg_dict
