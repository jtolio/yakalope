%%%----------------------------------------------------------------------
%%% File    : mod_roster.hrl
%%% Author  : Alexey Shchepin <alexey@sevcom.net>
%%% Purpose : Roster management
%%% Created :  5 Mar 2005 by Alexey Shchepin <alexey@sevcom.net>
%%% Id      : $Id: mod_roster.hrl 412 2007-11-15 10:10:09Z mremond $
%%%----------------------------------------------------------------------

-record(roster, {usj,
		 us,
		 jid,
		 name = "",
		 subscription = none,
		 ask = none,
		 groups = [],
		 askmessage = [],
		 xs = []}).

