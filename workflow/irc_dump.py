#!/usr/bin/python

import trac.env
import optparse
import os
import re

DEFAULT_TRAC_ENV = "/project/trac/newProject"

p = optparse.OptionParser("usage: %prog commitnumber")
opt, args = p.parse_args()
if len(args) != 1:
  p.error("Incorrect number of arguments")

repos = trac.env.open_environment(DEFAULT_TRAC_ENV).get_repository()
repos.sync()
changeset = repos.get_changeset(int(args[0]))

short_desc = changeset.message.strip()
author = changeset.author.strip()
url = "https://squall.cs.umn.edu/trac/newProject/changeset/" + args[0]

#replacing newlines with ' <n> '
exp = re.compile('(\n)')
short_desc = exp.sub(' <n> ', short_desc)

pid = os.fork()
if not pid:
  os.execl('/project/workflow/RndOracleSay.exp', 'Nothing', '(Yakalope)', 'SVN Commit', '(', author, ')', short_desc, '(', url, ')')

