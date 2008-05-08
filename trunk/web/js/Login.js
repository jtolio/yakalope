var Login = {
  login: function() {
    var LoginWindow = new Ext.Window({
        title: 'Welcome to Yakalope or BlabLab or something...',
        width: 300,
        modal:true,
        closable: false,
        resizable:false,
        items: new Ext.FormPanel({
            labelWidth:75,
            frame:true,
            defaultType:'textfield',
            items:[{
                fieldLabel:'Username',
                name:'username',
                allowBlank:false,
                maxLength: 128,
                maxLengthText: 'Username must be less than 128 characters',
            },{
                fieldLabel:'Password',
                name:'password',
                allowBlank:false,
                inputType:'password',
                maxLength:128,
                maxLengthText: 'Password must be less than 128 characters',
            }],
        }),         
     });
     var LoginWindowForm = LoginWindow.items.first();
     LoginWindowForm.addButton({
            text:'Login',
            name:'login',
         },
         function() {
           var values = LoginWindowForm.getForm().getValues();
           jabber.doLogin(values.username, values.password);
           yakalope.app.setUserName(values.username);
           LoginWindow.close();
         },
         LoginWindow);
                           
         LoginWindow.show(this);
    }
  }

