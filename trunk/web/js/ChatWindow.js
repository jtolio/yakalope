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
            this.addMsg(this.user, chatMessage + '<br>');
            //Send Message to Jabber Connection
            jabber.sendMsg(this.getId(), chatMessage);
        }
        msgArea.focus();
    },
    initComponent: function() {
        Ext.apply(this, {
            items: [{
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
                anchor:'100%'
            }],
            keys:{
                key:[10, 13],
                fn:this.sendHandler,
                scope:this
            },
        });
        ChatWindow.superclass.initComponent.apply(this, arguments);
    },
    render: function() {
        /*
         * Set up chat, chatStore, and dataview 
         * objects for use in the window
         */
        var chatId = 'chat' + this.getId();
        var chatStoreId = 'chatStore' + this.getId();
        var chat =  {
            id:chatId,
            msgs:[],
            update: function(msg, scope) {
                this.msgs.push(msg);
                scope.chatStore.load();
            },
            clear: function(scope) {
                this.msgs = new Array();
                scope.chatStore.load();
            }
        };
        var chatStore = new Ext.data.Store({
            id:chatStoreId,
            proxy: new Ext.data.MemoryProxy(chat),
            reader: new Ext.data.JsonReader({
                root:'msgs'},
            [
               {name: 'username'},
               {name: 'msg'}
            ]),
            listeners: {
                loadexception: function (o, responce, e, exception) {
                    Ext.MessageBox.alert('Error', exception);
                }
            }
        });
        var dataview = new Ext.DataView({
            id:'chatview' + this.getId(),
            layout:'fit',
            height:270,
            width:250,
            store:chatStore,
            cls:'chatview',
            tpl: new Ext.XTemplate(
            '<tpl for=".">',
            '<div class="msg"><b>{username}</b>: {msg}</div>',
            '</tpl>'),
            itemSelector:'div.msg'
        });
        
        this.chat = chat;
        this.chatStore = chatStore;
        this.items.insert(0, dataview.id, dataview);
        ChatWindow.superclass.render.apply(this, arguments);
    },
    addMsg:function(userName, msg) {
        var chat = Ext.getCmp(this.getId()).chat;
        var msg = {
            username: userName,
            msg: msg
        };
        chat.update(msg, this);
    }
 });
 
 Ext.reg('chatwindow', ChatWindow);
