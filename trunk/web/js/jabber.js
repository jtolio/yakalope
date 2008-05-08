var jabber = {
  u_n: '',
  p_w: '',
  con: new JSJaCHttpBindingConnection(),
  roster: [],
  myJid: '',
  init: function(){
    oDbg = new JSJaCConsoleLogger(2);
    // Try to resume a session
    try {
      this.con = new JSJaCHttpBindingConnection({'oDbg': oDbg});
      setupCon(this.con);      
      if (this.con.resume()) {}
    } 
    catch (e) {} // reading cookie failed - never mind
  },
  
  quit: function(){
    if (this.con && this.con.connected()) 
      this.con.disconnect();
  },
  
  /**
   * Registers handlers for XMPP stanzas
   * @param {JSJaCHttpBindingConnection} con
   */
  setupCon: function(con){
    con.registerHandler('message', jabber.handle.message);
    con.registerHandler('presence', jabber.handle.presence);
    con.registerHandler('onconnect', jabber.handle.connected);
    con.registerHandler('onerror', jabber.handle.error);
    con.registerHandler('status_changed', jabber.handle.statusChanged);
    con.registerHandler('ondisconnect', jabber.handle.disconnected);
    con.registerHandler('failure', jabber.handle.failure);
    con.registerIQGet('query', NS_VERSION, jabber.handle.iqVersion);
    con.registerIQGet('query', NS_TIME, jabber.handle.iqTime);
    con.registerIQSet('query', NS_ROSTER, jabber.handle.iqRosterSet);
    con.registerHandler('iq', 'query', NS_ROSTER, jabber.handle.iqRoster);
    con.registerHandler('iq', 'query', NS_DISCO_ITEMS, jabber.handle.iqDiscoItems);
    con.registerHandler('iq', 'query', NS_REGISTER, jabber.handle.iqRegister);
  },
  
  doLogin: function(username, password){
  
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
	  this.u_n = username;
	  this.p_w = password;
      this.myJid = oArgs.username + oArgs.domain;
      
      this.con.connect(oArgs);
    } 
    catch (e) {
      alert(e.toString());
    }
    finally {
      return false;
    }
  },
  send:function(packet) {
    try {
      this.con.send(packet);
    } catch(e) {
      Ext.MessageBox.alert('Error sending packet', e.message);
    }
  },
  /**
   * Sends a message
   * @param {JSJaCJID} user
   * @param {String} msg
   */
  sendMsg: function(user, msg){
    var aMsg = new JSJaCMessage();
    aMsg.setTo(new JSJaCJID(user.toString()));
    aMsg.setBody(msg);
    this.send(aMsg);
    return true;
  },
  
  getRoster: function(){
    var roster = new JSJaCIQ();
    roster.setIQ(null, 'get', 'roster_1');
    roster.setQuery(NS_ROSTER);
    this.send(roster);
  },
  addRosterItem: function(buddy){
    var iq = new JSJaCIQ();
    iq.setFrom(jabber.myJid);
    iq.setType('set');
    iq.setID('roster_set');
    var query = iq.setQuery(NS_ROSTER);
    var group = iq.buildNode('group', {}, buddy.group);
    var item = iq.buildNode('item', {
      jid: buddy.jid,
      name: buddy.name
    });
    item.appendChild(group);
    query.appendChild(item);
    this.con.send(iq);
  },
  addBuddy: function(buddy){
    this.addRosterItem(buddy);
    this.subscribe(buddy.jid);
    return buddy.jid;
  },

  discoverItems: function(){
    var iq = new JSJaCIQ();
    iq.setTo('squall.cs.umn.edu');
    iq.setType('get');
    iq.setID('get_items');
    iq.setQuery(NS_DISCO_ITEMS);
    this.send(iq);
  },

  getRegFields: function(to){
    var iq = new JSJaCIQ();
    iq.setTo(to);
    iq.setType('get');
    iq.setID('reg_get');
    iq.setQuery(NS_REGISTER);
    this.send(iq);
  },

  register: function(to, fields) {
    var iq = new JSJaCIQ();
    iq.setTo(to);
    iq.setType('set');
    iq.setID('reg');
    var query = iq.setQuery(NS_REGISTER);
    for (field in fields) {
      query.appendChild(
        iq.buildNode(field, {}, fields[field])
      );
    }
    this.send(iq);
  },

  setPresence: function(show, status) {
    var presence = new JSJaCPresence();
    presence.setShow(show);
    presence.setStatus(status);
    this.send(presence);
  },

  subscribe: function(jid){
    this.__subscription(jid, 'subscribe');
  },
  
  unsubscribe: function(jid){
    this.__subscription(jid, 'unsubscribe');
  },
  
  allowSubscription: function(jid){
    this.__subscription(jid, 'subscribed');
  },
  
  denySubscription: function(buddy){
    this.__subscription(jid, 'unsubscribed');
  },
  
  /**
   * Sends a subscription packet of a specified type
   * @param {JSJaCJID} buddy
   * @param {String} subType
   */
  __subscription: function(jid, subType){
    var presence = new JSJaCPacket('presence');
    presence.setTo(jid);
    presence.setType(subType);
    this.send(presence);
    Ext.MessageBox.alert('Error sending ' + subType, e.message);
    return false;
  },
  
  isConnected: function(){
    return this.con.connected();
  },
  handle: {
    iq: function(iq){
      if (iq.getType() != 'result') {
        var roster = new JSJaCIQ();
        roster.setIQ(null, 'result', iq.getID());
        roster.setQuery(NS_ROSTER);
        this.send(roster);
        console.log("Reply test: " + iq.reply().xml());
      }
    },
    
    message: function(aJSJaCPacket){
	  yakalope.app.addMsg(aJSJaCPacket.getFromJID().removeResource(), aJSJaCPacket.getBody().htmlEnc());
    },
    
    presence: function(aJSJaCPacket){
      var from = new JSJaCJID(aJSJaCPacket.getFrom());
      from.setResource(new String());
      var presence = aJSJaCPacket.getShow();
      if (aJSJaCPacket.getType()) {
        var type = aJSJaCPacket.getType();
      }
      if (aJSJaCPacket.getStatus()) {
        var status = aJSJaCPacket.getStatus();
      }      
      console.log(from + presence + status + type);
      roster.setPresence(from, presence, status, type);

      if (type == "subscribe") {
        Ext.MessageBox.confirm("Subscription request",
          "Approve subscription request from " + from.toString() + "?",
          function (approve) {
            console.log(approve);
            if (approve == 'yes')
              jabber.allowSubscription(from.toString());
            else
              jabber.denySubscription(from.toString());
        });
      }
    },

    error: function(aJSJaCPacket){
      if (jabber.con.connected()) 
        jabber.con.disconnect();
    },
    
    statusChanged: function(status){
      oDbg.log("status changed: " + status);
    },
    
    connected: function(){
      jabber.getRoster();
      jabber.con.send(new JSJaCPresence());
    },
    
    disconnected: function(){
      roster.clear();
      Login.login();
    },
    
    failure: function(aJSJaCPacket){
      alert("Failure: " + aJSJaCPacket.xml());
    },
    
    iqVersion: function(iq){
      this.send(iq.reply(
        [iq.buildNode('name', 'yakalope test'),
         iq.buildNode('version', JSJaC.Version),
         iq.buildNode('os', navigator.userAgent)]));
      return true;
    },
    
    iqTime: function(iq){
      var now = new Date();
      this.send(iq.reply(
        [iq.buildNode('display', now.toLocaleString()),
         iq.buildNode('utc', now.jabberDate()),
         iq.buildNode('tz',
           now.toLocaleString().substring(now.toLocaleString().lastIndexOf(' ') + 1))]));
      return true;
    },

    iqRoster: function(iq){
      var RosterItem = Ext.data.Record.create([
        { name: 'jid', mapping: '@jid' },
        { name: 'name', mapping: '@name' },
        { name: 'subscription', mapping: '@subscription' },
        { name: 'group' }          
      ]);
      var reader =  new Ext.data.XmlReader({
    	    record: 'item',
      }, RosterItem);
      // TODO: Load the result of the XmlReader directly into the roster store
      var result = reader.readRecords(iq.getQuery());

      var items = result.records;

      for (var i=0, il=items.length; i<il; i++) {
        roster.update(new Buddy(items[i].data.jid, items[i].data.subscription,
          items[i].data.name, items[i].data.group));
      }
    },
    iqRosterSet: function(iq){
      jabber.handle.iqRoster(iq);
    },

    iqDiscoItems: function(iq){
      alert(iq.xml());
    },

    iqRegister: function(iq){
      alert(iq.xml());
    }
  }
}

/**
 * Buddy type
 * @param {String} jid
 * @param {String} subscription Must be "none", "to", "from", "both"
 * @param {String} name Nickname
 * @param {String} group
 * @param {String} presence
 * @param {String} status
 * @param {String} type
 */
var Buddy = function(jid, subscription, name, group, presence, status, type){
  this.jid = new JSJaCJID(jid);
  this.subscription = subscription;
  this.name = name;
  this.group = group;
  this.presence = presence;
  this.status = status;
  this.type = type;

  for (var el in this) 
    if (typeof(this[el]) == 'undefined')
      this[el] = '';
}
/**
 * Compares self to another Buddy object
 * @param {Buddy} buddy
 */
Buddy.prototype.compareTo = function (buddy) {
  return this.jid.toString() == buddy.jid.toString();
}
/**
 * Updates buddy attributes without overwriting presence data
 * @param {Buddy} buddy
 */
Buddy.prototype.update = function (buddy) {
  this.jid = buddy.jid;
  this.subscription = buddy.subscription;
  this.name = buddy.name;
  this.group = buddy.group;
}

