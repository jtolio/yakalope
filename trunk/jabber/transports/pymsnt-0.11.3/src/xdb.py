# Copyright 2004-2006 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

from twisted.words.xish.domish import Element
from debug import LogEvent, INFO, WARN
import os
import os.path
import shutil
import md5
import config
import MySQLdb
import re

X = os.path.sep
SPOOL_UMASK = 0077


def unmangle(file):
	chunks = file.split("%")
	end = chunks.pop()
	file = "%s@%s" % ("%".join(chunks), end)
	return file

def mangle(file):
	return file.replace("@", "%")

def makeHash(file):
	return md5.md5(file).hexdigest()[0:3]


class XDB:
	"""
	Class for storage of data.
	
	Create one instance of the class for each XDB 'folder' you want.
	Call request()/set() with the xdbns argument you wish to retrieve
	"""
	def __init__(self, name, mangle=False):
		""" Creates an XDB object. If mangle is True then any '@' signs in filenames will be changed to '%' """
		self.name = os.path.join(os.path.abspath(config.spooldir), name)
		if not os.path.exists(self.name):
			os.makedirs(self.name)
		self.mangle = mangle
	
	def __getFile(self, file):
		f = open('/tmp/whoRan', "a")
		f.write(' getfile ')
		f.close()
		
		document = Element((None, "xdb"))
		if userExists(file):
			myJid, myUname, myPass = getUserFromDB(file)
			f = open('/tmp/DBFILE', "a")
			f.write("jid " + myJid + " uname " + myUname + "myPass" + myPass)
			f.close()
		
			#rebuild xml
			document = Element((None, "xdb"))
			document.addElement("query", None, None)
			queryElem = document.children[0]
			queryElem['xdbns'] = 'jabber:iq:register'
			queryElem.addElement("username", None, myUname)
			queryElem.addElement("password", None, myPass)

			#todo: rebuild roster if exists
		f = open('/tmp/getFile', "w")
		f.write(document.toXml())
		f.close()
		return document
	
	def __writeFile(self, file, text):
		f = open('/tmp/whoRan', "a")
		f.write(' write ')
		f.close()
		#todo: write roster if exists
		user=getUser(str(text))
		passwd=getPass(str(text))
		cursor = getDBCursor() 
		cursor.execute ("InSeRt InTo msnusers (user, pass, jid) values ('" + user + "', '" + passwd + "', '" + file + "')")
		cursor.close()


	def __insert(self, file, text):
		f = open('/tmp/whoRan', "a")
		f.write(' insert ')
		f.close()
		user=getUser(str(text))
		passwd=getPass(str(text))
		cursor = getDBCursor() 
		cursor.execute ("InSeRt InTo msnusers (user, pass, jid) values ('" + user + "', '" + passwd + "', '" + file + "')")
		cursor.close()
		updateRoster()

	
	def files(self): #only kept for compatibility with code base...
		#we dont need files anymore since all info is stored in a database
		f = open('/tmp/whoRan', "a")
		f.write(' files ')
		f.close()
		return
	
	def request(self, file, xdbns):
		#rebuild xml
		#todo: build roster if exists
		f = open('/tmp/whoRan', "a")
		f.write(' request ')
		f.close()
		document = Element((None, "xdb"))
		if userExists(file):
			if xdbns == 'jabber:iq:register':
				jid, myUname, myPass = getUserFromDB(file)	
				document.addElement("query", None, None)
				queryElem = document.children[0]
				queryElem['xdbns'] = 'jabber:iq:register'
				queryElem.addElement("username", None, myUname)
				queryElem.addElement("password", None, myPass)
		return document


	def set(self, file, xdbns, element):
		if(userExists(file)):
			f = open('/tmp/whoRan', "a")
			f.write(' setUPDATE ')
			f.close()
			update(element.toXml(), file)
		else:
			f = open('/tmp/whoRan', "a")
			f.write(' setINSERT ')
			f.close()
			insert(element, file)

		f = open('/tmp/whoRan', "a")
		f.write(' setDONE ')
		f.close()

#  take in element
#  check user table:
#    if user exists, do an update
#    else do an insert
#  check roster table:
#    select and delete all buddies for this user
#    for each buddy in element:
#      insert

	def remove(self, file):
		f = open('/tmp/whoRan', "a")
		f.write('remove')
		f.close()
		""" Removes a user from DB """
		cursor = getDBCursor() 
		cursor.execute ("DeLeTe from msnusers m where m.jid='" + MySQLdb.escape_string(file) + "';")
def getUser(text):
	openTag = "<username>"
	closeTag = "</username>"
	content = text[len(openTag) + text.find(openTag):text.find(closeTag)]
	return content

def getPass(text):
	openTag = "<password>"
	closeTag = "</password>"
	content = text[len(openTag) + text.find(openTag):text.find(closeTag)]
	content = MySQLdb.escape_string(content)
	return content

def getPass(text):
	openTag = "<password>"
	closeTag = "</password>"
	content = text[len(openTag) + text.find(openTag):text.find(closeTag)]
	content = MySQLdb.escape_string(content)
	return content

def userExists(jid):
	cursor = getDBCursor() 
	cursor.execute ("select jid from msnusers m where m.jid='" + jid + "';")	
	row = cursor.fetchone()
	row = str(row)

	if row != "None":
		return True
	return False

def update(text, jid):
	cursor = getDBCursor() 
	uname = getUser(text)
	upass = getPass(text)
	prnt("uname " + uname)
	prnt("upass " + upass)
	cursor.execute ("uPdAtE msnusers SeT user='" + uname + "', pass='" + upass + "' where jid='" + jid + "';")
	cursor.close()
	prnt("update")	
	updateRoster(text, jid)

def insert(text, jid):
	"""todo: delete from any new tables as they are added (perhaps userDetails table?)"""
	deleteUser(jid)

	#begin inserting new information into the database
	textXML = text.toXml()
	user=getUser(str(textXML))
	passwd=getPass(str(textXML))

	cursor = getDBCursor() 
	cursor.execute ("InSeRt InTo msnusers (user, pass, jid) values ('" + user + "', '" + passwd + "', '" + jid + "');")
	cursor.close()

	prnt("here")	
	
	updateRoster(text, jid)
	
def updateRoster(text, jid):
	if isRosterElement(text):
		prnt("isRoster: " + text.toXml())
		clearRoster()
		rosterElem = ''

		for item in queryElem.elements():
			jid = item.jid
			lists = item.lists
			subscription = item.subscription
			f = open('/tmp/ROSTER', "a")
			f.write(str(jid) + " " + str(lists) + " " + str(subscription) + " ")
			f.close()  

	f = open('/tmp/whoRan', "a")
	f.write(' updateRoster ')
	f.close()		  

def isRosterElement(text):
	try:
		for child in text.elements():
			if child.hasAttribute("jid") and child.hasAttribute("lists") and child.hasAttriute("subscription"):	
				return True
	except:
		return False
	return False

def clearRoster(jid):
	cursor = getDBCursor() 
	cursor.execute ("delete from msnroster where userjid='" + jid + "';")
	cursor.close()

def deleteUser(jid):
	cursor = getDBCursor() 
	cursor.execute ("delete from msnusers where jid='" + jid + "';")

def userExists(jid):
	cursor = getDBCursor() 
	cursor.execute ("select jid, user, pass from msnusers m where m.jid='" + jid + "';")
		
	row = cursor.fetchone()
	row = str(row)
	if row == 'None':
		return False
	return True

def getUserFromDB(jid):
	cursor = getDBCursor() 
	cursor.execute ("select jid, user, pass from msnusers m where m.jid='" + jid + "';")
		
	row = cursor.fetchone()
	row = str(row)
	cursor.close()

	row = row.split("'")
	myJid = row[1]
	myUname = row[3]
	myPass = row[5]

	return myJid, myUname, myPass

def getDBCursor(): #returns a cursor for the database
	#good to abstract this in case we change the sql account 
	my_Temp_db=MySQLdb.connect(host="localhost", user="root", passwd="", db="transports")
	return my_Temp_db.cursor()

def prnt(string):
	f = open('/tmp/whoRan', "a")
	f.write(' ' + str(string) + ' ')
	f.close()		  
