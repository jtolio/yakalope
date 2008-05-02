/*
 * Search
 */

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
  onClick: function(node){
    yakalope.app.createNewChatWindow(node.text);
  },
  getTreeRoot: function(){
    return this.items.first().root;
  },
  getTreePane: function(){
    return this.items.first();
  },
  initComponent: function(){
    Ext.apply(this, {
      tbar: [
		 new Ext.app.SearchField({
		 	id: 'search_field',
			width: 100,
            //store: store,
            paramName: 'search'
	  })],
      items: [{
          title: 'Search Results',
          defaults: {border: false},
          /*items: [ new Ext.grid.GridPanel({
              store: rosterStore,
              autoHeight: true,
              columns: [
               {id: 'jid', dataIndex: 'jid',
                  renderer: function (value, p, record) {
                    return String.format('{0}<br><span style="font-size:x-small;"><em>{1}</em>:{2}</span>',
                      value, record.data.presence, record.data.status);
                }},
                {dataIndex: 'group', hidden: true},
                {dataIndex: 'presence', hidden: true},
                {dataIndex: 'subscription', hidden: true},
                {dataIndex: 'status', hidden: true}
              ],
              view: new Ext.grid.GroupingView({
                forceFit: true,
                showGroupName: false,
                groupTextTpl: '{text} ({[values.rs.length]} {[values.rs.length > 1 ? "Buddies" : "Buddy"]})'
              }),
              frame: false,
              cls: 'blist-grid',
              listeners: {
                rowdblclick: function() {
                    var buddy = this.getSelectionModel().getSelected().data;
                    yakalope.app.createNewChatWindow(buddy.jid);
                }
              }
            })]*/
        }]
    });
    LogWin.superclass.initComponent.apply(this, arguments);
  }  
});

Ext.reg('logwin', LogWin);