# Copyright 2005 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

import md5
import struct

MSNP11_PRODUCT_ID = "PROD0090YUAUV{2B"
MSNP11_PRODUCT_KEY = "YMM8C_H7KCQ2S_KL"
MSNP11_MAGIC_NUM = 0x0E79A9C1


def doChallenge(chlData):
	md5digest = md5.md5(chlData + MSNP11_PRODUCT_KEY).digest()

	# Make array of md5 string ints
	md5Ints = struct.unpack("<llll", md5digest)
	md5Ints = [(x & 0x7fffffff) for x in md5Ints]

	# Make array of chl string ints
	chlData += MSNP11_PRODUCT_ID
	amount = 8 - len(chlData) % 8
	chlData += "".zfill(amount)
	chlInts = struct.unpack("<%di" % (len(chlData)/4), chlData)

	# Make the key
	high = 0
	low = 0
	i = 0
	while i < len(chlInts) - 1:
		temp = chlInts[i]
		temp = (MSNP11_MAGIC_NUM * temp) % 0x7FFFFFFF
		temp += high
		temp = md5Ints[0] * temp + md5Ints[1]
		temp = temp % 0x7FFFFFFF

		high = chlInts[i + 1]
		high = (high + temp) % 0x7FFFFFFF
		high = md5Ints[2] * high + md5Ints[3]
		high = high % 0x7FFFFFFF

		low = low + high + temp

		i += 2

	high = littleEndify((high + md5Ints[1]) % 0x7FFFFFFF)
	low = littleEndify((low + md5Ints[3]) % 0x7FFFFFFF)
	key = (high << 32L) + low
	key = littleEndify(key, "Q")

	longs = [x for x in struct.unpack(">QQ", md5digest)]
	longs = [littleEndify(x, "Q") for x in longs]
	longs = [x ^ key for x in longs]
	longs = [littleEndify(abs(x), "Q") for x in longs]
	
	out = ""
	for x in longs:
		x = hex(x)
		x = x[2:].strip("L")
		x = x.zfill(16)
		out += x.lower()
	
	return out

def littleEndify(num, c="L"):
	return struct.unpack(">" + c, struct.pack("<" + c, num))[0]


if __name__ == "__main__":
	import sys
	try:
		print doChallenge(sys.argv[1])
	except IndexError:
		print "No args passed"
		raise

