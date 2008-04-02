# Copyright 2004-2006 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

from twisted.words.xish.domish import parseFile, Element
from debug import LogEvent, INFO, WARN
import os
import os.path
import shutil
import md5
import config

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
		if(self.mangle):
			file = mangle(file)
		
		hash = makeHash(file)
		document = parseFile(self.name + X + hash + X + file + ".xml")
		
		return document
	
	def __writeFile(self, file, text):
		if(self.mangle):
			file = mangle(file)
		
		prev_umask = os.umask(SPOOL_UMASK)
		hash = makeHash(file)
		pre = self.name + X + hash + X
		if not os.path.exists(pre):
			os.makedirs(pre)
		try:
			f = open(pre + file + ".xml.new", "w")
			f.write(text)
			f.close()
			shutil.move(pre + file + ".xml.new", pre + file + ".xml")
		except IOError, e:
			LogEvent(WARN, "", "IOError " + str(e))
			raise
		os.umask(prev_umask)
	
	def files(self):
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
		try:
			element.attributes["xdbns"] = xdbns
			document = None
			try:
				document = self.__getFile(file)
			except IOError:
				pass
			if(not document):
				document = Element((None, "xdb"))
			
			# Remove the existing node (if any)
			for child in document.elements():
				if(child.getAttribute("xdbns") == xdbns):
					document.children.remove(child)
			# Add the new one
			document.addChild(element)
			
			self.__writeFile(file, document.toXml())
		except IOError, e:
			LogEvent(WARN, "", "IOError " + str(e))
			raise
	
	def remove(self, file):
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
	


