/*
 * Search
 */

var store = new Ext.data.JsonStore({
		url: 'http://mylocaldjangoserver/recent',
		root: 'data',
		id: 'id',
		fields: ['id']
	});
	store.on('loadexception', function(proxy, store, response, e) {
		alert('loadexception: ' + e.message);
});
 
LogWin = Ext.extend(Ext.Panel, {
  id: 'logwin',
  split: true,
  width: 225,
  minSize: 150,
  maxSize: 400,
  collapsible: true,
  rootVisible: false,
  lines: false,
  layout: 'accordion',
  defaults: {
  border: false
  },
  layoutConfig: {
    animate: true
  },
  initComponent: function(){
    Ext.apply(this, {
      tbar: [
		 new Ext.app.SearchField({
		 	id: 'search_field',
			width: 150,
            store: store,
            paramName: 'search'
	  }), {
        text: 'Search',
        id: 'search_button',
        handler: function(){
			alert(Ext.getCmp('search_field').getValue());
		},
        scope: this
      }],
    });
    LogWin.superclass.initComponent.apply(this, arguments);
  }  
});

Ext.reg('logwin', LogWin);