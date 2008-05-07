/*
 * Buddy List
 */

var roster = {
  // Online buddies
  online: [],
  // Full roster
  roster: [],
  update: function (buddy) {
    for (var i=0, il=this.roster.length; i<il; i++) {
      if (this.roster[i].compareTo(buddy)) {
        this.roster[i].update(buddy);
        rosterStore.load();
        return;
      }
    }
    this.roster.push(buddy);    
    rosterStore.load();
  },
  setPresence: function (jid, presence, status, type) {
    // If the buddy comes online, move them to 'online'
    if (type != 'unavailable') {
      for (var i=0, il=this.roster.length; i<il; i++) {
        if (this.roster[i].jid.toString() == jid.toString()) {
          this.online.push(this.roster[i]);
          this.roster.remove(this.roster[i]);
        }
      }
    }
    for (var i=0, il=this.online.length; i<il; i++) {
      if (this.online[i].jid.toString() == jid.toString()) {
        this.online[i].presence = presence;
        this.online[i].status = status;
        this.online[i].type = type;
        // If the buddy goes offline, remove from online list
        if (type == 'unavailable') {
         var buddy = this.online[i];
         this.online.remove(this.online[i]);
         this.roster.push(buddy);
        }
      }
    }
    rosterStore.load();
  },
  clear: function () {
    this.online = [];
    this.roster = [];
    rosterStore.load();
  }
}

var rosterStore = new Ext.data.GroupingStore({
  id: 'rosterStore',
  proxy: new Ext.data.MemoryProxy(roster),
  reader: new Ext.data.JsonReader({
    root: 'online',
    },[
      {name: 'jid'},
      {name: 'subscription'},
      {name: 'name'},
      {name: 'group'},
      {name: 'presence'},
      {name: 'status'}    
  ]),
  sortInfo: {field: 'jid', direction: "ASC"},
  groupField: 'group'
});
rosterStore.on('loadexception', function(proxy, store, response, e) {
	console.log('loadexception: ' + e.message);
});

BuddyList = Ext.extend(Ext.Panel, {
  id: 'buddylist',
  split: true,
  width: 225,
  minSize: 150,
  maxSize: 400,
  collapsible: true,
  rootVisible: false,
  lines: false,
  defaults: {
    border: false
  },
  layoutConfig: {
    animate: true
  },
  onClick: function(node){
    yakalope.app.createNewChatWindow(node.text);
  },
  getTreeRoot: function(){
    return this.items.first().root;
  },
  getTreePane: function(){
    return this.items.first();
  },
  addBuddyDlg: function(){
    var servicesStore = new Ext.data.SimpleStore({
      id: 'services-store',
      fields: ['service', 'serviceName'],
      data: [['squall.cs.umn.edu', 'squall.cs.umn.edu']    /*['yakalope.com', 'Yakalope'],
       ['msn.yakalope.com', 'MSN'],
       ['aim.yakalope.com', 'AIM'],
       ['icq.yakalope.com', 'ICQ'],
       ['irc.yakalope.com', 'IRC']*/
      ],
    });
    var window = new Ext.Window({
      title: 'Add a Buddy',
      width: 300,
      items: new Ext.FormPanel({
      labelWidth: 50,
      frame: true,
      defaultType: 'textfield',
      items: [{
        fieldLabel: 'Name',
        name: 'buddyname',
        allowBlank: false,
      }, new Ext.form.ComboBox({
        id: 'serviceType',
        name: 'serviceType',
        fieldLabel: 'Service',
        //hiddenName: 'serviceType_hidden',
        value: servicesStore.getAt(0).data.service,
        store: servicesStore,
        valueField: 'service',
        displayField: 'serviceName',
        mode: 'local',
        forceSelection: true,
        triggerAction: 'all'
      })],
      }),
    });
    var form = window.items.first();
    form.addButton({
      text: 'Add',
      name: 'add',
    }, function(){
      var values = form.getForm().getValues();
      jabber.addBuddy(new Buddy(values.buddyname + '@' + values.serviceType, 'none'));
      window.close();
    }, window);
    form.addButton({
      text: 'Cancel',
      name: 'cancel',
    }, function(){
      window.close();
    }, window);
    window.show(this);
  },
  removeBuddyDlg: function(){
    var window = new Ext.Window({
      title: 'Remove a Buddy',
      width: 300,
      items: new Ext.FormPanel({
      labelWidth: 75,
      frame: true,
      defaultType: 'textfield',
      items: [{
        fieldLabel: 'Buddy Name',
        name: 'buddyname',
        allowBlank: false,
      }, {
        fieldLabel: 'Service',
        name: 'service',
        allowBlank: false,
      }],
      }),
    });
    var form = window.items.first();
    form.addButton({
      text: 'Remove',
      name: 'remove',
    }, function(){
      var values = form.getForm().getValues();
      yakalope.app.getBuddyList().callRemoveBuddy(values.buddyname);
      window.close();
    }, window);
    form.addButton({
      text: 'Cancel',
      name: 'cancel',
    }, function(){
      window.close();
    }, window);
    window.show(this);
  },
  initComponent: function(){
    Ext.apply(this, {
      tbar: [{
        text: 'Add Buddy',
        id: 'addbuddy',
        handler: this.addBuddyDlg,
        scope: this
      }, {
        text: 'Remove Buddy',
        id: 'removebuddy',
        handler: this.removeBuddyDlg,
        scope: this
      }, {
        text: 'Logout',
        id: 'logout',
        handler: function(){
        jabber.quit()
      },
      scope: this
      }],
      items: [
          new Ext.grid.GridPanel({
              store: rosterStore,
              autoHeight: true,
              columns: [
                {id: 'jid', dataIndex: 'jid',
                  renderer: function (value, p, record) {
                    var tpl = new Ext.XTemplate(
                      '{jid}',
                      '<tpl if="presence || status">',
                        '<br/><span style="font-size:x-small;">',
                        '{presence}',
                        '<tpl if="presence &amp;&amp; status">',
                          ':',
                        '</tpl>',
                        '{status}',
                        '</span>',
                      '</tpl>'
                    );
                    return tpl.applyTemplate(record.data);
                }},
                {dataIndex: 'group', hidden: true},
                {dataIndex: 'presence', hidden: true},
                {dataIndex: 'subscription', hidden: true},
                {dataIndex: 'status', hidden: true}
              ],
              view: new Ext.grid.GroupingView({
                forceFit: true,
                showGroupName: false,
                groupTextTpl: '{text} ({[values.rs.length]} {[values.rs.length > 1 ? "Buddies" : "Buddy"]})'
              }),
              frame: false,
              cls: 'blist-grid',
              listeners: {
                rowdblclick: function() {
                    var buddy = this.getSelectionModel().getSelected().data;
                    yakalope.app.createNewChatWindow(buddy.jid);
                }
              },
              tbar: [new Ext.form.ComboBox({
                  id: 'presence',
                  //name: 'presence',                  
                  width: 70,
                  store: new Ext.data.SimpleStore({
                    fields: ['presence', 'readablePresence'],
                    data: [
                      ['', 'Available'],
                      ['away', 'Away'],
                      ['chat', 'Chatty'],
                      ['dnd', 'Do Not Disturb']/*,
                      ['unavailable', 'Offline']*/
                    ],
                  }),
                  displayField: 'readablePresence',
                  valueField: 'presence',
                  mode: 'local',
                  forceSelection: true,
                  triggerAction: 'all',
                  listeners: {
                    render: function (combo) {
                      combo.setValue(combo.store.collect('presence', true)[0]);
                    },
                    select: function (combo) {
                      var status = Ext.getCmp('status').getValue();
                      jabber.setPresence(combo.getValue(), status);
                    }
                  }
                }), ' ',
                new Ext.form.ComboBox({
                  id: 'status',
                  emptyText: 'Set status...',
                  hideTrigger: true, // Temporary until we save previous status messages
                  store: new Ext.data.SimpleStore({
                    fields: ['status'],
                    data: [] // TODO: This will store previous status messages
                  }),
                  displayField: 'status',
                  mode: 'local',
                  width: 145,
                  queryDelay: 500,
                  hideLabel: true,
                  listeners: {
                    beforequery: function (q) {
                      var presence = Ext.getCmp('presence').getValue();
                      jabber.setPresence(presence, q.query);
                    }
                  }
                })]
            })]
    });
    BuddyList.superclass.initComponent.apply(this, arguments);
    //Ext.getCmp('presence').selectFirst();
  }  
});

Ext.reg('buddylist', BuddyList);
