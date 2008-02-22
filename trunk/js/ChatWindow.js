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
    scope:this,
    height:278,
    width:300,
    autoScroll:true,
    bodyBorder:true,
    
    /* Runtime Variables */
    
    initComponent: function() {
        Ext.apply(this, {
            
            items:[{
                id:'chat ' + this.getId(),
                split: false,
                height:225,
                width:295,
                autoScroll:true,
                items: [{
                    id: 'chatpanel ' + this.getId(),
                    autoHeight:true,
                    bodyBorder:true,
                }]
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
    },
    addMsg: function(msg) {
        chatPanel = this.items.first();
        chatPanelElement = chatPanel.items.first().getEl();
        insertedElement = chatPanelElement.insertHtml('afterBegin', msg);
        return chatPanel.getEl().scroll('down', 10, true);
    },
 });
 
 Ext.reg('chatwindow', ChatWindow);