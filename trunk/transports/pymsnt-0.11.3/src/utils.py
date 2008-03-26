# Copyright 2004-2005 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details



def getLang(el):
	return el.getAttribute((u'http://www.w3.org/XML/1998/namespace', u'lang'))


import sha
def socks5Hash(sid, initiator, target):
	return sha.new("%s%s%s" % (sid, initiator, target)).hexdigest()


import urllib
import os.path
def getURLBits(url, assumedType=None):
	type, rest = urllib.splittype(url)
	if assumedType and type != assumedType:
		return
	hostport, path = urllib.splithost(rest)
	host, port = urllib.splitnport(hostport, 80)
	filename = os.path.basename(path)
	return host, port, path, filename


try:
	import Image
	import StringIO
	
	def convertToPNG(imageData):
		inbuff = StringIO.StringIO(imageData)
		outbuff = StringIO.StringIO()
		Image.open(inbuff).save(outbuff, "PNG")
		outbuff.seek(0)
		imageData = outbuff.read()
		return imageData
except ImportError:
	print "WARNING! Only PNG avatars will be understood by this transport. Please install the Python Imaging Library."

	def convertToPNG(imageData):
		return ""


errorCodeMap = {
"bad-request"			:	400,
"conflict"			:	409,
"feature-not-implemented"	:	501,
"forbidden"			:	403,
"gone"				:	302,
"internal-server-error"		:	500,
"item-not-found"		:	404,
"jid-malformed"			:	400,
"not-acceptable"		:	406,
"not-allowed"			:	405,
"not-authorized"		:	401,
"payment-required"		:	402,
"recipient-unavailable"		:	404,
"redirect"			:	302,
"registration-required"		:	407,
"remote-server-not-found"	:	404,
"remote-server-timeout"		:	504,
"resource-constraint"		:	500,
"service-unavailable"		:	503,
"subscription-required"		:	407,
"undefined-condition"		:	500,
"unexpected-request"		:	400
}



