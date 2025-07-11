# shared/npp_utils.py
# A part of notepadPlusPlusAccessEnhancement add-on
# Copyright (C) 2020-2025, paulber19
# This file is covered by the GNU General Public License.


import addonHandler
import api
import speech
import winUser
import time
import queueHandler

import ui
try:
	# NVDA >= 2024.1
	speech.speech.SpeechMode.onDemand
	speakOnDemand = {"speakOnDemand": True}
except AttributeError:
	# NVDA <= 2023.3
	speakOnDemand = {}

addonHandler.initTranslation()

# winuser.h constant

WM_SYSCOMMAND = 0x112
MOUSEEVENTF_WHEEL = 0x0800


def isOpened(dialog):
	if dialog._instance is None:
		return False
	# Translators: the label of a dialog box message.
	msg = _("%s dialog is allready open") % dialog.title
	queueHandler.queueFunction(queueHandler.eventQueue, speech.speakMessage, msg)
	return True


def makeAddonWindowTitle(dialogTitle):
	curAddon = addonHandler.getCodeAddon()
	addonSummary = curAddon.manifest['summary']
	# Translators: title of all add-on dialog boxs.
	return _("{addonSummary}'s add-on - {dialogTitle}").format(
		addonSummary=addonSummary, dialogTitle=dialogTitle)


def getPositionXY(obj):
	location = obj.location
	(x, y) = (int(location[0]) + int(location[2] / 2), int(location[1]) + int(location[3] / 2))
	return (x, y)


def mouseClick(obj, rightButton=False, twice=False):
	api.moveMouseToNVDAObject(obj)
	api.setMouseObject(obj)
	if not rightButton:
		winUser.mouse_event(winUser.MOUSEEVENTF_LEFTDOWN, 0, 0, None, None)
		winUser.mouse_event(winUser.MOUSEEVENTF_LEFTUP, 0, 0, None, None)
		if twice:
			time.sleep(0.1)
			winUser.mouse_event(winUser.MOUSEEVENTF_LEFTDOWN, 0, 0, None, None)
			winUser.mouse_event(winUser.MOUSEEVENTF_LEFTUP, 0, 0, None, None)
	else:
		winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTDOWN, 0, 0, None, None)
		winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTUP, 0, 0, None, None)
		if twice:
			time.sleep(0.1)
			winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTDOWN, 0, 0, None, None)
			winUser.mouse_event(winUser.MOUSEEVENTF_RIGHTUP, 0, 0, None, None)


def MouseWheelForward():
	winUser.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, 120, None)


def MouseWheelBack():
	winUser.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, -120, None)


def executeWithSpeakOnDemand(func, *args, **kwargs):
	from speech.speech import _speechState, SpeechMode
	if not speakOnDemand or _speechState.speechMode != SpeechMode.onDemand:
		return func(*args, **kwargs)
	_speechState.speechMode = SpeechMode.talk
	ret = func(*args, **kwargs)
	_speechState.speechMode = SpeechMode.onDemand
	return ret


def messageWithSpeakOnDemand(msg):
	executeWithSpeakOnDemand(ui.message, msg)
