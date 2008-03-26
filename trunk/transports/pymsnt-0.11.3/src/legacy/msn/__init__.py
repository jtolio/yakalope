# Copyright 2006 James Bunton <james@delx.cjb.net> 
# Licensed for distribution under the GPL version 2, check COPYING for details

from msnw import MSNConnection, MultiSwitchboardSession
from msn import FORWARD_LIST, ALLOW_LIST, BLOCK_LIST, REVERSE_LIST, PENDING_LIST
from msn import STATUS_ONLINE, STATUS_OFFLINE, STATUS_HIDDEN, STATUS_IDLE, STATUS_AWAY, STATUS_BUSY, STATUS_BRB, STATUS_PHONE, STATUS_LUNCH
from msn import MSNContact, MSNContactList

def setDebug(value):
	msn.LINEDEBUG = value
	msn.MESSAGEDEBUG = value
	msn.MSNP2PDEBUG = value

