Ext.BLANK_IMAGE_URL = "extjs/resources/images/default/s.gif"

function setupCon(connection) {
    connection.registerHandler
}

function initConnection() {
    oDbg = function(){};
    oDbg.log = function(){};
    connection = new JSJaCHttpBindingConnection({'oDbg':oDbg});
}

Ext.namespace('yakalope');
    
yakalope.app = function () {
    initConnection();
    return {
        init:function() {
    
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
                    width: 320,
                    style: 'padding:10px 10px 10px 10px',
                    items:[{
                        title: 'Chat > Buddy 1',
                        id:'chat1'
                    },{
                        title: 'Chat > Buddy 2',
                        id:'chat2'
                    }]
                },{
                    width: 320,
                    style: 'padding:10px 10px 10px 10px',
                    items: [{
                        title:'Chat > Buddy 3',
                        id:'chat3'
                    }]
                }]
                
                /* End Chat Area */
            
            },{
                                
                /* Buddy Window */
                
                region:'east',
                id:'buddylist',
                title:'Buddy List',
                margins:'10 0 0 0',
                cmargins: '10 0 0 0',
                xtype:'buddylist'

                /* End Buddy Window */ 

            }]
            
            /* End Main Layout */

            });
        }
    }
}();


Ext.onReady(yakalope.app.init, yakalope.app);