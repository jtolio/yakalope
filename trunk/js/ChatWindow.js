/*
 * Chat Window Class
 */


ChatWindow = Ext.extend(Ext.Panel,{
    
    /* Construction Time Variables */
    
    collapsible:true,
    frame:true,
    draggable:true,
    layout:'anchor',
    height:335,
    width:310,
    autoScroll:true,
    bodyBorder:true,
    cls:'x-chatwindow',
    draggable:true,

    
    /* Runtime Variables */
    
    sendHandler: function() {
        chatForm = this.items.last();
        chatField = chatForm.items.first();
        chatMessage = chatField.getValue();
        if (chatMessage != '') {
            chatField.setValue('');
            //prepend username
<<<<<<< .mine
            this.addMsg(this.user, chatMessage + '<br>');
=======
            this.addMsg('Me: ' + chatMessage + '<br>');
>>>>>>> .r21
            //Send Message to Jabber Connection
            jabber.sendMsg(this.getId(), chatMessage);
        }
        chatField.focus();
    },
    initComponent: function() {
        Ext.apply(this, {
            
            items:[{
                id:'chat ' + this.getId(),
                border:true,
                split:false,
                height:225,
                width:295,
                autoScroll:true,
                cls:'x-chatpanel',
                items: [{
                    id:'chatpanel ' + this.getId(),
                    autoHeight:true,
                    bodyBorder:true,
                }]
            },{
                id:'chatform ' + this.getId(),
                split:false,
                xtype:'form',
                layout:'column',
                anchor:'100%',
                autoHeight:true,
                key:'chatform',
                items: [{
                    columnWidth: 1,
                    id:'chatfield',
                    frame:true,
                    xtype:'textarea',
                    height:25,
                    name:'sendfield'
                }],
                buttons: [{
                    text:'Send',
                    id:'sendbutton',
                    minWidth:35,
                    handler: this.sendHandler,
                    scope:this,
                }]
            }]
        },{
            tools:[{
                id:'close',
                handler:function(e, targ, panel){
                    panel.ownerCt.remove(panel, true);
                }
            }]
        });
        ChatWindow.superclass.initComponent.apply(this, arguments);
    },
    render: function() {
        ChatWindow.superclass.render.apply(this, arguments);
    },
    addMsg:function(userName, msg) {
        var chat = this.items.first();
        var chatPanel = chat.items.first();
        var chatPanelElement = chatPanel.getEl();
<<<<<<< .mine
        chatPanelElement.insertHtml('beforeEnd', '<b>' + userName + "</b>: " + msg);
=======
        chatPanelElement.insertHtml('beforeEnd', ' ' + msg + '<br>');
>>>>>>> .r21
    },
 });
 
 Ext.reg('chatwindow', ChatWindow);
