var con;
var jabber = {
  init: function() {
    oDbg = new JSJaCConsoleLogger(2);

    try { // try to resume a session
      con = new JSJaCHttpBindingConnection({'oDbg':oDbg});

      setupCon(con);

      if (con.resume()) {
      }
    } catch (e) {} // reading cookie failed - never mind
  },
  
  quit: function() {
    if (con && con.connected())
      con.disconnect();
  },
  
  setupCon: function(con) {
    con.registerHandler('message',jabber.handle.message);
    con.registerHandler('presence',jabber.handle.presence);
    con.registerHandler('iq',jabber.handle.iq);
    con.registerHandler('onconnect',jabber.handle.connected);
    con.registerHandler('onerror',jabber.handle.error);
    con.registerHandler('status_changed',jabber.handle.statusChanged);
    con.registerHandler('ondisconnect',jabber.handle.disconnected);

    con.registerIQGet('query', NS_VERSION, jabber.handle.iqVersion);
    con.registerIQGet('query', NS_TIME, jabber.handle.iqTime);
  },
  
  doLogin: function() {
    try {
      // setup args for contructor
      oArgs = new Object();
      oArgs.httpbase = '/http-bind/';
      oArgs.timerval = 2000;

      if (typeof(oDbg) != 'undefined')
        oArgs.oDbg = oDbg;

      con = new JSJaCHttpBindingConnection(oArgs);

      jabber.setupCon(con);

      // setup args for connect method
      oArgs = new Object();
      oArgs.domain = 'squall.cs.umn.edu';
      oArgs.username = 'testing';
      oArgs.resource = 'yakalope';
      oArgs.pass = 'testing';
      oArgs.register = false;
      con.connect(oArgs);
    } catch (e) {
      alert(e.toString());
    } finally {
      return false;
    }
  },
  
  sendMsg: function(user, msg) {
    try {
      var aMsg = new JSJaCMessage();
      aMsg.setTo(new JSJaCJID(user.toString()));
      aMsg.setBody(msg);
      con.send(aMsg);
      return false;
    } catch (e) {
      alert("Error: " + e.message);
      return false;
    }
  },
  
  handle: {
    iq: function(aIQ) {
      Ext.getCmp('iResp').addMsg("<div class='msg'>IN (raw): " + aIQ.xml().htmlEnc() + '</div>');
      con.send(aIQ.errorReply(ERR_FEATURE_NOT_IMPLEMENTED));
    },
    
    message: function(aJSJaCPacket) {
      yakalope.app.addMsg(aJSJaCPacket.getFromJID(), aJSJaCPacket.getBody().htmlEnc());
    },
    
    presence: function(aJSJaCPacket) {
      var from = aJSJaCPacket.getFrom();
      var presence = aJSJaCPacket.getShow();
      if (aJSJaCPacket.getType()) {
        var type = aJSJaCPacket.getType();
      }
      if (aJSJaCPacket.getStatus()) {
        var status = aJSJaCPacket.getStatus();
      }
      if (type == "unavailable") {
        yakalope.app.removeBuddy(from);
      }
      if (presence == "away" || presence == "chat" ||
          presence == "dnd"  || presence == "xa") {
        yakalope.app.addBuddy(from);
      }
    },
    
    error: function(aJSJaCPacket) {
      if (con.connected())
        con.disconnect();
    },
    
    statusChanged: function(status) {
      oDbg.log("status changed: " + status);
    },
    
    connected: function() {
      con.send(new JSJaCPresence());
    },
    
    disconnected: function() {
    },
    
    iqVersion: function(iq) {
      con.send(iq.reply(
        [iq.buildNode('name', 'yakalope test'),
         iq.buildNode('version', JSJaC.Version),
         iq.buildNode('os', navigator.userAgent)]));
      return true;
    },

    iqTime: function(iq) {
      var now = new Date();
      con.send(iq.reply(
        [iq.buildNode('display',
            now.toLocaleString()),
         iq.buildNode('utc',
            now.jabberDate()),
         iq.buildNode('tz',
            now.toLocaleString().substring(now.toLocaleString().lastIndexOf(' ')+1))
        ]));
      return true;
    },
  }    
}

