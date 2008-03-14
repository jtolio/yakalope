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
        var node = this.getTreeRoot().firstChild;
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
            alert(node.text);
            if (node.text == userName) {
                alert(userName + " found");
                return true;
            } else {
                node = node.nextSibling;
            }
        }
        alert(userName + " not found");
        return false;
    },
    initComponent: function() {
        Ext.apply(this,{
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
