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
    clickHandler: function(userName) {
        alert(userName);
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
                            children:[{
                                text:'Jack',
                                iconCls:'user',
                                leaf:true,
                            },{
                                text:'Brian',
                                iconCls:'user',
                                leaf:true
                            },{
                                text:'Jon',
                                iconCls:'user',
                                leaf:true
                            },{
                                text:'Tim',
                                iconCls:'user',
                                leaf:true
                            },{
                                text:'Nige',
                                iconCls:'user',
                                leaf:true
                            },{
                                text:'Fred',
                                iconCls:'user',
                                leaf:true
                            },{
                                text:'Bob',
                                iconCls:'user',
                                leaf:true
                            }]
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