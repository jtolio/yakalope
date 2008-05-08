%%%----------------------------------------------------------------------
%%% File    : mod_custom_presence.erl
%%% Author  : Yakalope / Tor-Helge Persett
%%% Purpose : Intercept presence packages so that a client maintains a predefined presence-status
%%%----------------------------------------------------------------------
%%% Yakalope beta
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
	 filter_packet/1,
	 hostInfoLoop/1]).

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
start_vh(Host, _) ->

    %register hooks for filtering packets
    ejabberd_hooks:add(filter_packet, global, ?MODULE, filter_packet, 100),
    
    %spawn host process for module, and register aliases for it
    register(gen_mod:get_module_proc(Host, ?PROCNAME), spawn(?MODULE, init, [config])),
    	
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % WARNING! _Hack_ to make the (V)Hostname of the server running visible in       %
    % the "filter packet" function  												 %
    % Hostname name is cruicial when picking what presence packets to filter 		 %
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    register(hostInfoProcess, spawn(?MODULE, hostInfoLoop, [Host])).
 
 %Message loop for the "Hostname" process
 hostInfoLoop(Host) ->
 	receive
 		{get_host, Callback} -> 
 			Callback ! {host, Host},
 			hostInfoLoop(Host);
 		stop ->
 			exit(normal)
 	end.
 
%%%%%%%%%%%%%%%%%
%Packet filtering
%%%%%%%%%%%%%%%%%
filter_packet(drop) ->
	drop;
	
filter_packet({From, To, Packet}) ->
 
	%brake the packet into parts
	{xmlelement, Tag, Attrs, _}  = Packet,
	
	
	case {From#jid.lserver, {Tag, xml:get_attr_s("type", Attrs)}} of  
	
				% If the packet is a presence stanca, and presence type is unavailable => we should intercept
				{FromHost, {"presence", "unavailable"}} ->
				   
				   	% retrieve Host information from hostname information process
					Host = getHost(),
					case Host of FromHost ->
				
						% this is an unavailable presence packet which is sent from a Yakalope user
						% => check if modification is necessary
						processUnavailablePresence({From, To, Packet});
				
						_ ->
					
						%this presence packet is not from a yakalope user
						{From, To, Packet}
					
					end;
	
				% If the packet is a presence probe we should check if it is directed to a yakalope user
				% and if it is, create a new presence stanca based on the recepients yakalope offline message and status
				{_, {"presence", "probe"}} ->
				
					Host = getHost(),
					case To#jid.lserver of Host  ->
				
						% this is a probe directed to a yakalope user - process it
						processPresenceProbe({From, To, Packet, Host});
				
						_ ->

						% DEBUG
						% error_logger:info_msg("Packet: From:~s To:~s~n~s~n", 
			    		%					[From#jid.luser++"@"++From#jid.lserver, To#jid.luser++"@"++To#jid.lserver, xml:element_to_string(Packet)]),

						% this probe is not directed to a yakalope user - let through
						{From, To, Packet}
					
					end;
				
		    	_ ->
		    	
		    		% If it's not a presence stanca we have a couple of hacky special cases to take care of:
		    		
					% When a message / message composing information is relayed from the msn tranport to a jabber contact who are currently offline
					% the server will respond with an error message - we need to drop this message to ensure that the
					% user still remains at his / her status
					
		    		case {From#jid.server, xml:get_path_s(Packet, [{elem, "error"}, {attr, "code"}])} of {"localhost", "503"} ->

						% DEBUG
						% error_logger:info_msg("Packet dropped: From:~s To:~s~n~s~n", 
						%					[From#jid.luser++"@"++From#jid.lserver, To#jid.luser++"@"++To#jid.lserver, xml:element_to_string(Packet)]),
		    			
		    			drop;

		    			_->		    	
			    		
			    		% DEBUG
			    		% error_logger:info_msg("Packet: From:~s To:~s~n~s~n", 
			    		%					[From#jid.luser++"@"++From#jid.lserver, To#jid.luser++"@"++To#jid.lserver, xml:element_to_string({xmlelement, Tag,	Attrs, Els})]),
			    		{From, To, Packet}
			    		
			    	end
			    	
	end.

% Function for processing presence stancas of type=probe
% check if to-user is online - if not, pull up offline status from database
processPresenceProbe({From, To, Packet, Host}) ->

	% Walk through the current Ejabberd session list, and detect if the recepient
	% of this presence probe is online
	IsToUserOnline = (length(
							lists:filter(		
											fun
												({User, UserHost, _}) when ((User==To#jid.luser) and (UserHost==To#jid.lserver)) ->
												 	true;
												( _ ) ->
													false
											end,
											ejabberd_sm:get_vh_session_list(Host) 
										)
							) > 0),
	% Note:
	% ejabberd_sm:get_vh_session_list returns a list in the following format: [{User, Host, Resource}|....]	
	
	case IsToUserOnline of 
		true ->
			% User is online - let the presence probe through
			{From, To, Packet};
		_ ->
			% User is offline - return offline messsage / status
			processUnavailablePresence({To, From, Packet})
	end.


% helper method for retreiving virtual running host
getHost() ->
	% retrieve Host information from module host proc
	hostInfoProcess ! {get_host, self()},
	receive 
		{host, TempHost} ->
				TempHost
	end.

% Function for processing presence packets of type=unavailable
% The presence packet is modified to reflect a users
% offline message and / or offline status.
% If the user has no status / message defined
% the message is returned untouched.
processUnavailablePresence({From, To, Packet}) ->
	
   	% DEBUG
	% error_logger:info_msg("Packet modified from: From:~s To:~s~n~s~n", 
	%					[From#jid.luser++"@"++From#jid.lserver, To#jid.luser++"@"++To#jid.lserver, xml:element_to_string(Packet)]),

	% query database for offline status and message for current user
	{selected,
		["offline_status","offline_msg"],
		[{StatusTemp,MsgTemp}]} = ejabberd_odbc:sql_query(From#jid.lserver, 
									"select offline_status, offline_msg from users where username='"++ejabberd_odbc:escape(From#jid.luser)++"';"),%

	% remove nulls
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

	% if the status is null, we should not interfer at all
	% return the original Packet			
	case Status of 
		"" ->
			{From, To, Packet};
		_ ->
			% user has a predefined status message and status
			% generate new presence xml stanza
			% but add old content of presence stanca as well (ie. everything contained within <presence></presence>)
	
			{xmlelement, _, _ , Els}  = Packet,
			NewPacket = {xmlelement, "presence", [], [ 
														{xmlelement, "priority", [], [{xmlcdata, "50"}]}, %pick a number ;)
														{xmlelement, "show", [], [{xmlcdata, Status}]}, 
													   	{xmlelement, "status", [], [{xmlcdata, Msg}]} | Els									   
													   ]},

			%DEBUG																	   
			%error_logger:info_msg("Packet modified to: From:~s To:~s~n~s~n", 
			%					[From#jid.luser++"@"++From#jid.lserver, To#jid.luser++"@"++To#jid.lserver, xml:element_to_string(NewPacket)]),
		
			%return new packet					
			{From, To, NewPacket}
		
	end.

% init for module host process
init(Config) ->	
    loop(Config).


% message loop for main module process
loop(Config) ->
    receive
		{call, Caller, get_config} ->
			% get_config requests from Ejabberd
			Caller ! {config, Config},
			loop(Config);
	
		stop ->
			% exit module host process
			exit(normal)
    
    end.
    
% stop function - called when the module is unloaded
stop(Host) ->

	%remove hooks
    ejabberd_hooks:delete(filter_packet, Host,
			  ?MODULE, filter_packet, 100),
			  		  
    %stop main module process
    gen_mod:get_module_proc(Host, ?PROCNAME) ! stop,
    
    %stop host name process
    hostInfoProcess ! stop,
    
    ok.
