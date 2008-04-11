# Copyright 2004-2006 James Bunton <james@delx.cjb.net> 
# Licensed for distribution under the GPL version 2, check COPYING for details


class VersionNumber:
	def __init__(self, vstring):
		self.varray = [0]
		index = 0 
		flag = True
		for c in vstring:
			if c == '.':
				self.varray.append(0)
				index += 1
				flag = True
			elif c.isdigit() and flag:
				self.varray[index] *= 10
				self.varray[index] += int(c)
			else:
				flag = False
	
	def __cmp__(self, other):
		return cmp(self.varray, other.varray)


