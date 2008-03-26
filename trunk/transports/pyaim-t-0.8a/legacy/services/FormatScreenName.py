# Copyright 2005-2006 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
from twisted.words.xish.domish import Element
from twisted.words.protocols.jabber.jid import internJID
from debug import LogEvent, INFO, WARN, ERROR
import config
import lang
import globals

class FormatScreenName:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.adhoc.addCommand("formatscreenname", self.incomingIq, "command_FormatScreenName")

	def incomingIq(self, el):
		to = el.getAttribute("from")
		toj = internJID(to)
		ID = el.getAttribute("id")
		ulang = utils.getLang(el)

		sessionid = None
		fmtsn = None

		for command in el.elements():
			sessionid = command.getAttribute("sessionid")
			if command.getAttribute("action") == "cancel":
				self.pytrans.adhoc.sendCancellation("formatscreenname", el, sessionid)
				return
			for child in command.elements():
				if child.name == "x" and child.getAttribute("type") == "submit":
					for field in child.elements():
						if field.name == "field" and field.getAttribute("var") == "fmtsn":
							for value in field.elements():
								if value.name == "value":
									fmtsn = value.__str__()

		if not self.pytrans.sessions.has_key(toj.userhost()) or not hasattr(self.pytrans.sessions[toj.userhost()].legacycon, "bos"):
			self.pytrans.adhoc.sendError("formatscreenname", el, errormsg=lang.get("command_NoSession", ulang), sessionid=sessionid)
		elif fmtsn:
			self.changeSNFormat(el, fmtsn, sessionid)
		else:
			self.pytrans.sessions[toj.userhost()].legacycon.bos.getFormattedScreenName().addCallback(self.sendForm, el)

	def sendForm(self, current, el, sessionid=None, errormsg=None):
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
		command.attributes["node"] = "formatscreenname"
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
		x.attributes["xmlns"] = globals.XDATA
		x.attributes["type"] = "form"

		title = x.addElement("title")
		title.addContent(lang.get("command_FormatScreenName", ulang))

		instructions = x.addElement("instructions")
		instructions.addContent(lang.get("command_FormatScreenName_Instructions", ulang))

		fmtsn = x.addElement("field")
		fmtsn.attributes["type"] = "text-single"
		fmtsn.attributes["var"] = "fmtsn"
		fmtsn.attributes["label"] = lang.get("command_FormatScreenName_FMTScreenName", ulang)
		if current[1]:
			fmtsn.addElement("value").addContent(current[1])

		self.pytrans.send(iq)

	def changeSNFormat(self, el, fmtsn, sessionid):
		to = el.getAttribute("from")
		toj = internJID(to)

		self.pytrans.sessions[toj.userhost()].legacycon.bos.changeScreenNameFormat(fmtsn).addCallback(self.snfmtChangeResults, el, sessionid)

	def snfmtChangeResults(self, results, el, sessionid):
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
		command.attributes["node"] = "formatscreenname"
		command.attributes["xmlns"] = globals.COMMANDS
		command.attributes["status"] = "completed"

		note = command.addElement("note")
		if results[3]:
			note.attributes["type"] = "error"
			note.addContent(results[3][1])
		else:
			note.attributes["type"] = "info"
			note.addContent(lang.get("command_Done", ulang))

		self.pytrans.send(iq)
