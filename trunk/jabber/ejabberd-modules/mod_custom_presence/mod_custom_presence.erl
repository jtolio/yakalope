%%%----------------------------------------------------------------------
%%% File    : mod_custom_presence.erl
%%% Author  : Yakalope / Tor-Helge Persett
%%% Purpose : Intercept presence packages so that a client maintains a predefined presence-status
%%%----------------------------------------------------------------------
%%% Yakalope version XX
%%% For use with Ejabberd 1.2 or newer
%%%----------------------------------------------------------------------
%%% Overview:
%%%----------------------------------------------------------------------

-module(mod_custom_presence).
-author('yakalope@yakalope.biz').

-behaviour(gen_mod).

-export([start/2,
         init/1,
	 stop/1,
	 filter_packet/1]).

-include("ejabberd.hrl").
-include("jlib.hrl").

-define(PROCNAME, ?MODULE).

start(Host, Opts) ->
    case gen_mod:get_opt(host_config, Opts, []) of
	[] ->
	    start_vh(Host, Opts);
	HostConfig ->
	    start_vhs(Host, HostConfig)
    end.


start_vhs(_, []) ->
    ok;
    
start_vhs(Host, [{Host, Opts}| Tail]) ->
    start_vh(Host, Opts),
    start_vhs(Host, Tail);
    
    
start_vhs(Host, [{_VHost, _Opts}| Tail]) ->
    start_vhs(Host, Tail).
    
    
%starting an instance of the module for a particular vhost
start_vh(Host, Opts) ->

    %register hooks for filtering packets
    ejabberd_hooks:add(filter_packet, Host, ?MODULE, filter_packet, 100).
 
filter_packet(drop) ->
	drop;
	
filter_packet({From, To, Packet}) ->

	%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
	% TODO: when a user logs on to the server we need to send that user a presence packet for each user that  %
	% are not currently logged on to yakalope, but has a predefined offline message and / or status defined.  %
	%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
	
	%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
	% TODO: check that this module works with the AIM, Yahoo, and ICQ transports. Only tested for MSN so %
	% far. For the MSN transport it was necessary to drop a error 503 packet in order to keep the        %
	% user logged on. This may be different for the other transports.                                    %
	%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
	
	%brake the packet into parts
	{xmlelement, Tag, Attrs, Els}  = Packet,
	
	%case the packet is a presence stanca, and presence type is unavailable => we should intercept
	case {From#jid.lserver, {Tag, xml:get_attr_s("type", Attrs)}} of  {Host, {"presence", "unavailable"}} ->
				   
				   	%DEBUG
					% error_logger:info_msg("Packet modified from: From:~s To:~s~n~s~n", 
					%					[From#jid.luser++"@"++From#jid.lserver, To#jid.luser++"@"++To#jid.lserver, xml:element_to_string(Packet)]),
					
					%query database for offline status and message for current user

					{selected,
						["offline_status","offline_msg"],
					
						[{StatusTemp,MsgTemp}]} = ejabberd_odbc:sql_query(From#jid.lserver, 
													"select offline_status, offline_msg from users where username='"++ejabberd_odbc:escape(From#jid.luser)++"';"),%
					%remove nulls
					Status = case StatusTemp of null ->
								"";
								_ ->
								StatusTemp
						     end,
					Msg = case MsgTemp of null ->
								"";
								_ ->
								MsgTemp
						  end,
					
					%if the status is null, we should not interfer at all
					%forward the original Packet			
					case Status of "" ->
							{From, To, Packet};
						_ ->
							%user has a predefined status message and status
							%generate new presence xml stanza						
							NewPacket = {xmlelement, "presence", [], [ 
																		{xmlelement, "priority", [], [{xmlcdata, "50"}]}, %pick a number ;)
																		{xmlelement, "show", [], [{xmlcdata, Status}]}, 
																	   	{xmlelement, "status", [], [{xmlcdata, Msg}]}										   
																	   ]},

							%DEBUG																	   
							%error_logger:info_msg("Packet modified to: From:~s To:~s~n~s~n", 
							%					[From#jid.luser++"@"++From#jid.lserver, To#jid.luser++"@"++To#jid.lserver, xml:element_to_string(NewPacket)]),
							
							%return new packet					
							{From, To, NewPacket}
							
						end;
		
		    	_ ->
		    	
					%When a message is relayed from the msn tranport to a jabber contact who are currently offline
					%the server will respond with an error message - we need to drop this message to ensure that the
					%user still remains at his / her status
		    		case {From#jid.server, xml:get_path_s(Packet, [{elem, "error"}, {attr, "code"}])} of {"localhost", "503"} ->

						%error_logger:info_msg("Packet dropped: From:~s To:~s~n~s~n", 
						%					[From#jid.luser++"@"++From#jid.lserver, To#jid.luser++"@"++To#jid.lserver, xml:element_to_string(Packet)]),
		    			drop;

		    			_->		    	
			    		%error_logger:info_msg("Packet: From:~s To:~s~n~s~n", 
			    		%					[From#jid.luser++"@"++From#jid.lserver, To#jid.luser++"@"++To#jid.lserver, xml:element_to_string({xmlelement, Tag,	Attrs, Els})]),
			    		{From, To, Packet}
			    		
			    	end
			    	
	end.    	


%stop method - called when the module is unloaded
stop(Host) ->

	%remove hooks
    ejabberd_hooks:delete(filter_packet, Host,
			  ?MODULE, filter_packet, 100),
			  		  
    %stop main module process
   % gen_mod:get_module_proc(Host, ?PROCNAME) ! stop,
    
    ok.
