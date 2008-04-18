var jabber = {
  con: new JSJaCHttpBindingConnection(),
  roster: new Array(),
  myJid: new String(),
  init: function() {
    oDbg = new JSJaCConsoleLogger(2);

    try { // try to resume a session
      this.con = new JSJaCHttpBindingConnection({'oDbg':oDbg});
      setupCon(this.con);

      if (this.con.resume()) {
      }
    } catch (e) {} // reading cookie failed - never mind
  },
  
  quit: function() {
    if (this.con && this.con.connected())
      this.con.disconnect();
  },
  
  /**
   * Registers handlers for XMPP stanzas
   * @param {JSJaCHttpBindingConnection} con
   */
  setupCon: function(con) {
    con.registerHandler('message', jabber.handle.message);
    con.registerHandler('presence', jabber.handle.presence);
    //con.registerHandler('iq', jabber.handle.iq);
    con.registerHandler('onconnect', jabber.handle.connected);
    con.registerHandler('onerror', jabber.handle.error);
    con.registerHandler('status_changed', jabber.handle.statusChanged);
    con.registerHandler('ondisconnect', jabber.handle.disconnected);
    con.registerHandler('failure', jabber.handle.failure);

    con.registerIQGet('query', NS_VERSION, jabber.handle.iqVersion);
    con.registerIQGet('query', NS_TIME, jabber.handle.iqTime);
    //con.registerIQGet('query', NS_ROSTER, jabber.handle.iqRosterGet);
    con.registerIQSet('query', NS_ROSTER, jabber.handle.iqRosterSet);
    con.registerHandler('iq', 'query', NS_ROSTER, jabber.handle.iqRoster);
  },
  
  doLogin: function(username, password) {
    
    try {
      // setup args for contructor
      oArgs = new Object();
      oArgs.httpbase = '/http-bind/';
      oArgs.timerval = 2000;

      if (typeof(oDbg) != 'undefined')
        oArgs.oDbg = oDbg;

      this.con = new JSJaCHttpBindingConnection(oArgs);

      jabber.setupCon(this.con);

      // setup args for connect method
      oArgs = new Object();
      oArgs.domain = 'squall.cs.umn.edu';
      oArgs.username = username;
      oArgs.resource = 'yakalope';
      oArgs.pass = password;
      oArgs.register = false;			
			this.myJid = oArgs.username + oArgs.domain;

      this.con.connect(oArgs);
    } catch (e) {
      alert("I am here")
      alert(e.toString());
    } finally {
      return false;
    }
  },
  /**
   * Sends a message
   * @param {JSJaCJID} user
   * @param {String} msg
   */
  sendMsg: function(user, msg) {
    try {
      var aMsg = new JSJaCMessage();
      aMsg.setTo(new JSJaCJID(user.toString()));
      aMsg.setBody(msg);
      this.con.send(aMsg);
      alert(aMsg.xml());
      return false;
    } catch (e) {
      alert("Error: " + e.message);
      return false;
    }
  },
  
  getRoster: function() {
    try {
      var roster = new JSJaCIQ();
      roster.setIQ(null, 'get', 'roster_1');
      roster.setQuery(NS_ROSTER);
      //roster.setFrom('');
      this.con.send(roster);
    } catch (e) {
      alert("Error getting roster: " + e.message);
      return false;
    }
  },
  
  subscribe: function(buddy) {
    this.__subscription(buddy, 'subscribe');
  },
  
  unsubscribe: function(buddy) {
    this.__subscription(buddy, 'unsubscribe');
  },
  
  allowSubscription: function(buddy) {
    this.__subscription(buddy, 'subscribed');
  },
  
  denySubscription: function(buddy) {
    this.__subscription(buddy, 'unsubscribed');
  },
  
  /**
   * Sends a subscription packet of a specified type
   * @param {JSJaCJID} buddy
   * @param {String} subType
   */
  __subscription: function(buddy, subType) {
    try {
      var presence = new JSJaCPacket('presence');
      presence.setTo(new JSJaCJID(buddy));
      presence.setType(subType);
      this.con.send(presence);
    } catch (e) {
      alert("Error sending '" + subType + "': " + e.message);
      return false;
    }
  },
  addRosterItem: function(jid, name, group) {
    var iq = new JSJaCIQ();
    iq.setFrom(jabber.myJid);
    iq.setType('set');
    iq.setID('roster_set');
    var query = iq.setQuery(NS_ROSTER);
    var group = iq.buildNode('group', {}, group); 
    var item = iq.buildNode('item', {jid:jid, name:name});
    item.appendChild(group);
    query.appendChild(item);
    alert(iq.xml());
    //this.con.send(iq);
  },
  isConnected: function () {
    return this.con.connected();
  },
  handle: {
    iq: function(aIQ) {
      alert("IN (raw): " + aIQ.xml());
      jabber.con.send(aIQ.errorReply(ERR_FEATURE_NOT_IMPLEMENTED));
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
      if (type == "subscribe") {
        var approve = prompt("allow " + from +"?", "subscribe");
        alert(approve);
        if (approve) {
            jabber.allowSubscription(from);
        } else {
            jabber.denySubscription(from);
        }
      }  
      if (presence == "away" || presence == "chat" ||
          presence == "dnd"  || presence == "xa") {
        yakalope.app.addBuddy(from);
      }
    },
    
    error: function(aJSJaCPacket) {
      if (jabber.con.connected())
        jabber.con.disconnect();
    },
    
    statusChanged: function(status) {
      oDbg.log("status changed: " + status);
    },
    
    connected: function() {
      jabber.con.send(new JSJaCPresence());
      jabber.getRoster();
    },
    
    disconnected: function() {
    },

    failure: function(aJSJaCPacket) {
      alert("Failure: " + aJSJaCPacket.xml());
    },
    
    iqVersion: function(iq) {
      jabber.con.send(iq.reply(
        [iq.buildNode('name', 'yakalope test'),
         iq.buildNode('version', JSJaC.Version),
         iq.buildNode('os', navigator.userAgent)]));
      return true;
    },

    iqTime: function(iq) {
      var now = new Date();
      jabber.con.send(iq.reply(
        [iq.buildNode('display',
            now.toLocaleString()),
         iq.buildNode('utc',
            now.jabberDate()),
         iq.buildNode('tz',
            now.toLocaleString().substring(now.toLocaleString().lastIndexOf(' ')+1))
        ]));
      return true;
    },
    
    iqRoster: function(iq) {
	    try {
				// Respond with 'result' packet
	      var roster = new JSJaCIQ();
	      roster.setIQ(null, 'result', iq.getID());
	      roster.setQuery(NS_ROSTER);
	      jabber.con.send(roster);
				
		  var result = XMLTools.getXmlRecords(['group'], 'item', iq.getQuery());
				
        for(var i=0; i<result.records.length; i++) {
            var node = result.records[i].node;
            var jid = node.getAttribute('jid');
            var name = node.getAttribute('name');
            var subscription = node.getAttribute('subscription');
            var group = result.records[i].data['group'];
            yakalope.app.addBuddy(new Buddy(jid, subscription, name, group));
        }
      } catch (e) {
        alert("Error: " + e.message);
        return false;
      }
    },
    
    iqRosterSet: function (iq) {
      alert(iq.getQuery());

	  var node = iq.getQuery().firstChild;
	  var jid = node.getAttribute('jid');
	  var name = node.getAttribute('name');
	  var subscription = node.getAttribute('subscription');
	  var group = node.firstChild.nodeValue;
	  var buddy = new Buddy(jid, subscription, name, group);
	  yakalope.app.addBuddy(buddy);				

    },
  }    
}

/**
 * Buddy type
 * @param {String} jid
 * @param {String} subscription Must be "none", "to", "from", "both"
 * @param {String} name Nickname
 * @param {String} group
 */
var Buddy = function (jid, subscription, name, group) {
  this.jid = new JSJaCJID(jid);
  this.subscription = subscription;
  this.name = name;
  this.group = group;
}

var XMLTools = {
  /**
   * Simple map function. We use this instead of built-ins so we aren't
   * relying on too much javascript version complexity.
   * @param {Object} fun: Function to apply to the list
   * @param {Array} alist: List of things to apply the function to
   */
  map: function(fun, alist){
    var tmp = [];
    for (var i = 0; i < alist.length; i++) 
      tmp.push(fun(alist[i]));
    return tmp;
  },

  /**
   * Wrapper for the Ext.XMLReader which will generate a list of
   * record objects with key-value pairings.
   * @param {Array} tag_list: list of strings, will be the XML tags
   * that are placed into a record object.
   * @param {String} record_name: name of record that will appear in
   * a series.
   * @param {Object} xml_obj: the xml document to parse the data from
   */
  getXmlRecords: function(tag_list, record_name, xml_obj){
    tag_list = this.map(function(tag){
      return {
        name: tag
      };
    }, tag_list);
    var RecordObj = Ext.data.Record.create(tag_list);
    var readerObj = new Ext.data.XmlReader({
      record: record_name
    }, RecordObj);
    return readerObj.readRecords(xml_obj);
  },
}
