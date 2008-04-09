%%%----------------------------------------------------------------------
%%% File    : mod_log_pipe.erl
%%% Author  : Yakalope / Tor-Helge Persett
%%% Purpose : Forward chat messages to an external logging daemon
%%% Code based on: mod_log_chat.erl - developed by Jérôme Sautret <jerome.sautret@process-one.net>
%%%----------------------------------------------------------------------
%%% Yakalope version XX
%%% For use with Ejabberd 1.2 or newer
%%% Date: March 26, 2008

%%%----------------------------------------------------------------------
%%% Overview:
%%% This module creates two (Erlang) processes - one "main" module process 
%%% and one process which is responsible for handling the connection to the
%%% external logging daemon.
%%%----------------------------------------------------------------------

-module(mod_log_pipe).
-author('yakalope@yakalope.biz').

-behaviour(gen_mod).

-export([start/2,
         init/1,initPort/3,
	 stop/1,
	 log_packet_send/3,
	 log_packet_receive/4]).

-include("ejabberd.hrl").
-include("jlib.hrl").

-define(PROCNAME, ?MODULE).
-define(LOGDAEMON_PATH, "./loggerdaemon.py").

-record(config, {daemon_path=?LOGDAEMON_PATH}).

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

	%retreive path of logging daemon (supplied with the configuration of the plugin)
	LogdaemonPath = gen_mod:get_opt(daemon_path, Opts, ?LOGDAEMON_PATH),
		    
    %register hooks for messages sent and received
    ejabberd_hooks:add(user_send_packet, Host, ?MODULE, log_packet_send, 55),
    ejabberd_hooks:add(user_receive_packet, Host, ?MODULE, log_packet_receive, 55),
    
    %spawn host process for module, and register alias for it
    register(gen_mod:get_module_proc(Host, ?PROCNAME),
    	spawn(?MODULE, init, [#config{daemon_path=LogdaemonPath}])).
    
    
%init for module host process
init(Config)->

	case Config of #config{daemon_path=LogdaemonPath} ->

		%spawn our logging pipe process which will receive messages
		%from the host module process and forward them to the external process    
		%register logloop as an alias for our logging pipe process
		register(logloop, 
			spawn(?MODULE, initPort, [LogdaemonPath, self(), none]))
			
	end,			
    loop(Config).


%message loop for main module process
loop(Config) ->
    receive
		{call, Caller, get_config} ->
			%get_config requests from Ejabberd
			Caller ! {config, Config},
			loop(Config);
	
		{restartDaemon, LogdaemonPath, Reason} ->
			%restart the process which forwards messages to the external logging daemon
			register(logloop, 
				spawn(?MODULE, initPort, [LogdaemonPath, self(), Reason])),
			loop(Config);
	
		stop ->
			%stop the module ->
			%stop the external logging daemon message loop
			logloop ! portStop,
			%exit module host process
			exit(normal)
    
    end.


initPort(ExtPrg, CallingProcess, OldTermReason) ->

    %if this process exit, then it will not exit, but a {'EXIT', FromPid, Reason}
    %message would be sent to this process instead
    process_flag(trap_exit, true),
    
    %invoke the external logger daemon and register it as an Erlang Port
    %which we can send messages to like any other Erlang process
    %packets is here configured to have a maxlength of 2^(_2_ bytes * 8 bits / byte) bytes
    Port = open_port({spawn, ExtPrg}, [{packet, 2}]),
    
    %invoke port loop
    daemonLoop(Port, ExtPrg, CallingProcess, OldTermReason).
    
    
daemonLoop(Port, ExtPrg, CallingProcess, OldTermReason) ->
    receive
    	{portCall, Msg} ->
    		%someone is calling the logging daemon
    		% - every time a message is supposed to be logged a message 
    		%   in this format is sent to the port
    		% -> forward message to the external process
    		Port ! {self(), {command, Msg}},
    		daemonLoop(Port, ExtPrg, CallingProcess, none); %reset old termination reason (if any), and continue to loop
    	portStop ->
    		%shutdown port
    		Port ! {self(), close},
    		exit(stopped);
    	{'EXIT',ExitPort,Reason} ->
    		if
    			(Port == ExitPort) and (OldTermReason /= Reason) ->
					 %our port is down.. request a restart of this process
					 %but only if this isn't the second time it terminate for 
					 %the same reason, and it hasn't been operational in the meantime
		    		 %TODO: is this the behavior we want?
		    		 CallingProcess ! {restartDaemon, ExtPrg, Reason},
		    		 ?ERROR_MSG("Lost pipe to ~s due to ~s ~n", [ExtPrg, Reason]), 
		    		 exit(Reason);
			
				true ->
					%our process has crashed... log?
					%TODO: write reason to logging daemon
					?ERROR_MSG("Pipe helper process has crashed ~n", []),
					exit(Reason)
			end
    end.

    
%method to feed text to the logging loop
feedText(Text) ->
	logloop ! {portCall, Text}.

	
%stop method - called when the module is unloaded
stop(Host) ->

	%remove hooks
    ejabberd_hooks:delete(user_send_packet, Host,
			  ?MODULE, log_packet_send, 55),
    ejabberd_hooks:delete(user_receive_packet, Host,
			  ?MODULE, log_packet_receive, 55),
			  		  
    %stop main module process
    gen_mod:get_module_proc(Host, ?PROCNAME) ! stop,
    
    ok.

log_packet_send(From, To, Packet) ->
    log_packet(From, To, Packet, From#jid.lserver).

log_packet_receive(_JID, From, To, _Packet) when From#jid.lserver == To#jid.lserver->
    ok; % only log at send time if the message is local to the server
    
log_packet_receive(_JID, From, To, Packet) ->
    log_packet(From, To, Packet, To#jid.lserver).

log_packet(From, To, Packet = {xmlelement, "message", Attrs, _Els}, Host) ->
    case xml:get_attr_s("type", Attrs) of
%	"groupchat" -> %% mod_muc_log already does it
%	    ok;
	"error" -> %% we don't log errors
	    ok;
	_ ->
	    write_packet(From, To, Packet, Host)
    end;
log_packet(_From, _To, _Packet, _Host) ->
    ok.

%write content of packet to the pipe 
write_packet(From, To, Packet, _) ->
	%extract subject and body from packet
    {Subject, Body} = {case xml:get_path_s(Packet, [{elem, "subject"}, cdata]) of
			   false ->
			       "";
			   Text ->
			       Text
		       end,
		       xml:get_path_s(Packet, [{elem, "body"}, cdata])},
	%check for an empty message - we don't care about those
    case Subject ++ Body of
        "" ->
            ok;
        _ -> 
        %this one is not empty
        %timestamp it
        DateList = case calendar:universal_time() of {{Y, M, D}, {H, Min, S}} -> [Y, M, D, H, Min, S] end,
        DateTimeStamp=io_lib:format(template(text, date), DateList),
	    %extract JIDs
	    FromJid = From#jid.luser++"@"++From#jid.lserver,
	    ToJid = To#jid.luser++"@"++To#jid.lserver,
		%feed data to the pipe
		feedText(io_lib:format(lists:flatten(template(text,everything)), [FromJid, ToJid, DateTimeStamp, Body]))
    end.

%template for one single message piped to the logging daemon
template(text, everything) ->
	"~s~n~s~n~s~n~s";
	
%template for time / date format
template(text, date) ->
    "~p-~2.2.0w-~2.2.0w ~2.2.0w:~2.2.0w:~2.2.0w".

