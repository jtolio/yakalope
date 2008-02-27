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
  
  sendMsg: function(aForm) {
    if (aForm.msg.value == '' || aForm.sendTo.value == '')
      return false;

    if (aForm.sendTo.value.indexOf('@') == -1)
      aForm.sendTo.value += '@' + con.domain;

    try {
      var aMsg = new JSJaCMessage();
      aMsg.setTo(new JSJaCJID(aForm.sendTo.value));
      aMsg.setBody(aForm.msg.value);
      con.send(aMsg);

      aForm.msg.value = '';

      return false;
    } catch (e) {
      html = "<div class='msg error''>Error: " + e.message + "</div>"; 
      Ext.getCmp('iResp').addMsg(html);
      //Ext.get('iResp').lastChild.scrollIntoView();
      //alert("Error: " + e.message);
      return false;
    }
  },
  
  handle: {
    iq: function(aIQ) {
      Ext.getCmp('iResp').addMsg("<div class='msg'>IN (raw): " + aIQ.xml().htmlEnc() + '</div>');
      //Ext.getCmp('iResp').lastChild.scrollIntoView();
      con.send(aIQ.errorReply(ERR_FEATURE_NOT_IMPLEMENTED));
    },
    
    message: function(aJSJaCPacket) {
      var html = '';
      html += '<div class="msg"><b>Received Message from ' + aJSJaCPacket.getFromJID() + ':</b>';
      html += aJSJaCPacket.getBody().htmlEnc() + '<br /></div>';
      Ext.getCmp('iResp').addMsg(html);
      //document.getElementById('iResp').lastChild.scrollIntoView();
    },
    
    presence: function(aJSJaCPacket) {
      var html = '<div class="msg">';
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

      Ext.getCmp('iResp').addMsg(html);
      //Ext.get('iResp').lastChild.scrollIntoView();
    },
    
    error: function(aJSJaCPacket) {
      Ext.getCmp('iResp').addMsg("An error occured:<br />" +
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
      Ext.getCmp('iResp').addMsg("<strong>Connected</strong><br />");

      con.send(new JSJaCPresence());
    },
    
    disconnected: function() {
      //document.getElementById('login_pane').style.display = '';
      //document.getElementById('sendmsg_pane').style.display = 'none';
      Ext.getCmp('iResp').addMsg("<strong>Disconnected</strong><br />");
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

