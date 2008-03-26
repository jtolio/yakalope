# Twisted, the Framework of Your Internet
# Copyright (C) 2001-2002 Matthew W. Lefkowitz
# Copyright (C) 2004-2005 James C. Bunton
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of version 2.1 of the GNU Lesser General Public
# License as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""
MSNP11 Protocol (client only) - semi-experimental

Stability: unstable.

This module provides support for clients using the MSN Protocol (MSNP11).
There are basically 3 servers involved in any MSN session:

I{Dispatch server}

The DispatchClient class handles connections to the
dispatch server, which basically delegates users to a
suitable notification server.

You will want to subclass this and handle the gotNotificationReferral
method appropriately.
    
I{Notification Server}

The NotificationClient class handles connections to the
notification server, which acts as a session server
(state updates, message negotiation etc...)

I{Switcboard Server}

The SwitchboardClient handles connections to switchboard
servers which are used to conduct conversations with other users.

There are also two classes (FileSend and FileReceive) used
for file transfers.

Clients handle events in two ways.

  - each client request requiring a response will return a Deferred,
    the callback for same will be fired when the server sends the
    required response
  - Events which are not in response to any client request have
    respective methods which should be overridden and handled in
    an adequate manner

Most client request callbacks require more than one argument,
and since Deferreds can only pass the callback one result,
most of the time the callback argument will be a tuple of
values (documented in the respective request method).
To make reading/writing code easier, callbacks can be defined in
a number of ways to handle this 'cleanly'. One way would be to
define methods like: def callBack(self, (arg1, arg2, arg)): ...
another way would be to do something like:
d.addCallback(lambda result: myCallback(*result)).

If the server sends an error response to a client request,
the errback of the corresponding Deferred will be called,
the argument being the corresponding error code.

B{NOTE}:
Due to the lack of an official spec for MSNP11, extra checking
than may be deemed necessary often takes place considering the
server is never 'wrong'. Thus, if gotBadLine (in any of the 3
main clients) is called, or an MSNProtocolError is raised, it's
probably a good idea to submit a bug report. ;)
Use of this module requires that PyOpenSSL is installed.

@author: U{Sam Jordan<mailto:sam@twistedmatrix.com>}
@author: U{James Bunton<mailto:james@delx.cjb.net>}
"""

from __future__ import nested_scopes

import twistfix
twistfix.main()

# Sibling imports
from twisted.protocols.basic import LineReceiver
from twisted.web.http import HTTPClient
import msnp11chl

# Twisted imports
from twisted.internet import reactor, task
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ReconnectingClientFactory, ClientFactory
try:
    from twisted.internet.ssl import ClientContextFactory
except ImportError:
    print "You must install pycrypto and pyopenssl."
    raise
from twisted.python import failure, log
from twisted.words.xish.domish import parseText, unescapeFromXml


# System imports
import types, operator, os, sys, base64, random, struct, random, sha, base64, StringIO, array, codecs, binascii
from urllib import quote, unquote


MSN_PROTOCOL_VERSION = "MSNP11 CVR0"      # protocol version
MSN_PORT             = 1863               # default dispatch server port
MSN_MAX_MESSAGE      = 1664               # max message length
MSN_CVR_STR          = "0x040c winnt 5.1 i386 MSNMSGR 7.0.0777 msmsgs"
MSN_AVATAR_GUID      = "{A4268EEC-FEC5-49E5-95C3-F126696BDBF6}"
MSN_MSNFTP_GUID      = "{5D3E02AB-6190-11D3-BBBB-00C04F795683}"
MSN_MAXINT           = 2**31 - 1

# auth constants
LOGIN_SUCCESS  = 1
LOGIN_FAILURE  = 2
LOGIN_REDIRECT = 3

# list constants
FORWARD_LIST = 1
ALLOW_LIST   = 2
BLOCK_LIST   = 4
REVERSE_LIST = 8
PENDING_LIST = 16

# phone constants
HOME_PHONE   = "PHH"
WORK_PHONE   = "PHW"
MOBILE_PHONE = "PHM"
HAS_PAGER    = "MOB"
HAS_BLOG     = "HSB"

# status constants
STATUS_ONLINE  = 'NLN'
STATUS_OFFLINE = 'FLN'
STATUS_HIDDEN  = 'HDN'
STATUS_IDLE    = 'IDL'
STATUS_AWAY    = 'AWY'
STATUS_BUSY    = 'BSY'
STATUS_BRB     = 'BRB'
STATUS_PHONE   = 'PHN'
STATUS_LUNCH   = 'LUN'

PINGSPEED = 50.0

LINEDEBUG = False
MESSAGEDEBUG = False
MSNP2PDEBUG = False


P2PSEQ = [-3, -2, 0, -1, 1, 2, 3, 4, 5, 6, 7, 8]
def p2pseq(n):
    if n > 5:
        return n - 3
    else:
        return P2PSEQ[n]


def getVal(inp):
    return inp.split('=')[1]

def getVals(params):
    userHandle = ""
    screenName = ""
    userGuid   = ""
    lists      = -1
    groups     = []
    for p in params:
        if not p:
            continue
        elif p[0] == 'N':
            userHandle = getVal(p)
        elif p[0] == 'F':
            screenName = unquote(getVal(p))
        elif p[0] == 'C':
            userGuid = getVal(p)
        elif p.isdigit():
            lists = int(p)
        else: # Must be the groups
            try:
                groups = p.split(',')
            except:
                raise MSNProtocolError, "Unknown LST/ADC response" + str(params) # debug

    return userHandle, screenName, userGuid, lists, groups

def ljust(s, n, c):
    """ Needed for Python 2.3 compatibility """
    return s + (n-len(s))*c

if sys.byteorder == "little":
    def utf16net(s):
        """ Encodes to utf-16 and ensures network byte order. Strips the BOM """
        a = array.array("h", s.encode("utf-16")[2:])
        a.byteswap()
        return a.tostring()
else:
    def utf16net(s):
        """ Encodes to utf-16 and ensures network byte order. Strips the BOM """
        return s.encode("utf-16")[2:]

def b64enc(s):
    return base64.encodestring(s).replace("\n", "")

def b64dec(s):
    for pad in ["", "=", "==", "A", "A=", "A=="]: # Stupid MSN client!
        try:
            return base64.decodestring(s + pad)
        except:
            pass
    raise ValueError("Got some very bad base64!")

def random_guid():
    format = "{%4X%4X-%4X-%4X-%4X-%4X%4X%4X}"
    data = []
    for x in xrange(8):
        data.append(random.random() * 0xAAFF + 0x1111)
    data = tuple(data)

    return format % data

def checkParamLen(num, expected, cmd, error=None):
    if error == None: error = "Invalid Number of Parameters for %s" % cmd
    if num != expected: raise MSNProtocolError, error

def _parseHeader(h, v):
    """
    Split a certin number of known
    header values with the format:
    field1=val,field2=val,field3=val into
    a dict mapping fields to values.
    @param h: the header's key
    @param v: the header's value as a string
    """

    if h in ('passporturls','authentication-info','www-authenticate'):
        v = v.replace('Passport1.4','').lstrip()
        fields = {}
        for fieldPair in v.split(','):
            try:
                field,value = fieldPair.split('=',1)
                fields[field.lower()] = value
            except ValueError:
                fields[field.lower()] = ''
        return fields
    else: return v

def _parsePrimitiveHost(host):
    # Ho Ho Ho
    h,p = host.replace('https://','').split('/',1)
    p = '/' + p
    return h,p

def _login(userHandle, passwd, nexusServer, cached=0, authData=''):
    """
    This function is used internally and should not ever be called
    directly.
    """
    cb = Deferred()
    def _cb(server, auth):
        loginFac = ClientFactory()
        loginFac.protocol = lambda : PassportLogin(cb, userHandle, passwd, server, auth)
        reactor.connectSSL(_parsePrimitiveHost(server)[0], 443, loginFac, ClientContextFactory())

    if cached:
        _cb(nexusServer, authData)
    else:
        fac = ClientFactory()
        d = Deferred()
        d.addCallbacks(_cb, callbackArgs=(authData,))
        d.addErrback(lambda f: cb.errback(f))
        fac.protocol = lambda : PassportNexus(d, nexusServer)
        reactor.connectSSL(_parsePrimitiveHost(nexusServer)[0], 443, fac, ClientContextFactory())
    return cb


class PassportNexus(HTTPClient):
    
    """
    Used to obtain the URL of a valid passport
    login HTTPS server.

    This class is used internally and should
    not be instantiated directly -- that is,
    The passport logging in process is handled
    transparantly by NotificationClient.
    """

    def __init__(self, deferred, host):
        self.deferred = deferred
        self.host, self.path = _parsePrimitiveHost(host)

    def connectionMade(self):
        HTTPClient.connectionMade(self)
        self.sendCommand('GET', self.path)
        self.sendHeader('Host', self.host)
        self.endHeaders()
        self.headers = {}

    def handleHeader(self, header, value):
        h = header.lower()
        self.headers[h] = _parseHeader(h, value)

    def handleEndHeaders(self):
        if self.connected: self.transport.loseConnection()
        if not self.headers.has_key('passporturls') or not self.headers['passporturls'].has_key('dalogin'):
            self.deferred.errback(failure.Failure(failure.DefaultException("Invalid Nexus Reply")))
        else:
            self.deferred.callback('https://' + self.headers['passporturls']['dalogin'])

    def handleResponse(self, r): pass

class PassportLogin(HTTPClient):
    """
    This class is used internally to obtain
    a login ticket from a passport HTTPS
    server -- it should not be used directly.
    """

    _finished = 0

    def __init__(self, deferred, userHandle, passwd, host, authData):
        self.deferred = deferred
        self.userHandle = userHandle
        self.passwd = passwd
        self.authData = authData
        self.host, self.path = _parsePrimitiveHost(host)

    def connectionMade(self):
        self.sendCommand('GET', self.path)
        self.sendHeader('Authorization', 'Passport1.4 OrgVerb=GET,OrgURL=http://messenger.msn.com,' +
                                         'sign-in=%s,pwd=%s,%s' % (quote(self.userHandle), quote(self.passwd), self.authData))
        self.sendHeader('Host', self.host)
        self.endHeaders()
        self.headers = {}

    def handleHeader(self, header, value):
        h = header.lower()
        self.headers[h] = _parseHeader(h, value)

    def handleEndHeaders(self):
        if self._finished: return
        self._finished = 1 # I think we need this because of HTTPClient
        if self.connected: self.transport.loseConnection()
        authHeader = 'authentication-info'
        _interHeader = 'www-authenticate'
        if self.headers.has_key(_interHeader): authHeader = _interHeader
        try:
            info = self.headers[authHeader]
            status = info['da-status']
            handler = getattr(self, 'login_%s' % (status,), None)
            if handler:
                handler(info)
            else: raise Exception()
        except Exception, e:
            self.deferred.errback(failure.Failure(e))

    def handleResponse(self, r): pass

    def login_success(self, info):
        ticket = info['from-pp']
        ticket = ticket[1:len(ticket)-1]
        self.deferred.callback((LOGIN_SUCCESS, ticket))

    def login_failed(self, info):
        self.deferred.callback((LOGIN_FAILURE, unquote(info['cbtxt'])))

    def login_redir(self, info):
        self.deferred.callback((LOGIN_REDIRECT, self.headers['location'], self.authData))

class MSNProtocolError(Exception):
    """
    This Exception is basically used for debugging
    purposes, as the official MSN server should never
    send anything _wrong_ and nobody in their right
    mind would run their B{own} MSN server.
    If it is raised by default command handlers
    (handle_BLAH) the error will be logged.
    """
    pass

class MSNMessage:

    """
    I am the class used to represent an 'instant' message.

    @ivar userHandle: The user handle (passport) of the sender
                      (this is only used when receiving a message)
    @ivar screenName: The screen name of the sender (this is only used
                      when receiving a message)
    @ivar message: The message
    @ivar headers: The message headers
    @type headers: dict
    @ivar length: The message length (including headers and line endings)
    @ivar ack: This variable is used to tell the server how to respond
               once the message has been sent. If set to MESSAGE_ACK
               (default) the server will respond with an ACK upon receiving
               the message, if set to MESSAGE_NACK the server will respond
               with a NACK upon failure to receive the message.
               If set to MESSAGE_ACK_NONE the server will do nothing.
               This is relevant for the return value of
               SwitchboardClient.sendMessage (which will return
               a Deferred if ack is set to either MESSAGE_ACK or MESSAGE_NACK  
               and will fire when the respective ACK or NACK is received).
               If set to MESSAGE_ACK_NONE sendMessage will return None.
    """
    MESSAGE_ACK      = 'A'
    MESSAGE_ACK_FAT  = 'D'
    MESSAGE_NACK     = 'N'
    MESSAGE_ACK_NONE = 'U'

    ack = MESSAGE_ACK

    def __init__(self, length=0, userHandle="", screenName="", message="", specialMessage=False):
        self.userHandle = userHandle
        self.screenName = screenName
        self.specialMessage = specialMessage
        self.message = message
        self.headers = {'MIME-Version' : '1.0', 'Content-Type' : 'text/plain; charset=UTF-8'}
        self.length = length
        self.readPos = 0

    def _calcMessageLen(self):
        """
        used to calculte the number to send
        as the message length when sending a message.
        """
        return reduce(operator.add, [len(x[0]) + len(x[1]) + 4  for x in self.headers.items()]) + len(self.message) + 2

    def delHeader(self, header):
        """ delete the desired header """
        if self.headers.has_key(header):
            del self.headers[header]

    def setHeader(self, header, value):
        """ set the desired header """
        self.headers[header] = value

    def getHeader(self, header):
        """
        get the desired header value
        @raise KeyError: if no such header exists.
        """
        return self.headers[header]

    def hasHeader(self, header):
        """ check to see if the desired header exists """
        return self.headers.has_key(header)

    def getMessage(self):
        """ return the message - not including headers """
        return self.message

    def setMessage(self, message):
        """ set the message text """
        self.message = message


class MSNObject:
    """
    Used to represent a MSNObject. This can be currently only be an avatar.

    @ivar creator: The userHandle of the creator of this picture.
    @ivar imageDataFunc: A function to return the PNG image data (only for our own avatar)
    @ivar type: Always set to 3, for avatar.
    @ivar size: The size of the image.
    @ivar location: The filename of the image.
    @ivar friendly: Unknown.
    @ivar text: The textual representation of this MSNObject.
    """
    def __init__(self, s=""):
        """ Pass a XML MSNObject string to parse it, or pass no arguments for a null MSNObject to be created. """
        self.setNull()
        if s:
            self.parse(s)
    
    def setData(self, creator, imageDataFunc):
        """ Set the creator and imageData for this object """
        imageData = imageDataFunc()
        self.creator = creator
        self.imageDataFunc = imageDataFunc
        self.size = len(imageData)
        self.type = 3
        self.location = "TMP" + str(random.randint(1000,9999))
        self.friendly = "AAA="
        self.sha1d = b64enc(sha.sha(imageData).digest())
        self.makeText()
    
    def setNull(self):
        self.creator = ""
        self.imageDataFunc = lambda: None
        self.size = 0
        self.type = 0
        self.location = ""
        self.friendly = ""
        self.sha1d = ""
        self.text = ""
    
    def makeText(self):
        """ Makes a textual representation of this MSNObject. Stores it in self.text """
        h = []
        h.append("Creator")
        h.append(self.creator)
        h.append("Size")
        h.append(str(self.size))
        h.append("Type")
        h.append(str(self.type))
        h.append("Location")
        h.append(self.location)
        h.append("Friendly")
        h.append(self.friendly)
        h.append("SHA1D")
        h.append(self.sha1d)
        sha1c = b64enc(sha.sha("".join(h)).digest())
        self.text = '<msnobj Creator="%s" Size="%s" Type="%s" Location="%s" Friendly="%s" SHA1D="%s" SHA1C="%s"/>' % (self.creator, str(self.size), str(self.type), self.location, self.friendly, self.sha1d, sha1c)
    
    def parse(self, s):
        e = parseText(s, True)
        if not e:
            return # Parse failed
        try:
            self.creator = e.getAttribute("Creator")
            self.size = int(e.getAttribute("Size"))
            self.type = int(e.getAttribute("Type"))
            self.location = e.getAttribute("Location")
            self.friendly = e.getAttribute("Friendly")
            self.sha1d = e.getAttribute("SHA1D")
            self.text = s
        except TypeError:
            self.setNull()
        except ValueError:
            self.setNull()


class MSNContact:
    
    """
    This class represents a contact (user).

    @ivar userGuid: The contact's user guid (unique string)
    @ivar userHandle: The contact's user handle (passport).
    @ivar screenName: The contact's screen name.
    @ivar groups: A list of all the group IDs which this
                  contact belongs to.
    @ivar lists: An integer representing the sum of all lists
                 that this contact belongs to.
    @ivar caps: int, The capabilities of this client
    @ivar msnobj: The MSNObject representing the contact's avatar
    @ivar status: The contact's status code.
    @type status: str if contact's status is known, None otherwise.
    @ivar personal: The contact's personal message .
    @type personal: str if contact's personal message is known, None otherwise.

    @ivar homePhone: The contact's home phone number.
    @type homePhone: str if known, otherwise None.
    @ivar workPhone: The contact's work phone number.
    @type workPhone: str if known, otherwise None.
    @ivar mobilePhone: The contact's mobile phone number.
    @type mobilePhone: str if known, otherwise None.
    @ivar hasPager: Whether or not this user has a mobile pager
    @ivar hasBlog: Whether or not this user has a MSN Spaces blog
                    (true=yes, false=no)
    """
    MSNC1 = 0x10000000
    MSNC2 = 0x20000000
    MSNC3 = 0x30000000
    MSNC4 = 0x40000000
    
    def __init__(self, userGuid="", userHandle="", screenName="", lists=0, caps=0, msnobj=None, groups={}, status=None, personal=""):
        self.userGuid = userGuid
        self.userHandle = userHandle
        self.screenName = screenName
        self.lists = lists
        self.caps = caps
        self.msnobj = msnobj
        self.msnobjGot = True
        self.groups = [] # if applicable
        self.status = status # current status
        self.personal = personal

        # phone details
        self.homePhone   = None
        self.workPhone   = None
        self.mobilePhone = None
        self.hasPager    = None
        self.hasBlog     = None

    def setPhone(self, phoneType, value):
        """
        set phone numbers/values for this specific user.
        for phoneType check the *_PHONE constants and HAS_PAGER
        """

        t = phoneType.upper()
        if t == HOME_PHONE: self.homePhone = value
        elif t == WORK_PHONE: self.workPhone = value
        elif t == MOBILE_PHONE: self.mobilePhone = value
        elif t == HAS_PAGER: self.hasPager = value
        elif t == HAS_BLOG: self.hasBlog = value
        #else: raise ValueError, "Invalid Phone Type: " + t

    def addToList(self, listType):
        """
        Update the lists attribute to
        reflect being part of the
        given list.
        """
        self.lists |= listType

    def removeFromList(self, listType):
        """
        Update the lists attribute to
        reflect being removed from the
        given list.
        """
        self.lists ^= listType

class MSNContactList:
    """
    This class represents a basic MSN contact list.

    @ivar contacts: All contacts on my various lists
    @type contacts: dict (mapping user handles to MSNContact objects)
    @ivar groups: a mapping of group ids to group names
                  (groups can only exist on the forward list)
    @type groups: dict

    B{Note}:
    This is used only for storage and doesn't effect the
    server's contact list.
    """

    def __init__(self):
        self.contacts = {}
        self.groups = {}
        self.autoAdd = 0
        self.privacy = 0
        self.version = 0

    def _getContactsFromList(self, listType):
        """
        Obtain all contacts which belong
        to the given list type.
        """
        return dict([(uH,obj) for uH,obj in self.contacts.items() if obj.lists & listType])

    def addContact(self, contact):
        """
        Add a contact
        """
        self.contacts[contact.userHandle] = contact

    def remContact(self, userHandle):
        """
        Remove a contact
        """
        try:
            del self.contacts[userHandle]
        except KeyError: pass

    def getContact(self, userHandle):
        """
        Obtain the MSNContact object
        associated with the given
        userHandle.
        @return: the MSNContact object if
                 the user exists, or None.
        """
        try:
            return self.contacts[userHandle]
        except KeyError:
            return None

    def getBlockedContacts(self):
        """
        Obtain all the contacts on my block list
        """
        return self._getContactsFromList(BLOCK_LIST)

    def getAuthorizedContacts(self):
        """
        Obtain all the contacts on my auth list.
        (These are contacts which I have verified
        can view my state changes).
        """
        return self._getContactsFromList(ALLOW_LIST)

    def getReverseContacts(self):
        """
        Get all contacts on my reverse list.
        (These are contacts which have added me
        to their forward list).
        """
        return self._getContactsFromList(REVERSE_LIST)

    def getContacts(self):
        """
        Get all contacts on my forward list.
        (These are the contacts which I have added
        to my list).
        """
        return self._getContactsFromList(FORWARD_LIST)

    def setGroup(self, id, name):
        """
        Keep a mapping from the given id
        to the given name.
        """
        self.groups[id] = name

    def remGroup(self, id):
        """
        Removed the stored group
        mapping for the given id.
        """
        try:
            del self.groups[id]
        except KeyError: pass
        for c in self.contacts:
            if id in c.groups: c.groups.remove(id)


class MSNEventBase(LineReceiver):
    """
    This class provides support for handling / dispatching events and is the
    base class of the three main client protocols (DispatchClient,
    NotificationClient, SwitchboardClient)
    """

    def __init__(self):
        self.ids = {} # mapping of ids to Deferreds
        self.currentID = 0
        self.connected = 0
        self.setLineMode()
        self.currentMessage = None

    def connectionLost(self, reason):
        self.ids = {}
        self.connected = 0

    def connectionMade(self):
        self.connected = 1

    def _fireCallback(self, id, *args):
        """
        Fire the callback for the given id
        if one exists and return 1, else return false
        """
        if self.ids.has_key(id):
            self.ids[id][0].callback(args)
            del self.ids[id]
            return 1
        return 0

    def _nextTransactionID(self):
        """ return a usable transaction ID """
        self.currentID += 1
        if self.currentID > 1000: self.currentID = 1
        return self.currentID

    def _createIDMapping(self, data=None):
        """
        return a unique transaction ID that is mapped internally to a
        deferred .. also store arbitrary data if it is needed
        """
        id = self._nextTransactionID()
        d = Deferred()
        self.ids[id] = (d, data)
        return (id, d)

    def checkMessage(self, message):
        """
        process received messages to check for file invitations and
        typing notifications and other control type messages
        """
        raise NotImplementedError

    def sendLine(self, line):
        if LINEDEBUG: log.msg("<< " + line)
        LineReceiver.sendLine(self, line)

    def lineReceived(self, line):
        if LINEDEBUG: log.msg(">> " + line)
        if not self.connected: return
        if self.currentMessage:
            self.currentMessage.readPos += len(line+"\r\n")
            try:
                header, value = line.split(':')
                self.currentMessage.setHeader(header, unquote(value).lstrip())
                return
            except ValueError:
                #raise MSNProtocolError, "Invalid Message Header"
                line = ""
            if line == "" or self.currentMessage.specialMessage:
                self.setRawMode()
                if self.currentMessage.readPos == self.currentMessage.length: self.rawDataReceived("") # :(
                return
        try:
            cmd, params = line.split(' ', 1)
        except ValueError:
            raise MSNProtocolError, "Invalid Message, %s" % repr(line)

        if len(cmd) != 3: raise MSNProtocolError, "Invalid Command, %s" % repr(cmd)
        if cmd.isdigit():
            id = params.split(' ')[0]
            if id.isdigit() and self.ids.has_key(int(id)):
                id = int(id)
                self.ids[id][0].errback(int(cmd))
                del self.ids[id]
                return
            else:       # we received an error which doesn't map to a sent command
                self.gotError(int(cmd))
                return

        handler = getattr(self, "handle_%s" % cmd.upper(), None)
        if handler:
            try: handler(params.split(' '))
            except MSNProtocolError, why: self.gotBadLine(line, why)
        else:
            self.handle_UNKNOWN(cmd, params.split(' '))

    def rawDataReceived(self, data):
        if not self.connected: return
        extra = ""
        self.currentMessage.readPos += len(data)
        diff = self.currentMessage.readPos - self.currentMessage.length
        if diff > 0:
            self.currentMessage.message += data[:-diff]
            extra = data[-diff:]
        elif diff == 0:
            self.currentMessage.message += data
        else:
            self.currentMessage.message += data
            return
        del self.currentMessage.readPos
        m = self.currentMessage
        self.currentMessage = None
        if MESSAGEDEBUG: log.msg(m.message)
        try:
            if not self.checkMessage(m):
                self.setLineMode(extra)
                return
        except Exception, e:
            self.setLineMode(extra)
            raise
        self.gotMessage(m)
        self.setLineMode(extra)

    ### protocol command handlers - no need to override these.

    def handle_MSG(self, params):
        checkParamLen(len(params), 3, 'MSG')
        try:
            messageLen = int(params[2])
        except ValueError: raise MSNProtocolError, "Invalid Parameter for MSG length argument"
        self.currentMessage = MSNMessage(length=messageLen, userHandle=params[0], screenName=unquote(params[1]))

    def handle_UNKNOWN(self, cmd, params):
        """ implement me in subclasses if you want to handle unknown events """
        log.msg("Received unknown command (%s), params: %s" % (cmd, params))

    ### callbacks

    def gotBadLine(self, line, why):
        """ called when a handler notifies me that this line is broken """
        log.msg('Error in line: %s (%s)' % (line, why))

    def gotError(self, errorCode):
        """
        called when the server sends an error which is not in
        response to a sent command (ie. it has no matching transaction ID)
        """
        log.msg('Error %s' % (errorCodes[errorCode]))


class DispatchClient(MSNEventBase):
    """
    This class provides support for clients connecting to the dispatch server
    @ivar userHandle: your user handle (passport) needed before connecting.
    """

    def connectionMade(self):
        MSNEventBase.connectionMade(self)
        self.sendLine('VER %s %s' % (self._nextTransactionID(), MSN_PROTOCOL_VERSION))

    ### protocol command handlers ( there is no need to override these )

    def handle_VER(self, params):
        versions = params[1:]
        if versions is None or ' '.join(versions) != MSN_PROTOCOL_VERSION:
            self.transport.loseConnection()
            raise MSNProtocolError, "Invalid version response"
        id = self._nextTransactionID()
        self.sendLine("CVR %s %s %s" % (id, MSN_CVR_STR, self.factory.userHandle))

    def handle_CVR(self, params):
        self.sendLine("USR %s TWN I %s" % (self._nextTransactionID(), self.factory.userHandle))

    def handle_XFR(self, params):
        if len(params) < 4: raise MSNProtocolError, "Invalid number of parameters for XFR"
        id, refType, addr = params[:3]
        # was addr a host:port pair?
        try:
            host, port = addr.split(':')
        except ValueError:
            host = addr
            port = MSN_PORT
        if refType == "NS":
            self.gotNotificationReferral(host, int(port))

    ### callbacks

    def gotNotificationReferral(self, host, port):
        """
        called when we get a referral to the notification server.

        @param host: the notification server's hostname
        @param port: the port to connect to
        """
        pass


class DispatchFactory(ClientFactory):
    """
    This class keeps the state for the DispatchClient.

    @ivar userHandle: the userHandle to request a notification
                      server for.
    """
    protocol = DispatchClient
    userHandle = ""



class NotificationClient(MSNEventBase):
    """
    This class provides support for clients connecting
    to the notification server.
    """

    factory = None # sssh pychecker

    def __init__(self, currentID=0):
        MSNEventBase.__init__(self)
        self.currentID = currentID
        self._state = ['DISCONNECTED', {}]
        self.pingCounter = 0
        self.pingCheckTask = None
        self.msnobj = MSNObject()

    def _setState(self, state):
        self._state[0] = state

    def _getState(self):
        return self._state[0]

    def _getStateData(self, key):
        return self._state[1][key]

    def _setStateData(self, key, value):
        self._state[1][key] = value

    def _remStateData(self, *args):
        for key in args: del self._state[1][key]

    def connectionMade(self):
        MSNEventBase.connectionMade(self)
        self._setState('CONNECTED')
        self.sendLine("VER %s %s" % (self._nextTransactionID(), MSN_PROTOCOL_VERSION))
        self.factory.resetDelay()

    def connectionLost(self, reason):
        self._setState('DISCONNECTED')
        self._state[1] = {}
        if self.pingCheckTask:
            self.pingCheckTask.stop()
            self.pingCheckTask = None
        MSNEventBase.connectionLost(self, reason)

    def _getEmailFields(self, message):
        fields = message.getMessage().strip().split('\n')
        values = {}
        for i in fields:
            a = i.split(':')
            if len(a) != 2: continue
            f, v = a
            f = f.strip()
            v = v.strip()
            values[f] = v
        return values

    def _gotInitialEmailNotification(self, message):
        values = self._getEmailFields(message)
        try:
            inboxunread = int(values["Inbox-Unread"])
            foldersunread = int(values["Folders-Unread"])
        except KeyError:
            return
        if foldersunread + inboxunread > 0: # For some reason MSN sends notifications about empty inboxes sometimes?
            self.gotInitialEmailNotification(inboxunread, foldersunread)

    def _gotEmailNotification(self, message):
        values = self._getEmailFields(message)
        try:
            mailfrom = values["From"]
            fromaddr = values["From-Addr"]
            subject = values["Subject"]
            junkbeginning = "=?\"us-ascii\"?Q?"
            junkend = "?="
            subject = subject.replace(junkbeginning, "").replace(junkend, "").replace("_", " ")
        except KeyError:
            # If any of the fields weren't found then it's not a big problem. We just ignore the message
            return
        self.gotRealtimeEmailNotification(mailfrom, fromaddr, subject)

    def _gotMSNAlert(self, message):
        notification = parseText(message.message, beExtremelyLenient=True)
        siteurl = notification.getAttribute("siteurl")
        notid = notification.getAttribute("id")

        msg = None
        for e in notification.elements():
            if e.name == "MSG":
                msg = e
                break
        else: return

        msgid = msg.getAttribute("id")

        action = None
        subscr = None
        bodytext = None
        for e in msg.elements():
            if e.name == "ACTION":
                action = e.getAttribute("url")
            if e.name == "SUBSCR":
                subscr = e.getAttribute("url")
            if e.name == "BODY":
                for e2 in e.elements():
                    if e2.name == "TEXT":
                        bodytext = e2.__str__()
        if not (action and subscr and bodytext): return

        actionurl = "%s&notification_id=%s&message_id=%s&agent=messenger" % (action, notid, msgid) # Used to have $siteurl// at the beginning, but it seems to not work with that now. Weird
        subscrurl = "%s&notification_id=%s&message_id=%s&agent=messenger" % (subscr, notid, msgid)

        self.gotMSNAlert(bodytext, actionurl, subscrurl)

    def _gotUBX(self, message):
        msnContact = self.factory.contacts.getContact(message.userHandle)
        if not msnContact: return
        lm = message.message.lower()
        p1 = lm.find("<psm>") + 5
        p2 = lm.find("</psm>")
        if p1 >= 0 and p2 >= 0:
            personal = unescapeFromXml(message.message[p1:p2])
            msnContact.personal = personal
            self.contactPersonalChanged(message.userHandle, personal)
        else:
            msnContact.personal = ''
            self.contactPersonalChanged(message.userHandle, '')

    def checkMessage(self, message):
        """ hook used for detecting specific notification messages """
        cTypes = [s.lstrip() for s in message.getHeader('Content-Type').split(';')]
        if 'text/x-msmsgsprofile' in cTypes:
            self.gotProfile(message)
            return 0
        elif "text/x-msmsgsinitialemailnotification" in cTypes:
            self._gotInitialEmailNotification(message)
            return 0
        elif "text/x-msmsgsemailnotification" in cTypes:
            self._gotEmailNotification(message)
            return 0
        elif "NOTIFICATION" == message.userHandle and message.specialMessage == True:
            self._gotMSNAlert(message)
            return 0
        elif "UBX" == message.screenName and message.specialMessage == True:
            self._gotUBX(message)
            return 0
        return 1

    ### protocol command handlers - no need to override these

    def handle_VER(self, params):
        versions = params[1:]
        if versions is None or ' '.join(versions) != MSN_PROTOCOL_VERSION:
            self.transport.loseConnection()
            raise MSNProtocolError, "Invalid version response"
        self.sendLine("CVR %s %s %s" % (self._nextTransactionID(), MSN_CVR_STR, self.factory.userHandle))

    def handle_CVR(self, params):
        self.sendLine("USR %s TWN I %s" % (self._nextTransactionID(), self.factory.userHandle))

    def handle_USR(self, params):
        if not (4 <= len(params) <= 6):
            raise MSNProtocolError, "Invalid Number of Parameters for USR"

        mechanism = params[1]
        if mechanism == "OK":
            self.loggedIn(params[2], int(params[3]))
        elif params[2].upper() == "S":
            # we need to obtain auth from a passport server
            f = self.factory
            d = _login(f.userHandle, f.password, f.passportServer, authData=params[3])
            d.addCallback(self._passportLogin)
            d.addErrback(self._passportError)

    def _passportLogin(self, result):
        if result[0] == LOGIN_REDIRECT:
            d = _login(self.factory.userHandle, self.factory.password,
                       result[1], cached=1, authData=result[2])
            d.addCallback(self._passportLogin)
            d.addErrback(self._passportError)
        elif result[0] == LOGIN_SUCCESS:
            self.sendLine("USR %s TWN S %s" % (self._nextTransactionID(), result[1]))
        elif result[0] == LOGIN_FAILURE:
            self.loginFailure(result[1])

    def _passportError(self, failure):
        self.loginFailure("Exception while authenticating: %s" % failure)

    def handle_CHG(self, params):
        id = int(params[0])
        if not self._fireCallback(id, params[1]):
            if self.factory: self.factory.status = params[1]
            self.statusChanged(params[1])

    def handle_ILN(self, params):
        #checkParamLen(len(params), 6, 'ILN')
        msnContact = self.factory.contacts.getContact(params[2])
        if not msnContact: return
        msnContact.status = params[1]
        msnContact.screenName = unquote(params[3])
        if len(params) > 4: msnContact.caps = int(params[4])
        if len(params) > 5 and params[5] != "0":
            self.handleAvatarHelper(msnContact, params[5])
        else:
            self.handleAvatarGoneHelper(msnContact)
        self.gotContactStatus(params[2], params[1], unquote(params[3]))

    def handleAvatarGoneHelper(self, msnContact):
        if msnContact.msnobj:
            msnContact.msnobj = None
            msnContact.msnobjGot = True
            self.contactAvatarChanged(msnContact.userHandle, "")

    def handleAvatarHelper(self, msnContact, msnobjStr):
        msnobj = MSNObject(unquote(msnobjStr))
        if not msnContact.msnobj or msnobj.sha1d != msnContact.msnobj.sha1d:
            if MSNP2PDEBUG: log.msg("Updated MSNObject received!" + msnobjStr)
            msnContact.msnobj = msnobj
            msnContact.msnobjGot = False
            self.contactAvatarChanged(msnContact.userHandle, binascii.hexlify(b64dec(msnContact.msnobj.sha1d)))

    def handle_CHL(self, params):
        checkParamLen(len(params), 2, 'CHL')
        response = msnp11chl.doChallenge(params[1])
        self.sendLine("QRY %s %s %s" % (self._nextTransactionID(), msnp11chl.MSNP11_PRODUCT_ID, len(response)))
        self.transport.write(response)

    def handle_QRY(self, params):
        pass

    def handle_NLN(self, params):
        if not self.factory: return
        msnContact = self.factory.contacts.getContact(params[1])
        if not msnContact: return
        msnContact.status = params[0]
        msnContact.screenName = unquote(params[2])
        if len(params) > 3: msnContact.caps = int(params[3])
        if len(params) > 4 and params[4] != "0":
            self.handleAvatarHelper(msnContact, params[4])
        else:
            self.handleAvatarGoneHelper(msnContact)
        self.contactStatusChanged(params[1], params[0], unquote(params[2]))

    def handle_FLN(self, params):
        checkParamLen(len(params), 1, 'FLN')
        msnContact = self.factory.contacts.getContact(params[0])
        if msnContact:
            msnContact.status = STATUS_OFFLINE
        self.contactOffline(params[0])

    def handle_LST(self, params):
        if self._getState() != 'SYNC': return

        userHandle, screenName, userGuid, lists, groups = getVals(params)

        if not userHandle or lists < 1:
            raise MSNProtocolError, "Unknown LST " + str(params) # debug
        contact = MSNContact(userGuid, userHandle, screenName, lists)
        if contact.lists & FORWARD_LIST:
            contact.groups.extend(map(str, groups))
        self._getStateData('list').addContact(contact)
        self._setStateData('last_contact', contact)
        sofar = self._getStateData('lst_sofar') + 1
        if sofar == self._getStateData('lst_reply'):
            # this is the best place to determine that
            # a syn realy has finished - msn _may_ send
            # BPR information for the last contact
            # which is unfortunate because it means
            # that the real end of a syn is non-deterministic.
            # to handle this we'll keep 'last_contact' hanging
            # around in the state data and update it if we need
            # to later.
            self._setState('SESSION')
            contacts = self._getStateData('list')
            phone = self._getStateData('phone')
            id = self._getStateData('synid')
            self._remStateData('lst_reply', 'lsg_reply', 'lst_sofar', 'phone', 'synid', 'list')
            self._fireCallback(id, contacts, phone)
        else:
            self._setStateData('lst_sofar',sofar)

    def handle_BLP(self, params):
        # If this is in response to a SYN, then there will be a transaction ID
        try:
            id = int(params[0])
            self.factory.contacts.privacy = listCodeToID[params[1].lower()]
            self._fireCallback(id, params[1])
        except ValueError:
            self._getStateData('list').privacy = listCodeToID[params[0].lower()]

    def handle_GTC(self, params):
        # If this is in response to a SYN, then there will be a transaction ID
        try:
            id = int(params[0])
            if params[1].lower() == "a": self._fireCallback(id, 0)
            elif params[1].lower() == "n": self._fireCallback(id, 1)
            else: raise MSNProtocolError, "Invalid Paramater for GTC" # debug
        except ValueError:
            if params[0].lower() == "a": self._getStateData('list').autoAdd = 0
            elif params[0].lower() == "n": self._getStateData('list').autoAdd = 1
            else: raise MSNProtocolError, "Invalid Paramater for GTC" # debug

    def handle_SYN(self, params):
        id = int(params[0])
        contacts = MSNContactList()
        self._setStateData('list', contacts)
        self._setStateData('phone', [])
        self._setStateData('lst_reply', int(params[3]))
        self._setStateData('lsg_reply', int(params[4]))
        self._setStateData('lst_sofar', 0)
        if params[3] == "0": # No LST will be received. New account?
            self._setState('SESSION')
            self._fireCallback(id, contacts, [])

    def handle_LSG(self, params):
        if self._getState() == 'SYNC':
            self._getStateData('list').groups[params[1]] = unquote(params[0])

    def handle_PRP(self, params):
        if params[1] == "MFN":
            self._fireCallback(int(params[0]))
        else:
            try:
                self._fireCallback(int(params[0]), int(params[1]), unquote(params[3]))
            except ValueError:
                self._getStateData('phone').append((params[0], unquote(params[1])))

    def handle_BPR(self, params):
        numParams = len(params)
        if numParams == 2: # part of a syn
            self._getStateData('last_contact').setPhone(params[0], unquote(params[1]))
        elif numParams == 4:
            if not self.factory.contacts: raise MSNProtocolError, "handle_BPR called with no contact list" # debug
            self.factory.contacts.version = int(params[0])
            userHandle, phoneType, number = params[1], params[2], unquote(params[3])
            self.factory.contacts.getContact(userHandle).setPhone(phoneType, number)
            self.gotPhoneNumber(userHandle, phoneType, number)


    def handle_ADG(self, params):
        checkParamLen(len(params), 5, 'ADG')
        id = int(params[0])
        if not self._fireCallback(id, int(params[1]), unquote(params[2]), int(params[3])):
            raise MSNProtocolError, "ADG response does not match up to a request" # debug

    def handle_RMG(self, params):
        checkParamLen(len(params), 3, 'RMG')
        id = int(params[0])
        if not self._fireCallback(id, int(params[1]), int(params[2])):
            raise MSNProtocolError, "RMG response does not match up to a request" # debug

    def handle_REG(self, params):
        checkParamLen(len(params), 5, 'REG')
        id = int(params[0])
        if not self._fireCallback(id, int(params[1]), int(params[2]), unquote(params[3])):
            raise MSNProtocolError, "REG response does not match up to a request" # debug

    def handle_ADC(self, params):
        if not self.factory.contacts: raise MSNProtocolError, "handle_ADC called with no contact list"
        numParams = len(params)
        if numParams < 3 or params[1].upper() not in ('AL','BL','RL','FL','PL'):
            raise MSNProtocolError, "Invalid Paramaters for ADC" # debug
        id = int(params[0])
        listType = params[1].lower()
        userHandle, screenName, userGuid, ignored1, groups = getVals(params[2:])

        if groups and listType.upper() != FORWARD_LIST:
            raise MSNProtocolError, "Only forward list can contain groups" # debug

        if not self._fireCallback(id, listCodeToID[listType], userGuid, userHandle, screenName):
            c = self.factory.contacts.getContact(userHandle)
            if not c:
                c = MSNContact(userGuid=userGuid, userHandle=userHandle, screenName=screenName)
                self.factory.contacts.addContact(c)
            c.addToList(PENDING_LIST)
            self.userAddedMe(userGuid, userHandle, screenName)

    def handle_REM(self, params):
        if not self.factory.contacts: raise MSNProtocolError, "handle_REM called with no contact list available!"
        numParams = len(params)
        if numParams < 3 or params[1].upper() not in ('AL','BL','FL','RL','PL'):
            raise MSNProtocolError, "Invalid Paramaters for REM" # debug
        id = int(params[0])
        listType = params[1].lower()
        userHandle = params[2]
        groupID = None
        if numParams == 4:
            if params[1] != "FL": raise MSNProtocolError, "Only forward list can contain groups" # debug
            groupID = int(params[3])
        if not self._fireCallback(id, listCodeToID[listType], userHandle, groupID):
            if listType.upper() != "RL": return
            c = self.factory.contacts.getContact(userHandle)
            if not c: return
            c.removeFromList(REVERSE_LIST)
            if c.lists == 0: self.factory.contacts.remContact(c.userHandle)
            self.userRemovedMe(userHandle)

    def handle_XFR(self, params):
        checkParamLen(len(params), 5, 'XFR')
        id = int(params[0])
        # check to see if they sent a host/port pair
        try:
            host, port = params[2].split(':')
        except ValueError:
            host = params[2]
            port = MSN_PORT

        if not self._fireCallback(id, host, int(port), params[4]):
            raise MSNProtocolError, "Got XFR (referral) that I didn't ask for .. should this happen?" # debug

    def handle_RNG(self, params):
        checkParamLen(len(params), 6, 'RNG')
        # check for host:port pair
        try:
            host, port = params[1].split(":")
            port = int(port)
        except ValueError:
            host = params[1]
            port = MSN_PORT
        self.gotSwitchboardInvitation(int(params[0]), host, port, params[3], params[4],
                                      unquote(params[5]))

    def handle_NOT(self, params):
        checkParamLen(len(params), 1, 'NOT')
        try:
            messageLen = int(params[0])
        except ValueError: raise MSNProtocolError, "Invalid Parameter for NOT length argument"
        self.currentMessage = MSNMessage(length=messageLen, userHandle="NOTIFICATION", specialMessage=True)
        self.setRawMode()

    def handle_UBX(self, params):
        checkParamLen(len(params), 2, 'UBX')
        try:
            messageLen = int(params[1])
        except ValueError: raise MSNProtocolError, "Invalid Parameter for UBX length argument"
        if messageLen > 0:
            self.currentMessage = MSNMessage(length=messageLen, userHandle=params[0], screenName="UBX", specialMessage=True)
            self.setRawMode()
        else:
            self._gotUBX(MSNMessage(userHandle=params[0]))

    def handle_UUX(self, params):
        checkParamLen(len(params), 2, 'UUX')
        if params[1] != '0': return
        id = int(params[0])
        self._fireCallback(id)

    def handle_OUT(self, params):
        checkParamLen(len(params), 1, 'OUT')
        self.factory.stopTrying()
        if params[0] == "OTH": self.multipleLogin()
        elif params[0] == "SSD": self.serverGoingDown()
        else: raise MSNProtocolError, "Invalid Parameters received for OUT" # debug

    def handle_QNG(self, params):
        self.pingCounter = 0 # They replied to a ping. We'll forgive them for any they may have missed, because they're alive again now

    # callbacks

    def pingChecker(self):
        if self.pingCounter > 5:
            # The server has ignored 5 pings, lets kill the connection
            self.transport.loseConnection()
        else:
            self.sendLine("PNG")
            self.pingCounter += 1

    def pingCheckerStart(self, *args):
        self.pingCheckTask = task.LoopingCall(self.pingChecker)
        self.pingCheckTask.start(PINGSPEED)

    def loggedIn(self, userHandle, verified):
        """
        Called when the client has logged in.
        The default behaviour of this method is to
        update the factory with our screenName and
        to sync the contact list (factory.contacts).
        When this is complete self.listSynchronized
        will be called.

        @param userHandle: our userHandle
        @param verified: 1 if our passport has been (verified), 0 if not.
                         (i'm not sure of the significace of this)
        @type verified: int
        """
        d = self.syncList()
        d.addCallback(self.listSynchronized)
        d.addCallback(self.pingCheckerStart)

    def loginFailure(self, message):
        """
        Called when the client fails to login.

        @param message: a message indicating the problem that was encountered
        """
        pass

    def gotProfile(self, message):
        """
        Called after logging in when the server sends an initial
        message with MSN/passport specific profile information
        such as country, number of kids, etc.
        Check the message headers for the specific values.

        @param message: The profile message
        """
        pass

    def listSynchronized(self, *args):
        """
        Lists are now synchronized by default upon logging in, this
        method is called after the synchronization has finished
        and the factory now has the up-to-date contacts.
        """
        pass

    def contactAvatarChanged(self, userHandle, hash):
        """
        Called when we receive the first, or a new <msnobj/> from a
        contact.

        @param userHandle: contact who's msnobj has been changed
        @param hash: sha1 hash of their avatar as hex string
        """

    def statusChanged(self, statusCode):
        """
        Called when our status changes and its not in response to a
        client command.

        @param statusCode: 3-letter status code
        """
        pass

    def gotContactStatus(self, userHandle, statusCode, screenName):
        """
        Called when we receive a list of statuses upon login.

        @param userHandle: the contact's user handle (passport)
        @param statusCode: 3-letter status code
        @param screenName: the contact's screen name
        """
        pass

    def contactStatusChanged(self, userHandle, statusCode, screenName):
        """
        Called when we're notified that a contact's status has changed.

        @param userHandle: the contact's user handle (passport)
        @param statusCode: 3-letter status code
        @param screenName: the contact's screen name
        """
        pass

    def contactPersonalChanged(self, userHandle, personal):
        """
        Called when a contact's personal message changes.

        @param userHandle: the contact who changed their personal message
        @param personal  : the new personal message
        """
        pass

    def contactOffline(self, userHandle):
        """
        Called when a contact goes offline.

        @param userHandle: the contact's user handle
        """
        pass

    def gotMessage(self, message):
        """
        Called when there is a message from the notification server
        that is not understood by default.

        @param message: the MSNMessage.
        """
        pass

    def gotMSNAlert(self, body, action, subscr):
        """
        Called when the server sends an MSN Alert (http://alerts.msn.com)

        @param body  : the alert text
        @param action: a URL with more information for the user to view
        @param subscr: a URL the user can use to modify their alert subscription
        """
        pass

    def gotInitialEmailNotification(self, inboxunread, foldersunread):
        """
        Called when the server sends you details about your hotmail
        inbox. This is only ever called once, on login.

        @param inboxunread  : the number of unread items in your inbox
        @param foldersunread: the number of unread items in other folders
        """
        pass

    def gotRealtimeEmailNotification(self, mailfrom, fromaddr, subject):
        """
        Called when the server sends us realtime email
        notification. This means that you have received
        a new email in your hotmail inbox.

        @param mailfrom: the sender of the email
        @param fromaddr: the sender of the email (I don't know :P)
        @param subject : the email subject
        """
        pass

    def gotPhoneNumber(self, userHandle, phoneType, number):
        """
        Called when the server sends us phone details about
        a specific user (for example after a user is added
        the server will send their status, phone details etc.

        @param userHandle: the contact's user handle (passport)
        @param phoneType: the specific phoneType
                          (*_PHONE constants or HAS_PAGER)
        @param number: the value/phone number.
        """
        pass

    def userAddedMe(self, userGuid, userHandle, screenName):
        """
        Called when a user adds me to their list. (ie. they have been added to
        the reverse list.

        @param userHandle: the userHandle of the user
        @param screenName: the screen name of the user
        """
        pass

    def userRemovedMe(self, userHandle):
        """
        Called when a user removes us from their contact list
        (they are no longer on our reverseContacts list.

        @param userHandle: the contact's user handle (passport)
        """
        pass

    def gotSwitchboardInvitation(self, sessionID, host, port,
                                 key, userHandle, screenName):
        """
        Called when we get an invitation to a switchboard server.
        This happens when a user requests a chat session with us.

        @param sessionID: session ID number, must be remembered for logging in
        @param host: the hostname of the switchboard server
        @param port: the port to connect to
        @param key: used for authorization when connecting
        @param userHandle: the user handle of the person who invited us
        @param screenName: the screen name of the person who invited us
        """
        pass

    def multipleLogin(self):
        """
        Called when the server says there has been another login
        under our account, the server should disconnect us right away.
        """
        pass

    def serverGoingDown(self):
        """
        Called when the server has notified us that it is going down for
        maintenance.
        """
        pass

    # api calls

    def changeStatus(self, status):
        """
        Change my current status. This method will add
        a default callback to the returned Deferred
        which will update the status attribute of the
        factory.

        @param status: 3-letter status code (as defined by
                       the STATUS_* constants)
        @return: A Deferred, the callback of which will be
                 fired when the server confirms the change
                 of status.  The callback argument will be
                 a tuple with the new status code as the
                 only element.
        """
        
        id, d = self._createIDMapping()
        self.sendLine("CHG %s %s %s %s" % (id, status, str(MSNContact.MSNC1 | MSNContact.MSNC2 | MSNContact.MSNC3 | MSNContact.MSNC4), quote(self.msnobj.text)))
        def _cb(r):
            self.factory.status = r[0]
            return r
        return d.addCallback(_cb)

    def setPrivacyMode(self, privLevel):
        """
        Set my privacy mode on the server.

        B{Note}:
        This only keeps the current privacy setting on
        the server for later retrieval, it does not
        effect the way the server works at all.

        @param privLevel: This parameter can be true, in which
                          case the server will keep the state as
                          'al' which the official client interprets
                          as -> allow messages from only users on
                          the allow list.  Alternatively it can be
                          false, in which case the server will keep
                          the state as 'bl' which the official client
                          interprets as -> allow messages from all
                          users except those on the block list.
                          
        @return: A Deferred, the callback of which will be fired when
                 the server replies with the new privacy setting.
                 The callback argument will be a tuple, the only element
                 of which being either 'al' or 'bl' (the new privacy setting).
        """

        id, d = self._createIDMapping()
        if privLevel: self.sendLine("BLP %s AL" % id)
        else: self.sendLine("BLP %s BL" % id)
        return d

    def syncList(self):
        """
        Used for keeping an up-to-date contact list.
        A callback is added to the returned Deferred
        that updates the contact list on the factory
        and also sets my state to STATUS_ONLINE.

        B{Note}:
        This is called automatically upon signing
        in using the version attribute of
        factory.contacts, so you may want to persist
        this object accordingly. Because of this there
        is no real need to ever call this method
        directly.

        @return: A Deferred, the callback of which will be
                 fired when the server sends an adequate reply.
                 The callback argument will be a tuple with two
                 elements, the new list (MSNContactList) and
                 your current state (a dictionary).  If the version
                 you sent _was_ the latest list version, both elements
                 will be None. To just request the list send a version of 0.
        """

        self._setState('SYNC')
        id, d = self._createIDMapping(data=None)
        self._setStateData('synid',id)
        self.sendLine("SYN %s %s %s" % (id, 0, 0))
        def _cb(r):
            self.changeStatus(STATUS_ONLINE)
            if r[0] is not None:
                self.factory.contacts = r[0]
            return r
        return d.addCallback(_cb)

    def setPhoneDetails(self, phoneType, value):
        """
        Set/change my phone numbers stored on the server.

        @param phoneType: phoneType can be one of the following
                          constants - HOME_PHONE, WORK_PHONE,
                          MOBILE_PHONE, HAS_PAGER.
                          These are pretty self-explanatory, except
                          maybe HAS_PAGER which refers to whether or
                          not you have a pager.
        @param value: for all of the *_PHONE constants the value is a
                      phone number (str), for HAS_PAGER accepted values
                      are 'Y' (for yes) and 'N' (for no).

        @return: A Deferred, the callback for which will be fired when
                 the server confirms the change has been made. The
                 callback argument will be a tuple with 2 elements, the
                 first being the new list version (int) and the second
                 being the new phone number value (str).
        """
        raise "ProbablyDoesntWork"
        # XXX: Add a default callback which updates
        # factory.contacts.version and the relevant phone
        # number
        id, d = self._createIDMapping()
        self.sendLine("PRP %s %s %s" % (id, phoneType, quote(value)))
        return d

    def addListGroup(self, name):
        """
        Used to create a new list group.
        A default callback is added to the
        returned Deferred which updates the
        contacts attribute of the factory.

        @param name: The desired name of the new group.

        @return: A Deferred, the callbacck for which will be called
                 when the server clarifies that the new group has been
                 created.  The callback argument will be a tuple with 3
                 elements: the new list version (int), the new group name
                 (str) and the new group ID (int).
        """

        raise "ProbablyDoesntWork"
        id, d = self._createIDMapping()
        self.sendLine("ADG %s %s 0" % (id, quote(name)))
        def _cb(r):
            if self.factory.contacts:
                self.factory.contacts.version = r[0]
                self.factory.contacts.setGroup(r[1], r[2])
            return r
        return d.addCallback(_cb)

    def remListGroup(self, groupID):
        """
        Used to remove a list group.
        A default callback is added to the
        returned Deferred which updates the
        contacts attribute of the factory.

        @param groupID: the ID of the desired group to be removed.

        @return: A Deferred, the callback for which will be called when
                 the server clarifies the deletion of the group.
                 The callback argument will be a tuple with 2 elements:
                 the new list version (int) and the group ID (int) of
                 the removed group.
        """

        raise "ProbablyDoesntWork"
        id, d = self._createIDMapping()
        self.sendLine("RMG %s %s" % (id, groupID))
        def _cb(r):
            self.factory.contacts.version = r[0]
            self.factory.contacts.remGroup(r[1])
            return r
        return d.addCallback(_cb)

    def renameListGroup(self, groupID, newName):
        """
        Used to rename an existing list group.
        A default callback is added to the returned
        Deferred which updates the contacts attribute
        of the factory.

        @param groupID: the ID of the desired group to rename.
        @param newName: the desired new name for the group.

        @return: A Deferred, the callback for which will be called
                 when the server clarifies the renaming.
                 The callback argument will be a tuple of 3 elements,
                 the new list version (int), the group id (int) and
                 the new group name (str).
        """
        
        raise "ProbablyDoesntWork"
        id, d = self._createIDMapping()
        self.sendLine("REG %s %s %s 0" % (id, groupID, quote(newName)))
        def _cb(r):
            self.factory.contacts.version = r[0]
            self.factory.contacts.setGroup(r[1], r[2])
            return r
        return d.addCallback(_cb)

    def addContact(self, listType, userHandle):
        """
        Used to add a contact to the desired list.
        A default callback is added to the returned
        Deferred which updates the contacts attribute of
        the factory with the new contact information.
        If you are adding a contact to the forward list
        and you want to associate this contact with multiple
        groups then you will need to call this method for each
        group you would like to add them to, changing the groupID
        parameter. The default callback will take care of updating
        the group information on the factory's contact list.

        @param listType: (as defined by the *_LIST constants)
        @param userHandle: the user handle (passport) of the contact
                           that is being added

        @return: A Deferred, the callback for which will be called when
                 the server has clarified that the user has been added.
                 The callback argument will be a tuple with 4 elements:
                 the list type, the contact's user handle, the new list
                 version, and the group id (if relevant, otherwise it
                 will be None)
        """
        
        id, d = self._createIDMapping()
        try: # Make sure the contact isn't actually on the list
            if self.factory.contacts.getContact(userHandle).lists & listType: return
        except AttributeError: pass
        listType = listIDToCode[listType].upper()
        if listType == "FL":
            self.sendLine("ADC %s %s N=%s F=%s" % (id, listType, userHandle, userHandle))
        else:
            self.sendLine("ADC %s %s N=%s" % (id, listType, userHandle))

        def _cb(r):
            if not self.factory: return
            c = self.factory.contacts.getContact(r[2])
            if not c:
                c = MSNContact(userGuid=r[1], userHandle=r[2], screenName=r[3])
                self.factory.contacts.addContact(c)
            #if r[3]: c.groups.append(r[3])
            c.addToList(r[0])
            return r
        return d.addCallback(_cb)

    def remContact(self, listType, userHandle):
        """
        Used to remove a contact from the desired list.
        A default callback is added to the returned deferred
        which updates the contacts attribute of the factory
        to reflect the new contact information.

        @param listType: (as defined by the *_LIST constants)
        @param userHandle: the user handle (passport) of the
                           contact being removed

        @return: A Deferred, the callback for which will be called when
                 the server has clarified that the user has been removed.
                 The callback argument will be a tuple of 3 elements:
                 the list type, the contact's user handle and the group ID
                 (if relevant, otherwise it will be None)
        """
        
        id, d = self._createIDMapping()
        try: # Make sure the contact is actually on this list
            if not (self.factory.contacts.getContact(userHandle).lists & listType): return
        except AttributeError: return
        listType = listIDToCode[listType].upper()
        if listType == "FL":
            try:
                c = self.factory.contacts.getContact(userHandle)
                userGuid = c.userGuid
            except AttributeError: return
            self.sendLine("REM %s FL %s" % (id, userGuid))
        else:
            self.sendLine("REM %s %s %s" % (id, listType, userHandle))

        def _cb(r):
            if listType == "FL":
                r = (r[0], userHandle, r[2]) # make sure we always get a userHandle
            l = self.factory.contacts
            c = l.getContact(r[1])
            if not c: return
            group = r[2]
            shouldRemove = 1
            if group: # they may not have been removed from the list
                c.groups.remove(group)
                if c.groups: shouldRemove = 0
            if shouldRemove:
                c.removeFromList(r[0])
                if c.lists == 0: l.remContact(c.userHandle)
            return r
        return d.addCallback(_cb)

    def changeScreenName(self, newName):
        """
        Used to change your current screen name.
        A default callback is added to the returned
        Deferred which updates the screenName attribute
        of the factory and also updates the contact list
        version.

        @param newName: the new screen name

        @return: A Deferred, the callback for which will be called
                 when the server acknowledges the change.
                 The callback argument will be an empty tuple.
        """

        id, d = self._createIDMapping()
        self.sendLine("PRP %s MFN %s" % (id, quote(newName)))
        def _cb(r):
            self.factory.screenName = newName
            return r
        return d.addCallback(_cb)

    def changePersonalMessage(self, personal):
        """
        Used to change your personal message.

        @param personal: the new screen name

        @return: A Deferred, the callback for which will be called
                 when the server acknowledges the change.
                 The callback argument will be a tuple of 1 element,
                 the personal message.
        """

        id, d = self._createIDMapping()
        data = ""
        if personal:
            data = "<Data><PSM>" + personal + "</PSM><CurrentMedia></CurrentMedia></Data>"
        self.sendLine("UUX %s %s" % (id, len(data)))
        self.transport.write(data)
        def _cb(r):
            self.factory.personal = personal
            return (personal,)
        return d.addCallback(_cb)

    def changeAvatar(self, imageDataFunc, push):
        """
        Used to change the avatar that other users see.

        @param imageDataFunc: a function to return the PNG image data to set as the avatar
        @param push     : whether to push the update to the server
                          (it will otherwise be sent with the next
                          changeStatus())

        @return: If push==True, a Deferred, the callback for which
                 will be called when the server acknowledges the change.
                 The callback argument will be the same as for changeStatus.
        """

        checkMsnobj = MSNObject()
        checkMsnobj.setData(self.factory.userHandle, imageDataFunc)
        if self.msnobj and self.msnobj.sha1d == checkMsnobj.sha1d:
            return # Avatar hasn't changed
        if imageDataFunc:
            # We need to keep the same MSNObject instance, as it is
            # passed on to SwitchboardClient objects
            self.msnobj.setData(self.factory.userHandle, imageDataFunc)
        else:
            self.msnobj.setNull()
        if push:
            return self.changeStatus(self.factory.status) # Push to server


    def requestSwitchboardServer(self):
        """
        Used to request a switchboard server to use for conversations.

        @return: A Deferred, the callback for which will be called when
                 the server responds with the switchboard information.
                 The callback argument will be a tuple with 3 elements:
                 the host of the switchboard server, the port and a key
                 used for logging in.
        """

        id, d = self._createIDMapping()
        self.sendLine("XFR %s SB" % id)
        return d

    def logOut(self):
        """
        Used to log out of the notification server.
        After running the method the server is expected
        to close the connection.
        """
        
        if self.pingCheckTask:
            self.pingCheckTask.stop()
            self.pingCheckTask = None
        self.factory.stopTrying()
        self.sendLine("OUT")
        self.transport.loseConnection()

class NotificationFactory(ReconnectingClientFactory):
    """
    Factory for the NotificationClient protocol.
    This is basically responsible for keeping
    the state of the client and thus should be used
    in a 1:1 situation with clients.

    @ivar contacts: An MSNContactList instance reflecting
                    the current contact list -- this is
                    generally kept up to date by the default
                    command handlers.
    @ivar userHandle: The client's userHandle, this is expected
                      to be set by the client and is used by the
                      protocol (for logging in etc).
    @ivar screenName: The client's current screen-name -- this is
                      generally kept up to date by the default
                      command handlers.
    @ivar password: The client's password -- this is (obviously)
                    expected to be set by the client.
    @ivar passportServer: This must point to an msn passport server
                          (the whole URL is required)
    @ivar status: The status of the client -- this is generally kept
                  up to date by the default command handlers
    @ivar maxRetries: The number of times the factory will reconnect
                      if the connection dies because of a network error.
    """

    contacts = None
    userHandle = ''
    screenName = ''
    password = ''
    passportServer = 'https://nexus.passport.com/rdr/pprdr.asp'
    status = 'NLN'
    protocol = NotificationClient
    maxRetries = 5


class SwitchboardClient(MSNEventBase):
    """
    This class provides support for clients connecting to a switchboard server.

    Switchboard servers are used for conversations with other people
    on the MSN network. This means that the number of conversations at
    any given time will be directly proportional to the number of
    connections to varioius switchboard servers.

    MSN makes no distinction between single and group conversations,
    so any number of users may be invited to join a specific conversation
    taking place on a switchboard server.

    @ivar key: authorization key, obtained when receiving
               invitation / requesting switchboard server.
    @ivar userHandle: your user handle (passport)
    @ivar sessionID: unique session ID, used if you are replying
                     to a switchboard invitation
    @ivar reply: set this to 1 in connectionMade or before to signifiy
                 that you are replying to a switchboard invitation.
    @ivar msnobj: the MSNObject for the user's avatar. So that the
                  switchboard can distribute it to anyone who asks.
    """

    key = 0
    userHandle = ""
    sessionID = ""
    reply = 0
    msnobj = None

    _iCookie = 0

    def __init__(self):
        MSNEventBase.__init__(self)
        self.pendingUsers = {}
        self.cookies = {'iCookies' : {}} # will maybe be moved to a factory in the future
        self.slpLinks = {}

    def connectionMade(self):
        MSNEventBase.connectionMade(self)
        self._sendInit()

    def connectionLost(self, reason):
        self.cookies['iCookies'] = {}
        MSNEventBase.connectionLost(self, reason)

    def _sendInit(self):
        """
        send initial data based on whether we are replying to an invitation
        or starting one.
        """
        id = self._nextTransactionID()
        if not self.reply:
            self.sendLine("USR %s %s %s" % (id, self.userHandle, self.key))
        else:
            self.sendLine("ANS %s %s %s %s" % (id, self.userHandle, self.key, self.sessionID))

    def _newInvitationCookie(self):
        self._iCookie += 1
        if self._iCookie > 1000: self._iCookie = 1
        return self._iCookie

    def _checkTyping(self, message, cTypes):
        """ helper method for checkMessage """
        if 'text/x-msmsgscontrol' in cTypes and message.hasHeader('TypingUser'):
            self.gotContactTyping(message)
            return 1

    def _checkFileInvitation(self, message, info):
        """ helper method for checkMessage """
        if not info.get('Application-GUID', '').upper() == MSN_MSNFTP_GUID: return 0
        try:
            cookie = info['Invitation-Cookie']
            filename = info['Application-File']
            filesize = int(info['Application-FileSize'])
            connectivity = (info.get('Connectivity', 'n').lower() == 'y')
        except KeyError:
            log.msg('Received munged file transfer request ... ignoring.')
            return 0
        raise NotImplementedError
        self.gotSendRequest(msnft.MSNFTP_Receive(filename, filesize, message.userHandle, cookie, connectivity, self))
        return 1

    def _handleP2PMessage(self, message):
        """ helper method for msnslp messages (file transfer & avatars) """
        if not message.getHeader("P2P-Dest") == self.userHandle: return
        packet = message.message
        binaryFields = BinaryFields(packet=packet)
        if binaryFields[5] == BinaryFields.BYEGOT:
            pass # Ignore the ACKs to SLP messages
        elif binaryFields[0] != 0:
            slpLink = self.slpLinks.get(binaryFields[0])
            if not slpLink:
                # Link has been killed. Ignore
                return
            if slpLink.remoteUser == message.userHandle:
                slpLink.handlePacket(packet)
        elif binaryFields[5] == BinaryFields.ACK:
            pass # Ignore the ACKs to SLP messages
        else:
            slpMessage = MSNSLPMessage(packet)
            slpLink = None
            # Always try and give a slpMessage to a slpLink first.
            # If none can be found, and it was INVITE, then create
            # one to handle the session.
            for slpLink in self.slpLinks.values():
                if slpLink.sessionGuid == slpMessage.sessionGuid:
                    slpLink.handleSLPMessage(slpMessage)
                    break
            else:
                slpLink = None # Was not handled

            if not slpLink and slpMessage.method == "INVITE":
                if slpMessage.euf_guid == MSN_MSNFTP_GUID:
                    context = FileContext(slpMessage.context)
                    slpLink = SLPLink_FileReceive(remoteUser=slpMessage.fro, switchboard=self, filename=context.filename, filesize=context.filesize, sessionID=slpMessage.sessionID, sessionGuid=slpMessage.sessionGuid, branch=slpMessage.branch)
                    self.slpLinks[slpMessage.sessionID] = slpLink
                    self.gotFileReceive(slpLink)
                elif slpMessage.euf_guid == MSN_AVATAR_GUID:
                    # Check that we have an avatar to send
                    if self.msnobj:
                        slpLink = SLPLink_AvatarSend(remoteUser=slpMessage.fro, switchboard=self, filesize=self.msnobj.size, sessionID=slpMessage.sessionID, sessionGuid=slpMessage.sessionGuid)
                        slpLink.write(self.msnobj.imageDataFunc())
                        slpLink.close()
                    else:
                        # They shouldn't have sent a request if we have
                        # no avatar. So we'll just ignore them.
                        # FIXME We should really send an error
                        pass
                if slpLink:
                    self.slpLinks[slpMessage.sessionID] = slpLink
            if slpLink:
                # Always need to ACK these packets if we can
                slpLink.sendP2PACK(binaryFields)


    def checkMessage(self, message):
        """
        hook for detecting any notification type messages
        (e.g. file transfer)
        """
        cTypes = [s.lstrip() for s in message.getHeader('Content-Type').split(';')]
        if self._checkTyping(message, cTypes): return 0
#        if 'text/x-msmsgsinvite' in cTypes:
            # header like info is sent as part of the message body.
#            info = {}
#            for line in message.message.split('\r\n'):
#                try:
#                    key, val = line.split(':')
#                    info[key] = val.lstrip()
#                except ValueError: continue
#            if self._checkFileInvitation(message, info): return 0
        elif 'application/x-msnmsgrp2p' in cTypes:
            self._handleP2PMessage(message)
            return 0
        return 1

    # negotiation
    def handle_USR(self, params):
        checkParamLen(len(params), 4, 'USR')
        if params[1] == "OK":
            self.loggedIn()

    # invite a user
    def handle_CAL(self, params):
        checkParamLen(len(params), 3, 'CAL')
        id = int(params[0])
        if params[1].upper() == "RINGING":
            self._fireCallback(id, int(params[2])) # session ID as parameter

    # user joined
    def handle_JOI(self, params):
        checkParamLen(len(params), 2, 'JOI')
        self.userJoined(params[0], unquote(params[1]))

    # users participating in the current chat
    def handle_IRO(self, params):
        checkParamLen(len(params), 5, 'IRO')
        self.pendingUsers[params[3]] = unquote(params[4])
        if params[1] == params[2]:
            self.gotChattingUsers(self.pendingUsers)
            self.pendingUsers = {}

    # finished listing users
    def handle_ANS(self, params):
        checkParamLen(len(params), 2, 'ANS')
        if params[1] == "OK":
            self.loggedIn()

    def handle_ACK(self, params):
        checkParamLen(len(params), 1, 'ACK')
        self._fireCallback(int(params[0]), None)

    def handle_NAK(self, params):
        checkParamLen(len(params), 1, 'NAK')
        self._fireCallback(int(params[0]), None)

    def handle_BYE(self, params):
        #checkParamLen(len(params), 1, 'BYE') # i've seen more than 1 param passed to this
        self.userLeft(params[0])

    # callbacks

    def loggedIn(self):
        """
        called when all login details have been negotiated.
        Messages can now be sent, or new users invited.
        """
        pass

    def gotChattingUsers(self, users):
        """
        called after connecting to an existing chat session.

        @param users: A dict mapping user handles to screen names
                      (current users taking part in the conversation)
        """
        pass

    def userJoined(self, userHandle, screenName):
        """
        called when a user has joined the conversation.

        @param userHandle: the user handle (passport) of the user
        @param screenName: the screen name of the user
        """
        pass

    def userLeft(self, userHandle):
        """
        called when a user has left the conversation.

        @param userHandle: the user handle (passport) of the user.
        """
        pass

    def gotMessage(self, message):
        """
        called when we receive a message.

        @param message: the associated MSNMessage object
        """
        pass

    def gotFileReceive(self, fileReceive):
        """
        called when we receive a file send request from a contact.
        Default action is to reject the file.

        @param fileReceive: msnft.MSNFTReceive_Base instance
        """
        fileReceive.reject()


    def gotSendRequest(self, fileReceive):
        """
        called when we receive a file send request from a contact

        @param fileReceive: msnft.MSNFTReceive_Base instance
        """
        pass

    def gotContactTyping(self, message):
        """
        called when we receive the special type of message notifying
        us that a contact is typing a message.

        @param message: the associated MSNMessage object
        """
        pass

    # api calls

    def inviteUser(self, userHandle):
        """
        used to invite a user to the current switchboard server.

        @param userHandle: the user handle (passport) of the desired user.

        @return: A Deferred, the callback for which will be called
                 when the server notifies us that the user has indeed
                 been invited.  The callback argument will be a tuple
                 with 1 element, the sessionID given to the invited user.
                 I'm not sure if this is useful or not.
        """

        id, d = self._createIDMapping()
        self.sendLine("CAL %s %s" % (id, userHandle))
        return d

    def sendMessage(self, message):
        """
        used to send a message.

        @param message: the corresponding MSNMessage object.

        @return: Depending on the value of message.ack.
                 If set to MSNMessage.MESSAGE_ACK or
                 MSNMessage.MESSAGE_NACK a Deferred will be returned,
                 the callback for which will be fired when an ACK or
                 NACK is received - the callback argument will be
                 (None,). If set to MSNMessage.MESSAGE_ACK_NONE then
                 the return value is None.
        """

        if message.ack not in ('A','N','D'): id, d = self._nextTransactionID(), None
        else: id, d = self._createIDMapping()
        if message.length == 0: message.length = message._calcMessageLen()
        self.sendLine("MSG %s %s %s" % (id, message.ack, message.length))
        # Apparently order matters with these
        orderMatters = ("MIME-Version", "Content-Type", "Message-ID")
        for header in orderMatters:
            if message.hasHeader(header):
                self.sendLine("%s: %s" % (header, message.getHeader(header)))
        # send the rest of the headers
        for header in [h for h in message.headers.items() if h[0] not in orderMatters]:
            self.sendLine("%s: %s" % (header[0], header[1]))
        self.transport.write("\r\n")
        self.transport.write(message.message)
        if MESSAGEDEBUG: log.msg(message.message)
        return d

    def sendAvatarRequest(self, msnContact):
        """
        used to request an avatar from a user in this switchboard
        session.

        @param msnContact: the msnContact object to request an avatar for

        @return: A Deferred, the callback for which will be called
                 when the avatar transfer succeeds.
                 The callback argument will be a tuple with one element,
                 the PNG avatar data.
        """
        if not msnContact.msnobj: return
        d = Deferred()
        def bufferClosed(data):
            d.callback((data,))
        buffer = StringBuffer(bufferClosed)
        buffer.error = lambda: None
        slpLink = SLPLink_AvatarReceive(remoteUser=msnContact.userHandle, switchboard=self, consumer=buffer, context=msnContact.msnobj.text)
        self.slpLinks[slpLink.sessionID] = slpLink
        return d

    def sendFile(self, msnContact, filename, filesize):
        """
        used to send a file to a contact.

        @param msnContact: the MSNContact object to send a file to.
        @param filename: the name of the file to send.
        @param filesize: the size of the file to send.
        
        @return: (fileSend, d) A FileSend object and a Deferred.
                 The Deferred will pass one argument in a tuple,
                 whether or not the transfer is accepted. If you
                 receive a True, then you can call write() on the
                 fileSend object to send your file. Call close()
                 when the file is done.
                 NOTE: You MUST write() exactly as much as you
                 declare in filesize.
        """
        if not msnContact.userHandle: return
        # FIXME, check msnContact.caps to see if we should use old-style
        fileSend = SLPLink_FileSend(remoteUser=msnContact.userHandle, switchboard=self, filename=filename, filesize=filesize)
        self.slpLinks[fileSend.sessionID] = fileSend
        return fileSend, fileSend.acceptDeferred

    def sendTypingNotification(self):
        """
        Used to send a typing notification. Upon receiving this
        message the official client will display a 'user is typing'
        message to all other users in the chat session for 10 seconds.
        You should send one of these every 5 seconds as long as the
        user is typing.
        """
        m = MSNMessage()
        m.ack = m.MESSAGE_ACK_NONE
        m.setHeader('Content-Type', 'text/x-msmsgscontrol')
        m.setHeader('TypingUser', self.userHandle)
        m.message = "\r\n"
        self.sendMessage(m)

    def sendFileInvitation(self, fileName, fileSize):
        """
        send an notification that we want to send a file.

        @param fileName: the file name
        @param fileSize: the file size

        @return: A Deferred, the callback of which will be fired
                 when the user responds to this invitation with an
                 appropriate message. The callback argument will be
                 a tuple with 3 elements, the first being 1 or 0
                 depending on whether they accepted the transfer
                 (1=yes, 0=no), the second being an invitation cookie
                 to identify your follow-up responses and the third being
                 the message 'info' which is a dict of information they
                 sent in their reply (this doesn't really need to be used).
                 If you wish to proceed with the transfer see the
                 sendTransferInfo method.
        """
        cookie = self._newInvitationCookie()
        d = Deferred()
        m = MSNMessage()
        m.setHeader('Content-Type', 'text/x-msmsgsinvite; charset=UTF-8')
        m.message += 'Application-Name: File Transfer\r\n'
        m.message += 'Application-GUID: %s\r\n' % MSN_MSNFTP_GUID
        m.message += 'Invitation-Command: INVITE\r\n'
        m.message += 'Invitation-Cookie: %s\r\n' % str(cookie)
        m.message += 'Application-File: %s\r\n' % fileName
        m.message += 'Application-FileSize: %s\r\n\r\n' % str(fileSize)
        m.ack = m.MESSAGE_ACK_NONE
        self.sendMessage(m)
        self.cookies['iCookies'][cookie] = (d, m)
        return d

    def sendTransferInfo(self, accept, iCookie, authCookie, ip, port):
        """
        send information relating to a file transfer session.

        @param accept: whether or not to go ahead with the transfer
                       (1=yes, 0=no)
        @param iCookie: the invitation cookie of previous replies
                        relating to this transfer
        @param authCookie: the authentication cookie obtained from
                           an FileSend instance
        @param ip: your ip
        @param port: the port on which an FileSend protocol is listening.
        """
        m = MSNMessage()
        m.setHeader('Content-Type', 'text/x-msmsgsinvite; charset=UTF-8')
        m.message += 'Invitation-Command: %s\r\n' % (accept and 'ACCEPT' or 'CANCEL')
        m.message += 'Invitation-Cookie: %s\r\n' % iCookie
        m.message += 'IP-Address: %s\r\n' % ip
        m.message += 'Port: %s\r\n' % port
        m.message += 'AuthCookie: %s\r\n' % authCookie
        m.message += '\r\n'
        m.ack = m.MESSAGE_NACK
        self.sendMessage(m)


class FileReceive:
    def __init__(self, filename, filesize, userHandle):
        self.consumer = None
        self.finished = False
        self.error = False
        self.buffer = []
        self.filename, self.filesize, self.userHandle = filename, filesize, userHandle

    def reject(self):
        raise NotImplementedError

    def accept(self, consumer):
        if self.consumer: raise "AlreadyAccepted"
        self.consumer = consumer
        for data in self.buffer:
            self.consumer.write(data)
        self.buffer = None
        if self.finished:
            self.consumer.close()
        if self.error:
            self.consumer.error()

    def write(self, data):
        if self.error or self.finished:
            raise IOError, "Attempt to write in an invalid state"
        if self.consumer:
            self.consumer.write(data)
        else:
            self.buffer.append(data)

    def close(self):
        self.finished = True
        if self.consumer:
            self.consumer.close()

class FileContext:
    """ Represents the Context field for P2P file transfers """
    def __init__(self, data=""):
        if data:
            self.parse(data)
        else:
            self.filename = ""
            self.filesize = 0

    def pack(self):
        if MSNP2PDEBUG: log.msg("FileContext packing:", self.filename, self.filesize)
        data = struct.pack("<LLQL", 638, 0x03, self.filesize, 0x01)
        data = data[:-1] # Uck, weird, but it works
        data += utf16net(self.filename)
        data = ljust(data, 570, '\0')
        data += struct.pack("<L", 0xFFFFFFFFL)
        data = ljust(data, 638, '\0')
        return data

    def parse(self, packet):
        self.filesize = struct.unpack("<Q", packet[8:16])[0]
        chunk = packet[19:540]
        chunk = chunk[:chunk.find('\x00\x00')]
        self.filename = unicode((codecs.BOM_UTF16_BE + chunk).decode("utf-16"))
        if MSNP2PDEBUG: log.msg("FileContext parsed:", self.filesize, self.filename)


class BinaryFields:
    """ Utility class for the binary header & footer in p2p messages """
    ACK = 0x02
    WAIT = 0x04
    ERR = 0x08
    DATA = 0x20
    BYEGOT = 0x40
    BYESENT = 0x80
    DATAFT = 0x1000030

    def __init__(self, fields=None, packet=None):
        if fields:
            self.fields = fields
        else:
            self.fields = [0] * 10
            if packet:
                self.unpackFields(packet)
    
    def __getitem__(self, key):
        return self.fields[key]
    
    def __setitem__(self, key, value):
        self.fields[key] = value
    
    def unpackFields(self, packet):
        self.fields = struct.unpack("<LLQQLLLLQ", packet[0:48])
        self.fields += struct.unpack(">L", packet[len(packet)-4:])
        if MSNP2PDEBUG:
            out = "Unpacked fields: "
            for i in self.fields:
                out += hex(i) + ' '
            log.msg(out)
    
    def packHeaders(self):
        f = tuple(self.fields)
        if MSNP2PDEBUG:
            out = "Packed fields: "
            for i in self.fields:
                out += hex(i) + ' '
            log.msg(out)
        return struct.pack("<LLQQLLLLQ", f[0], f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8])
    
    def packFooter(self):
        return struct.pack(">L", self.fields[9])
    

class MSNSLPMessage:
    """ Representation of a single MSNSLP message """
    def __init__(self, packet=None):
        self.method = ""
        self.status = ""
        self.to = ""
        self.fro = ""
        self.branch = ""
        self.cseq = 0
        self.sessionGuid = ""
        self.sessionID = None
        self.euf_guid = ""
        self.data = "\r\n" + chr(0)
        if packet:
            self.parse(packet)

    def create(self, method=None, status=None, to=None, fro=None, branch=None, cseq=0, sessionGuid=None, data=None):
        self.method = method
        self.status = status
        self.to = to
        self.fro = fro
        self.branch = branch
        self.cseq = cseq
        self.sessionGuid = sessionGuid
        if data: self.data = data
    
    def setData(self, ctype, data):
        self.ctype = ctype
        s = []
        order = ["EUF-GUID", "SessionID", "AppID", "Context", "Bridge", "Listening","Bridges", "NetID", "Conn-Type", "UPnPNat", "ICF", "Hashed-Nonce"]
        for key in order:
            if key == "Context" and data.has_key(key):
                s.append("Context: %s\r\n" % b64enc(data[key]))
            elif data.has_key(key):
                s.append("%s: %s\r\n" % (key, str(data[key])))
        s.append("\r\n"+chr(0))
        
        self.data = "".join(s)
    
    def parse(self, s):
        s = s[48:len(s)-4:]
        if s.find("MSNSLP/1.0") < 0: return

        lines = s.split("\r\n")
        
        # Get the MSNSLP method or status
        msnslp = lines[0].split(" ")
        if MSNP2PDEBUG: log.msg("Parsing MSNSLPMessage %s %s" % (len(s), s))
        if msnslp[0] in ("INVITE", "BYE"):
            self.method = msnslp[0].strip()
        else:
            self.status = msnslp[1].strip()

        lines.remove(lines[0])
        
        for line in lines:
            line = line.split(":")
            if len(line) < 1: continue
            try:
                if len(line) > 2 and line[0] == "To":
                    self.to = line[2][:line[2].find('>')]
                elif len(line) > 2 and line[0] == "From":
                    self.fro = line[2][:line[2].find('>')]
                elif line[0] == "Call-ID":
                    self.sessionGuid = line[1].strip()
                elif line[0] == "CSeq":
                    self.cseq = int(line[1].strip())
                elif line[0] == "SessionID":
                    self.sessionID = int(line[1].strip())
                elif line[0] == "EUF-GUID":
                    self.euf_guid = line[1].strip()
                elif line[0] == "Content-Type":
                    self.ctype = line[1].strip()
                elif line[0] == "Context":
                    self.context = b64dec(line[1])
                elif line[0] == "Via":
                    self.branch = line[1].split(";")[1].split("=")[1].strip()
            except:
                if MSNP2PDEBUG:
                    log.msg("Error parsing MSNSLP message.")
                    raise

    def __str__(self):
        s = []
        if self.method:
           s.append("%s MSNMSGR:%s MSNSLP/1.0\r\n" % (self.method, self.to))
        else:
            if   self.status == "200": status = "200 OK"
            elif self.status == "603": status = "603 Decline"
            s.append("MSNSLP/1.0 %s\r\n" % status)
        s.append("To: <msnmsgr:%s>\r\n" % self.to)
        s.append("From: <msnmsgr:%s>\r\n" % self.fro)
        s.append("Via: MSNSLP/1.0/TLP ;branch=%s\r\n" % self.branch)
        s.append("CSeq: %s \r\n" % str(self.cseq))
        s.append("Call-ID: %s\r\n" % self.sessionGuid)
        s.append("Max-Forwards: 0\r\n")
        s.append("Content-Type: %s\r\n" % self.ctype)
        s.append("Content-Length: %s\r\n\r\n" % len(self.data))
        s.append(self.data)
        return "".join(s)

class SeqID:
    """ Utility for handling the weird sequence IDs in p2p messages """
    def __init__(self, baseID=None):
        if baseID:
            self.baseID = baseID
        else:
            self.baseID = random.randint(1000, MSN_MAXINT)
        self.pos = -1

    def get(self):
        return p2pseq(self.pos) + self.baseID
    
    def next(self):
        self.pos += 1
        return self.get()
    

class StringBuffer(StringIO.StringIO):
    def __init__(self, notifyFunc=None):
        self.notifyFunc = notifyFunc
        StringIO.StringIO.__init__(self)

    def close(self):
        if self.notifyFunc:
            self.notifyFunc(self.getvalue())
            self.notifyFunc = None
        StringIO.StringIO.close(self)


class SLPLink:
    def __init__(self, remoteUser, switchboard, sessionID, sessionGuid):
        self.dataFlag = 0
        if not sessionID:
            sessionID = random.randint(1000, MSN_MAXINT)
        if not sessionGuid:
            sessionGuid = random_guid()
        self.remoteUser = remoteUser
        self.switchboard = switchboard
        self.sessionID = sessionID
        self.sessionGuid = sessionGuid
        self.seqID = SeqID()

    def killLink(self):
        if MSNP2PDEBUG: log.msg("killLink")
        def kill():
            if MSNP2PDEBUG: log.msg("killLink - kill()")
            if not self.switchboard: return
            del self.switchboard.slpLinks[self.sessionID]
            self.switchboard = None
        # This is so that handleP2PMessage can still use the SLPLink
        # one last time, for ACKing BYEs and 601s.
        reactor.callLater(0, kill)

    def warn(self, text):
        log.msg("Warning in transfer: %s %s" % (self, text))

    def sendP2PACK(self, ackHeaders):
        binaryFields = BinaryFields()
        binaryFields[0] = ackHeaders[0]
        binaryFields[1] = self.seqID.next()
        binaryFields[3] = ackHeaders[3]
        binaryFields[5] = BinaryFields.ACK
        binaryFields[6] = ackHeaders[1]
        binaryFields[7] = ackHeaders[6]
        binaryFields[8] = ackHeaders[3]
        self.sendP2PMessage(binaryFields, "")

    def sendSLPMessage(self, cmd, ctype, data, branch=None):
        msg = MSNSLPMessage()
        if cmd.isdigit():
            msg.create(status=cmd, to=self.remoteUser, fro=self.switchboard.userHandle, branch=branch, cseq=1, sessionGuid=self.sessionGuid)
        else:
            msg.create(method=cmd, to=self.remoteUser, fro=self.switchboard.userHandle, branch=random_guid(), cseq=0, sessionGuid=self.sessionGuid)
        msg.setData(ctype, data)
        msgStr = str(msg)
        binaryFields = BinaryFields()
        binaryFields[1] = self.seqID.next()
        binaryFields[3] = len(msgStr)
        binaryFields[4] = binaryFields[3]
        binaryFields[6] = random.randint(1000, MSN_MAXINT)
        self.sendP2PMessage(binaryFields, msgStr)

    def sendP2PMessage(self, binaryFields, msgStr):
        packet = binaryFields.packHeaders() + msgStr + binaryFields.packFooter()

        message = MSNMessage(message=packet)
        message.setHeader("Content-Type", "application/x-msnmsgrp2p")
        message.setHeader("P2P-Dest", self.remoteUser)
        message.ack = MSNMessage.MESSAGE_ACK_FAT
        self.switchboard.sendMessage(message)

    def handleSLPMessage(self, slpMessage):
        raise NotImplementedError



    

class SLPLink_Send(SLPLink):
    def __init__(self, remoteUser, switchboard, filesize, sessionID=None, sessionGuid=None):
        SLPLink.__init__(self, remoteUser, switchboard, sessionID, sessionGuid)
        self.handlePacket = None
        self.offset = 0
        self.filesize = filesize
        self.data = ""
    
    def send_dataprep(self):
        if MSNP2PDEBUG: log.msg("send_dataprep")
        binaryFields = BinaryFields()
        binaryFields[0] = self.sessionID
        binaryFields[1] = self.seqID.next()
        binaryFields[3] = 4
        binaryFields[4] = 4
        binaryFields[6] = random.randint(1000, MSN_MAXINT)
        binaryFields[9] = 1
        self.sendP2PMessage(binaryFields, chr(0) * 4)

    def write(self, data):
        if MSNP2PDEBUG: log.msg("write")
        i = 0
        data = self.data + data
        self.data = ""
        length = len(data)
        while i < length:
            if i + 1202 < length:
                self._writeChunk(data[i:i+1202])
                i += 1202
            else:
                self.data = data[i:]
                return

    def _writeChunk(self, chunk):
        if MSNP2PDEBUG: log.msg("writing chunk")
        binaryFields = BinaryFields()
        binaryFields[0] = self.sessionID
        if self.offset == 0:
            binaryFields[1] = self.seqID.next()
        else:
            binaryFields[1] = self.seqID.get()
        binaryFields[2] = self.offset
        binaryFields[3] = self.filesize
        binaryFields[4] = len(chunk)
        binaryFields[5] = self.dataFlag
        binaryFields[6] = random.randint(1000, MSN_MAXINT)
        binaryFields[9] = 1
        self.offset += len(chunk)
        self.sendP2PMessage(binaryFields, chunk)
    
    def close(self):
        if self.data:
            self._writeChunk(self.data)
        #self.killLink()
    
    def error(self):
        pass
        # FIXME, should send 601 or something

class SLPLink_FileSend(SLPLink_Send):
    def __init__(self, remoteUser, switchboard, filename, filesize):
        SLPLink_Send.__init__(self, remoteUser=remoteUser, switchboard=switchboard, filesize=filesize)
        self.dataFlag = BinaryFields.DATAFT
        # Send invite & wait for 200OK before sending dataprep
        context = FileContext()
        context.filename = filename
        context.filesize = filesize
        data = {"EUF-GUID" : MSN_MSNFTP_GUID,\
                "SessionID": self.sessionID,\
                "AppID"    : 2,\
                "Context"  : context.pack() }
        self.sendSLPMessage("INVITE", "application/x-msnmsgr-sessionreqbody", data)
        self.acceptDeferred = Deferred()

    def handleSLPMessage(self, slpMessage):
        if slpMessage.status == "200":
            if slpMessage.ctype == "application/x-msnmsgr-sessionreqbody":
                data = {"Bridges"     : "TRUDPv1 TCPv1",\
                        "NetID"       : "0",\
                        "Conn-Type"   : "Firewall",\
                        "UPnPNat"     : "false",\
                        "ICF"         : "true",}
                        #"Hashed-Nonce": random_guid()}
                self.sendSLPMessage("INVITE", "application/x-msnmsgr-transreqbody", data)
            elif slpMessage.ctype == "application/x-msnmsgr-transrespbody":
                self.acceptDeferred.callback((True,))
                self.handlePacket = self.wait_data_ack
        else:
            if slpMessage.status == "603":
                self.acceptDeferred.callback((False,))
            if MSNP2PDEBUG: log.msg("SLPLink is over due to decline, error or BYE")
            self.data = ""
            self.killLink()

    def wait_data_ack(self, packet):
        if MSNP2PDEBUG: log.msg("wait_data_ack")
        binaryFields = BinaryFields()
        binaryFields.unpackFields(packet)

        if binaryFields[5] != BinaryFields.ACK:
            self.warn("field5," + str(binaryFields[5]))
            return

        self.sendSLPMessage("BYE", "application/x-msnmsgr-sessionclosebody", {})
        self.handlePacket = None

    def close(self):
        self.handlePacket = self.wait_data_ack
        SLPLink_Send.close(self)


class SLPLink_AvatarSend(SLPLink_Send):
    def __init__(self, remoteUser, switchboard, filesize, sessionID=None, sessionGuid=None):
        SLPLink_Send.__init__(self, remoteUser=remoteUser, switchboard=switchboard, filesize=filesize, sessionID=sessionID, sessionGuid=sessionGuid)
        self.dataFlag = BinaryFields.DATA
        self.sendSLPMessage("200", "application/x-msnmsgr-sessionreqbody", {"SessionID":self.sessionID})
        self.send_dataprep()
        self.handlePacket = lambda packet: None

    def handleSLPMessage(self, slpMessage):
        if MSNP2PDEBUG: log.msg("BYE or error")
        self.killLink()

    def close(self):
        SLPLink_Send.close(self)
        # Keep the link open to wait for a BYE

class SLPLink_Receive(SLPLink):
    def __init__(self, remoteUser, switchboard, consumer, context=None, sessionID=None, sessionGuid=None):
        SLPLink.__init__(self, remoteUser, switchboard, sessionID, sessionGuid)
        self.handlePacket = None
        self.consumer = consumer
        self.pos = 0

    def wait_dataprep(self, packet):
        if MSNP2PDEBUG: log.msg("wait_dataprep")
        binaryFields = BinaryFields()
        binaryFields.unpackFields(packet)

        if binaryFields[3] != 4:
            self.warn("field3," + str(binaryFields[3]))
            return
        if binaryFields[4] != 4:
            self.warn("field4," + str(binaryFields[4]))
            return
        # Just ignore the footer
        #if binaryFields[9] != 1:
        #    self.warn("field9," + str(binaryFields[9]))
        #   return

        self.sendP2PACK(binaryFields)
        self.handlePacket = self.wait_data

    def wait_data(self, packet):
        if MSNP2PDEBUG: log.msg("wait_data")
        binaryFields = BinaryFields()
        binaryFields.unpackFields(packet)

        if binaryFields[5] != self.dataFlag:
            self.warn("field5," + str(binaryFields[5]))
            return
        # Just ignore the footer
        #if binaryFields[9] != 1:
        #    self.warn("field9," + str(binaryFields[9]))
        #   return
        offset = binaryFields[2]
        total = binaryFields[3]
        length = binaryFields[4]

        data = packet[48:-4]
        if offset != self.pos:
            self.warn("Received packet out of order")
            self.consumer.error()
            return
        if len(data) != length:
            self.warn("Received bad length of slp")
            self.consumer.error()
            return
        
        self.pos += length

        self.consumer.write(str(data))

        if self.pos == total:
            self.sendP2PACK(binaryFields)
            self.consumer.close()
            self.handlePacket = None
            self.doFinished()

    def doFinished(self):
        raise NotImplementedError


class SLPLink_FileReceive(SLPLink_Receive, FileReceive):
    def __init__(self, remoteUser, switchboard, filename, filesize, sessionID, sessionGuid, branch):
        SLPLink_Receive.__init__(self, remoteUser=remoteUser, switchboard=switchboard, consumer=self, sessionID=sessionID, sessionGuid=sessionGuid)
        self.dataFlag = BinaryFields.DATAFT
        self.initialBranch = branch
        FileReceive.__init__(self, filename, filesize, remoteUser)

    def reject(self):
        # Send a 603 decline
        if not self.switchboard: return
        self.sendSLPMessage("603", "application/x-msnmsgr-sessionreqbody", {"SessionID":self.sessionID}, branch=self.initialBranch)
        self.killLink()

    def accept(self, consumer):
        FileReceive.accept(self, consumer)
        if not self.switchboard: return
        self.sendSLPMessage("200", "application/x-msnmsgr-sessionreqbody", {"SessionID":self.sessionID}, branch=self.initialBranch)
        self.handlePacket = self.wait_data # Moved here because sometimes the second INVITE seems to be skipped

    def handleSLPMessage(self, slpMessage):
        if slpMessage.method == "INVITE": # The second invite
            data = {"Bridge"      : "TCPv1",\
                    "Listening"   : "false",\
                    "Hashed-Nonce": "{00000000-0000-0000-0000-000000000000}"}
            self.sendSLPMessage("200", "application/x-msnmsgr-transrespbody", data, branch=slpMessage.branch)
#            self.handlePacket = self.wait_data # Moved up
        else:
            if MSNP2PDEBUG: log.msg("It's either a BYE or an error")
            self.killLink()
            # FIXME, do some error handling if it was an error

    def doFinished(self):
        #self.sendSLPMessage("BYE", "application/x-msnmsgr-sessionclosebody", {})
        #self.killLink()
        # Wait for BYE? #FIXME
        pass

class SLPLink_AvatarReceive(SLPLink_Receive):
    def __init__(self, remoteUser, switchboard, consumer, context):
        SLPLink_Receive.__init__(self, remoteUser=remoteUser, switchboard=switchboard, consumer=consumer, context=context)
        self.dataFlag = BinaryFields.DATA
        data = {"EUF-GUID" : MSN_AVATAR_GUID,\
                "SessionID": self.sessionID,\
                "AppID"    : 1,\
                "Context"  : context}
        self.sendSLPMessage("INVITE", "application/x-msnmsgr-sessionreqbody", data)
        self.handlePacket = self.wait_dataprep

    def handleSLPMessage(self, slpMessage):
        if slpMessage.method == "INVITE": # The second invite
            data = {"Bridge"      : "TCPv1",\
                    "Listening"   : "false",\
                    "Hashed-Nonce": "{00000000-0000-0000-0000-000000000000}"}
            self.sendSLPMessage("200", "application/x-msnmsgr-transrespbody", data, branch=slpMessage.branch)
        elif slpMessage.status == "200":
            pass
            #self.handlePacket = self.wait_dataprep # Moved upwards
        else:
            if MSNP2PDEBUG: log.msg("SLPLink is over due to error or BYE")
            self.killLink()

    def doFinished(self):
        self.sendSLPMessage("BYE", "application/x-msnmsgr-sessionclosebody", {})

# mapping of error codes to error messages
errorCodes = {

    200 : "Syntax error",
    201 : "Invalid parameter",
    205 : "Invalid user",
    206 : "Domain name missing",
    207 : "Already logged in",
    208 : "Invalid username",
    209 : "Invalid screen name",
    210 : "User list full",
    215 : "User already there",
    216 : "User already on list",
    217 : "User not online",
    218 : "Already in mode",
    219 : "User is in the opposite list",
    223 : "Too many groups",
    224 : "Invalid group",
    225 : "User not in group",
    229 : "Group name too long",
    230 : "Cannot remove group 0",
    231 : "Invalid group",
    280 : "Switchboard failed",
    281 : "Transfer to switchboard failed",

    300 : "Required field missing",
    301 : "Too many FND responses",
    302 : "Not logged in",

    400 : "Message not allowed",
    402 : "Error accessing contact list",
    403 : "Error accessing contact list",

    500 : "Internal server error",
    501 : "Database server error",
    502 : "Command disabled",
    510 : "File operation failed",
    520 : "Memory allocation failed",
    540 : "Wrong CHL value sent to server",

    600 : "Server is busy",
    601 : "Server is unavaliable",
    602 : "Peer nameserver is down",
    603 : "Database connection failed",
    604 : "Server is going down",
    605 : "Server unavailable",

    707 : "Could not create connection",
    710 : "Invalid CVR parameters",
    711 : "Write is blocking",
    712 : "Session is overloaded",
    713 : "Too many active users",
    714 : "Too many sessions",
    715 : "Not expected",
    717 : "Bad friend file",
    731 : "Not expected",

    800 : "Requests too rapid",

    910 : "Server too busy",
    911 : "Authentication failed",
    912 : "Server too busy",
    913 : "Not allowed when offline",
    914 : "Server too busy",
    915 : "Server too busy",
    916 : "Server too busy",
    917 : "Server too busy",
    918 : "Server too busy",
    919 : "Server too busy",
    920 : "Not accepting new users",
    921 : "Server too busy",
    922 : "Server too busy",
    923 : "No parent consent",
    924 : "Passport account not yet verified"

}

# mapping of status codes to readable status format
statusCodes = {

    STATUS_ONLINE  : "Online",
    STATUS_OFFLINE : "Offline",
    STATUS_HIDDEN  : "Appear Offline",
    STATUS_IDLE    : "Idle",
    STATUS_AWAY    : "Away",
    STATUS_BUSY    : "Busy",
    STATUS_BRB     : "Be Right Back",
    STATUS_PHONE   : "On the Phone",
    STATUS_LUNCH   : "Out to Lunch"

}

# mapping of list ids to list codes
listIDToCode = {

    FORWARD_LIST : 'fl',
    BLOCK_LIST   : 'bl',
    ALLOW_LIST   : 'al',
    REVERSE_LIST : 'rl',
    PENDING_LIST : 'pl'

}

# mapping of list codes to list ids
listCodeToID = {}
for id,code in listIDToCode.items():
    listCodeToID[code] = id

del id, code
