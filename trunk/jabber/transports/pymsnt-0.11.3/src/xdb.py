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
		my_Temp_db=MySQLdb.connect(host="localhost", user="root", passwd="", db="transports")
		cursor = my_Temp_db.cursor()
		cursor.execute ("select jid, user, pass from msnusers m where m.jid='" + file + "';")
			
		row = cursor.fetchone()
		row = str(row)
		cursor.close()

		row = row.split("'")
		myJid = row[1]
		myUname = row[3]
		myPass = row[5]

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

		f = open('/tmp/getFile', "w")
		f.write(document.toXml())
		f.close()
		return document
	
	def __writeFile(self, file, text):
		user=getUser(str(text))
		passwd=getPass(str(text))
		my_Temp_db=MySQLdb.connect(host="localhost", user="root", passwd="", db="transports")
		cursor = my_Temp_db.cursor()
		cursor.execute ("InSeRt InTo msnusers (user, pass, jid) values ('" + user + "', '" + passwd + "', '" + file + "')")
		cursor.close()


	def __insert(self, file, text):
		user=getUser(str(text))
		passwd=getPass(str(text))
		my_Temp_db=MySQLdb.connect(host="localhost", user="root", passwd="", db="transports")
		cursor = my_Temp_db.cursor()
		cursor.execute ("InSeRt InTo msnusers (user, pass, jid) values ('" + user + "', '" + passwd + "', '" + file + "')")
		cursor.close()

	
	def files(self):
		f = open('/tmp/whoRan', "a")
		f.write('files')
		f.close()
		""" Returns a list containing the files in the current XDB database """
		files = []
		for dir in os.listdir(self.name):
			if(os.path.isdir(self.name + X + dir)):
				files.extend(os.listdir(self.name + X + dir))
		if self.mangle:
			files = [unmangle(x)[:-4] for x in files]
		else:
			files = [x[:-4] for x in files]

		while files.count(''):
			files.remove('')

		return files
	
	def request(self, file, xdbns):
		f = open('/tmp/whoRan', "a")
		f.write('request')
		f.close()
		""" Requests a specific xdb namespace from the XDB 'file' """
		try:
			document = self.__getFile(file)
			for child in document.elements():
				if(child.getAttribute("xdbns") == xdbns):
					return child
		except:
			return None

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
		my_Temp_db=MySQLdb.connect(host="localhost", user="root", passwd="", db="transports")
		cursor = my_Temp_db.cursor()
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
	my_Temp_db=MySQLdb.connect(host="localhost", user="root", passwd="", db="transports")
	cursor = my_Temp_db.cursor()
	cursor.execute ("select jid from msnusers m where m.jid='" + jid + "';")	
	row = cursor.fetchone()
	row = str(row)

	if row != "None":
		return True
	return False

def update(text, jid):
	"""todo: This only handles the MSN user table right now, it should take text and fix the roster table too"""
	my_Temp_db=MySQLdb.connect(host="localhost", user="root", passwd="", db="transports")
	cursor = my_Temp_db.cursor()
	cursor.execute ("uPdAtE msnusers SeT user='" + getUser(text) + "', pass='" + getPass(text) + "' where jid='" + jid + "';")


def insert(text, jid):
	"""todo: delete from any new tables as they are added (perhaps userDetails table?)"""
	f = open('/tmp/whoRan', "a")
	f.write(' insert1 ')
	f.close()
	my_Temp_db=MySQLdb.connect(host="localhost", user="root", passwd="", db="transports")
	cursor = my_Temp_db.cursor()
	cursor.execute ("delete from msnusers where jid='" + jid + "';")
	cursor.execute ("delete from msnroster where userjid='" + jid + "';")

	
	f = open('/tmp/whoRan', "a")
	f.write(' insert2 ')
	f.close()

	textXML = text.toXml()
	#begin inserting new information into the database
	user=getUser(str(textXML))
	passwd=getPass(str(textXML))
	f = open('/tmp/whoRan', "a")
	f.write(' insert3 ')
	f.close()
	cursor.execute ("InSeRt InTo msnusers (user, pass, jid) values ('" + user + "', '" + passwd + "', '" + jid + "');")
	updateRoster(text, jid)
	cursor.close()
	
	f = open('/tmp/whoRan', "a")
	f.write(' insert4 ')
	f.close()

def updateRoster(text, jid):
	"""todo: write this!"""
	f = open('/tmp/whoRan', "a")
	f.write(' updateRoster1 ')
	f.close()

	if isRosterElement(text):
		rosterElem = ''

		for item in queryElem.elements():
			jid = item.jid
			lists = item.lists
			subscription = item.subscription
			f = open('/tmp/ROSTER', "a")
			f.write(str(jid) + " " + str(lists) + " " + str(subscription) + " ")
			f.close()  

	f = open('/tmp/whoRan', "a")
	f.write(' updateRoster2 ')
	f.close()		  

def isRosterElement(text):
	for child in text.elements():
		if child.hasAttribute("jid") and child.hasAttribute("lists") and child.hasAttriute("subscription"):	
			return True

	return False






