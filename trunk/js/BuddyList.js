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
    addBuddy: function(userName) {
        var friendTreeNode = this.items.first().root.firstChild;
        if (!this.containsBuddy(friendTreeNode, userName)) {
            var newBuddy = new Ext.tree.AsyncTreeNode({
                text:userName,
                iconCls:'user',
                leaf:true, 
            });
            newBuddy.on('click', this.onClick);
            return friendTreeNode.appendChild(newBuddy);
        }
        return null;
    },
    containsBuddy: function(tree, userName) {
        var node = tree.firstChild;
        while (node != null) {
            if (node.text == userName) {
                return true;
            } else {
                node = node.nextSibling;
            }
        }
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
