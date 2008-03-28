# Copyright 2005-2006 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
from twisted.words.xish.domish import Element
from twisted.words.protocols.jabber.jid import internJID
from tlib import oscar
from debug import LogEvent, INFO, WARN, ERROR
import config
import lang
import globals
import re

class AIMURITranslate:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.adhoc.addCommand("aimuritranslate", self.incomingIq, "command_AIMURITranslate")

	def incomingIq(self, el):
		to = el.getAttribute("from")
		toj = internJID(to)
		ID = el.getAttribute("id")
		ulang = utils.getLang(el)

		sessionid = None
		uri = None

		for command in el.elements():
			sessionid = command.getAttribute("sessionid")
			if command.getAttribute("action") == "cancel":
				self.pytrans.adhoc.sendCancellation("aimuritranslate", el, sessionid)
				return
			for child in command.elements():
				if child.name == "x" and child.getAttribute("type") == "submit":
					for field in child.elements():
						if field.name == "field" and field.getAttribute("var") == "uri":
							for value in field.elements():
								if value.name == "value":
									uri = value.__str__()

		if not self.pytrans.sessions.has_key(toj.userhost()) or not hasattr(self.pytrans.sessions[toj.userhost()].legacycon, "bos"):
			self.pytrans.adhoc.sendError("aimuritranslate", el, errormsg=lang.get("command_NoSession", ulang), sessionid=sessionid)
		elif uri:
			self.translateUri(el, uri, sessionid=sessionid)
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
		command.attributes["node"] = "aimuritranslate"
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
		title.addContent(lang.get("command_AIMURITranslate", ulang))

		instructions = x.addElement("instructions")
		instructions.addContent(lang.get("command_AIMURITranslate_Instructions", ulang))

		email = x.addElement("field")
		email.attributes["type"] = "text-single"
		email.attributes["var"] = "uri"
		email.attributes["label"] = lang.get("command_AIMURITranslate_URI", ulang)

		self.pytrans.send(iq)

	def translateUri(self, el, uri, sessionid=None):
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
		command.attributes["node"] = "aimuritranslate"
		command.attributes["xmlns"] = globals.COMMANDS
		command.attributes["status"] = "completed"

		session = self.pytrans.sessions[toj.userhost()]

		m = re.match('\s*aim:([^\?]+)\?([^\s]+)\s*', uri)
		handled = False
		if m != None:
			cmd = m.group(1)
			cmd = cmd.lower() # I don't like case-sensitive cmds
			payload = m.group(2)
			pieces = payload.split("&")
			options = {}
			for p in pieces:
				if not p or p.find("=") == -1: continue
				option,value = p.split("=", 2)
				option = option.lower() # Ditto
				options[option] = value
			if cmd == "buddyicon":
				# What the hell?
				# aim:BuddyIcon?Src=http://cdn-aimtoday.aol.com/aimtoday_buddyicons/inside_aol_1
				# It's a buddy icon alright, but..?
				# Maybe this sets your buddy icon?
				pass
			elif cmd == "gochat":
				# Ah yes, a chatroom, lets invite the submitter
				roomname = options.get('roomname', None)
				if roomname:
					exchange = options.get('exchange', 4)
					from legacy.glue import aim2jid, LegacyGroupchat
					groupchat = LegacyGroupchat(session=session, resource=session.highestResource(), ID=roomname.replace(' ','_')+"%"+str(exchange))
					groupchat.sendUserInvite(config.jid)
					handled = True
			elif cmd == "goim":
				# Send a message, to yourself, or someone else
				from legacy.glue import aim2jid
				message = options.get('message', None)
				screenname = options.get('screenname', None)
				if message:
					if screenname:
						# send message to someone else
						text = oscar.dehtml(message)
						text = text.strip()
						session.legacycon.sendMessage(aim2jid(screenname), None, text, False, utils.prepxhtml(message))
						handled = True
					else:
						# send message to self
						text = oscar.dehtml(message)
						text = text.strip()
						session.sendMessage(to=toj.userhost(), fro=config.jid, body=text, mtype="chat", xhtml=utils.prepxhtml(message))
						handled = True

		note = command.addElement("note")
		if not handled:
			note.attributes["type"] = "error"
			note.addContent(lang.get("command_AIMURITranslate_Failed", ulang))
		else:
			note.attributes["type"] = "info"
			note.addContent(lang.get("command_Done", ulang))

		self.pytrans.send(iq)
