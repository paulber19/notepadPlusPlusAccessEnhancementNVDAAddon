# appModules/notepad++\npp_editWindow.py
# A part of the NotepadPlusPlusAccessEnhancement addon
# Copyright (C) 2020-2023 paulber19
# This file is covered by the GNU General Public License.

import addonHandler
import globalVars
import weakref
from NVDAObjects.behaviors import EditableTextWithAutoSelectDetection, EditableTextWithSuggestions
import api
import speech
import braille
import ui
from queueHandler import registerGeneratorObject
import textInfos
import tones
import time
import eventHandler
import scriptHandler
from scriptHandler import script
from scriptHandler import isScriptWaiting, willSayAllResume
import sys
import treeInterceptorHandler
import os
import wx
import NVDAObjects.window.scintilla
import watchdog
import review
import ctypes
from . import npp_convert
from .import forPython
from .forPython.python import PythonDocument, InterpreterError
from . import npp_application
from . import npp_browseMode
_curAddon = addonHandler.getCodeAddon()
sharedPath = os.path.join(_curAddon.path, "shared")
sys.path.append(sharedPath)
from npp_NVDAStrings import NVDAString
from npp_addonConfigManager import _addonConfigManager
from npp_informationDialog import InformationDialog
del sys.path[-1]

addonHandler.initTranslation()

from controlTypes.outputReason import OutputReason


_addonSummary = _curAddon.manifest['summary']
_scriptCategory = _addonSummary
# global timer
_scriptTimer = None
# scintilla definitions complement
SCI_INSERTTEXT = 2003
SCI_GOTOLINE = 2024
SCI_GETLINEINDENTATION = 2127
SCI_POSITIONFROMLINE = 2167
SCI_GETTABINDENTS = 2261
SCI_GETLINEINDENTPOSITION = 2128
SCI_GETCOLUMN = 2129
SCI_LINEDELETE = 2338
SCI_DELETERANGE = 2645
SCI_DELLINELEFT = 2395
SCI_DELLINERIGHT = 2396
SCI_COPY = 2178
SCI_GOTOPOS = 2025
SCI_TAB = 2327


class ScintillaTextInfoEx (NVDAObjects.window.scintilla.ScintillaTextInfo):
	def getCurrentLineNumber(self):
		offset = self._getCaretOffset()
		ret = self._getLineNumFromOffset(offset)
		return ret

	def goToLine(self, lineID):
		watchdog.cancellableSendMessage(self.obj.windowHandle, SCI_GOTOLINE, lineID, 0)
		eventHandler.executeEvent("caret", self.obj)
		self.obj._caretScriptPostMovedHelper(textInfos.UNIT_LINE, None, None)
		speech.speakMessage(_("Start of line"))

	def getLineIndentPosition(self, lineID):
		pos = watchdog.cancellableSendMessage(self.obj.windowHandle, SCI_GETLINEINDENTPOSITION, lineID, 0)
		return pos

	def getCurrentColumn(self):
		Pos = self._getCaretOffset()
		col = watchdog.cancellableSendMessage(self.obj.windowHandle, SCI_GETCOLUMN, Pos, 0)
		return col


from .npp_scriptDesc import (
	makeDesc,
	PRE_Line,
	PRE_Document,
	PRE_Python,
	PRE_Markdown,
)


# a part of buildin NVDA appmodule
class CharacterRangeStructLongLong(ctypes.Structure):
	"""By default character ranges in Scintilla are represented by longs.
	However long is not big enough for files over 2 GB,
	therefore in 64-bit builds of Notepad++ 8.3 and later
	these ranges are represented by longlong.
	"""
	_fields_ = [
		('cpMin', ctypes.c_longlong),
		('cpMax', ctypes.c_longlong),
	]


class ScintillaTextInfoNpp83(ScintillaTextInfoEx):
	"""Text info for 64-bit builds of Notepad++ 8.3 and later.
	"""

	class TextRangeStruct(ctypes.Structure):
		_fields_ = [
			('chrg', CharacterRangeStructLongLong),
			('lpstrText', ctypes.c_char_p),
		]


import queueHandler
_dSpellCheckReportDelay = None
from keyboardHandler import KeyboardInputGesture
_copyAllMisspelledWordsToClipboardGesture = KeyboardInputGesture.fromName(
	_addonConfigManager.getCopyAllMisspelledWordsToClipboardShortCut())


class NPPDocument (
	NVDAObjects.window.scintilla.Scintilla,
	EditableTextWithAutoSelectDetection, EditableTextWithSuggestions):
	"""An edit window that implements all of the scripts on the edit field for Notepad++"""
	treeInterceptorClass = npp_browseMode.NPPDocumentTreeInterceptor
	shouldCreateTreeInterceptor = False
	overfflowingBeepTimer = None
	__gestures = {
		"kb:upArrow": "reportLineOverflow",
		"kb:downArrow": "reportLineOverflow",
		# notepad ++ command keys:
		"kb:control+b": "goToMatchingBrace",
		"kb:f2": "goToNextBookmark",
		"kb:shift+f2": "goToPreviousBookmark",
		"kb:f3": "reportFindResult",
		"kb:shift+f3": "reportFindResult",
		"kb:control+pageUp": "tabChange",
		"kb:control+pageDown": "tabChange",
		"kb:control+w": "tabChange",
		"kb:tab": "reportIndent",
		"kb:shift+tab": "reportIndent",
		"kb:Enter": "EnterKey",
		"kb:Home": "HomeKey",
	}

	def _get_TextInfo(self):
		if self.appModule.is64BitProcess:
			appVerMajor, appVerMinor, *__ = self.appModule.productVersion.split(".")
			# When retrieving the version, Notepad++ concatenates
			# minor, patch, build in major.minor.patch.build to the form of major.minor
			# https://github.com/notepad-plus-plus/npp-usermanual/blob/master/content/docs/plugin-communication.md#nppm_getnppversion
			# e.g. '8.3' for '8.3', '8.21' for '8.2.1' and '8.192' for '8.1.9.2'.
			# Therefore, only use the first digit of the minor version to match against version 8.3 or later.
			if int(appVerMajor) >= 8 and int(appVerMinor[0]) >= 3:
				return ScintillaTextInfoNpp83
		return ScintillaTextInfoEx

	def initOverlayClass(self):
		pass

	def _get_name(self):
		# Notepad++ names the edit window "N" for some stupid reason.
		return ""

	def event_gainFocus(self):
		forPython.setLevelMark(self)
		super(NPPDocument, self).event_gainFocus()
		# Hack: finding the edit field from the foreground window is unreliable.
		# If we previously cached an object, this will clean it up, allowing it to be garbage collected.
		self.appModule.edit = None
		self.appModule._edit = weakref.ref(self)

	def event_loseFocus(self):
		# Hack: finding the edit field from the foreground window is unreliable, so cache it here.
		# We can't use the weakref cache, because NVDA probably (?) kill this object off when it loses focus.
		# Also, derek is too lazy to verify this when it already works.
		self.appModule.edit = self

	def event_typedCharacter(self, ch):
		super(NPPDocument, self).event_typedCharacter(ch)
		if not _addonConfigManager.toggleLineLengthIndicator(False):
			return
		textInfo = self.makeTextInfo(textInfos.POSITION_CARET)
		textInfo.expand(textInfos.UNIT_LINE)
		if textInfo.bookmark.endOffset - textInfo.bookmark.startOffset >= _addonConfigManager.getMaxLineLength():
			tones.beep(500, 50)

	def event_caret(self):
		super(NPPDocument, self).event_caret()
		if not _addonConfigManager.toggleLineLengthIndicator(False):
			return
		# stop overflowingBeepTimer if it's running
		if self.overfflowingBeepTimer is not None:
			self.overfflowingBeepTimer .Stop()
			self.overfflowingBeepTimer = None
		pos = self._getStatusLineInfos()["Col"]
		if int(pos) > _addonConfigManager.getMaxLineLength():
			# after goToFirstOverflowingCharacter script, there are several event_caret
			# so delay the emission of the beep
			self.overfflowingBeepTimer = wx.CallLater(450, tones.beep, 500, 50)

	def checkForDSpellCheckErrors(self, text):
		global _dSpellCheckReportDelay

		def callback(prevClipData):
			clipdataText = api.getClipData()
			if prevClipData != "":
				api.copyToClip(prevClipData)
			if clipdataText == "":
				return
			errors = clipdataText.splitlines()
			if len(errors) > 200:
				return
			from nvwave import playWaveFile
			for error in errors:
				if error in text:
					playWaveFile(os.path.join(globalVars.appDir, "waves", "textError.wav"))
					return

		if _dSpellCheckReportDelay is not None:
			_dSpellCheckReportDelay .Stop()
		_dSpellCheckReportDelay = None
		text = text.replace("\n", "")
		text = text.replace("\r", "")
		if text == "":
			return
		try:
			prevClipData = api.getClipData()
		except Exception:
			prevClipData = ""
		queueHandler.queueFunction(
			queueHandler.eventQueue,
			_copyAllMisspelledWordsToClipboardGesture .send)
		wx.CallLater(300, callback, prevClipData)

	def _caretScriptPostMovedHelper(self, speakUnit, gesture, info=None):
		if isScriptWaiting():
			return
		if not info:
			try:
				info = self.makeTextInfo(textInfos.POSITION_CARET)
			except Exception:
				return
		# Forget the word currently being typed as the user has moved the caret somewhere else.
		speech.clearTypedWordBuffer()
		review.handleCaretMove(info)
		if speakUnit and (not gesture or not willSayAllResume(gesture)):
			info.expand(speakUnit)
			if speakUnit == textInfos.UNIT_LINE and _addonConfigManager.toggleReportSpellingErrorsOption(False):
				global _dSpellCheckReportDelay
				if _dSpellCheckReportDelay is not None:
					_dSpellCheckReportDelay .Stop()
				_dSpellCheckReportDelay = wx.CallLater(300, self.checkForDSpellCheckErrors, info.text)
			forPython.mySpeakTextInfo(info, unit=speakUnit, reason=OutputReason.CARET)
		braille.handler.handleCaretMove(self)

	def script_HomeKey(self, gesture):
		gesture.send()
		time.sleep(0.3)
		api.processPendingEvents()
		forPython.SayPosition()
		obj = api.getFocusObject()
		info = obj.makeTextInfo(textInfos.POSITION_CARET)
		info.expand(textInfos.UNIT_CHARACTER)
		speech.speakMessage(info.text)

	def script_EnterKey(self, gesture):
		def callback(oldLine):
			info = self.makeTextInfo(textInfos.POSITION_CARET)
			line = info.getCurrentLineNumber()
			if line != oldLine:
				forPython.SayPosition()
		info = self.makeTextInfo(textInfos.POSITION_CARET)
		oldLine = info.getCurrentLineNumber()
		gesture.send()
		wx.CallLater(400, callback, oldLine)

	@script(
		# Translators: Input help mode message for move To previous Line With Only Tab Or Space command.
		description=makeDesc(PRE_Line, _("Move to previous line with only tab or space")),
		category=_scriptCategory,
		gestures=("kb:windows+control+shift+n",)
	)
	def script_moveToPreviousLineWithOnlyTabOrSpace(self, gesture):
		info = self.makeTextInfo(textInfos.POSITION_CARET)
		PythonDocument.moveToLineWithOnlyTabOrSpace(info, False)

	@script(
		# Translators: Input help mode message for move To Next Line With Only Tab Or Space command.
		description=makeDesc(PRE_Line, _("Move to next line with only tab or space")),
		category=_scriptCategory,
		gestures=("kb:windows+control+n",)
	)
	def script_moveToNextLineWithOnlyTabOrSpace(self, gesture):
		info = self.makeTextInfo(textInfos.POSITION_CARET)
		PythonDocument.moveToLineWithOnlyTabOrSpace(info, True)

	@script(
		# Translators: Input help mode message for move To Next Line Ending With Tab Or Space command.
		description=makeDesc(PRE_Line, _("Move to next line ending with tab or space character")),
		category=_scriptCategory,
		gestures=("kb:windows+control+k",)
	)
	def script_moveToNextLineEndingWithTabOrSpace(self, gesture):
		info = self.makeTextInfo(textInfos.POSITION_CARET)
		PythonDocument.moveToLineEndingWithTabOrspace(info, True)

	@script(
		# Translators: Input help mode message for move To previous Line Ending With Tab Or Space command.
		description=makeDesc(PRE_Line, _("Move to previous line ending with tab or space character")),
		category=_scriptCategory,
		gestures=("kb:windows+control+shift+k",)
	)
	def script_moveToPreviousLineEndingWithTabOrSpace(self, gesture):
		info = self.makeTextInfo(textInfos.POSITION_CARET)
		PythonDocument.moveToLineEndingWithTabOrspace(info, False)

	@script(
		# Translators: Input help mode message for move To next Class command.
		description=makeDesc(PRE_Python, _("Move to next python class")),
		category=_scriptCategory,
		gestures=("kb:alt+f9",)
	)
	def script_moveToNextClass(self, gesture):
		info = self.makeTextInfo(textInfos.POSITION_CARET)
		PythonDocument.nextClass(info)

	@script(
		# Translators: Input help mode message for move To Previous Class command.
		description=makeDesc(PRE_Python, _("Move to previous python class")),
		category=_scriptCategory,
		gestures=("kb:alt+f8",)
	)
	def script_moveToPreviousClass(self, gesture):
		info = self.makeTextInfo(textInfos.POSITION_CARET)
		PythonDocument.previousClass(info)

	@script(
		# Translators: Input help mode message for move To Next Method command.
		description=makeDesc(PRE_Python, _("Move to next python method")),
		category=_scriptCategory,
		gestures=("kb:control+f9",)
	)
	def script_moveToNextMethod(self, gesture):
		info = self.makeTextInfo(textInfos.POSITION_CARET)
		PythonDocument.nextMethod(info)

	@script(
		# Translators: Input help mode message for move To Previous Method command.
		description=makeDesc(PRE_Python, _("Move to previous python method")),
		category=_scriptCategory,
		gestures=("kb:control+f8",)
	)
	def script_moveToPreviousMethod(self, gesture):
		info = self.makeTextInfo(textInfos.POSITION_CARET)
		PythonDocument.previousMethod(info)

	@script(
		# Translators: Input help mode message for move To Next Class Or Method command.
		description=makeDesc(PRE_Python, _("Move to next python class or method")),
		category=_scriptCategory,
		gestures=("kb:control+alt+f9",)
	)
	def script_moveToNextClassOrMethod(self, gesture):
		info = self.makeTextInfo(textInfos.POSITION_CARET)
		PythonDocument.nextClassOrMethod(info)

	@script(
		# Translators: Input help mode message for move To Previous Class Or Method command.
		description=makeDesc(PRE_Python, _("Move to previous python class or method")),
		category=_scriptCategory,
		gestures=("kb:control+alt+f8",)
	)
	def script_moveToPreviousClassOrMethod(self, gesture):
		info = self.makeTextInfo(textInfos.POSITION_CARET)
		PythonDocument.previousClassOrMethod(info)

	def script_reportIndent(self, gesture):
		info = self.makeTextInfo(textInfos.POSITION_CARET)
		col = info.getCurrentColumn()
		lineID = info.getCurrentLineNumber()
		indentPos = info.getLineIndentPosition(lineID)
		gesture.send()
		if col > indentPos:
			speech.speakMessage(gesture.displayName)
			return
		time.sleep(0.1)
		self._caretScriptPostMovedHelper(textInfos.UNIT_LINE, None, None)

	def setLevel(self, level):
		info = self.makeTextInfo(textInfos.POSITION_CARET)
		lineID = info.getCurrentLineNumber()
		indentPos = info.getLineIndentPosition(lineID)
		watchdog.cancellableSendMessage(info.obj.windowHandle, SCI_GOTOPOS, indentPos, 0)
		watchdog.cancellableSendMessage(info.obj.windowHandle, SCI_DELLINELEFT, 0, 0)
		if level:
			i = level
			while i:
				watchdog.cancellableSendMessage(info.obj.windowHandle, SCI_TAB, 0, 0)
				i = i - 1

		self._caretScriptPostMovedHelper(textInfos.UNIT_LINE, None, None)

	@script(
		# Translators: Input help mode message for delete indentation command.
		description=makeDesc(PRE_Line, _("Delete indentation")),
		category=_scriptCategory,
		gestures=("kb:control+%s" % chr(0xb2), "kb:control+0",)
	)
	def script_deleteIndentation(self, gesture):
		self.setLevel(0)

	# Translators: Input help mode message for set  indentation level command.
	setLevelToDoc = _("Set the indentation to level {level} ({level} tabs)")

	@script(
		# Translators: Input help mode message for set  indentation level command.
		description=makeDesc(PRE_Line, _("Set the indentation to level 1(1 tab)")),
		category=_scriptCategory,
		gesture="kb:control+1"
	)
	def script_setLevel1(self, gesture):
		self.setLevel(1)

	@script(
		description=makeDesc(PRE_Line, setLevelToDoc.format(level=2)),
		category=_scriptCategory,
		gesture="kb:control+2"
	)
	def script_setLevel2(self, gesture):
		self.setLevel(2)

	@script(
		description=makeDesc(PRE_Line, setLevelToDoc.format(level=3)),
		category=_scriptCategory,
		gesture="kb:control+3"
	)
	def script_setLevel3(self, gesture):
		self.setLevel(3)

	@script(
		description=makeDesc(PRE_Line, setLevelToDoc.format(level=4)),
		category=_scriptCategory,
		gesture="kb:control+4"
	)
	def script_setLevel4(self, gesture):
		self.setLevel(4)

	@script(
		description=makeDesc(PRE_Line, setLevelToDoc.format(level=5)),
		category=_scriptCategory,
		gesture="kb:control+5"
	)
	def script_setLevel5(self, gesture):
		self.setLevel(5)

	@script(
		description=makeDesc(PRE_Line, setLevelToDoc.format(level=6)),
		category=_scriptCategory,
		gesture="kb:control+6"
	)
	def script_setLevel6(self, gesture):
		self.setLevel(6)

	@script(
		description=makeDesc(PRE_Line, setLevelToDoc.format(level=7)),
		category=_scriptCategory,
		gesture="kb:control+7"
	)
	def script_setLevel7(self, gesture):
		self.setLevel(7)

	@script(
		description=makeDesc(PRE_Line, setLevelToDoc.format(level=8)),
		category=_scriptCategory,
		gesture="kb:control+8"
	)
	def script_setLevel8(self, gesture):
		self.setLevel(8)

	@script(
		description=makeDesc(PRE_Line, setLevelToDoc.format(level=9)),
		category=_scriptCategory,
		gesture="kb:control+9"
	)
	def script_setLevel9(self, gesture):
		self.setLevel(9)

	def script_goToMatchingBrace(self, gesture):
		gesture.send()
		info = self.makeTextInfo(textInfos.POSITION_CARET).copy()
		# Expand to line.
		info.expand(textInfos.UNIT_LINE)
		if info.text.strip() in ['{', '}', "(", ")"]:
			# This line is only one brace. Not very helpful to read, lets read the previous and next line as well.
			# Move it's start back a line.
			info.move(textInfos.UNIT_LINE, -1, endPoint="start")
			# Move it's end one line, forward.
			info.move(textInfos.UNIT_LINE, 1, endPoint="end")
			# speak the info.
			registerGeneratorObject((speech.speakMessage(i) for i in info.text.split("\n")))
		else:
			text = forPython.FormatLine(info.text)
			speech.speakMessage(text)

	def script_goToNextBookmark(self, gesture):
		self.speakActiveLineIfChanged(gesture)

	def script_goToPreviousBookmark(self, gesture):
		self.speakActiveLineIfChanged(gesture)

	def speakActiveLineIfChanged(self, gesture):
		old = self.makeTextInfo(textInfos.POSITION_CARET)
		gesture.send()
		new = self.makeTextInfo(textInfos.POSITION_CARET)
		if new.bookmark.startOffset != old.bookmark.startOffset:
			new.expand(textInfos.UNIT_LINE)
			text = forPython.FormatLine(new.text)
			speech.speakMessage(text)
		else:
			# Translators: message to the user to report no more bookmark.
			speech.speakMessage(_("No more bookmark"))

	def script_reportLineOverflow(self, gesture):
		if self.appModule.isAutocomplete:
			gesture.send()
			return
		self.script_caret_moveByLine(gesture)
		if not _addonConfigManager.toggleLineLengthIndicator(False):
			return
		info = self.makeTextInfo(textInfos.POSITION_CARET)
		info.expand(textInfos.UNIT_LINE)
		if len(info.text.strip('\r\n\t ')) > _addonConfigManager.getMaxLineLength():
			tones.beep(500, 50)

	@script(
		# Translators: Input help mode message for toggleLongLineindicatorcommand.
		description=_("Toggle long line indicator"),
		category=_scriptCategory,
		gestures=("kb:windows+control+f4", )
	)
	def script_toggleLongLineIndicator(self, gesture):
		if _addonConfigManager.toggleLineLengthIndicator(True):
			# Translators: message to user to report long lines.
			speech.speakMessage(_("Report  Long lines"))
		else:
			# Translators: message to user to  long line report desactivated.
			speech.speakMessage(_("Don't report long lines"))

	@script(
		# Translators: Input help mode message for go to next long line command.
		description=makeDesc(PRE_Line, _("Go to next line that is exceeds the maximum line length")),
		category=_scriptCategory,
		gestures=("kb:windows+control+l",)
	)
	def script_goToNextLongLine(self, gesture):
		info = self.makeTextInfo(textInfos.POSITION_CARET)
		PythonDocument.goToLongLine(info, True)

	@script(
		# Translators: Input help mode message for go to previous long line command.
		description=makeDesc(PRE_Line, _("Go to previous line that is exceeds the maximum line length")),
		category=_scriptCategory,
		gestures=("kb:windows+control+shift+l",)
	)
	def script_goToPreviousLongLine(self, gesture):
		info = self.makeTextInfo(textInfos.POSITION_CARET)
		PythonDocument.goToLongLine(info, False)

	@script(
		# Translators: Input help mode message for go To First Overflowing Character command.
		description=makeDesc(PRE_Line, _("Moves to the first character that is after the maximum line length")),
		category=_scriptCategory,
		gestures=("kb:windows+control+o",)
	)
	def script_goToFirstOverflowingCharacter(self, gesture):
		print("goToFirstOverflowingCharacter")
		info = self.makeTextInfo(textInfos.POSITION_CARET)
		info.expand(textInfos.UNIT_LINE)
		if len(info.text) > _addonConfigManager.getMaxLineLength():
			info.move(textInfos.UNIT_CHARACTER, _addonConfigManager.getMaxLineLength(), "start")
			info.updateCaret()
			info.collapse()
			info.expand(textInfos.UNIT_CHARACTER)
			speech.speakMessage(info.text)

	def _getStatusLineInfos(self):
		info = self.parent.next.next.firstChild.getChild(2).name
		info = info.replace(chr(0xa0), "")
		tempList = info.split("    ")
		d = {}
		for item in tempList:
			(name, value) = item.strip().split(" : ")
			d[name] = value
		return d

	@script(
		# Translators: Input help mode message for report Line Info command.
		description=makeDesc(PRE_Line, _(
			"Report current caret position."
			" Twice: report number of selected characters"
		)),
		category=_scriptCategory,
		gestures=("kb:windows+control+i",)
	)
	def script_reportLineInfo(self, gesture):
		global _scriptTimer
		if _scriptTimer is not None:
			_scriptTimer.Stop()
			_scriptTimer = None
		info = self._getStatusLineInfos()
		if scriptHandler.getLastScriptRepeatCount() == 0:
			# Translators: message to user to report current position.
			msg = _("line {0}, column {1}") .format(info["Ln"], info["Col"])
		else:
			selection = info["Sel"].split(" | ")
			if int(selection[0]) == 0:
				msg = _("no selection")
			else:
				nb = int(selection[0])
				nbCharsMsg = _("%s characters selectionned") % nb if nb > 1 else _("one character selected")
				nbLinesMsg = _("%s lines") % selection[1] if int(selection[1]) > 1 else _("one line")
				msg = _("{0} selected on {1}") .format(nbCharsMsg, nbLinesMsg)
		ui.message(msg)

	def script_reportFindResult(self, gesture):
		old = self.makeTextInfo(textInfos.POSITION_SELECTION)
		gesture.send()
		new = self.makeTextInfo(textInfos.POSITION_SELECTION)
		if new.bookmark.startOffset != old.bookmark.startOffset:
			new.expand(textInfos.UNIT_LINE)
			text = forPython.FormatLine(new.text)
			speech.speakMessage(text)
		else:
			# Translators: Message shown when there are no more search results in this direction
			# using the notepad++ find command.
			speech.speakMessage(_("No more search results in this direction"))

	@script(
		# Translators: Input help mode message for convert To HTMLDialog command.
		description=makeDesc(
			PRE_Markdown,
			_(
				"Open the dialog to Treat the edit window content as MarkDown or txt2tags document "
				"and display it as webpage in the internal or external default browser"
				"Twice: treate with last selected parameters.")
		),
		category=_scriptCategory,
		gestures=("kb:windows+control+f8",)
	)
	def script_convertToHTMLDialog(self, gesture):
		global _scriptTimer

		if _scriptTimer is not None:
			_scriptTimer.Stop()
			_scriptTimer = None
		document = self.makeTextInfo(textInfos.POSITION_ALL).text
		if scriptHandler.getLastScriptRepeatCount() == 0:
			_scriptTimer = wx.CallLater(250, npp_convert.ConvertToHTMLDialog.run, document)
		else:
			conv = npp_convert.ConvertToHTML(document)
			wx.CallLater(100, conv.convertAndDisplay, )

	# Translators: open the dialog to interprets the edit window content as markdown
	# or t2tToTags document and shows it in the internal or in the external (default) Browser

	def script_tabChange(self, gesture):

		def tabChange():
			obj = api.getFocusObject()
			eventHandler.queueEvent("focusEntered", api.getForegroundObject())
			eventHandler.queueEvent("gainFocus", obj)
			npp_application.Tabs().sayCurrentDocumentPosition()
		gesture.send()
		wx.CallLater(200, tabChange)

	@script(
		# Translators: Input help mode message for compare Selection To Clip  command.
		description=makeDesc(PRE_Document, _("Compare selected text to text in clipboard")),
		category=_scriptCategory,
		gestures=("kb:windows+control+f2",),
	)
	def script_compareSelectionToClip(self, gesture):

		clipDatas = api.getClipData()
		if len(clipDatas) == 0:
			speech.speakMessage(_("clipboard is empty"))
			return
		infos = self.getSelectionInfo()
		if infos is None:
			speech.speakMessage(_("no selection"))
			return
		textList = []

		f1 = infos.text.splitlines()
		f2 = clipDatas.splitlines()
		f1_line = f1[0] if len(f1) else None
		f2_line = f2[0] if len(f2) else None
		line_no = 1
		# Loop if either file1 or file2 has not reached EOF
		while f1_line is not None or f2_line is not None:
			# Strip the leading whitespaces
			if f1_line is None:
				f1_line = ""
			f1_line = f1_line.rstrip()
			if f2_line is None:
				f2_line = ""
			f2_line = f2_line.rstrip()
			# Compare the lines from both file
			if f1_line != f2_line:
				# If a line does not exist on file2 then mark the output with + sign
				if f2_line == '' and f1_line != '':
					textList.append(">+" + "Line-%d: " % line_no + f1_line)
				# otherwise output the line on file1 and mark it with > sign
				elif f1_line != '':
					textList.append(">" + "Line-%d: " % line_no + f1_line)
				# If a line does not exist on file1 then mark the output with + sign
				if f1_line == '' and f2_line != '':
					textList.append("<+" + "Line-%d: " % line_no + f2_line)
				# otherwise output the line on file2 and mark it with < sign
				elif f2_line != '':
					textList.append("<" + "Line-%d: " % line_no + f2_line)
				textList.append("")
			# Read the next line from the file
			f1_line = f1[line_no] if line_no < len(f1) else None
			f2_line = f2[line_no] if line_no < len(f2) else None
			# Increment line counter
			line_no += 1
		text = "\n".join(textList)
		# Translators: this is the title of informationdialog box to show text differences.
		dialogTitle = _("Differences between selected text and text in clipboard")
		InformationDialog.run(None, dialogTitle, "", text)

	def moveToHeading(self, next=True):
		focus = api.getFocusObject()
		if hasattr(self, "treeInterceptor") and self.treeInterceptor:
			obj = self.treeInterceptor
		else:
			ti = treeInterceptorHandler.update(self, force=True)
			if focus in ti:
				focus.treeInterceptor = ti
				obj = focus.treeInterceptor
		if not next:
			obj.script_previousHeading(None)
		else:
			obj.script_nextHeading(None)

	@script(
		# Translators: Input help mode message for move To Previous Heading command.
		description=makeDesc(PRE_Document, NVDAString("moves to the previous heading")),
		category=_scriptCategory,
		gestures=("kb:windows+control+shift+h",)
	)
	def script_moveToPreviousHeading(self, gesture):
		self.moveToHeading(False)

	@script(
		# Translators: Input help mode message for move To next Heading command.
		description=makeDesc(PRE_Document, NVDAString("moves to the next heading")),
		category=_scriptCategory,
		gestures=("kb:windows+control+h",)
	)
	def script_moveToNextHeading(self, gesture):
		self.moveToHeading(True)

	@script(
		# Translators: Input help mode message for import With Python command.
		description=makeDesc(PRE_Python, _("Import document's text as a Python module")),
		category=_scriptCategory,
		gestures=("kb:windows+control+f7",)
	)
	def script_importWithPython(self, gesture):
		focus = api.getFocusObject()
		ti = focus.makeTextInfo(textInfos.POSITION_ALL)
		code = ti.text
		try:
			PythonDocument.importCode(code, "essai")
			speech.speakMessage(_("python code imported without error"))
		except InterpreterError as err:
			speech.speakMessage("%s" % err)
			info = self.makeTextInfo(textInfos.POSITION_CARET)
			info.expand(textInfos.UNIT_STORY)
			lineID = err.lineNumber - 1
			info.goToLine(lineID)
