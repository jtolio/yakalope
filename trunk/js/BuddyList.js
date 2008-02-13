/*
 * Buddy List
 */
 
 BuddyList = Ext.extend(Ext.Panel, {
    id: 'buddylist',
    title: 'Buddy List',
    width: 250,
    height: 400,
    iconCls: 'accordion',
    shim: false,
    animCollapse: true,
    layout: 'accordion',
    border: false,
    frame: true,
    layoutConfig: {
        animate: true
    },
    initComponent: function() {
        Ext.apply(this,{
           items: [
            new Ext.tree.TreePanel({
                id: 'buddytree',
                loader: new Ext.tree.TreeLoader(),
                rootVisible: false,
                lines: false,
                autoScroll: true,
                root: new Ext.tree.AsyncTreeNode({
                    text:'Online',
                    children:[{
                        text: 'Friends',
                        expanded: true,
                        children: [{
                            text:'Jack',
                            iconCls:'user',
                            leaf:true
                        },{
                            text:'Brian',
                            iconCls:'user',
                            leaf:true
                        },{
                            text:'Jon',
                            iconCls:'user',
                            leaf:true
                        }]
                        
                    }]    
                })
            }),{
                title:'Settings',
                html:'<p>Somethin useful would be in here.</p>',
                autoScroll:true
            }] 
        });
        
        BuddyList.superclass.initComponent.apply(this, arguments);
    }
    
 });
 
 Ext.reg('buddylist', BuddyList);