/*
 * Chat Window Class
 */
 
ChatWindow = Ext.extend(Ext.Panel,{
    
    /* Construction Time Variables */
    
    collapsible: true,
    frame: true,
    draggable: true,
    cls: 'x-portlet',
    layout: 'anchor',
    addMsg: function(msg) {
        var chatPanel = this.findById('chatpanel');
        chatPanel.insertHtml('beforeEnd', msg);
        chatPanel.repaint();
    }
    
    /* Runtime Variables */
    
    initComponent: function() {
        Ext.apply(this, {
            items:[{
                id:'chatpanel',
                split: false,
                offsets: '-50 -5',
                width: 150,
                height: 300,
                autoScroll: true,
            },{
                id:'chatform',
                split: false,
                xtype: 'form',
                layout: 'column',
                anchor: '100%',
                items: [{
                    columnWidth: 1,
                    frame: true,
                    xtype: 'textfield',
                    name: 'sendfield'
                }]
            }]
        },{
            tools:[{
                id: 'close',
                handler: function(e, targ, panel){
                    panel.ownerCt.remove(panel, true);
                }
            }]
        });
        
        ChatWindow.superclass.initComponent.apply(this, arguments);
    }
 });
 
 Ext.reg('chatwindow', ChatWindow);