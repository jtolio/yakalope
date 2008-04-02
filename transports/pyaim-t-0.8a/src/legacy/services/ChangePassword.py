# Copyright 2005-2006 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
from twisted.words.xish.domish import Element
from twisted.words.protocols.jabber.jid import internJID
from debug import LogEvent, INFO, WARN, ERROR
import config
import lang
import globals

class ChangePassword:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.adhoc.addCommand("changepassword", self.incomingIq, "command_ChangePassword")

	def incomingIq(self, el):
		to = el.getAttribute("from")
		toj = internJID(to)
		ID = el.getAttribute("id")
		ulang = utils.getLang(el)

		sessionid = None
		oldpassword = None
		newpassword = None
		newpasswordagain = None

		for command in el.elements():
			sessionid = command.getAttribute("sessionid")
			if command.getAttribute("action") == "cancel":
				self.pytrans.adhoc.sendCancellation("changepassword", el, sessionid)
				return
			for child in command.elements():
				if child.name == "x" and child.getAttribute("type") == "submit":
					for field in child.elements():
						if field.name == "field" and field.getAttribute("var") == "newpassword":
							for value in field.elements():
								if value.name == "value":
									newpassword = value.__str__()
						elif field.name == "field" and field.getAttribute("var") == "newpasswordagain":
							for value in field.elements():
								if value.name == "value":
									newpasswordagain = value.__str__()
						elif field.name == "field" and field.getAttribute("var") == "oldpassword":
							for value in field.elements():
								if value.name == "value":
									oldpassword = value.__str__()

		if not self.pytrans.sessions.has_key(toj.userhost()) or not hasattr(self.pytrans.sessions[toj.userhost()].legacycon, "bos"):
			self.pytrans.adhoc.sendError("changepassword", el, errormsg=lang.get("command_NoSession", ulang), sessionid=sessionid)
		elif newpassword and newpassword != newpasswordagain:
			self.sendForm(el, sessionid=sessionid, errormsg=lang.get("command_ChangePassword_Mismatch", ulang))
		elif oldpassword and newpassword:
			self.changePassword(el, oldpassword, newpassword, sessionid)
		else:
			self.sendForm(el)

	def sendForm(self, el, sessionid=None, errormsg=None):
		to = el.getAttribute("from")
		ID = el.getAttribute("id")
		ulang = utils.getLang(el)

		iq = Element((None, "iq"))
		iq.attributes["to"] = to
		iq.attributes["from"] = config.jid
		if ID:
			iq.attributes["id"] = ID
		iq.attributes["type"] = "result"

		command = iq.addElement("command")
		if sessionid:
			command.attributes["sessionid"] = sessionid
		else:
			command.attributes["sessionid"] = self.pytrans.makeMessageID()
		command.attributes["node"] = "changepassword"
		command.attributes["xmlns"] = globals.COMMANDS
		command.attributes["status"] = "executing"

		if errormsg:
			note = command.addElement("note")
			note.attributes["type"] = "error"
			note.addContent(errormsg)

		actions = command.addElement("actions")
		actions.attributes["execute"] = "complete"
		actions.addElement("complete")

		x = command.addElement("x")
		x.attributes["xmlns"] = "jabber:x:data"
		x.attributes["type"] = "form"

		title = x.addElement("title")
		title.addContent(lang.get("command_ChangePassword", ulang))

		instructions = x.addElement("instructions")
		instructions.addContent(lang.get("command_ChangePassword_Instructions", ulang))

		oldpassword = x.addElement("field")
		oldpassword.attributes["type"] = "text-private"
		oldpassword.attributes["var"] = "oldpassword"
		oldpassword.attributes["label"] = lang.get("command_ChangePassword_OldPassword", ulang)

		newpassword = x.addElement("field")
		newpassword.attributes["type"] = "text-private"
		newpassword.attributes["var"] = "newpassword"
		newpassword.attributes["label"] = lang.get("command_ChangePassword_NewPassword", ulang)

		newpassworda = x.addElement("field")
		newpassworda.attributes["type"] = "text-private"
		newpassworda.attributes["var"] = "newpasswordagain"
		newpassworda.attributes["label"] = lang.get("command_ChangePassword_NewPasswordAgain", ulang)

		self.pytrans.send(iq)

	def changePassword(self, el, oldpassword, newpassword, sessionid):
		to = el.getAttribute("from")
		toj = internJID(to)

		self.pytrans.sessions[toj.userhost()].legacycon.bos.changePassword(oldpassword, newpassword).addCallback(self.pwdChangeResults, el, sessionid, newpassword)

	def pwdChangeResults(self, results, el, sessionid, newpassword):
		to = el.getAttribute("from")
		toj = internJID(to)
		ID = el.getAttribute("id")
		ulang = utils.getLang(el)

		iq = Element((None, "iq"))
		iq.attributes["to"] = to
		iq.attributes["from"] = config.jid
		if ID:
			iq.attributes["id"] = ID
		iq.attributes["type"] = "result"

		command = iq.addElement("command")
		if sessionid:
			command.attributes["sessionid"] = sessionid
		else:
			command.attributes["sessionid"] = self.pytrans.makeMessageID()
		command.attributes["node"] = "changepassword"
		command.attributes["xmlns"] = globals.COMMANDS
		command.attributes["status"] = "completed"

		note = command.addElement("note")
		if results[3]:
			note.attributes["type"] = "error"
			note.addContent(lang.get("command_ChangePassword_Failed", ulang))
		else:
			note.attributes["type"] = "info"
			note.addContent(lang.get("command_Done", ulang))
			(username, oldpassword) = self.pytrans.xdb.getRegistration(toj.userhost())
			self.pytrans.xdb.setRegistration(toj.userhost(), username, newpassword)

		self.pytrans.send(iq)
