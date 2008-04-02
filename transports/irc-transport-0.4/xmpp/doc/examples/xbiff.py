#!/usr/bin/python
# $Id: xbiff.py,v 1.2 2006/10/06 12:30:42 normanr Exp $
import sys,os,xmpp,time,select

class Bot:

    def __init__(self,jabber):
        self.jabber = jabber

    def register_handlers(self):
        self.jabber.RegisterHandler('message',self.xmpp_message)

    def xmpp_message(self, con, event):
        type = event.getType()
        fromjid = event.getFrom().getStripped()
        if type in ['message', 'chat', None]:
	    print fromjid+':',event.getBody()
	    if event.getBody():
	        p = xmpp.protocol.Presence(to=fromjid,status=event.getBody())
	        self.jabber.send(p)
	    p = xmpp.protocol.Presence(to=fromjid,typ='unavailable')
	    self.jabber.send(p)

    def xmpp_connect(self):
        con=self.jabber.connect()
        if not con:
            sys.stderr.write('could not connect!\n')
            return False
        sys.stderr.write('connected with %s\n'%con)
        auth=self.jabber.auth(jid.getNode(),jidparams['password'],resource=jid.getResource())
        if not auth:
            sys.stderr.write('could not authenticate!\n')
            return False
        sys.stderr.write('authenticated using %s\n'%auth)
        self.register_handlers()
        return con

if __name__ == '__main__':

    if len(sys.argv) < 1:
        print "Syntax: xbiff"
        sys.exit(0)
    
    jidparams={}
    if os.access(os.environ['HOME']+'/.xbiff',os.R_OK):
        for ln in open(os.environ['HOME']+'/.xbiff').readlines():
            if not ln[0] in ('#',';'):
                key,val=ln.strip().split('=',1)
                jidparams[key.lower()]=val
    for mandatory in ['jid','password']:
        if mandatory not in jidparams.keys():
            open(os.environ['HOME']+'/.xbiff','w').write('#Uncomment fields before use and type in correct credentials.\n#JID=romeo@montague.net/resource (/resource is optional)\n#PASSWORD=juliet\n')
            print 'Please point ~/.xbiff config file to valid JID for sending messages.'
            sys.exit(0)
    
    jid=xmpp.protocol.JID(jidparams['jid'])
    cl=xmpp.Client(jid.getDomain(),debug=[])
    
    bot=Bot(cl)

    if not bot.xmpp_connect():
        sys.stderr.write("Could not connect to server, or password mismatch!\n")
        sys.exit(1)

    #cl.SendInitPresence(requestRoster=0)   # you may need to uncomment this for old server
    
    socketlist = {cl.Connection._sock:'xmpp'}
    online = 1

    while online:
        (i , o, e) = select.select(socketlist.keys(),[],[],1)
        for each in i:
            if socketlist[each] == 'xmpp':
                cl.Process(1)
            else:
                raise Exception("Unknown socket type: %s" % repr(socketlist[each]))
    #cl.disconnect()
