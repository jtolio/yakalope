/*
 * Buddy List
 */
 
 BuddyList = Ext.extend(Ext.Panel, {
    id: 'buddylist',
		split: true,
		width: 225,
		minSize: 150,
		maxSize: 400,
		//collapsible: true,
		rootVisible: false,
		lines: false,
		layout: 'accordion',
    layoutConfig: {
        animate: true
    },
    onClick: function(node) {
        yakalope.app.createNewChatWindow(node.text);
    },
    getTreeRoot: function() {
        return this.items.first().root;
    },
    getTreePane: function() {
        return this.items.first();
    },
    addBuddy: function(buddy) {
        var friendRoot = this.getTreeRoot().firstChild;
        if (!this.containsBuddy(buddy)) {
            var newBuddy = new Ext.tree.AsyncTreeNode({
                id: buddy.jid,
                text: jid.toString(),
                object: buddy,
                iconCls: 'user',
                leaf: true
            });
            newBuddy.on('click', this.onClick);
            return friendRoot.appendChild(newBuddy);
        }
        return null;
    },
    removeBuddy: function(buddy) {
        var tree = this.getTreeRoot();
        var node = tree.firstChild.firstChild;
        while (node != null) {
            if (node.id.toString() == buddy.jid.toString()) {
                node.remove();
                break;
            }
            node = node.nextSibling;
        }
    },
    clearBuddyList: function() {
        var tree = this.getTreeRoot();
        var node = tree.firstChild.firstChild;
        while (node != null) {
            nextnode = node.nextSibling;
            node.remove();
            node = nextnode;
        }
    },
    containsBuddy: function(buddy) {
        var tree = this.getTreeRoot();
        var node = tree.firstChild;
        node = node.firstChild;
        while (node != null) {
            if (node.id.toString() == buddy.jid.toString()) {
                return true;
            } else {
                node = node.nextSibling;
            }
        }
        return false;
    },
    callRemoveBuddy: function(username) {
      var scope = yakalope.app.getBuddyList();
      scope.removeBuddy(username);
  },
  addBuddyDlg: function() {
     var servicesStore = new Ext.data.SimpleStore({
      id: 'services-store',
      fields:['service', 'serviceName'],
      data: [
			  ['squall.cs.umn.edu', 'squall.cs.umn.edu']
        /*['yakalope.com', 'Yakalope'],
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
        labelWidth:50,
        frame:true,
        defaultType:'textfield',
        items:[{
          fieldLabel:'Name',
          name:'buddyname',
          allowBlank:false,
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
      text:'Add',
      name:'add',
    },
    function() {
      var values = form.getForm().getValues();
			jabber.addBuddy(new Buddy(values.buddyname + '@' + values.serviceType, 'none'));
      window.close();
    },
    window);
    form.addButton({
      text:'Cancel',
      name:'cancel',
    },
    function() {
      window.close();
    },
    window);
    window.show(this);
  },
  removeBuddyDlg: function() {
    var window = new Ext.Window({
			title: 'Remove a Buddy',
      width: 300,
      items: new Ext.FormPanel({
        labelWidth:75,
        frame:true,
        defaultType:'textfield',
        items:[{
          fieldLabel:'Buddy Name',
          name:'buddyname',
          allowBlank:false,
        },{
          fieldLabel:'Service',
          name:'service',
          allowBlank:false,
        }],
      }),
    });
    var form = window.items.first();
    form.addButton({
        text:'Remove',
        name:'remove',
      },
      function() {
        var values = form.getForm().getValues();
        yakalope.app.getBuddyList().callRemoveBuddy(values.buddyname);
        window.close();
      },
      window);
    form.addButton({
        text:'Cancel',
        name:'cancel',
      },
      function() {
        window.close();
      },
      window);
    window.show(this);
  },
  initComponent: function() {
    Ext.apply(this,{
      tbar: [{
        text:'Add Buddy',
        id:'addbuddy',
        handler:this.addBuddyDlg,
        scope:this,
      },{
        text:'Remove Buddy',
        id:'removebuddy',
        handler:this.removeBuddyDlg,
        scope:this,
      }],
      items: [
        new Ext.tree.TreePanel({
          id:'im-tree',
          title: 'Online Users',
          loader: new Ext.tree.TreeLoader(),
          rootVisible:false,
          lines:false,
          autoScroll:true,
          root: new Ext.tree.AsyncTreeNode({
            text:'Online',
            loaded:true,
            children:[{
              text:'Friends',
              expanded:true,
              children:[],
            }]
          })
        }),{
          title:'Settings',
          html:'<p>Something userful would be in here.</p>',
        }
      ]     
    });
    BuddyList.superclass.initComponent.apply(this, arguments);
  }
  
 });
 
 Ext.reg('buddylist', BuddyList);
