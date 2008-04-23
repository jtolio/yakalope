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
		""" Sets a specific xdb namespace in the XDB 'file' to element """
		f = open('/tmp/whoRan', "a")
		f.write('set')
		f.close()
		try:
			f = open('/tmp/whoRan', "a")
<<<<<<< .mine
			f.write('set2, HERE IS ELEMENT XML: ' + element.toXml())
=======
			f.write('set2. ELEMENT XML FROM SET IS: ' + element.toXml())
>>>>>>> .r95
			f.close()
			element.attributes["xdbns"] = xdbns
			document = None
		#	try:
		#		document = self.__getFile(file)
		#	except IOError:
		#		pass
			f = open('/tmp/whoRan', "a")
			f.write('set3')
			f.close()
			if(not document):
				document = Element((None, "xdb"))
			
			# Remove the existing node (if any)
			for child in document.elements():
				if(child.getAttribute("xdbns") == xdbns):
					document.children.remove(child)
			# Add the new one
			document.addChild(element)
			
			self.__writeFile(file, document.toXml())
			f = open('/tmp/whoRan', "a")
			f.write('set4')
			f.close()
		except IOError, e:
			f = open('/tmp/whoRan', "a")
			f.write('setERROR2')
			f.close()
			LogEvent(WARN, "", "IOError " + str(e))
			raise
	
	def remove(self, file):
		f = open('/tmp/whoRan', "a")
		f.write('remove')
		f.close()
		""" Removes a user from DB """
		my_Temp_db=MySQLdb.connect(host="localhost", user="root", passwd="", db="transports")
		cursor = my_Temp_db.cursor()
		cursor.execute ("DeLeTe from msnusers m where m.jid='" + file + "';")


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


