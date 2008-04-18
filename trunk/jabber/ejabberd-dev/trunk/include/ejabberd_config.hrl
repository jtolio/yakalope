%%%----------------------------------------------------------------------
%%% File    : ejabberd_config.hrl
%%% Author  : Mickael Remond <mickael.remond@process-one.net>
%%% Purpose : ejabberd configuration internal data structures.
%%% Created : 5 Nov 2007 by Mickael Remond <mickael.remond@process-one.net>
%%% Id      : $Id: ejabberd_config.hrl 412 2007-11-15 10:10:09Z mremond $
%%%----------------------------------------------------------------------

-record(config, {key, value}).
-record(local_config, {key, value}).
-record(state, {opts = [],
		hosts = [],
		override_local = false,
		override_global = false,
		override_acls = false}).
