/*
 * Chat Window Class
 */


ChatWindow = Ext.extend(Ext.Window, {
    
    /* Construction Time Variables */
    
    width: 250,
    height: 350,
    iconCls: "u-tree-user-node",
    closable: false,
    constrain: true,
    border:false,
    collapsible:true,
    closable:true,
    layout:'anchor',
 
    /* Runtime Variables */
    
    sendHandler: function() {
        var msgArea = this.items.last();
        var chatMessage = msgArea.getValue();
        if (chatMessage != '') {
            msgArea.setValue('');
            //prepend username
            this.addMsg(this.user, chatMessage + '<br>');
            //Send Message to Jabber Connection
            jabber.sendMsg(this.getId(), chatMessage);
        }
        msgArea.focus();
    },
    initComponent: function() {
        Ext.apply(this, {      
            items: [{
                id:'chatpanel',
                layout:'fit',
                height:270,
                width:250,
                cls:'x-chatarea',
                anchor:'100% 82%',
                html:'hi',
            },{
                id:'msgarea',
                layout:'fit',
                height:50,
                split:true,
                hideBorders:false,
                border:false,
                xtype:'textarea',
                hideLabel:true,
                maxLength:4000,
                maxLengthText:'The maximum length text for this field is 4000',
                style:'overflow: auto;',
                anchor:'100%',
            }],
            keys:{
                key: [10, 13],
                fn: this.sendHandler,
                scope:this,
            },
        });
        ChatWindow.superclass.initComponent.apply(this, arguments);
    },
    render: function() {
        ChatWindow.superclass.render.apply(this, arguments);
    },
    addMsg:function(userName, msg) {
        var chatArea = this.items.first();
        var chatAreaElement = chatArea.getEl();
        chatAreaElement.insertHtml('beforeEnd','<b>' + userName + "</b>: " + msg);
    },
 });
 
 Ext.reg('chatwindow', ChatWindow);
