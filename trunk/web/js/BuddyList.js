/*
 * Buddy List
 */

var roster = {
  buddies: [],
  update: function (buddy) {
    for (var i=0, il=this.buddies.length; i<il; i++) {
      if (this.buddies[i].compareTo(buddy)) {
        this.buddies[i].update(buddy);
        rosterStore.load();
        return;
      }
    }
    this.buddies.push(buddy);    
    rosterStore.load();
  },
  setPresence: function (jid, presence, status, type) {
    for (var i=0, il=this.buddies.length; i<il; i++) {
      if (this.buddies[i].jid.toString() == jid.toString()) {
        this.buddies[i].presence = presence;
        this.buddies[i].status = status;
        this.buddies[i].type = type;
      }
    }
    rosterStore.load();
  },
  clear: function () {
    this.buddies = new Array();
    rosterStore.load();
  }
}

var rosterStore = new Ext.data.GroupingStore({
  id: 'rosterStore',
  proxy: new Ext.data.MemoryProxy(roster),
  reader: new Ext.data.JsonReader({
    root: 'buddies',
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
  layout: 'accordion',
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
      items: [{
          title: 'Buddies',
          defaults: {border: false},
          items: [ new Ext.grid.GridPanel({
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
              }
            })]
        }, /*{
        title: 'Settings',
        html: '<p>Something userful would be in here.</p>',
      }*/]
    });
    BuddyList.superclass.initComponent.apply(this, arguments);
  }  
});

Ext.reg('buddylist', BuddyList);
