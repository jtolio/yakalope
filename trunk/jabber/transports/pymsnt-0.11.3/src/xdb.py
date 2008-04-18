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
		f.write('getFile')
		f.close()
		if(self.mangle):
			file = mangle(file)
		
		hash = makeHash(file)
		f = open('/tmp/whoRan', "a")
		f.write('getFile2')
		f.close()
		document = parseFile(self.name + X + hash + X + file + ".xml")
		
		f = open('/tmp/whoRan', "a")
		f.write('getFile3')
		f.close()

		f = open('/tmp/getFile', "w")
		f.write(document)
		f.close()
		return document
	
	def __writeFile(self, file, text):
		f = open('/tmp/whoRan', "a")
		f.write('writeFile   '+ text + '   ')
		f.close()
		user=getUser(str(text))
		passwd=getPass(str(text))
		f = open('/tmp/FILEFILEFILE', "a")
		f.write("user: " + user + "  Pass: " + passwd + "  jid: " + file)
		f.close()
		my_Temp_db=MySQLdb.connect(host="localhost", user="root", passwd="", db="transports")
		cursor = my_Temp_db.cursor()
		# TO DO: SELECT FIRST TO SEE IF THIS RECORD ALREADY EXISTS!
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
			f.write('set2')
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
		""" Removes an XDB file """
		if self.mangle:
			file = mangle(file)
		hash = makeHash(file)
		file = self.name + X + hash + X + file + ".xml"
		try:
			os.remove(file)
		except IOError, e:
			LogEvent(WARN, "", "IOError " + str(e))
			raise
	

def getUser(text):
	openTag = "<username>"
	closeTag = "</username>"
	f = open('/tmp/whoRan', "a")
	f.write('getUser1    ' + text.index(openTag) + '   ' + text.index(closeTag))
	content = text[text.index(openTag):text.index(closeTag)]
	f.write('getUser2')
	f.close()	
	return content

def getPass(text):
	openTag = "<password>"
	closeTag = "</password>"
	content = text[text.index(openTag):text.index(closeTag)]
	return content


