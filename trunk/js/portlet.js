/*
 * Ext JS Library 2.0.1
 * Copyright(c) 2006-2008, Ext JS, LLC.
 * licensing@extjs.com
 * 
 * http://extjs.com/license
 */

Ext.ux.Portlet = Ext.extend(Ext.Panel, {
    anchor: '100%',
    frame:true,
    collapsible:true,
    draggable:true,
    cls:'x-portlet',
    /*items:[
        new Ext.FormPanel({
            labelWidth: 75,
            frame: true,
            bodyStyle: 'padding:5px 5px 0',
            width: 350,
            defaults: {width: 230},
            defaultType: 'textField',
            items:[{
                xtype:'textfield',
                name: 'send',
                anchor: '95%'
            }]
        })
    ]*/
});
Ext.reg('portlet', Ext.ux.Portlet);      