# Copyright 2004-2005 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

from twisted.words.xish.domish import parseFile

import sys, os

import config



def invalidError(text):
	print text
	print "Exiting..."
	sys.exit(1)


def importFile(configFile):
	# Check the file exists
	if not os.path.isfile(configFile):
		print "Configuration file not found. You need to create a config.xml file in the PyMSNt directory."
		sys.exit(1)

	# Get ourself a DOM
	try:
		root = parseFile(configFile)
	except Exception, e:
		invalidError("Error parsing configuration file: " + str(e))

	# Store all the options in config
	for el in root.elements():
		try:
			tag = el.name
			cdata = str(el)
			children = [x for x in el.elements()]
			if children:
				# For options like <admins><jid>user1@host.com</jid><jid>user2@host.com</jid></admins>
				if type(getattr(config, tag)) != list:
					invalidError("Tag %s in your configuration file should be a list (ie, must have subtags)." % (tag))
				myList = getattr(config, tag)
				for child in children:
					s = child.__str__()
					myList.append(s)
			elif cdata:
				# For config options like <ip>127.0.0.1</ip>
				if type(getattr(config, tag)) != str:
					invalidError("Tag %s in your configuration file should not be a string (ie, no cdata)." % (tag))
				setattr(config, tag, cdata)
			else:
				# For config options like <sessionGreeting/>
				t = type(getattr(config, tag))
				if not (t == bool or t == int):
					invalidError("Tag %s in your configuration file should not be a boolean (ie, must have cdata or subtags)." % (tag))
				setattr(config, tag, True)
		except AttributeError:
			print "Tag %s in your configuration file is not a defined tag. Ignoring!" % (tag)
	

def importOptions(options):
	for o in options:
		if hasattr(config, o):
			setattr(config, o, options[o])
		else:
			print "Option %s is not a defined option. Ignoring!" % (o)

def reloadConfig(file=None, options=None):
	if file:
		importFile(file)
	if options:
		importOptions(options)

