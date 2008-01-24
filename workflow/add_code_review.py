#!/usr/bin/python
"""
JT's AddCodeReview script version .1
Written by JT Olds (jtolds.com) for Chipmark (chipmark.com)
Based heavily on csv2trac.py written by Felix Collins.
csv2trac.py was based heavily on sourceforge2trac.py.

Permission granted by Felix Collins to redistribute however I'd like, so this
code is being placed in the public domain.

TODO(jtolds): rewrite to use the Trac ticket API instead of writing directly to
              the database.
"""

import trac.env
from trac.ticket import Ticket
import time
import optparse

DEFAULT_TRAC_ENV = "/project/trac/newProject"
CC_EMAIL_ADDRESS = ""
DEFAULT_TICKET_PRIORITY = "minor"
MAX_SUMMARY_LEN = 60

def AddCodeReview(commit_number, env=DEFAULT_TRAC_ENV):
    commit_number=int(commit_number)
    
    env = trac.env.open_environment(env)
    repos = env.get_repository()
    repos.sync()
    changeset = repos.get_changeset(commit_number)
    
    short_desc = changeset.message.strip()
    author = changeset.author.strip()
    if len(short_desc) == 0:
      short_desc = "commit [%d] had no summary!" % commit_number
    if len(author) == 0:
      author = "somebody"
      
    newTicket = Ticket(env)
    newTicket.populate({ "type": "code_review",
                         "priority": DEFAULT_TICKET_PRIORITY,
                         "cc": CC_EMAIL_ADDRESS,
                         "status": "new",
                         "component": "other",
                         "reporter": author,
                         "owner": "somebody",
                         "version": "",
                         "summary": "Code Review: %s [%d]" %
                              (short_desc[:MAX_SUMMARY_LEN], commit_number),
                         "description": "''Code review for commit [%d] by %s "
                                  "''\n\n%s\n\n''Make sure that this code has "
                                  "unit tests! ''" %
                                  (commit_number, author, short_desc),
                         "keywords": "codereview",
                       })
    newTicket.insert()


def main():
    p = optparse.OptionParser("usage: %prog commitnumber [/path/to/trac]")
    opt, args = p.parse_args()
    if len(args) == 1:
      AddCodeReview(args[0])    
    elif len(args) == 2:
      AddCodeReview(args[0], args[1])
    else:
      p.error("Incorrect number of arguments")


if __name__ == '__main__':
  main()
