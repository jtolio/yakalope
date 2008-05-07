/*
 * Search
 */


var store1 = new Ext.data.JsonStore({
	url: 'https://squall.cs.umn.edu/yakalope/search',
	root: 'data',
	fields: ['idnum']
});
store1.on('loadexception', function(proxy, store, response, e) {
	alert('loadexception: ' + e.message);
});

var store2 = new Ext.data.JsonStore({
	url: 'https://squall.cs.umn.edu/yakalope/login',
	root: 'type',
	fields: ['type']
});

store2.on('loadexception', function(proxy, store, response, e) {
	alert('loadexception: ' + e.message);
});

  //store.load(login function)
  //store.load(search )
  
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
            store: store1,
            paramName: 'search'
	  }), {
        text: 'Search',
        id: 'search_button',
        handler: function(){
			//store2.load({params: {username: jabber.u_n + "@squall.cs.umn.edu", password: jabber.p_w}})
			//alert(Ext.getCmp('search_field').getValue());
			alert(jabber.u_n + "squall.cs.umn.edu" + " " + jabber.p_w);
		},
        scope: this
      }],
	  /*items:[
	  	new Ext.grid.GridPanel({
		    store: store1,
			height: 350,
			loadMask: {msg: 'Loading...'},
		    columns: [{id:'chat_msg', header: "Title", width: 300, dataIndex: 'idnum', sortable: false}]
    })]*/
    });
    LogWin.superclass.initComponent.apply(this, arguments);
  }  
});

Ext.reg('logwin', LogWin);


