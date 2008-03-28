# -*- coding: UTF-8 -*-
# Copyright 2004-2006 James Bunton <james@delx.cjb.net> 
# Licensed for distribution under the GPL version 2, check COPYING for details


import config

def get(lang=config.lang):
	if not isinstance(lang, basestring):
		lang = config.lang
	lang = lang.replace("-", "_")
	if hasattr(strings, lang):
		return getattr(strings, lang)
	if hasattr(strings, config.lang):
		return getattr(strings, config.lang)
	return strings.en


# If you change or add any strings in this file please contact the translators listed below
# Everything must be in UTF-8
# Look for language codes here - http://www.w3.org/WAI/ER/IG/ert/iso639.htm
# Current languages: English, Portugese, Dutch, German, French, Spanish

class strings:
	class en: # English - James Bunton <mailto:james@delx.cjb.net>
		# Text that may get sent to the user. Useful for translations. Keep any %s symbols you see or you will have troubles later
		registerText = u"Please type your MSN Passport (user@hotmail.com) into the username field and your password.\nFor more information see http://msn-transport.jabberstudio.org/docs/users"
		gatewayTranslator = u"Enter the user's MSN account."
		userMapping = u"The MSN contact %s has a Jabber ID %s. It is recommended to talk to this person through Jabber."
		notLoggedIn = u"Error. You must log into the transport before sending messages."
		notRegistered = u"Sorry. You do not appear to be registered with this transport. Please register and try again. If you are having trouble registering please contact your Jabber administrator."
		waitForLogin = u"Sorry, this message cannot be delivered yet. Please try again when the transport has finished logging in."
		groupchatInvite = u"You have been invited into a groupchat on the legacy service. You must join this room to switch into groupchat mode %s.\nIf you do not join this room you will not be able to participate in the groupchat, but you will still appear to have joined it to contacts on the MSN service."
		groupchatFailJoin1 = u"You did not join the groupchat room %s.\nThe following users were in the groupchat:"
		groupchatFailJoin2 = u"You have been removed from this room on the legacy service. The following was said before you were disconnected, while you appeared to be in the groupchat to the contacts on the legacy service."
		groupchatPrivateError = u"Sorry. You cannot send private messages to users in this groupchat. Please instead add the user to your contact list and message them that way."
		groupchatAdvocacy = u"%s has invited you to a Jabber chatroom. To join this room you need to be using Jabber. Please see %s for more information."
		msnMaintenance = u"Notification from Microsoft. The MSN Messenger network will be going down for maintenance."
		msnMultipleLogin = u"Your MSN account has been logged in elsewhere. Please logout at the other location and then reactivate the MSN transport."
		msnNotVerified = u"Your MSN passport %s, has not had it's email address verified. MSN users will not be able to see your nickname, and will be warned that your account may not be legitimate. Please see Microsoft for details."
		msnLoginFailure = u"MSN transport could not log into your MSN account %s. Please check that your password is correct. You may need to re-register the transport."
		msnFailedMessage = u"This message could not be delivered. Please check that the contact is online, and that their address on your contact list is correct.\n\n"
		msnDroppedMessage = u"(Automated message)\nA message from this person did not get delivered to you. Please report this to your Jabber server administrator."
		msnInitialMail = u"Hotmail notification\n\nUnread message in inbox: %s\nUnread messages in folders: %s"
		msnRealtimeMail = u"Hotmail notification\n\nFrom: %s <%s>\n Subject: %s"
		msnDisconnected = u"Disconnected from MSN servers: %s"
		msnConnectFailed = u"Failed to connect to MSN servers: %s"
		msnFtSizeRejected = u"A file '%s' was rejected because it was over the size limit of %s bytes. To exchange larger files to this person, please use Jabber. See %s for details."

		command_CommandList = u"PyMSNt Commands"
		command_Done = "Command completed."
		command_ConnectUsers = u"Connect all registered users"
		command_Statistics = u"Statistics for PyMSNt"
		command_OnlineUsers = u"Online Users"
		command_TotalUsers = u"Total Connections"
		command_Uptime = u"Uptime"
		command_MessageCount = u"Message Count"
		command_FailedMessageCount = u"Failed Message Count"
		command_AvatarCount = u"Avatar Count"
		command_FailedAvatarCount = u"Failed Avatar Count"
		command_OnlineUsers_Desc = u"The number of users currently connected to the service."
		command_TotalUsers_Desc = u"The number of connections since the service started."
		command_Uptime_Desc = u"How long the service has been running, in seconds."
		command_MessageCount_Desc = u"How many messages have been transferred to and from the MSN network."
		command_FailedMessageCount_Desc = u"The number of messages that didn't make it to the MSN recipient and were bounced."
		command_AvatarCount_Desc = u"How many avatars have been transferred to and from the MSN network."
		command_FailedAvatarCount_Desc = u"The number of avatar transfers that have failed."
	en_US = en # en-US is the same as en, so are the others
	en_AU = en
	en_GB = en

	class pt: # asantos
		# Text that may get sent to the user. Useful for translations. Keep any %s symbols you see or you will have troubles later
		registerText = u"Para acederes ao Serviço de MSN, tens que inserir o teu username (eg. alex@hotmail.com) e password respectiva."
		gatewayTranslator = u"Enter the user's MSN account."
		userMapping = u"O contacto MSN %s tem o seguinte Jabber ID %s. É recomendável falar com este contacto através do Jabber."
		notLoggedIn = u"Erro. Tens que efectuar o login no serviço de transporte antes de começar a enviar mensagens."
		notRegistered = u"Pedimos Desculpa mas não deverás ter o registo correcto neste serviço de transporte. Tenta registar-te novamente, por favor. Se continuas a ter problemas no registo, contacta-nos por favor (eg. messenger@hotmail.com)."
		waitForLogin = u"Erro, esta mensagem não poderá ser entregue imediatamente. Por favor tenta de novo, quando o serviço de transporte acabar de efectuar login."
		groupchatInvite = u"You have been invited into a groupchat on the legacy service. You must join this room to switch into groupchat mode %s.\nIf you do not join this room you will not be able to participate in the groupchat, but you will still appear to have joined it to contacts on the MSN service."
		groupchatFailJoin1 = u"You did not join the groupchat room %s.\nThe following users were in the groupchat:"
		groupchatFailJoin2 = u"You have been removed from this room on the legacy service. The following was said before you were disconnected, while you appeared to be in the groupchat to the contacts on the legacy service."
		groupchatPrivateError = u"Sorry. You cannot send private messages to users in this groupchat. Please instead add the user to your contact list and message them that way."
		groupchatAdvocacy = u"%s has invited you to a Jabber chatroom. To join this room you need to be using Jabber. Please see %s for more information."
		msnMaintenance = u"Notification from Microsoft. The MSN Messenger network will be going down for maintenance."
		msnMultipleLogin = u"A tua conta de MSN foi activada noutro computador. Por favor desliga a ligação no outro computador para retomar o serviço de transporte."
		msnNotVerified = u"O teu MSN passport %s, não verificou correctamente o teu email. Utilizadores de MSN não vão conseguir ver o teu nickname, e vão ser avisados que a tua conta poderá não ser legitima. Confirma com a Microsoft os teus detalhes."
		msnLoginFailure = u"O serviço de transporte de MSN não conseguiu activar a ligação com a tua conta %s. Confirma se a tua password está correcta. Poderás ter que te registar de novo no serviço."
		msnFailedMessage = u"Esta mensagem não pode ser entregue. Confirma por favor se o contacto está online e se o endereço usado na buddylist está correcto\n\n"
		msnDroppedMessage = u"(Automated message)\nA message from this person did not get delivered to you. Please report this to your Jabber server administrator."
		msnInitialMail = u"Hotmail notification\n\nUnread message in inbox: %s\nUnread messages in folders: %s"
		msnRealtimeMail = u"Hotmail notification\n\nFrom: %s <%s>\n Subject: %s"
		msnDisconnected = u"Desligado dos servidores MSN: %s"
		msnConnectFailed = u"Failed to connect to MSN servers: %s"
		msnFtSizeRejected = u"A file '%s' was rejected because it was over the size limit of %s bytes. To exchange larger files to this person, please use Jabber. See %s for details."

		command_CommandList = u"PyMSNt Commands"
		command_Done = "Command completed."
		command_ConnectUsers = u"Connect all registered users"
		command_Statistics = u"Statistics for PyMSNt"
		command_OnlineUsers = u"Online Users"
		command_TotalUsers = u"Total Connections"
		command_Uptime = u"Uptime"
		command_MessageCount = u"Message Count"
		command_AvatarCount = u"Avatar Count"
		command_FailedAvatarCount = u"Failed Avatar Count"
		command_FailedMessageCount = u"Failed Message Count"
		command_OnlineUsers_Desc = u"The number of users currently connected to the service."
		command_TotalUsers_Desc = u"The number of connections since the service started."
		command_Uptime_Desc = u"How long the service has been running, in seconds."
		command_MessageCount_Desc = u"How many messages have been transferred to and from the MSN network."
		command_FailedMessageCount_Desc = u"The number of messages that didn't make it to the MSN recipient and were bounced."
		command_AvatarCount_Desc = u"How many avatars have been transferred to and from the MSN network."
		command_FailedAvatarCount_Desc = u"The number of avatar transfers that have failed."

	class nl: # Dutch - Matthias Therry <matthias.therry@pi.be>, Sander Devrieze <s.devrieze@pandora.be>
		registerText = u"Voer uw MSN Passport (gebruiker@hotmail.com) en uw wachtwoord in. Geef ook het vaste deel van uw bijnaam op.\nRaadpleeg voor meer informatie http://msn-transport.jabberstudio.org/docs/user"
		gatewayTranslator = u"Voer de MSN-account van de gebruiker in."
		userMapping = u"Contactpersoon %s op het MSN-netwerk heeft ook een Jabber-ID. Het is het best om met hem via Jabber te chatten. Zijn Jabber-ID is %s."
		notLoggedIn = u"Fout: u moet eerst aanmelden op het transport alvorens berichten te verzenden."
		notRegistered = u"Fout: u bent niet geregistreerd op dit transport. Registreer u eerst en probeer daarna opnieuw. Contacteer de beheerder van uw Jabber-server bij registratieproblemen."
		waitForLogin = u"Fout: dit bericht kon nog niet worden afgeleverd. Probeer opnieuw wanneer het transport klaar is met aanmelden."
		groupchatInvite = u"U bent uitgenodigd voor een groepsgesprek op het MSN-netwerk. Neem deel door om te schakelen naar groepsgesprekmodus %s.\nAls u dit niet doet, zal u niet kunnen deelnemen aan het gesprek terwijl het voor de MSN-gebruikers lijkt alsof u toch aanwezig bent."
		groupchatFailJoin1 = u"U hebt niet deelgenomen aan het groepsgesprek in de chatruimte %s.\nVolgende personen waren er aanwezig:"
		groupchatFailJoin2 = u"U werd verwijderd uit deze chatruimte op het MSN-netwerk. Terwijl u voor de andere deelnemers in deze ruimte aanwezig leek, werd het volgende gezegd:"
		groupchatPrivateError = u"Fout: u kunt geen privé-berichten verzenden naar gebruikers in deze chatruimte. Voeg de gebruiker daarom toe aan uw contactpersonenlijst van MSN om hem zo persoonlijk te kunnen benaderen."
		groupchatAdvocacy = u"%s heeft u uitgenodigd op een chatruimte op het Jabber-netwerk. Deze ruimte kunt u alleen betreden via het Jabber-netwerk. Neem een kijkje op %s voor meer informatie."
		msnMaintenance = u"Bericht van Microsoft: het MSN-netwerk zal tijdelijk niet bereikbaar zijn door onderhoudswerken."
		msnMultipleLogin = u"Uw MSN-account is al ergens anders in gebruik. Meld u daar eerst af en heractiveer vervolgens dit transport."
		msnNotVerified = u"Het e-mailadres van uw MSN Passport %s werd nog niet geverifieerd. Daardoor zien MSN-gebruikers uw bijnaam niet en zullen ze gewaarschuwd worden dat uw account mogelijk nep is. Contacteer Microsoft voor meer informatie."
		msnLoginFailure = u"Het MSN-transport kon niet aanmelden op uw MSN-account %s. Controleer uw wachtwoord. Mogelijk moet u zich opnieuw registreren op dit transport."
		msnFailedMessage = u"Dit bericht kon niet worden afgeleverd. Controleer of de contactpersoon online is en of zijn adres op uw contactpersonenlijst juist is.\n\n"
		msnDroppedMessage = u"(Automatisch bericht)\nEen bericht van deze persoon raakte niet to bij jou. Breng de beheerder van uw Jabber-server hiervan op de hoogte."
		msnInitialMail = u"Hotmail-meldingen\n\nAantal ongelezen berichten in postvak in: %s\nAantal ongelezen berichten in mappen: %s"
		msnRealtimeMail = u"Hotmail-meldingen\n\nVan: %s <%s>\n Onderwerp: %s"
		msnDisconnected = u"De verbinding met de MSN-servers werd verbroken: %s"
		msnConnectFailed = u"Verbinden met MSN-servers mislukte: %s"
		msnFtSizeRejected = u"Het bestand '%s' werd geweigerd omdat het groter was dan %s. Als u grotere bestanden naar deze contactpersoon wilt verzenden, gebruik dan Jabber. Zie %s voor details."

		command_CommandList = u"Commando's voor PyMSNt"
		command_Done = "Commando beëindigd."
		command_ConnectUsers = u"Alle geregistreerde gebruikers verbinden"
		command_Statistics = u"Statistieken van PyMSNt"
		command_OnlineUsers = u"Online gebruikers"
		command_TotalUsers = u"Totaal aantal gebruikers"
		command_Uptime = u"Uptime"
		command_MessageCount = u"Aantal berichten"
		command_AvatarCount = u"Aantal avatars"
		command_FailedAvatarCount = u"Telling van avatars mislukt"
		command_FailedMessageCount = u"Telling van berichten mislukt"
		command_OnlineUsers_Desc = u"Het aantal gebruikers die momenteel dit transport gebruiken."
		command_TotalUsers_Desc = u"Het aantal verbindingen sinds het transport gestart werd."
		command_Uptime_Desc = u"Hoelang het transport al draait (seconden)."
		command_MessageCount_Desc = u"Hoeveel berichten er van en naar het MSN-netwerk overgebracht werden."
		command_FailedMessageCount_Desc = u"Het aantal berichten die zijn ontvanger op het MSN-netwerk niet bereikten en dus teruggestuurd werden."
		command_AvatarCount_Desc = u"Hoeveel avatars er van en naar het MSN-netwerk overgebracht werden."
		command_FailedAvatarCount_Desc = u"Het aantal overdrachten van avatars die mislukt zijn."
	dut = nl
	nla = nl
	
	
	
	class de: # German - Florian Holzhauer <xmpp:fh@jabber.ccc.de>
		registerText = u"Bitte trage Deine MSN-Passport-ID (user@hotmail.com) als User ein, sowie Dein Passwort und Deinen Nickname.\n Mehr Informationen zu diesem Gateway findest Du unter http://msn-transport.jabberstudio.org/docs/users"
		gatewayTranslator = u"Enter the user's MSN account."
		userMapping = u"The MSN contact %s has a Jabber ID %s. It is recommended to talk to this person through Jabber."
		notLoggedIn = u"Fehler. Du musst beim Gateway eingeloggt sein bevor Du Nachrichten schicken kannst."
	 	notRegistered = u"Sorry, Du scheinst Dich bei diesem Gateway noch nicht registriert zu haben. Bitte registriere Dich und versuche es noch einmal. Bei Problemen wendest Du Dich am besten an Deinen Jabber-Administrator"
		waitForLogin = u"Sorry, die Nachricht kann noch nicht uebermittelt werden. Bitte versuche es noch einmal wenn das Gateway bei MSN eingeloggt ist."
		groupchatInvite = u"Du wurdest zu einem MSN-Groupchat eingeladen. Du musst dem Groupchat %s beitreten um teilnehmen zu können, ansonsten kannst Du an dem Groupchat nicht teilnehmen, obwohl es für die anderen Teilnehmer so aussieht, als ob Du im Raum bist."
		groupchatFailJoin1 = u"Du hast den Groupchat-Raum %s nicht betreten.\n Die folgenden User waren im Groupchat:"
		groupchatFailJoin2 = u"Du bist aus diesem Groupchat-Raum ausgeloggt worden. Das folgende wurde in dem Chat gesagt bevor du ausgeloggt wurdest:"
		groupchatPrivateError = u"Du kannst keine privaten Nachrichten an Mitglieder dieses Groupchats schicken. Bitte füge sie stattdessen deinem Roster hinzu."
		groupchatAdvocacy = u"%s has invited you to a Jabber chatroom. To join this room you need to be using Jabber. Please see %s for more information."
		msnMaintenance = u"Das MSN Messenger Network wird aus Wartungsgründen von Microsoft heruntergefahren. Bis später!"
		msnMultipleLogin = u"Du bist bereits mit einem anderen Client im MSN Network eingeloggt. Bitte logge den anderen Client aus und aktiviere dann diesen Transport wieder."
		msnNotVerified = u"Dein MSN-Account %s hat keine von Microsoft überprüfte eMail-Adresse. Andere MSN-User können daher Deinen Nickname nicht sehen und werden gewarnt dass dein Account gefälscht sein koennte. Bitte besuche die MSN-Seiten für Details."
		msnLoginFailure = u"Der Login beim MSN-Account %s ist fehlgeschlagen. Bitte überprüfe Dein Passwort und registriere Dich gegebenenfalls erneut."
		msnFailedMessage = u"Die Nachricht konnte nicht übermittelt werden. Bitte prüfe, dass der Contact online ist, und seine Adresse in deiner Contact­List korrekt ist.\nDie Nachricht war:\n\n"
		msnDroppedMessage = u"(Automated message)\nA message from this person did not get delivered to you. Please report this to your Jabber server administrator."
		msnInitialMail = u"Hotmail notification\n\nUngelesene Nachrichten in der Inbox: %s\nUngelesene Nachrichten in anderen Ordnern: %s"
		msnRealtimeMail = u"Hotmail notification\n\nNeue Nachricht von %s <%s>\n Subject: %s"
		msnDisconnected = u"Die Verbindung zum MSN-Server wurde getrennt: %s"
		msnConnectFailed = u"Failed to connect to MSN servers: %s"
		msnFtSizeRejected = u"A file '%s' was rejected because it was over the size limit of %s bytes. To exchange larger files to this person, please use Jabber. See %s for details."

		command_CommandList = u"PyMSNt Commands"
		command_Done = "Command completed."
		command_ConnectUsers = u"Connect all registered users"
		command_Statistics = u"Statistics for PyMSNt"
		command_OnlineUsers = u"Online Users"
		command_TotalUsers = u"Total Connections"
		command_Uptime = u"Uptime"
		command_MessageCount = u"Message Count"
		command_AvatarCount = u"Avatar Count"
		command_FailedAvatarCount = u"Failed Avatar Count"
		command_FailedMessageCount = u"Failed Message Count"
		command_OnlineUsers_Desc = u"The number of users currently connected to the service."
		command_TotalUsers_Desc = u"The number of connections since the service started."
		command_Uptime_Desc = u"How long the service has been running, in seconds."
		command_MessageCount_Desc = u"How many messages have been transferred to and from the MSN network."
		command_FailedMessageCount_Desc = u"The number of messages that didn't make it to the MSN recipient and were bounced."
		command_AvatarCount_Desc = u"How many avatars have been transferred to and from the MSN network."
		command_FailedAvatarCount_Desc = u"The number of avatar transfers that have failed."


	class fr: # French - Lucas Nussbaum <lucas@lucas-nussbaum.net>
		# Former translator: Alexandre Viard <mailto:ebola@courrier.homelinux.org>
		registerText = u"Merci d'entrer votre adresse MSN (utilisateur@hotmail.com) dans le champ utilisateur, votre mot de passe et le pseudonyme désiré.\nPour plus d'informations : http://msn-transport.jabberstudio.org/docs/users"
		gatewayTranslator = u"Saisir l'adresse MSN du contact."
		userMapping = u"Votre contact MSN %s a une adresse Jabber %s. Il est recommandé de lui parler par l'intermédiaire de Jabber."
		notLoggedIn = u"Erreur. Vous devez vous connecter au transport avant d'envoyer un message."
		notRegistered = u"Désolé. Vous ne semblez pas être enregistré auprès du transport. Merci de vous enregistrer et de réessayer. Si vous avez des problèmes pour l'enregistrement, merci de contacter votre administrateur Jabber."
		waitForLogin = u"Désolé, ce message ne peut pas être envoyé maintenant. Merci de réessayer quand le transport aura fini de vous connecter."
		groupchatInvite = u"Vous avez été invité à une conférence multi-utilisateurs. Vous devez rejoindre la salle %s pour faire partie de la conférence.\nSi vous ne le faites pas, vous ne pourrez pas y participer, mais vous apparaitrez quand même connecté à la salle pour les autres participants."
		groupchatFailJoin1 = u"Vous n'avez pas rejoint la salle de conférence %s.\nLes utilisateurs suivant y étaient connectés :"
		groupchatFailJoin2 = u"Vous avez été déconnecté de la salle par le serveur MSN. Les messages suivants on été échangés avant que vous soyez déconnecté, pendant que vous apparaissiez connecté à la salle pour les autres utilisateurs."
		groupchatPrivateError = u"Désolé. Vous ne pouvez pas envoyer des messages privés aux contacts de cette conférence. Merci de les ajouter à votre liste de contact et leur envoyer un message."
		groupchatAdvocacy = u"%s vous a invité à une salle de discussion Jabber. Pour rejoindre cette salle, vous devez utiliser Jabber. Jetez un coup d'oeil à %s pour plus d'informations."
		msnMaintenance = u"Notification en provenance de Microsoft. Le réseau MSN Messenger va être arrêté pour maintenance."
		msnMultipleLogin = u"Votre compte MSN a été utilisé à un autre endroit. Merci de vous déconnecter de celui-ci et de réactiver le transport MSN."
		msnNotVerified = u"L'adresse email de votre compte MSN %s n'a pas été vérifiée. Les utilisateurs MSN ne pourront pas voir votre pseudo et seront informés que votre compte n'est peut-être pas légitime. Merci de vous informer auprès de Microsoft pour plus de détails."
		msnLoginFailure = u"Le transport MSN n'a pas pu se connecter à votre compte MSN %s. Merci de vérifier que votre mot de passe est correct. Vous aurez peut-être à vous ré-enregistrer avec le transport."
		msnFailedMessage = u"Ce message n'a pas pu être délivré. Merci de vérifier que votre contact est en ligne et que son adresse est correcte.\n\n"
		msnInitialMail = u"Notification Hotmail\n\n Message(s) non lu(s) dans votre boîte de réception : %s\nMessage(s) non lu(s) dans le dossier : %s"
		msnRealtimeMail = u"Notification Hotmail\n\nDe: %s <%s>\n Sujet: %s"
		msnDisconnected = u"Déconnecté du serveur MSN: %s"
		msnConnectFailed = u"Failed to connect to MSN servers: %s"
		msnFtSizeRejected = u"A file '%s' was rejected because it was over the size limit of %s bytes. To exchange larger files to this person, please use Jabber. See %s for details."
		
		command_CommandList = u"Commandes PyMSNt"
		command_Done = "Command completed."
		command_ConnectUsers = u"Connect all registered users"
		command_Statistics = u"Statistiques de PyMSNt"
		command_OnlineUsers = u"Utilisateurs connectés"
		command_TotalUsers = u"Nombre total de connexions depuis le démarrage du service"
		command_Uptime = u"Uptime"
		command_MessageCount = u"Nombre de messages"
		command_AvatarCount = u"Nombre d'avatars"
		command_FailedAvatarCount = u"Nombre d'avatars avec échec"
		command_FailedMessageCount = u"Nombre de messages avec échec"
		command_OnlineUsers_Desc = u"Nombre d'utilisateurs connectés à ce service actuellement"
		command_TotalUsers_Desc = u"Nombre total de connexions depuis le démarrage du service"
		command_Uptime_Desc = u"Durée de fonctionnement du service (en secondes)"
		command_MessageCount_Desc = u"Nombre de messages transférés depuis et vers le réseau MSN"
		command_FailedMessageCount_Desc = u"Nombre de messages qui n'ont pas pu être transférés vers le réseau MSN"
		command_AvatarCount_Desc = u"Nombre d'avatars transférés depuis et vers le réseau MSN"
		command_FailedAvatarCount_Desc = u"Nombre d'avatars qui n'ont pas pu être transférés"
	fr_FR = fr
	fr_LU = fr
	fr_CH = fr
	fr_CA = fr
	fr_BE = fr

	class es: # Spanish - luis peralta <mailto:peralta@spisa.act.uji.es>
		# Text that may get sent to the user. Useful for translations. Keep any %s symbols you see or you will have troubles later
		registerText = u"Por favor, introduce tu cuenta MSN Passport (user@hotmail.com) en el campo de usuario, la contraseña y el nick o apodo que desees.\nPara más información visita http://msn-transport.jabberstudio.org/docs/users"
		gatewayTranslator = u"Introduce la cuenta de usuario MSN."
		userMapping = u"El contacto MSN %s tiene Jabber ID %s. Se recomienda que te comuniques con esta persona utilizando Jabber."
		notLoggedIn = u"Error. Tienes que iniciar sesión en el transporte antes de poder enviar mensajes."
		notRegistered = u"Lo sentimos. Parece que no estás registrado con este transporte. Por favor, regístrate y prueba de nuevo. Si tienes algún problema registrándote contacta por favor con el administrador del servidor Jabber."
		waitForLogin = u"Lo sentimos, tu mensaje no puede ser enviado todavía. Vuelve a probar cuando el transporte haya acabado de iniciar sesión."
		groupchatInvite = u"Te han invitado a una sala de charla a través de MSN. Tienes que entrar a la sala %s para pasar a modo de charla entre varios.\nSi no entras en la sala, no podrás participar, pero a los contactos MSN les parecerá que te has unido a la charla."
		groupchatFailJoin1 = u"No has entrado en la sala %s.\nLos siguientes usuarios estaban en la sala:"
		groupchatFailJoin2 = u"Has sido eliminado de la charla a tres en el servicio MSN. Lo siguiente se dijo antes de que salieses, mientras al resto de contactos les parecía que todavía estabas en la sala."
		groupchatPrivateError = u"Lo sentimos. No puedes mandar mensajes privados a usuarios en esta sala de charla. Por favor, añade al usuario a tu lista de contactos y charla desde ahí."
		groupchatAdvocacy = u"%s has invited you to a Jabber chatroom. To join this room you need to be using Jabber. Please see %s for more information."
		msnMaintenance = u"Notificación de Microsoft. La red de MSN Messenger va a estar en mantenimiento."
		msnMultipleLogin = u"Tu cuenta MSN está siendo utilizada desde otro ordenador. Por favor, cierra sesión en el otro sitio para reactivar el transporte MSN."
		msnNotVerified = u"Tu cuenta %s de MSN passport no ha sido verificada. Los usuarios de MSN no podrán ver tu nick o apodo y se les avisará de que puede que tu cuenta no sea legítima. Contacta con Microsoft para más detalles."
		msnLoginFailure = u"El transporte MSN no ha podido iniciar sesión con la cuenta %s. Por favor, comprueba que tu contraseña sea correcta. Puede que tengas que registrarte de nuevo con el transporte."
		msnFailedMessage = u"Este mensaje no ha podido ser entregado. Por favor, comprueba que el contacto esté conectado y que su dirección en tu lista de contactos sea correcta.\n\n"
		msnDroppedMessage = u"(Automated message)\nA message from this person did not get delivered to you. Please report this to your Jabber server administrator."
		msnInitialMail = u"Notificación de Hotmail\n\nMensajes sin leer en la bandeja de entrada: %s\nMensajes sin leer en otras carpetas: %s"
		msnRealtimeMail = u"Notificación de Hotmail\n\nDe: %s <%s>\nAsunto: %s"
		msnDisconnected = u"Desconexión de los servidores MSN: %s"
		msnConnectFailed = u"Failed to connect to MSN servers: %s"
		msnFtSizeRejected = u"A file '%s' was rejected because it was over the size limit of %s bytes. To exchange larger files to this person, please use Jabber. See %s for details."

		command_CommandList = u"PyMSNt Commands"
		command_Done = "Command completed."
		command_ConnectUsers = u"Connect all registered users"
		command_Statistics = u"Statistics for PyMSNt"
		command_OnlineUsers = u"Online Users"
		command_TotalUsers = u"Total Connections"
		command_Uptime = u"Uptime"
		command_MessageCount = u"Message Count"
		command_AvatarCount = u"Avatar Count"
		command_FailedAvatarCount = u"Failed Avatar Count"
		command_FailedMessageCount = u"Failed Message Count"
		command_OnlineUsers_Desc = u"The number of users currently connected to the service."
		command_TotalUsers_Desc = u"The number of connections since the service started."
		command_Uptime_Desc = u"How long the service has been running, in seconds."
		command_MessageCount_Desc = u"How many messages have been transferred to and from the MSN network."
		command_FailedMessageCount_Desc = u"The number of messages that didn't make it to the MSN recipient and were bounced."
		command_AvatarCount_Desc = u"How many avatars have been transferred to and from the MSN network."
		command_FailedAvatarCount_Desc = u"The number of avatar transfers that have failed."
	es_ES = es
	es_AR = es
	es_BO = es
	es_CL = es
	es_PY = es
	es_PA = es
	es_PE = es
	es_UY = es
	es_VE = es
	es_PR = es
	es_NI = es
	es_MX = es
	es_HN = es
	es_EC = es
	es_GT = es
	es_CR = es
	es_SV = es
	es_DO = es
	es_CR = es
	
	class pl: # Polish - Tomasz Sterna <xmpp:smoku@chrome.pl>
		registerText = u"Wpisz proszę swój Paszport MSN (użytkownik@hotmail.com) w pola użytkownik i hasło."
		gatewayTranslator = u"Wpisz konto użytkownika MSN."
		userMapping = u"Kontakt MSN %s ma Jabber ID %s. Zaleca się rozmawianie z tą osobą przez Jabbera."
		notLoggedIn = u"Błąd. Musisz zalogować się do transportu zanim zaczniesz wysyłać wiadomości."
		notRegistered = u"Przykro mi. Wygląda na to, że nie zarejestrowałeś się jeszcze w tym transporcie. Zarejestruj się i spróbuj ponownie."
		waitForLogin = u"Wybacz, ale nie można jeszcze dostarczyć tej wiadomości. Spróbuj ponownie gdy transport zakończy logowanie się."
		groupchatInvite = u"Otrzymałeś zaproszenie do rozmowy grupowej na obcej usłudze. Musisz wejść do pokoju rozmów %s aby dołączyć do tej rozmowy.\nJeśli nie wejdziesz do tego pokoju, nie będziesz mógł uczestniczyć w rozmowie grupowej, ale kontaktom MSN będzie się wydawało, że uczestniczysz."
		groupchatFailJoin1 = u"Nie dołączyłeś do pokoju rozmów %s.\nByli w nim następujący użytkownicy:"
		groupchatFailJoin2 = u"Zostałeś usunięty z tego pokoju rozmów na obcej usłudze. W czasie gdy wyglądało, że uczestniczysz w rozmowie wyglądała ona tak."
		groupchatPrivateError = u"Wybacz, ale nie możesz wysyłać prywatnych wiadomości do uczestników tej rozmowy. Dodaj użytkownika do swojej listy kontaktów i napisz do niego używając jej."
		groupchatAdvocacy = u"%s zaprosił cię na Jabberowego czata. Aby do niego dołączyć musisz używać Jabbera. Więcej informacji znajdziesz na %s."
		msnMaintenance = u"Wiadomość od Microsoftu. Sieć MSN zostanie chwilowo wyłączona z powodu prac serwisowych."
		msnMultipleLogin = u"Twoje konto MSN zalogowało się gdzieś indziej. Wyloguj proszę tę lokację i reaktywuj transport MSN."
		msnNotVerified = u"Adres email Twojego Paszportu MSN %s, nie został potwierdzony. Użytkownicy MSN nie będą widzieli Twojego nicka, oraz będą ostrzegani, że Twoje konto może nie być wiarygodne. Więcej informacji znajdziesz u Microsoftu."
		msnLoginFailure = u"Transport MSN nie mógł zalogować się na konto MSN %s. Sprawdź proszę, czy hasło jest właściwe. Może być konieczna ponowna rejestracja w transporcie."
		msnFailedMessage = u"Wiadomość nie mogła zostać dostarczona. Sprawdź proszę czy kontakt jest online i czy jego adres na Twojej liście kontaktów jest dobry.\n\n"
		msnDroppedMessage = u"(Wiadomość automatyczna)\nWiadomość od tej osoby nie mogła zostać dostarczona do Ciebie. Zgłoś to proszę swojemu administratorowi serwera Jabbera."
		msnInitialMail = u"Powiadomienie Hotmail\n\nNieprzeczytane wiadomości w skrzynce odbiorczej: %s\nNieprzeczytane wiadomości w folderach: %s"
		msnRealtimeMail = u"Powiadomienie Hotmail\n\nOd: %s <%s>\n Temat: %s"
		msnDisconnected = u"Rozłączenie z sieci MSN: %s"
		msnConnectFailed = u"Failed to connect to MSN servers: %s"
		msnFtSizeRejected = u"A file '%s' was rejected because it was over the size limit of %s bytes. To exchange larger files to this person, please use Jabber. See %s for details."

		command_CommandList = u"Polecenia PyMSNt"
		command_Done = "Polecenie zakończone."
		command_ConnectUsers = u"Podłącz wszystkich zarejestrowanych użytkowników"
		command_Statistics = u"Statystyki PyMSNt"
		command_OnlineUsers = u"Użytkownicy Online"
		command_TotalUsers = u"Użytkownicy ogółem"
		command_Uptime = u"Uptime"
		command_MessageCount = u"Licznik wiadomości"
		command_FailedMessageCount = u"Licznik nieudanych wiadomości"
		command_AvatarCount = u"Licznik Awatarów"
		command_FailedAvatarCount = u"Licznik nieudanych Awatarów"
		command_OnlineUsers_Desc = u"Użytkownicy aktualnie podłączeni do usługi."
		command_TotalUsers_Desc = u"Liczba połączeń od uruchomienia usługi."
		command_Uptime_Desc = u"Jak długo działa usługa, w sekundach."
		command_MessageCount_Desc = u"Ile wiadomości przesłano do i z sieci MSN."
		command_FailedMessageCount_Desc = u"Liczba wiadomości które nie dotarły do użytkowników MSN i zostały odbite."
		command_AvatarCount_Desc = u"Ile awatarów zostało przesłanych z i do sieci MSN."
		command_FailedAvatarCount_Desc = u"Liczba nieudanych przesyłów awatara."
	pl_PL = pl

