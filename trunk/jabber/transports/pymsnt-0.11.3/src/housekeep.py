# Copyright 2005 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

from twisted.words.protocols.jabber.jid import internJID

import utils
import config
import xdb

import shutil
import sys
import os
import os.path


X = os.path.sep

def init():
	global noteList
	global noteListF

	try:
		notes = NotesToMyself()
		for note in noteList:
			if notes.check(note):
				noteListF[noteList.index(note)]()
				notes.append(note)
		notes.save()
	except:
		print "An error occurred during one of the automatic data update routines. Please report this bug."
		raise


class NotesToMyself:
	def __init__(self):
		pre = os.path.abspath(config.spooldir) + X + config.jid + X
		self.filename = pre + X + "notes_to_myself"
		self.notes = []
		
		if os.path.exists(self.filename):
			f = open(self.filename, "r")
			self.notes = [x.strip() for x in f.readlines()]
			f.close()
		else:
			if not os.path.exists(pre):
				os.makedirs(pre)
			global noteList
			self.notes = noteList
	
	def check(self, note):
		return self.notes.count(note) == 0
	
	def append(self, note):
		if self.check(note):
			self.notes.append(note)

	def save(self):
		f = open(self.filename, "w")
		for note in self.notes:
			f.write(note + "\n")
		f.close()



def doSpoolPrepCheck():
	pre = os.path.abspath(config.spooldir) + X + config.jid + X

	print "Checking spool files and stringprepping any if necessary...",

	for file in os.listdir(pre):
		try:
			if not os.path.isfile(file):
				continue
			file = xdb.unmangle(file).decode("utf-8")
			filej = internJID(file).full()
			if(file != filej):
				file = xdb.mangle(file)
				filej = xdb.mangle(filej)
				if(os.path.exists(filej)):
					print "Need to move", file, "to", filej, "but the latter exists!\nAborting!"
					sys.exit(1)
				else:
					shutil.move(pre + file, pre + filej)
		except:
			print "File: " + file
			raise
	print "done"


def doHashDirUpgrade():
	print "Upgrading your XDB structure to use hashed directories for speed...",

	# Do avatars...
	pre = os.path.join(os.path.abspath(config.spooldir), config.jid) + X + "avatars" + X
	if os.path.exists(pre):
		for file in os.listdir(pre):
			try:
				if os.path.isfile(pre + file):
					pre2 = pre + file[0:3] + X
					if not os.path.exists(pre2):
						os.makedirs(pre2)
					shutil.move(pre + file, pre2 + file)
			except:
				print "File: " + file
				raise
	
	# Do spool files...
	pre = os.path.join(os.path.abspath(config.spooldir), config.jid) + X
	if os.path.exists(pre):
		for file in os.listdir(pre):
			try:
				if os.path.isfile(pre + file) and file != "notes_to_myself":
					hash = file[0:2]
					pre2 = pre + hash + X
					if not os.path.exists(pre2):
						os.makedirs(pre2)

					if(os.path.exists(pre2 + file)):
						print "Need to move", file, "to", pre2 + file, "but the latter exists!\nAborting!"
						sys.exit(1)
					else:
						shutil.move(pre + file, pre2 + file)
			except:
				print "File: " + file

	print "done"


def doMD5HashDirUpgrade():
	print "Moving the avatar directory from msn.host.com up to the spool directory."

	pre = os.path.join(os.path.abspath(config.spooldir), config.jid) + X
	if os.path.exists(pre + "avatars"):
		# Remove the avatars dir that gets created when we import
		# legacy/glue.py (it only contains the defaultAvatar)
		shutil.rmtree(os.path.join(config.spooldir, "avatars"))
		shutil.move(pre + "avatars", os.path.join(config.spooldir, "avatars"))
	else:
		print "Could not move your cached avatars directory automatically. It is safe to delete it, the avatars will be recreated as necessary."


	print "Upgrading your spool directory to use md5 hashes."
	
	dirlist = os.listdir(pre)
	dir, hash, file = "","",""
	try:
		for dir in dirlist:
			if not os.path.isdir(pre + dir) or dir == "avatars" or len(dir) == 3:
				continue
			pre2 = pre + dir + X
			for file in os.listdir(pre2):
				if not os.path.isfile(pre2 + file):
					continue
				hash = xdb.makeHash(os.path.splitext(file)[0])
				if not os.path.exists(pre + hash):
					os.makedirs(pre + hash)
				shutil.move(pre2 + file, pre + hash + X + file)
			os.rmdir(pre2)
	except Exception, e:
		print "Error in migration", pre, dir, hash, file, str(e)
		sys.exit(1)



noteList = ["doSpoolPrepCheck", "doHashDirUpgrade", "doMD5HashDirUpgrade"]
noteListF = [doSpoolPrepCheck, doHashDirUpgrade, doMD5HashDirUpgrade]

