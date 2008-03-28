/*
 * Buddy List
 */
 
 BuddyList = Ext.extend(Ext.Panel, {
    id: 'buddylist',
    shim: true,
    iconCls:'accordion',
    width:200,
    frame:true,
    animCollapse: true,
    layout: 'accordion',
    border: false,
    frame: true,
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
    addBuddy: function(userName) {
        var friendRoot = this.getTreeRoot().firstChild;
        if (!this.containsBuddy(userName)) {
            var newBuddy = new Ext.tree.AsyncTreeNode({
                text:userName,
                iconCls:'user',
                leaf:true, 
            });
            newBuddy.on('click', this.onClick);
            return friendRoot.appendChild(newBuddy);
        }
        return null;
    },
    removeBuddy: function(userName) {
        var tree = this.getTreeRoot();
        var node = tree.firstChild.firstChild;
        while (node != null) {
            if (node.text == userName) {
                node.remove();
                break;
            }
            node = node.nextSibling;
        }
    },
    containsBuddy: function(userName) {
        var tree = this.getTreeRoot();
        var node = tree.firstChild;
        node = node.firstChild;
        while (node != null) {
            if (node.text == userName) {
                return true;
            } else {
                node = node.nextSibling;
            }
        }
        return false;
    },
    callAddBuddy: function(btn, username) {
        var scope = yakalope.app.getBuddyList();
        scope.addBuddy(username);
    },
    callRemoveBuddy: function(btn, username) {
        var scope = yakalope.app.getBuddyList();
        scope.removeBuddy(username);
    },
    addBuddyDlg: function() {
        var window = new Ext.Window({
            id:'add a buddy',
            layout:'fit',
            width:'200',
            height:'300',
            bodyStyle:'padding:5px 5px 0',
            closeAction:'hide',
            plain:false,
            frame:true,
            items: new Ext.FormPanel({
                labelWidth:75,
                frame:false,
                defaultType:'textfield',
                items:[{
                    fieldLabel:'Buddy Name',
                    name:'username',
                    allowBlank:false,
                },{
                    fieldLabel:'Transport',
                    name:'transport',
                    allowBlank:false,
                }]
            }),
            buttons: [{
                text:'submit',
                handler:this.callAddBuddy
            }],
        });
        window.show(this);
    },
    removeBuddyDlg: function() {
        Ext.MessageBox.prompt('remove a buddy', 'Enter a Buddy to Remove', this.callRemoveBuddy);
    },
    initComponent: function() {
        Ext.apply(this,{
            buttons: [{
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
