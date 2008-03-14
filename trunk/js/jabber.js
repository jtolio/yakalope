var con;
var jabber = {
  init: function() {
    oDbg = new JSJaCConsoleLogger(2);

    try { // try to resume a session
      con = new JSJaCHttpBindingConnection({'oDbg':oDbg});

      setupCon(con);

      if (con.resume()) {

        //document.getElementById('login_pane').style.display = 'none';
        //document.getElementById('sendmsg_pane').style.display = '';
        //document.getElementById('err').innerHTML = '';

      }
    } catch (e) {} // reading cookie failed - never mind
  },
  
  quit: function() {
    if (con && con.connected())
      con.disconnect();

    //document.getElementById('login_pane').style.display = '';
    //document.getElementById('sendmsg_pane').style.display = 'none';
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
    //document.getElementById('err').innerHTML = ''; // reset
    try {
      // setup args for contructor
      oArgs = new Object();
      //oArgs.httpbase = aForm.http_base.value;
      oArgs.httpbase = '/http-bind/';
      oArgs.timerval = 2000;

      if (typeof(oDbg) != 'undefined')
        oArgs.oDbg = oDbg;

      con = new JSJaCHttpBindingConnection(oArgs);

      jabber.setupCon(con);

      // setup args for connect method
      oArgs = new Object();
      oArgs.domain = 'jabberworld.org';
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
  
  sendMsg: function(recipient, msg) {
    if (msg == '' || recipient == '')
      return false;

    /*if (recipient.indexOf('@') == -1)
      recipient += '@' + con.domain;*/

    try {
      alert(recipient + ": " + msg);
      var aMsg = new JSJaCMessage();
      aMsg.setTo(new JSJaCJID(recipient));
      aMsg.setBody(msg);
      con.send(aMsg);
      return false;
    } catch (e) {
      oDbg.log("Error sendMsg: " + e.message);
      return false;
    }
  },
  
  handle: {
    iq: function(aIQ) {
      oDbg.log("IN (raw): " + aIQ.xml().htmlEnc());
      //Ext.getCmp('iResp').lastChild.scrollIntoView();
      con.send(aIQ.errorReply(ERR_FEATURE_NOT_IMPLEMENTED));
    },
    
    message: function(aJSJaCPacket) {
      yakalope.app.addMsg(aJSJaCPacket.getFrom(), aJSJaCPacket.getBody().htmlEnc());
    },
    
    presence: function(aJSJaCPacket) {
      /*var html = '<div class="msg">';
      if (!aJSJaCPacket.getType() && !aJSJaCPacket.getShow()) 
        html += '<b>'+aJSJaCPacket.getFromJID()+' has become available.</b>';
      else {
        html += '<b>'+aJSJaCPacket.getFromJID()+' has set his presence to ';
        if (aJSJaCPacket.getType())
          html += aJSJaCPacket.getType() + '.</b>';
        else
          html += aJSJaCPacket.getShow() + '.</b>';
        if (aJSJaCPacket.getStatus())
          html += ' ('+aJSJaCPacket.getStatus().htmlEnc()+')';
      }
      html += '</div>';

      oDbg.log(html);*/
      //Ext.get('iResp').lastChild.scrollIntoView();
      oDbg.log(aJSJaCPacket.getFrom());
      yakalope.app.addBuddy(aJSJaCPacket.getFrom());
    },
    
    error: function(aJSJaCPacket) {
      oDbg.log("An error occured:" +
        ("Code: " + e.getAttribute('code') + "\nType: " + e.getAttribute('type') +
        "\nCondition: " + e.firstChild.nodeName).htmlEnc()); 
      //document.getElementById('login_pane').style.display = '';
      //document.getElementById('sendmsg_pane').style.display = 'none';
      
      if (con.connected())
        con.disconnect();
    },
    
    statusChanged: function(status) {
      oDbg.log("status changed: " + status);
    },
    
    connected: function() {
      //document.getElementById('login_pane').style.display = 'none';
      //document.getElementById('sendmsg_pane').style.display = '';
      //document.getElementById('err').innerHTML = '';
      oDbg.log("Connected");
      con.send(new JSJaCPresence());
    },
    
    disconnected: function() {
      //document.getElementById('login_pane').style.display = '';
      //document.getElementById('sendmsg_pane').style.display = 'none';
      oDbg.log("Disconnected");
    },
    
    iqVersion: function(iq) {
      con.send(iq.reply([
                         iq.buildNode('name', 'yakalope test'),
                         iq.buildNode('version', JSJaC.Version),
                         iq.buildNode('os', navigator.userAgent)
                         ]));
      return true;
    },

    iqTime: function(iq) {
      var now = new Date();
      con.send(iq.reply([iq.buildNode('display',
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

