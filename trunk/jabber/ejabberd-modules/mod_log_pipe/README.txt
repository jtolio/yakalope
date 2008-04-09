mod_log_pipe
============

mod_log_pipe is a ejabberd chat logging module based on the mod_log_chat module.
The difference is that this deamon will forward all sent and received messages
to an external logging daemon - communicating through STDOUT

Compilation and installation
----------------------------

You need to have Erlang installed as well as the ejabberd-dev module
(checkout it in the same directory than mod_log_chat is).

- Run build.sh

- Copy generated mod_log_chat.beam file from the ebin directory to the
  directory where your ejabberd .beam files are.

- Edit the "modules" section of your ejabberd.cfg configuration file to
  suit your needs.

- Be sure that the directories where you want to create your log
  files exists and are writable by you ejabberd user.

- Restart ejabberd.
