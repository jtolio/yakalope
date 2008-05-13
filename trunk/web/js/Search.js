/*
 * Search
 */

var SearchResultArray = KArray2D(0,0);

var storeSearch = new Ext.data.Store({
  id: 'storeSearch',
  proxy: new Ext.data.MemoryProxy(SearchResultArray),
  reader: new Ext.data.ArrayReader({},[
      {name: 'screenName'},
      {name: 'convo'},
  ])
});
storeSearch.load();

LogWin = Ext.extend(Ext.Panel, {
  id: 'logwin',
  split: true,
  width: 225,
  minSize: 150,
  maxSize: 400,
  collapsible: true,
  rootVisible: false,
  lines: false,
  defaults: {
  border: false
  },
  layoutConfig: {
    animate: true
  },
  initComponent: function(){
    Ext.apply(this, {
	  items:[
	    new Ext.grid.GridPanel({
  		   store: storeSearch,
           width: 225,
           columns: [
              {id:'screenName', dataIndex: 'screenName', header: 'Screen Name'},
              {                 dataIndex: 'convo',      header: 'Converstation'}
            ],
			viewConfig: {
        		forceFit: true
    		},
    		sm: new Ext.grid.RowSelectionModel({singleSelect:true})
      })],
      tbar: [
		 new Ext.app.SearchField({
		 	id: 'search_field',
			width: 150,
            //store: store1,
            paramName: 'search'
	  }), {
        text: 'Search',
        id: 'search_button',
        handler: function(){
			Ext.Ajax.request({ //ajax request configuration  
				url: 'http://squall.cs.umn.edu/yakalope/login',
				method: 'GET',
				params: {
					username: jabber.u_n,
					password: jabber.p_w
				},
				failure: function(response, options){
					//something went wrong.
					Ext.MessageBox.alert('Warning', 'Failed to contact server...');
				},
				success: function(response, options){
					var loginResponse = Ext.util.JSON.decode(response.responseText);
					var loginFlag = loginResponse.ServerStatus.type;
					
					if (loginFlag == "success"){
						Ext.Ajax.request({ //ajax request configuration  
							url: 'http://squall.cs.umn.edu/yakalope/search',
							method: 'GET',
							params: {
								searchterm: Ext.getCmp('search_field').getValue(),
							},
							failure: function(response, options){
								//something went wrong.
								Ext.MessageBox.alert('Warning', 'Failed to contact server...');
							},
							success: function(response, options){
								var searchResponse = Ext.util.JSON.decode(response.responseText);
								var searchFlag = searchResponse.ServerStatus.type;
								
								if (searchFlag == "success"){
									var messages = searchResponse.ServerStatus.data;	
									var temp_msg = "";
									SearchResultArray = KArray2D(messages.length, 2);
									alert(messages.length);
																					
									for(var i=0;i<messages.length;i++){
										for(var j=0;j<messages[i].messages.length;j++){
											temp_msg = temp_msg + messages[i].messages[j].message_text + "\n";
										}
										SearchResultArray[i][0] = 'testing';
										SearchResultArray[i][1] = temp_msg
										temp_msg = "";	
									}
									for (var i = 0; i < messages.length; i++) {
									  alert(SearchResultArray[i][0] + " iiii "+SearchResultArray[i][1]);
									}	
									//storeSearch.add(SearchResultArray);	
				                    storeSearch.load();						
								}			
							}
						}); //end ajax request
					}			
				}
			}); //end ajax request
		},
        scope: this
      }]
    });
    LogWin.superclass.initComponent.apply(this, arguments);
  }  
});

Ext.reg('logwin', LogWin);


function KArray2D(NumOfRows,NumOfCols)
{
  var k=new Array(NumOfRows);
  for (i = 0; i < k.length; ++ i)
  k [i] = new Array (NumOfCols);

  return k;
}
