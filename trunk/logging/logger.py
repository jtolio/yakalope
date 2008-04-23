"""
  The purpose of this script is to act as an interface between the
  python logging module and the jabber log module. It takes in data
  in the form of "Data Packets" which contain 4 message fields with
  corresponding values.

   Data Packet format:
  +-------+--------------------+-----------------------------------+
  | Bytes | Type               | Description                       |
  +=======+====================+===================================+
  | 0 - 1 | Short (Big Endian) | Length of remaning packet data    |
  +-------+--------------------+-----------------------------------+
  | 2 - n | String             | Message information:              |
  |       |                    |                                   |
  |       |                    | [FROM]@[PROTOCOL].[HOSTNAME]      |
  |       |                    | [TO]@[PROTOCOL].[HOSTNAME]        |
  |       |                    | [TIME (GMT): YYYY-MM-DD HH:MM:SS] |
  |       |                    | [HTML FORMATTED MESSAGE]          |
  +-------+--------------------+-----------------------------------+

  The script accepts 3 arguments, the first being the location of
  the log data directory, the second the location of the log index
  directory, and the third being the hostname identifier of our
  users. One example of a hostname identifier would be
  "squall.cs.umn.edu" where our service users would be something
  like testuser@squall.cs.umn.edu
"""

import logmodule
import time
import calendar
import os
import sys


#Deal with command line arguments
if len(sys.argv) != 4:
    print "Usage:",sys.argv[0],"[data directory]","[index directory]",
    print "[hostname]"
else:
    #Prepare the logger module
    logmod = logmodule.LogModule();
    logmod.setDataDirectory(sys.argv[1])
    logmod.setIndexDirectory(sys.argv[2])
    hostname = sys.argv[3]


    while True:
        #Get the length of the incoming packet
        length_chunk = sys.stdin.read(2)
        if len(length_chunk) < 2:
            break
        mlength = ord(length_chunk[1]) + (ord(length_chunk[0]) << 8)

        data_chunk = sys.stdin.read(mlength)

        #Get the fields from the chunk
        raw_chunk = data_chunk.split("\n",3)
        raw_from = raw_chunk[0]
        raw_to = raw_chunk[1]
        raw_time = raw_chunk[2]
        raw_text = raw_chunk[3]

        #Process the fields
        to_parts = raw_to.rsplit("@",1)
        to_username = to_parts[0]
        if to_parts[1] == hostname:
            #username@hostname
            to_protocol = ""
        else:
            to_host_parts = to_parts[1].split(".",1)
            if len(to_host_parts) == 2:
                #username@protocol.hostname
                to_host = to_host_parts[1]
                to_protocol = to_host_parts[0]
            else:
                #unknown, treat it as one of our users
                to_host = to_parts[1]
                to_protocol = ""

        from_parts = raw_from.rsplit("@",1)
        from_username = from_parts[0]
        if from_parts[1] == hostname:
            #username@hostname
            from_protocol = ""
        else:
            from_host_parts = from_parts[1].split(".",1)
            if len(from_host_parts) == 2:
                #username@protocol.hostname
                from_host = from_host_parts[1]
                from_protocol = from_host_parts[0]
            else:
                #unknown, treat it as one of our users
                from_host = from_parts[1]
                from_protocol = ""

        #Determine the protocol to use for the conversation
        if to_protocol == "" and from_protocol == "":
            conversation_protocol = "jabber"
        elif to_protocol == "":
            conversation_protocol = from_protocol
        else:
            conversation_protocol = to_protocol

        #Convert the time to a UTC timestamp
        from_time_tuple = time.strptime(raw_time,'%Y-%m-%d %H:%M:%S')
        from_time = int(calendar.timegm(from_time_tuple))

        # If the to person was a user of our service, then log the message for
        # them. The way we determine is if no protocol is detected for that user.
        if to_protocol == "":
            logmod.addMessage(raw_to,
                              conversation_protocol,
                              from_username,
                              from_username,
                              from_time,
                              raw_text)

        # Repeat for the from user. This could cause redundancy of data if both
        # use our service, but the simplifications this provides make it worth it.
        if from_protocol == "":
            logmod.addMessage(raw_from,
                              conversation_protocol,
                              to_username,
                              from_username,
                              from_time,
                              raw_text)

        #Repeat until STDIN closes

    #End else (proper # of args given)