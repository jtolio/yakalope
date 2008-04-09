import logmodule
import time
import calendar
import os
import sys


#Perpare the logger module
logmod = logmodule.LogModule();
logmod.setDataDirectory("O:\\yakalope\\logging\\data\\")
logmod.setIndexDirectory("O:\\yakalope\\logging\\index\\")


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
    to_host_parts = to_parts[1].split(".",1)
    if len(to_host_parts) == 2:
        to_host = to_host_parts[1]
        to_protocol = to_host_parts[0]
    else:
        to_host = to_parts[1]
        to_protocol = ""

    from_parts = raw_from.rsplit("@",1)
    from_username = from_parts[0]
    from_host_parts = from_parts[1].split(".",1)
    if len(from_host_parts) == 2:
        from_host = from_host_parts[1]
        from_protocol = from_host_parts[0]
    else:
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
