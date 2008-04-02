Ext.BLANK_IMAGE_URL = "extjs/resources/images/default/s.gif"


Ext.namespace('yakalope');
    
yakalope.app = function () {
    var viewport;
    return {
        getViewport: function() {
            return viewport;
        },
        getChatArea: function () {
            return viewport.items.get('chatarea');
        },
        getBuddyList: function() {
            return viewport.items.get('buddylist');
        },
        init: function() {

		var LoginWindow = new Ext.Window({
			title: 'Welcome to Yakalope or BlabLab or something...',
                        width: 300,
                        modal: true,
                        items: new Ext.FormPanel({
                            labelWidth:75,
                            frame:true,
                            defaultType:'textfield',
                            items:[{
                                fieldLabel:'Username',
                                name:'username',
                                allowBlank:false,
                            },{
                                fieldLabel:'Password',
                                name:'password',
                                allowBlank:false,
                                InputType: 'password'
                            }],
                        }),
                        buttons: [{
                            id: 'login',
                            text: 'login'
                        }]
                });
           
                LoginWindow.show();
            
            jabber.init();
                
            /* Setup Layout of Main Window */
    
            viewport = new Ext.Viewport({
            layout: 'border',
            items:
            [{ 
                /* Chat Area */
                
                xtype:'panel',
                region:'center',
                margins:'10 0 0 0',
                id:'chatarea',
                key:'chatarea',
                dd:true,
                autoScroll:true,
           
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

            },{
                region:'south',
                buttons:[{
                    text:'Connect',
                    id:'connect',
                    handler:jabber.doLogin,
                },{
                    text:'Disconnect',
                    id:'disconnect',
                    handler:jabber.quit,
                }]
            }]
            
            /* End Main Layout */

            });
        },
        getUser: function() {
            return "test_user";
        },
        createNewChatWindow: function(chatId) {
            if (!Ext.get(chatId)) {
                var chatArea = yakalope.app.getChatArea();
                var newChat = new ChatWindow({
                    id:chatId,
                    title:chatId,
                    hidden:false,
                    key:chatId,
                    user:this.getUser(),
                });
                newChat.show(this);// = chatArea.add(newChat);
                //viewport.doLayout();
                return newChat;
            }
            return null;
        },
        removeChatWindow: function(chatId) {
            var chatArea = yakalope.app.getChatArea();
            chatArea.remove(chatId, true);
        },
        addMsg: function(chatId, msg) {
            var chatWindow = Ext.getCmp(chatId);
            if (chatWindow) {
                chatWindow.addMsg(chatId, msg);
            } else {
                var newChatWindow = yakalope.app.createNewChatWindow(chatId);
                newChatWindow.addMsg(chatId, msg);
            }
        },
        addBuddy: function(userName) {
            var buddyList = yakalope.app.getBuddyList();
            return buddyList.addBuddy(userName);
        },
        removeBuddy: function(userName){
            var buddyList = yakalope.app.getBuddyList();
            buddyList.removeBuddy(username);
        },
        clearBuddyList: function() {
            var buddyList = yakalope.app.getBuddyList();
            buddyList.clearBuddyList();
        }
    }
}();


Ext.onReady(yakalope.app.init, yakalope.app);