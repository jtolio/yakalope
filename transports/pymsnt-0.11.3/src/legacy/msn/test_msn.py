# Copyright (c) 2001-2005 Twisted Matrix Laboratories.
# Copyright (c) 2005-2006 James Bunton <james@delx.cjb.net> 
# Licensed for distribution under the GPL version 2, check COPYING for details


"""
Test cases for msn.
"""

# Settings
LOGGING = False




# Twisted imports
from twisted.protocols import loopback
from twisted.protocols.basic import LineReceiver
from twisted.internet.defer import Deferred
from twisted.internet import reactor, main
from twisted.python import failure, log
from twisted.trial import unittest

# System imports
import StringIO, sys, urllib, random, struct

import msn

if LOGGING:
    log.startLogging(sys.stdout)


def printError(f):
    print f

class StringIOWithoutClosing(StringIO.StringIO):
    disconnecting = 0
    def close(self): pass
    def loseConnection(self): pass

class LoopbackCon:
    def __init__(self, con1, con2):
        self.con1 = con1
        self.con2 = con2
        self.reconnect()

    def reconnect(self):
        self.con1ToCon2 = loopback.LoopbackRelay(self.con1)
        self.con2ToCon1 = loopback.LoopbackRelay(self.con2)
        self.con2.makeConnection(self.con1ToCon2)
        self.con1.makeConnection(self.con2ToCon1)
        self.connected = True

    def doSteps(self, steps=1):
        """ Returns true if the connection finished """
        count = 0
        while count < steps:
            reactor.iterate(0.01)
            self.con1ToCon2.clearBuffer()
            self.con2ToCon1.clearBuffer()
            if self.con1ToCon2.shouldLose:
                self.con1ToCon2.clearBuffer()
                count = -1
                break
            elif self.con2ToCon1.shouldLose:
                count = -1
                break
            else:
                count += 1
        if count == -1:
            self.disconnect()
            return True
        return False

    def disconnect(self):
        if self.connected:
            self.con1.connectionLost(failure.Failure(main.CONNECTION_DONE))
            self.con2.connectionLost(failure.Failure(main.CONNECTION_DONE))
            reactor.iterate()




##################
# Passport tests #
##################

class PassportTests(unittest.TestCase):

    def setUp(self):
        self.result = []
        self.deferred = Deferred()
        self.deferred.addCallback(lambda r: self.result.append(r))
        self.deferred.addErrback(printError)

    def testNexus(self):
        protocol = msn.PassportNexus(self.deferred, 'https://foobar.com/somepage.quux')
        headers = {
            'Content-Length' : '0',
            'Content-Type'   : 'text/html',
            'PassportURLs'   : 'DARealm=Passport.Net,DALogin=login.myserver.com/,DAReg=reg.myserver.com'
        }
        transport = StringIOWithoutClosing()
        protocol.makeConnection(transport)
        protocol.dataReceived('HTTP/1.0 200 OK\r\n')
        for (h,v) in headers.items(): protocol.dataReceived('%s: %s\r\n' % (h,v))
        protocol.dataReceived('\r\n')
        self.failUnless(self.result[0] == "https://login.myserver.com/")

    def _doLoginTest(self, response, headers):
        protocol = msn.PassportLogin(self.deferred,'foo@foo.com','testpass','https://foo.com/', 'a')
        protocol.makeConnection(StringIOWithoutClosing())
        protocol.dataReceived(response)
        for (h,v) in headers.items(): protocol.dataReceived('%s: %s\r\n' % (h,v))
        protocol.dataReceived('\r\n')

    def testPassportLoginSuccess(self):
        headers = {
            'Content-Length'      : '0',
            'Content-Type'        : 'text/html',
            'Authentication-Info' : "Passport1.4 da-status=success,tname=MSPAuth," +
                                    "tname=MSPProf,tname=MSPSec,from-PP='somekey'," +
                                    "ru=http://messenger.msn.com"
        }
        self._doLoginTest('HTTP/1.1 200 OK\r\n', headers)
        self.failUnless(self.result[0] == (msn.LOGIN_SUCCESS, 'somekey'))

    def testPassportLoginFailure(self):
        headers = {
            'Content-Type'     : 'text/html',
            'WWW-Authenticate' : 'Passport1.4 da-status=failed,' +
                                 'srealm=Passport.NET,ts=-3,prompt,cburl=http://host.com,' +
                                 'cbtxt=the%20error%20message'
        }
        self._doLoginTest('HTTP/1.1 401 Unauthorized\r\n', headers)
        self.failUnless(self.result[0] == (msn.LOGIN_FAILURE, 'the error message'))

    def testPassportLoginRedirect(self):
        headers = {
            'Content-Type'        : 'text/html',
            'Authentication-Info' : 'Passport1.4 da-status=redir',
            'Location'            : 'https://newlogin.host.com/'
        }
        self._doLoginTest('HTTP/1.1 302 Found\r\n', headers)
        self.failUnless(self.result[0] == (msn.LOGIN_REDIRECT, 'https://newlogin.host.com/', 'a'))



######################
# Notification tests #
######################

class DummyNotificationClient(msn.NotificationClient):
    def loggedIn(self, userHandle, verified):
        if userHandle == 'foo@bar.com' and verified:
            self.state = 'LOGIN'

    def gotProfile(self, message):
        self.state = 'PROFILE'

    def gotContactStatus(self, userHandle, code, screenName):
        if code == msn.STATUS_AWAY and userHandle == "foo@bar.com" and screenName == "Test Screen Name":
            c = self.factory.contacts.getContact(userHandle)
            if c.caps & msn.MSNContact.MSNC1 and c.msnobj:
                self.state = 'INITSTATUS'

    def contactStatusChanged(self, userHandle, code, screenName):
        if code == msn.STATUS_LUNCH and userHandle == "foo@bar.com" and screenName == "Test Name":
            self.state = 'NEWSTATUS'

    def contactAvatarChanged(self, userHandle, hash):
        if userHandle == "foo@bar.com" and hash == "b6b0bc4a5171dac590c593080405921275dcf284":
            self.state = 'NEWAVATAR'
        elif self.state == 'NEWAVATAR' and hash == "":
            self.state = 'AVATARGONE'
    
    def contactPersonalChanged(self, userHandle, personal):
        if userHandle == 'foo@bar.com' and personal == 'My Personal Message':
            self.state = 'GOTPERSONAL'
        elif userHandle == 'foo@bar.com' and personal == '':
            self.state = 'PERSONALGONE'

    def contactOffline(self, userHandle):
        if userHandle == "foo@bar.com": self.state = 'OFFLINE'

    def statusChanged(self, code):
        if code == msn.STATUS_HIDDEN: self.state = 'MYSTATUS'

    def listSynchronized(self, *args):
        self.state = 'GOTLIST'

    def gotPhoneNumber(self, userHandle, phoneType, number):
        self.state = 'GOTPHONE'

    def userRemovedMe(self, userHandle):
        c = self.factory.contacts.getContact(userHandle)
        if not c: self.state = 'USERREMOVEDME'

    def userAddedMe(self, userGuid, userHandle, screenName):
        c = self.factory.contacts.getContact(userHandle)
        if c and (c.lists | msn.PENDING_LIST) and (screenName == 'Screen Name'):
            self.state = 'USERADDEDME'

    def gotSwitchboardInvitation(self, sessionID, host, port, key, userHandle, screenName):
        if sessionID == 1234 and \
           host == '192.168.1.1' and \
           port == 1863 and \
           key == '123.456' and \
           userHandle == 'foo@foo.com' and \
           screenName == 'Screen Name':
            self.state = 'SBINVITED'

    def gotMSNAlert(self, body, action, subscr):
        self.state = 'NOTIFICATION'

    def gotInitialEmailNotification(self, inboxunread, foldersunread):
        if inboxunread == 1 and foldersunread == 0:
            self.state = 'INITEMAIL1'
        else:
            self.state = 'INITEMAIL2'

    def gotRealtimeEmailNotification(self, mailfrom, fromaddr, subject):
        if mailfrom == 'Some Person' and fromaddr == 'example@passport.com' and subject == 'newsubject':
            self.state = 'REALTIMEEMAIL'

class NotificationTests(unittest.TestCase):
    """ testing the various events in NotificationClient """

    def setUp(self):
        self.client = DummyNotificationClient()
        self.client.factory = msn.NotificationFactory()
        msn.MSNEventBase.connectionMade(self.client)
        self.client.state = 'START'

    def tearDown(self):
        self.client = None

    def testLogin(self):
        self.client.lineReceived('USR 1 OK foo@bar.com 1')
        self.failUnless((self.client.state == 'LOGIN'), 'Failed to detect successful login')

    def testProfile(self):
        m = 'MSG Hotmail Hotmail 353\r\nMIME-Version: 1.0\r\nContent-Type: text/x-msmsgsprofile; charset=UTF-8\r\n'
        m += 'LoginTime: 1016941010\r\nEmailEnabled: 1\r\nMemberIdHigh: 40000\r\nMemberIdLow: -600000000\r\nlang_preference: 1033\r\n'
        m += 'preferredEmail: foo@bar.com\r\ncountry: AU\r\nPostalCode: 90210\r\nGender: M\r\nKid: 0\r\nAge:\r\nsid: 400\r\n'
        m += 'kv: 2\r\nMSPAuth: 2CACCBCCADMoV8ORoz64BVwmjtksIg!kmR!Rj5tBBqEaW9hc4YnPHSOQ$$\r\n\r\n'
        self.client.dataReceived(m)
        self.failUnless((self.client.state == 'PROFILE'), 'Failed to detect initial profile')

    def testInitialEmailNotification(self):
        m =  'MIME-Version: 1.0\r\nContent-Type: text/x-msmsgsinitialemailnotification; charset=UTF-8\r\n'
        m += '\r\nInbox-Unread: 1\r\nFolders-Unread: 0\r\nInbox-URL: /cgi-bin/HoTMaiL\r\n'
        m += 'Folders-URL: /cgi-bin/folders\r\nPost-URL: http://www.hotmail.com\r\n\r\n'
        m =  'MSG Hotmail Hotmail %s\r\n' % (str(len(m))) + m
        self.client.dataReceived(m)
        self.failUnless((self.client.state == 'INITEMAIL1'), 'Failed to detect initial email notification')

    def testNoInitialEmailNotification(self):
        m =  'MIME-Version: 1.0\r\nContent-Type: text/x-msmsgsinitialemailnotification; charset=UTF-8\r\n'
        m += '\r\nInbox-Unread: 0\r\nFolders-Unread: 0\r\nInbox-URL: /cgi-bin/HoTMaiL\r\n'
        m += 'Folders-URL: /cgi-bin/folders\r\nPost-URL: http://www.hotmail.com\r\n\r\n'
        m =  'MSG Hotmail Hotmail %s\r\n' % (str(len(m))) + m
        self.client.dataReceived(m)
        self.failUnless((self.client.state != 'INITEMAIL2'), 'Detected initial email notification when I should not have')

    def testRealtimeEmailNotification(self):
        m =  'MSG Hotmail Hotmail 356\r\nMIME-Version: 1.0\r\nContent-Type: text/x-msmsgsemailnotification; charset=UTF-8\r\n'
        m += '\r\nFrom: Some Person\r\nMessage-URL: /cgi-bin/getmsg?msg=MSG1050451140.21&start=2310&len=2059&curmbox=ACTIVE\r\n'
        m += 'Post-URL: https://loginnet.passport.com/ppsecure/md5auth.srf?lc=1038\r\n'
        m += 'Subject: =?"us-ascii"?Q?newsubject?=\r\nDest-Folder: ACTIVE\r\nFrom-Addr: example@passport.com\r\nid: 2\r\n'
        self.client.dataReceived(m)
        self.failUnless((self.client.state == 'REALTIMEEMAIL'), 'Failed to detect realtime email notification')

    def testMSNAlert(self):
        m  = '<NOTIFICATION ver="2" id="1342902633" siteid="199999999" siteurl="http://alerts.msn.com">\r\n'
        m += '<TO pid="0x0006BFFD:0x8582C0FB" name="example@passport.com"/>\r\n'
        m += '<MSG pri="1" id="1342902633">\r\n'
        m += '<SUBSCR url="http://g.msn.com/3ALMSNTRACKING/199999999ToastChange?http://alerts.msn.com/Alerts/MyAlerts.aspx?strela=1"/>\r\n'
        m += '<ACTION url="http://g.msn.com/3ALMSNTRACKING/199999999ToastAction?http://alerts.msn.com/Alerts/MyAlerts.aspx?strela=1"/>\r\n'
        m += '<BODY lang="3076" icon="">\r\n'
        m += '<TEXT>utf8-encoded text</TEXT></BODY></MSG>\r\n'
        m += '</NOTIFICATION>\r\n'
        cmd = 'NOT %s\r\n' % str(len(m))
        m = cmd + m
        # Whee, lots of fun to test that lineReceived & dataReceived work well with input coming
        # in in (fairly) arbitrary chunks.
        map(self.client.dataReceived, [x+'\r\n' for x in m.split('\r\n')[:-1]])
        self.failUnless((self.client.state == 'NOTIFICATION'), 'Failed to detect MSN Alert message')

    def testListSync(self):
        self.client.makeConnection(StringIOWithoutClosing())
        msn.NotificationClient.loggedIn(self.client, 'foo@foo.com', 1)
        lines = [
            "SYN %s 2005-04-23T18:57:44.8130000-07:00 2005-04-23T18:57:54.2070000-07:00 1 3" % self.client.currentID,
            "GTC A",
            "BLP AL",
            "LSG Friends yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy",
            "LSG Other%20Friends yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyz",
            "LSG More%20Other%20Friends yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyya",
            "LST N=userHandle@email.com F=Some%20Name C=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx 13 yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy,yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyz",
        ]
        map(self.client.lineReceived, lines)
        contacts = self.client.factory.contacts
        contact = contacts.getContact('userHandle@email.com')
        #self.failUnless(contacts.version == 100, "Invalid contact list version")
        self.failUnless(contact.screenName == 'Some Name', "Invalid screen-name for user")
        self.failUnless(contacts.groups == {'yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy': 'Friends', \
                                            'yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyz': 'Other Friends', \
                                            'yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyya': 'More Other Friends'} \
                                            , "Did not get proper group list")
        self.failUnless(contact.groups == ['yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy', \
                                           'yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyz'] and \
                                           contact.lists == 13, "Invalid contact list/group info")
        self.failUnless(self.client.state == 'GOTLIST', "Failed to call list sync handler")
        self.client.logOut()

    def testStatus(self):
        # Set up the contact list
        self.client.makeConnection(StringIOWithoutClosing())
        msn.NotificationClient.loggedIn(self.client, 'foo@foo.com', 1)
        lines = [
            "SYN %s 2005-04-23T18:57:44.8130000-07:00 2005-04-23T18:57:54.2070000-07:00 1 0" % self.client.currentID,
            "GTC A",
            "BLP AL",
            "LST N=foo@bar.com F=Some%20Name C=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx 13 yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy,yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyz",
        ]
        map(self.client.lineReceived, lines)
        # Now test!
        msnobj = urllib.quote('<msnobj Creator="buddy1@hotmail.com" Size="24539" Type="3" Location="TFR2C.tmp" Friendly="AAA=" SHA1D="trC8SlFx2sWQxZMIBAWSEnXc8oQ=" SHA1C="U32o6bosZzluJq82eAtMpx5dIEI="/>')
        t = [('ILN 1 AWY foo@bar.com Test%20Screen%20Name 268435456 ' + msnobj, 'INITSTATUS', 'Failed to detect initial status report'),
             ('NLN LUN foo@bar.com Test%20Name 0', 'NEWSTATUS', 'Failed to detect contact status change'),
             ('NLN AWY foo@bar.com Test%20Name 0 ' + msnobj, 'NEWAVATAR', 'Failed to detect contact avatar change'),
             ('NLN AWY foo@bar.com Test%20Name 0', 'AVATARGONE', 'Failed to detect contact avatar disappearing'),
             ('FLN foo@bar.com', 'OFFLINE', 'Failed to detect contact signing off'),
             ('CHG 1 HDN 0 ' + msnobj, 'MYSTATUS', 'Failed to detect my status changing')]
        for i in t:
            self.client.lineReceived(i[0])
            self.failUnless((self.client.state == i[1]), i[2])

        # Test UBX
        self.client.dataReceived('UBX foo@bar.com 72\r\n<Data><PSM>My Personal Message</PSM><CurrentMedia></CurrentMedia></Data>')
        self.failUnless((self.client.state == 'GOTPERSONAL'), 'Failed to detect new personal message')
        self.client.dataReceived('UBX foo@bar.com 0\r\n')
        self.failUnless((self.client.state == 'PERSONALGONE'), 'Failed to detect personal message disappearing')
        self.client.logOut()

    def testAsyncPhoneChange(self):
        c = msn.MSNContact(userHandle='userHandle@email.com')
        self.client.factory.contacts = msn.MSNContactList()
        self.client.factory.contacts.addContact(c)
        self.client.makeConnection(StringIOWithoutClosing())
        self.client.lineReceived("BPR 101 userHandle@email.com PHH 123%20456")
        c = self.client.factory.contacts.getContact('userHandle@email.com')
        self.failUnless(self.client.state == 'GOTPHONE', "Did not fire phone change callback")
        self.failUnless(c.homePhone == '123 456', "Did not update the contact's phone number")
        self.failUnless(self.client.factory.contacts.version == 101, "Did not update list version")

    def testLateBPR(self):
        """
        This test makes sure that if a BPR response that was meant
        to be part of a SYN response (but came after the last LST)
        is received, the correct contact is updated and all is well
        """
        self.client.makeConnection(StringIOWithoutClosing())
        msn.NotificationClient.loggedIn(self.client, 'foo@foo.com', 1)
        lines = [
            "SYN %s 2005-04-23T18:57:44.8130000-07:00 2005-04-23T18:57:54.2070000-07:00 1 0" % self.client.currentID,
            "GTC A",
            "BLP AL",
            "LSG Friends yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy",
            "LST N=userHandle@email.com F=Some%20Name C=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx 13 yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy",
            "BPR PHH 123%20456"
        ]
        map(self.client.lineReceived, lines)
        contact = self.client.factory.contacts.getContact('userHandle@email.com')
        self.failUnless(contact.homePhone == '123 456', "Did not update contact's phone number")
        self.client.logOut()

    def testUserRemovedMe(self):
        self.client.factory.contacts = msn.MSNContactList()
        contact = msn.MSNContact(userHandle='foo@foo.com')
        contact.addToList(msn.REVERSE_LIST)
        self.client.factory.contacts.addContact(contact)
        self.client.lineReceived("REM 0 RL foo@foo.com")
        self.failUnless(self.client.state == 'USERREMOVEDME', "Failed to remove user from reverse list")

    def testUserAddedMe(self):
        self.client.factory.contacts = msn.MSNContactList()
        self.client.lineReceived("ADC 0 RL N=foo@foo.com F=Screen%20Name")
        self.failUnless(self.client.state == 'USERADDEDME', "Failed to add user to reverse lise")

    def testAsyncSwitchboardInvitation(self):
        self.client.lineReceived("RNG 1234 192.168.1.1:1863 CKI 123.456 foo@foo.com Screen%20Name")
        self.failUnless((self.client.state == 'SBINVITED'), 'Failed to detect switchboard invitation')


#######################################
# Notification with fake server tests #
#######################################

class FakeNotificationServer(msn.MSNEventBase):
    def handle_CHG(self, params):
        if len(params) < 4:
            params.append('')
        self.sendLine("CHG %s %s %s %s" % (params[0], params[1], params[2], params[3]))

    def handle_BLP(self, params):
        self.sendLine("BLP %s %s 100" % (params[0], params[1]))

    def handle_ADC(self, params):
        trid = params[0]
        list = msn.listCodeToID[params[1].lower()]
        if list == msn.FORWARD_LIST:
            userHandle = ""
            screenName = ""
            userGuid = ""
            groups = ""
            for p in params[2:]:
                if   p[0] == 'N':
                    userHandle = p[2:]
                elif p[0] == 'F':
                    screenName = p[2:]
                elif p[0] == 'C':
                    userGuid = p[2:]
                else:
                    groups = p
            if userHandle and userGuid:
                self.transport.loseConnection()
                return
            if userHandle:
                if not screenName:
                    self.transport.loseConnection()
                else:
                    self.sendLine("ADC %s FL N=%s F=%s C=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx %s" % (trid, userHandle, screenName, groups))
                return
            if userGuid:
                raise "NotImplementedError"
        else:
            if len(params) != 3:
                self.transport.loseConnection()
            if not params[2].startswith("N=") and params[2].count('@') == 1:
                self.transport.loseConnection()
            self.sendLine("ADC %s %s %s" % (params[0], params[1], params[2]))

    def handle_REM(self, params):
        if len(params) != 3:
            self.transport.loseConnection()
            return
        try:
            trid = int(params[0])
            listType = msn.listCodeToID[params[1].lower()]
        except:
            self.transport.loseConnection()
        if listType == msn.FORWARD_LIST and params[2].count('@') > 0:
            self.transport.loseConnection()
        elif listType != msn.FORWARD_LIST and params[2].count('@') != 1:
            self.transport.loseConnection()
        else:
            self.sendLine("REM %s %s %s" % (params[0], params[1], params[2]))

    def handle_PRP(self, params):
        if len(params) != 3:
            self.transport.loseConnection()
        if params[1] == "MFN":
            self.sendLine("PRP %s MFN %s" % (params[0], params[2]))
        else:
            # Only friendly names are implemented
            self.transport.loseConnection()

    def handle_UUX(self, params):
        if len(params) != 2:
            self.transport.loseConnection()
            return
        l = int(params[1])
        if l > 0:
            self.currentMessage = msn.MSNMessage(length=l, userHandle=params[0], screenName="UUX", specialMessage=True)
            self.setRawMode()
        else:
            self.sendLine("UUX %s 0" % params[0])

    def checkMessage(self, message):
        if message.specialMessage:
            if message.screenName == "UUX":
                self.sendLine("UUX %s 0" % message.userHandle)
                return 0
        return 1

    def handle_XFR(self, params):
        if len(params) != 2:
            self.transport.loseConnection()
            return
        if params[1] != "SB":
            self.transport.loseConnection()
            return
        self.sendLine("XFR %s SB 129.129.129.129:1234 CKI SomeSecret" % params[0])
        


class FakeNotificationClient(msn.NotificationClient):
    def doStatusChange(self):
        def testcb((status,)):
            if status == msn.STATUS_AWAY:
                self.test = 'PASS'
            self.transport.loseConnection()
        d = self.changeStatus(msn.STATUS_AWAY)
        d.addCallback(testcb)

    def doPrivacyMode(self):
        def testcb((priv,)):
            if priv.upper() == 'AL':
                self.test = 'PASS'
            self.transport.loseConnection()
        d = self.setPrivacyMode(True)
        d.addCallback(testcb)

    def doAddContactFL(self):
        def testcb((listType, userGuid, userHandle, screenName)):
            if listType & msn.FORWARD_LIST and \
               userGuid == "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" and \
               userHandle == "foo@bar.com" and \
               screenName == "foo@bar.com" and \
               self.factory.contacts.getContact(userHandle):
                self.test = 'PASS'
            self.transport.loseConnection()
        d = self.addContact(msn.FORWARD_LIST, "foo@bar.com")
        d.addCallback(testcb)

    def doAddContactAL(self):
        def testcb((listType, userGuid, userHandle, screenName)):
            if listType & msn.ALLOW_LIST and \
               userHandle == "foo@bar.com" and \
               not userGuid and not screenName and \
               self.factory.contacts.getContact(userHandle):
                self.test = 'PASS'
            self.transport.loseConnection()
        d = self.addContact(msn.ALLOW_LIST, "foo@bar.com")
        d.addCallback(testcb)

    def doRemContactFL(self):
        def testcb((listType, userHandle, groupID)):
            if listType & msn.FORWARD_LIST and \
               userHandle == "foo@bar.com":
                self.test = 'PASS'
            self.transport.loseConnection()
        d = self.remContact(msn.FORWARD_LIST, "foo@bar.com")
        d.addCallback(testcb)

    def doRemContactAL(self):
        def testcb((listType, userHandle, groupID)):
            if listType & msn.ALLOW_LIST and \
               userHandle == "foo@bar.com":
                self.test = 'PASS'
            self.transport.loseConnection()
        d = self.remContact(msn.ALLOW_LIST, "foo@bar.com")
        d.addCallback(testcb)

    def doScreenNameChange(self):
        def testcb(*args):
            self.test = 'PASS'
            self.transport.loseConnection()
        d = self.changeScreenName("Some new name")
        d.addCallback(testcb)

    def doPersonalChange(self, personal):
        def testcb((checkPersonal,)):
            if checkPersonal == personal:
                self.test = 'PASS'
            self.transport.loseConnection()
        d = self.changePersonalMessage(personal)
        d.addCallback(testcb)

    def doAvatarChange(self, dataFunc):
        def testcb(ignored):
            self.test = 'PASS'
            self.transport.loseConnection()
        d = self.changeAvatar(dataFunc, True)
        d.addCallback(testcb)

    def doRequestSwitchboard(self):
        def testcb((host, port, key)):
            if host == "129.129.129.129" and port == 1234 and key == "SomeSecret":
                self.test = 'PASS'
            self.transport.loseConnection()
        d = self.requestSwitchboardServer()
        d.addCallback(testcb)

class FakeServerNotificationTests(unittest.TestCase):
    """ tests the NotificationClient against a fake server. """

    def setUp(self):
        self.client = FakeNotificationClient()
        self.client.factory = msn.NotificationFactory()
        self.client.test = 'FAIL'
        self.server = FakeNotificationServer()
        self.loop = LoopbackCon(self.client, self.server)

    def tearDown(self):
        self.loop.disconnect()

    def testChangeStatus(self):
        self.client.doStatusChange()
        self.failUnless(self.loop.doSteps(10), 'Failed to disconnect')
        self.failUnless((self.client.test == 'PASS'), 'Failed to change status properly')

    def testSetPrivacyMode(self):
        self.client.factory.contacts = msn.MSNContactList()
        self.client.doPrivacyMode()
        self.failUnless(self.loop.doSteps(10), 'Failed to disconnect')
        self.failUnless((self.client.test == 'PASS'), 'Failed to change privacy mode')

    def testAddContactFL(self):
        self.client.factory.contacts = msn.MSNContactList()
        self.client.doAddContactFL()
        self.failUnless(self.loop.doSteps(10), 'Failed to disconnect')
        self.failUnless((self.client.test == 'PASS'), 'Failed to add contact to forward list')

    def testAddContactAL(self):
        self.client.factory.contacts = msn.MSNContactList()
        self.client.doAddContactAL()
        self.failUnless(self.loop.doSteps(10), 'Failed to disconnect')
        self.failUnless((self.client.test == 'PASS'), 'Failed to add contact to allow list')

    def testRemContactFL(self):
        self.client.factory.contacts = msn.MSNContactList()
        self.client.factory.contacts.addContact(msn.MSNContact(userGuid="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", userHandle="foo@bar.com", screenName="Some guy", lists=msn.FORWARD_LIST))
        self.client.doRemContactFL()
        self.failUnless(self.loop.doSteps(10), 'Failed to disconnect')
        self.failUnless((self.client.test == 'PASS'), 'Failed to remove contact from forward list')

    def testRemContactAL(self):
        self.client.factory.contacts = msn.MSNContactList()
        self.client.factory.contacts.addContact(msn.MSNContact(userGuid="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", userHandle="foo@bar.com", screenName="Some guy", lists=msn.ALLOW_LIST))
        self.client.doRemContactAL()
        self.failUnless(self.loop.doSteps(10), 'Failed to disconnect')
        self.failUnless((self.client.test == 'PASS'), 'Failed to remove contact from allow list')

    def testChangedScreenName(self):
        self.client.doScreenNameChange()
        self.failUnless(self.loop.doSteps(10), 'Failed to disconnect')
        self.failUnless((self.client.test == 'PASS'), 'Failed to change screen name properly')

    def testChangePersonal1(self):
        self.client.doPersonalChange("Some personal message")
        self.failUnless(self.loop.doSteps(10), 'Failed to disconnect')
        self.failUnless((self.client.test == 'PASS'), 'Failed to change personal message properly')

    def testChangePersonal2(self):
        self.client.doPersonalChange("")
        self.failUnless(self.loop.doSteps(10), 'Failed to disconnect')
        self.failUnless((self.client.test == 'PASS'), 'Failed to change personal message properly')

    def testChangeAvatar(self):
        self.client.doAvatarChange(lambda: "DATADATADATADATA")
        self.failUnless(self.loop.doSteps(10), 'Failed to disconnect')
        self.failUnless((self.client.test == 'PASS'), 'Failed to change avatar properly')

    def testRequestSwitchboard(self):
        self.client.doRequestSwitchboard()
        self.failUnless(self.loop.doSteps(10), 'Failed to disconnect')
        self.failUnless((self.client.test == 'PASS'), 'Failed to request switchboard')


#################################
# Notification challenges tests #
#################################

class DummyChallengeNotificationServer(msn.MSNEventBase):
    def doChallenge(self, challenge, response):
        self.state = 0
        self.response = response
        self.sendLine("CHL 0 " + challenge)

    def checkMessage(self, message):
        if message.message == self.response:
            self.state = "PASS"
        self.transport.loseConnection()
        return 0

    def handle_QRY(self, params):
        self.state = 1
        if len(params) == 3 and params[1] == "PROD0090YUAUV{2B" and params[2] == "32":
            self.state = 2
            self.currentMessage = msn.MSNMessage(length=32, userHandle="QRY", screenName="QRY", specialMessage=True)
            self.setRawMode()
        else:
            self.transport.loseConnection()

class DummyChallengeNotificationClient(msn.NotificationClient):
    def connectionMade(self):
        msn.MSNEventBase.connectionMade(self)

    def handle_CHL(self, params):
        msn.NotificationClient.handle_CHL(self, params)
        self.transport.loseConnection()


class NotificationChallengeTests(unittest.TestCase):
    """ tests the responses to the CHLs the server sends """

    def setUp(self):
        self.client = DummyChallengeNotificationClient()
        self.server = DummyChallengeNotificationServer()
        self.loop = LoopbackCon(self.client, self.server)
    
    def tearDown(self):
        self.loop.disconnect()
    
    def testChallenges(self):
        challenges = [('13038318816579321232', 'b01c13020e374d4fa20abfad6981b7a9'),
                      ('23055170411503520698', 'ae906c3f2946d25e7da1b08b0b247659'),
                      ('37819769320541083311', 'db79d37dadd9031bef996893321da480'),
                      ('93662730714769834295', 'd619dfbb1414004d34d0628766636568'),
                      ('31154116582196216093', '95e96c4f8cfdba6f065c8869b5e984e9')]
        for challenge, response in challenges:
            self.loop.reconnect()
            self.server.doChallenge(challenge, response)
            self.failUnless(self.loop.doSteps(10), 'Failed to disconnect')
            self.failUnless((self.server.state == 'PASS'), 'Incorrect challenge response.')
        

###########################
# Notification ping tests #
###########################

class DummyPingNotificationServer(LineReceiver):
    def lineReceived(self, line):
        if line.startswith("PNG") and self.good:
            self.sendLine("QNG 50")

class DummyPingNotificationClient(msn.NotificationClient):
    def connectionMade(self):
        msn.MSNEventBase.connectionMade(self)
        self.pingCheckerStart()

    def sendLine(self, line):
        msn.NotificationClient.sendLine(self, line)
        self.count += 1
        if self.count > 10:
            self.transport.loseConnection() # But not for real, just to end the test

    def connectionLost(self, reason):
        if self.count <= 10:
            self.state = 'DISCONNECTED'

class NotificationPingTests(unittest.TestCase):
    """ tests pinging in the NotificationClient class """

    def setUp(self):
        msn.PINGSPEED = 0.1
        self.client = DummyPingNotificationClient()
        self.server = DummyPingNotificationServer()
        self.client.factory = msn.NotificationFactory()
        self.server.factory = msn.NotificationFactory()
        self.client.state = 'CONNECTED'
        self.client.count = 0
        self.loop = LoopbackCon(self.client, self.server)

    def tearDown(self):
        msn.PINGSPEED = 50.0
        self.client.logOut()
        self.loop.disconnect()

    def testPingGood(self):
        self.server.good = True
        self.loop.doSteps(100)
        self.failUnless((self.client.state == 'CONNECTED'), 'Should be connected.')

    def testPingBad(self):
        self.server.good = False
        self.loop.doSteps(100)
        self.failUnless((self.client.state == 'DISCONNECTED'), 'Should be disconnected.')




###########################
# Switchboard basic tests #
###########################

class DummySwitchboardServer(msn.MSNEventBase):
    def handle_USR(self, params):
        if len(params) != 3:
            self.transport.loseConnection()
        if params[1] == 'foo@bar.com' and params[2] == 'somekey':
            self.sendLine("USR %s OK %s %s" % (params[0], params[1], params[1]))

    def handle_ANS(self, params):
        if len(params) != 4:
            self.transport.loseConnection()
        if params[1] == 'foo@bar.com' and params[2] == 'somekey' and params[3] == 'someSID':
            self.sendLine("ANS %s OK" % params[0])

    def handle_CAL(self, params):
        if len(params) != 2:
            self.transport.loseConnection()
        if params[1] == 'friend@hotmail.com':
            self.sendLine("CAL %s RINGING 1111122" % params[0])
        else:
            self.transport.loseConnection()

    def checkMessage(self, message):
        if message.message == 'Hi how are you today?':
            self.sendLine("ACK " + message.userHandle) # Relies on TRID getting stored in userHandle trick
        else:
            self.transport.loseConnection()
        return 0

class DummySwitchboardClient(msn.SwitchboardClient):
    def loggedIn(self):
        self.state = 'LOGGEDIN'
        self.transport.loseConnection()

    def gotChattingUsers(self, users):
        if users == {'fred@hotmail.com': 'fred', 'jack@email.com': 'jack has a nickname!'}:
            self.state = 'GOTCHATTINGUSERS'

    def userJoined(self, userHandle, screenName):
        if userHandle == "friend@hotmail.com" and screenName == "friend nickname":
            self.state = 'USERJOINED'

    def userLeft(self, userHandle):
        if userHandle == "friend@hotmail.com":
            self.state = 'USERLEFT'

    def gotContactTyping(self, message):
        if message.userHandle == 'foo@bar.com':
            self.state = 'USERTYPING'

    def gotMessage(self, message):
        if message.userHandle == 'friend@hotmail.com' and \
           message.screenName == 'Friend Nickname' and \
           message.message == 'Hello.':
            self.state = 'GOTMESSAGE'

    def doSendInvite(self):
        def testcb((sid,)):
            if sid == 1111122:
                self.state = 'INVITESUCCESS'
            self.transport.loseConnection()
        d = self.inviteUser('friend@hotmail.com')
        d.addCallback(testcb)

    def doSendMessage(self):
        def testcb(ignored):
            self.state = 'MESSAGESUCCESS'
            self.transport.loseConnection()
        m = msn.MSNMessage()
        m.setHeader("Content-Type", "text/plain; charset=UTF-8")
        m.message = 'Hi how are you today?'
        m.ack = msn.MSNMessage.MESSAGE_ACK
        d = self.sendMessage(m)
        d.addCallback(testcb)
    

class SwitchboardBasicTests(unittest.TestCase):
    """ Tests basic functionality of switchboard sessions """
    def setUp(self):
        self.client = DummySwitchboardClient()
        self.client.state = 'START'
        self.client.userHandle = 'foo@bar.com'
        self.client.key = 'somekey'
        self.client.sessionID = 'someSID'
        self.server = DummySwitchboardServer()
        self.loop = LoopbackCon(self.client, self.server)
 
    def tearDown(self):
        self.loop.disconnect()
 
    def _testSB(self, reply):
        self.client.reply = reply
        self.failUnless(self.loop.doSteps(10), 'Failed to disconnect')
        self.failUnless((self.client.state == 'LOGGEDIN'), 'Failed to login with reply='+str(reply))

    def testReply(self):
        self._testSB(True)
 
    def testAsync(self):
        self._testSB(False)

    def testChattingUsers(self):
        lines = ["IRO 1 1 2 fred@hotmail.com fred",
                 "IRO 1 2 2 jack@email.com jack%20has%20a%20nickname%21"]
        for line in lines:
            self.client.lineReceived(line)
        self.failUnless((self.client.state == 'GOTCHATTINGUSERS'), 'Failed to get chatting users')

    def testUserJoined(self):
        self.client.lineReceived("JOI friend@hotmail.com friend%20nickname")
        self.failUnless((self.client.state == 'USERJOINED'), 'Failed to notice user joining')

    def testUserLeft(self):
        self.client.lineReceived("BYE friend@hotmail.com")
        self.failUnless((self.client.state == 'USERLEFT'), 'Failed to notice user leaving')

    def testTypingCheck(self):
        m =  'MSG foo@bar.com Foo 80\r\n'
        m += 'MIME-Version: 1.0\r\n'
        m += 'Content-Type: text/x-msmsgscontrol\r\n'
        m += 'TypingUser: foo@bar\r\n'
        m += '\r\n\r\n'
        self.client.dataReceived(m)
        self.failUnless((self.client.state == 'USERTYPING'), 'Failed to detect typing notification')

    def testGotMessage(self):
        m =  'MSG friend@hotmail.com Friend%20Nickname 68\r\n'
        m += 'MIME-Version: 1.0\r\n'
        m += 'Content-Type: text/plain; charset=UTF-8\r\n'
        m += '\r\nHello.'
        self.client.dataReceived(m)
        self.failUnless((self.client.state == 'GOTMESSAGE'), 'Failed to detect message')

    def testInviteUser(self):
        self.client.doSendInvite()
        self.failUnless(self.loop.doSteps(10), 'Failed to disconnect')
        self.failUnless((self.client.state == 'INVITESUCCESS'), 'Failed to invite user')

    def testSendMessage(self):
        self.client.doSendMessage()
        self.failUnless(self.loop.doSteps(10), 'Failed to disconnect')
        self.failUnless((self.client.state == 'MESSAGESUCCESS'), 'Failed to send message')


################
# MSNP2P tests #
################

class DummySwitchboardP2PServerHelper(msn.MSNEventBase):
    def __init__(self, server):
        msn.MSNEventBase.__init__(self)
        self.server = server

    def handle_USR(self, params):
        if len(params) != 3:
            self.transport.loseConnection()
        self.userHandle = params[1]
        if params[1] == 'foo1@bar.com' and params[2] == 'somekey1':
            self.sendLine("USR %s OK %s %s" % (params[0], params[1], params[1]))
        if params[1] == 'foo2@bar.com' and params[2] == 'somekey2':
            self.sendLine("USR %s OK %s %s" % (params[0], params[1], params[1]))

    def checkMessage(self, message):
        return 1

    def gotMessage(self, message):
        message.userHandle = self.userHandle
        message.screenName = self.userHandle
        self.server.gotMessage(message, self)

    def sendMessage(self, message):
        if message.length == 0: message.length = message._calcMessageLen()
        self.sendLine("MSG %s %s %s" % (message.userHandle, message.screenName, message.length))
        self.sendLine('MIME-Version: %s' % message.getHeader('MIME-Version'))
        self.sendLine('Content-Type: %s' % message.getHeader('Content-Type'))
        for header in [h for h in message.headers.items() if h[0].lower() not in ('mime-version','content-type')]:
            self.sendLine("%s: %s" % (header[0], header[1]))
        self.transport.write("\r\n")
        self.transport.write(message.message)


class DummySwitchboardP2PServer:
    def __init__(self):
        self.clients = []

    def newClient(self):
        c = DummySwitchboardP2PServerHelper(self)
        self.clients.append(c)
        return c

    def gotMessage(self, message, sender):
        for c in self.clients:
            if c != sender:
                c.sendMessage(message)

class DummySwitchboardP2PClient(msn.SwitchboardClient):
    def gotMessage(self, message):
        if message.message == "Test Message" and message.userHandle == "foo1@bar.com":
            self.status = "GOTMESSAGE"

    def gotFileReceive(self, fileReceive):
        self.fileReceive = fileReceive

class SwitchboardP2PTests(unittest.TestCase):
    def setUp(self):
        self.server  = DummySwitchboardP2PServer()
        self.client1 = DummySwitchboardP2PClient()
        self.client1.key = 'somekey1'
        self.client1.userHandle = 'foo1@bar.com'
        self.client2 = DummySwitchboardP2PClient()
        self.client2.key = 'somekey2'
        self.client2.userHandle = 'foo2@bar.com'
        self.client2.status = "INIT"
        self.loop1 = LoopbackCon(self.client1, self.server.newClient())
        self.loop2 = LoopbackCon(self.client2, self.server.newClient())

    def tearDown(self):
        self.loop1.disconnect()
        self.loop2.disconnect()

    def _loop(self, steps=1):
        for i in xrange(steps):
            self.loop1.doSteps(1)
            self.loop2.doSteps(1)

    def testMessage(self):
        self.client1.sendMessage(msn.MSNMessage(message='Test Message'))
        self._loop()
        self.failUnless((self.client2.status == "GOTMESSAGE"), "Fake switchboard server not working.")

    def _generateData(self):
        data = ''
        for i in xrange(3000):
            data += struct.pack("<L", random.randint(0, msn.MSN_MAXINT))
        return data
    
    def testAvatars(self):
        self.gotAvatar = False

        # Set up the avatar for client1
        imageData = self._generateData()
        self.client1.msnobj = msn.MSNObject()
        self.client1.msnobj.setData('foo1@bar.com', lambda: imageData)
        self.client1.msnobj.makeText()

        # Make client2 request the avatar
        def avatarCallback((data,)):
            self.gotAvatar = (data == imageData)
        msnContact = msn.MSNContact(userHandle='foo1@bar.com', msnobj=self.client1.msnobj)
        d = self.client2.sendAvatarRequest(msnContact)
        d.addCallback(avatarCallback)

        # Let them do their thing
        self._loop(10)

        # Check that client2 got the avatar
        self.failUnless((self.gotAvatar), "Failed to transfer avatar")

    def testFilesHappyPath(self):
        fileData = self._generateData()
        self.gotFile = False

        # Send the file (client2->client1)
        msnContact = msn.MSNContact(userHandle='foo1@bar.com', caps=msn.MSNContact.MSNC1)
        fileSend, d = self.client2.sendFile(msnContact, "myfile.txt", len(fileData))
        def accepted((yes,)):
            if yes:
                fileSend.write(fileData)
                fileSend.close()
            else:
                raise "TransferDeclined"
        def failed():
            raise "TransferError"
        d.addCallback(accepted)
        d.addErrback(failed)

        # Let the request get pushed to client1
        self._loop(10)

        # Receive the file
        def finished(data):
            self.gotFile = (data == fileData)
        fileBuffer = msn.StringBuffer(finished)
        fileReceive = self.client1.fileReceive
        self.failUnless((fileReceive.filename == "myfile.txt" and fileReceive.filesize == len(fileData)), "Filename or length wrong.")
        fileReceive.accept(fileBuffer)

        # Lets transfer!!
        self._loop(10)

        self.failUnless((self.gotFile), "Failed to transfer file")

    def testFilesHappyChunkedPath(self):
        fileData = self._generateData()
        self.gotFile = False

        # Send the file (client2->client1)
        msnContact = msn.MSNContact(userHandle='foo1@bar.com', caps=msn.MSNContact.MSNC1)
        fileSend, d = self.client2.sendFile(msnContact, "myfile.txt", len(fileData))
        def accepted((yes,)):
            if yes:
                fileSend.write(fileData[:len(fileData)/2])
                fileSend.write(fileData[len(fileData)/2:])
                fileSend.close()
            else:
                raise "TransferDeclined"
        def failed():
            raise "TransferError"
        d.addCallback(accepted)
        d.addErrback(failed)

        # Let the request get pushed to client1
        self._loop(10)

        # Receive the file
        def finished(data):
            self.gotFile = (data == fileData)
        fileBuffer = msn.StringBuffer(finished)
        fileReceive = self.client1.fileReceive
        self.failUnless((fileReceive.filename == "myfile.txt" and fileReceive.filesize == len(fileData)), "Filename or length wrong.")
        fileReceive.accept(fileBuffer)

        # Lets transfer!!
        self._loop(10)

        self.failUnless((self.gotFile), "Failed to transfer file")

    def testTwoFilesSequential(self):
        self.testFilesHappyPath()
        self.testFilesHappyPath()

    def testFilesDeclinePath(self):
        fileData = self._generateData()
        self.gotDecline = False

        # Send the file (client2->client1)
        msnContact = msn.MSNContact(userHandle='foo1@bar.com', caps=msn.MSNContact.MSNC1)
        fileSend, d = self.client2.sendFile(msnContact, "myfile.txt", len(fileData))
        def accepted((yes,)):
            self.failUnless((not yes), "Failed to understand a decline.")
            self.gotDecline = True
        def failed():
            raise "TransferError"
        d.addCallback(accepted)
        d.addErrback(failed)

        # Let the request get pushed to client1
        self._loop(10)

        # Decline the file
        fileReceive = self.client1.fileReceive
        fileReceive.reject()

        # Let the decline get pushed to client2
        self._loop(10)

        self.failUnless((self.gotDecline), "Failed to understand a decline, ignored.")


################
# MSNFTP tests #
################

#class FileTransferTestCase(unittest.TestCase):
#    """ test FileSend against FileReceive """
#    skip = "Not implemented"
#
#    def setUp(self):
#        self.input = StringIOWithoutClosing()
#        self.input.writelines(['a'] * 7000)
#        self.input.seek(0)
#        self.output = StringIOWithoutClosing()
#
#    def tearDown(self):
#        self.input = None
#        self.output = None
#
#    def testFileTransfer(self):
#        auth = 1234
#        sender = msnft.MSNFTP_FileSend(self.input)
#        sender.auth = auth
#        sender.fileSize = 7000
#        client = msnft.MSNFTP_FileReceive(auth, "foo@bar.com", self.output)
#        client.fileSize = 7000
#        loop = LoopbackCon(client, sender)
#        loop.doSteps(100)
#        self.failUnless((client.completed and sender.completed), "send failed to complete")
#        self.failUnless((self.input.getvalue() == self.output.getvalue()), "saved file does not match original")


