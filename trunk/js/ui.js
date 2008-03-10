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
        createNewChatWindow: function(chatId) {
            if (!Ext.get(chatId)) {
                var chatArea = yakalope.app.getChatArea();
                var newChat = new ChatWindow({
                    id:chatId,
                    title:chatId,
                    hidden:false,
                    key:chatId,
                });
                newChat = chatArea.add(newChat);
                viewport.doLayout();
                return newChat;
            }
            return null;
        },
        addBuddy: function(userName) {
            var buddyList = yakalope.app.getBuddyList();
            return buddyList.addBuddy(userName);
        },
        removeChatWindow: function(chatId) {
            var chatArea = yakalope.app.getChatArea();
            chatArea.remove(chatId, true);
        },  
    }
}();


Ext.onReady(yakalope.app.init, yakalope.app);
