/*
 * Send Form for use in the Chat window
 */
 
var SendForm = function(config) {
    SendForm.superclass.constructor(this, {
        width: 250,
        frame: true,
        id: 'sendform',
        items: [{
            xtype: 'textfield',
            name: 'sendfield',
            anchor: '95%',
        }]
    });
}

Ext.extend(SendForm, Ext.form.FormPanel);