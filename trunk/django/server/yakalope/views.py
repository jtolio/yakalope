# Create your views here.
from django.shortcuts import HttpResponse
from models import ServerStatus
from models import Users
from django.utils import simplejson
from models import LogMessage        #TODO: CHANGE TO IMPORT LOGMODULE
from models import LogConversation   #TODO: REMOVE

#Logs in the user
"""
DATA: username=XXXXX&password=XXXXX
returns Status object on success, type=success, message="", data=null
returns Status object on failure, type=failure, message=description, data=null
"""
def login(request):
    c_user = request.GET.get('username','')
    c_pass = request.GET.get('password','')

    valid_login = False
    if c_user and c_pass:
        if c_user == "test" and c_pass == "123456":
            valid_login = True
        #TODO: REPLACE WITH REAL LOGIN CHECKING CODE

    if valid_login:
        response = ServerStatus("success","",None);
    else:
        response = ServerStatus("failure","",None);

    return HttpResponse(convertToJSON(response), mimetype="text/plain")



#Performs a search of a user's logged messages
"""
DATA: searchterm=XXXXXXXX
returns Status object on success, type=success, message="",
        data=Array of Conversation Objects
returns Status object on failure, type=failure, message=description, data=null
"""
def search(request):
    c_query = request.GET.get('searchterm','')

    if c_query:
        pass #Nothing right now

    response = ServerStatus("failure","not yet written",None);
    return HttpResponse(convertToJSON(response), mimetype="text/plain")



#Gathers recent messages from the user's logged messages
"""
returns Status object on success, type=success, message="",
        data=Array of Conversation Objects
returns Status object on failure, type=failure, message=description, data=null
"""
def recent(request):
    response = ServerStatus("success","",[LogConversation(),LogConversation()]);
    return HttpResponse(convertToJSON(response), mimetype="text/plain")



#Logs the user out of the system, clearing the session
"""
returns Status object ALWAYS, type=success, message="", data=null
"""
def logout(request):
    response = ServerStatus("failure","",None);
    return HttpResponse(convertToJSON(response), mimetype="text/plain")





#Converts the following to JSON:
#  ServerStatus object with the following possible "data" values:
#    None
#    Array of logmodule.LogConversation objects
def convertToJSON(obj):
    if isinstance(obj, ServerStatus):
        if obj.data != None:
            data_dict = []
            for convo in obj.data:
                if isinstance(convo, LogConversation):
                    con_dict = convo.toDict()
                    data_dict.append(con_dict);
                else:
                    return "(INVALID JSON CONVERSION: " + \
                           "Expected LogConversation object)"
        else:
            data_dict = None


        obj_dict = {"type": obj.type,
                    "message": obj.message,
                    "data": data_dict}
        return simplejson.dumps(obj_dict)
    else:
        return "(INVALID JSON CONVERSION: " + \
               "Expected ServerStatus object)"