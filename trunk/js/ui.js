Ext.BLANK_IMAGE_URL = "../trunk/extjs/resources/images/default/s.gif"

Ext.onReady(function() {
    
    /* Setup Layout of Main Window */
    
    viewport = new Ext.Viewport({
        layout: 'border',
        items:
        [{  
            /* Log Window */
                
            region: 'west',
            id: 'logs',
            title: 'Logs',
            split: true,
            isCollapsed: false,
            width: 200,
            minSize: 175,
            maxSize: 400,
            collapsible: true,
            margins: '10 0 0 0',
            cmargins: '10 0 0 0',
            layout: 'accordion',
            layoutConfig: {
                animateConfig: true
            },
            items: [{
                html: Ext.example.shortBogusMarktup,
                title:'Navigation',
                autoScroll: true,
                border: false,
                iconCls: 'nav'
            },{
                title:'Settings',
                html: Ext.example.shortBogusMarkup,
                border: false,
                autoScroll: true,
                iconCls: 'settings'
            }]
            
            /* End Log Window */
        
        },{
        
            /* Chat Area */
            
            xtype:'portal',
            region: 'center',
            margins: '10 0 0 0',
            id: 'chatarea',
            items:[{
                width: '50%',
                style: 'padding:10px 10px 10px 10px',
                items:[{
                    title: 'Chat > Buddy 1',
                },{
                    title: 'Chat > Buddy 2',
                }]
            },{
                width: '50%',
                style: 'padding:10px 10px 10px 10px',
                items: [{
                    title:'Chat > Buddy 3',
                }]
            }]
            
            /* End Chat Area */
            
        },{
            
            /* Buddy Window */
            
            region:'east',
            id:'buddylist',
            title:'Buddy List',
            width:250,
            height:400,
            animCollapse:true,
            layout:'accordion',
            border:true,
            margins:'10 0 0 0',
            cmargins:'10 0 0 0',
            collapsible:true,
            layoutConfig:{
                animate:true
            },
            items: [
                new Ext.tree.TreePanel({
                    id:'im-tree',
                    title: 'Online Users',
                    loader: new Ext.tree.TreeLoader(),
                    rootVisible:false,
                    lines:false,
                    autoScroll:true,
                    tools:[{
                        id:'refresh',
                        on:{
                            click: function(){
                                var tree = Ext.getCmp('im-tree');
                                tree.body.mask('Loading', 'x-mask-loading');
                                tree.root.reload();
                                tree.root.collapse(true, false);
                                setTimeout(function(){ // mimic a server call
                                    tree.body.unmask();
                                    tree.root.expand(true, true);
                                }, 1000);
                            }
                        }
                    }],
                    root: new Ext.tree.AsyncTreeNode({
                        text:'Online',
                        children:[{
                            text:'Friends',
                            expanded:true,
                            children:[{
                                text:'Nikki',
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
                        },{
                            text:'Family',
                            expanded:true,
                            children:[{
                                text:'Kelly',
                                iconCls:'user-girl',
                                leaf:true
                            },{
                                text:'Sara',
                                iconCls:'user-girl',
                                leaf:true
                            },{
                                text:'Zack',
                                iconCls:'user-kid',
                                leaf:true
                            },{
                                text:'John',
                                iconCls:'user-kid',
                                leaf:true
                            }]
                        }]
                    })
                }), {
                    title: 'Settings',
                    html:'<p>Something useful would be in here.</p>',
                    autoScroll:true
                },{
                    title: 'Even More Stuff',
                    html : '<p>Something useful would be in here.</p>'
                },{
                    title: 'My Stuff',
                    html : '<p>Something useful would be in here.</p>'
                }
            ]
            /* End Buddy Window */
        
        }]
        
        /* End Main Layout */
        
    });
});