# appModules\notepad++\npp_browseMode.py
# A part of notepadPlusPlusAccessEnhancement addon
# Copyright (C) 2020-2023 paulber19
# This file is covered by the GNU General Public License.

import addonHandler
import browseMode
import re
import textInfos
from speech.sayAll import CURSOR
import winUser
import treeInterceptorHandler
import ui
from scriptHandler import willSayAllResume
import speech
from textInfos import DocumentWithPageTurns
from . import forPython
import os
import sys
from controlTypes.outputReason import OutputReason


_curAddon = addonHandler.getCodeAddon()
sharedPath = os.path.join(_curAddon.path, "shared")
sys.path.append(sharedPath)
from npp_NVDAStrings import NVDAString
del sys.path[-1]

addonHandler.initTranslation()


class ElementsListDialog(browseMode.ElementsListDialog):
	ELEMENT_TYPES = (
		browseMode.ElementsListDialog.ELEMENT_TYPES[1],
		browseMode.ElementsListDialog.ELEMENT_TYPES[0],
		("blockQuote", _("block quote")),
	)

	def initElementType(self, elType):
		super(ElementsListDialog, self).initElementType(elType)
		self.activateButton.Disable()
		self.SetAffirmativeId(self.moveButton.GetId())


class NPPDocumentBrowseModeTextInfo(treeInterceptorHandler.RootProxyTextInfo):
	def __init__(self, obj, position):
		from .npp_editWindow import NPPDocument
		if isinstance(position, NPPDocument):
			position = textInfos.POSITION_CARET
		super(NPPDocumentBrowseModeTextInfo, self).__init__(obj, position)

	def _get_focusableNVDAObjectAtStart(self):
		return self.obj.rootNVDAObject

	def find(self, searchPattern, caseSensitive=False, reverse=False, elementsList=False):
		if searchPattern is None:
			return False
		if reverse:
			inText = self.innerTextInfo._getTextRange(
				0, self.innerTextInfo._getLineOffsets(self.innerTextInfo._startOffset)[0])[::-1]
		else:
			inText = self.innerTextInfo._getTextRange(
				self.innerTextInfo._startOffset,
				self.innerTextInfo._getStoryLength()) if elementsList and self.innerTextInfo._startOffset == 0\
				else self.innerTextInfo._getTextRange(
					self.innerTextInfo._getLineOffsets(self.innerTextInfo._startOffset)[1],
					self.innerTextInfo._getStoryLength())
		m = re.search(
			searchPattern, inText, (0 if caseSensitive else re.IGNORECASE) | re.UNICODE | re.DOTALL | re.MULTILINE)
		if not m:
			return False
		if reverse:
			offset = self.innerTextInfo._getLineOffsets(self.innerTextInfo._startOffset)[0] - m.end()
		else:
			offset = self.innerTextInfo._startOffset + 1 + m.start() if elementsList and\
				self.innerTextInfo._startOffset == 0 else\
				self.innerTextInfo._getLineOffsets(self.innerTextInfo._startOffset)[1] + m.start()
		self.innerTextInfo._startOffset = self.innerTextInfo._endOffset = offset
		return True


class BrowseModeTreeInterceptorEx(browseMode.BrowseModeTreeInterceptor):
	__gestures = {}
	scriptCategory = _("Extended browse mode for Notepad++")

	@classmethod
	def addQuickNav(cls, itemType, key, nextDoc, nextError, prevDoc, prevError, readUnit=None):
		map = cls.__gestures
		"""Adds a script for the given quick nav item.
		@param itemType: The type of item, I.E. "heading" "Link" ...
		@param key: The quick navigation key to bind to the script.
		hift is automatically added for the previous item gesture. E.G. h for heading
		@param nextDoc: The command description to bind to the script that yields the next quick nav item.
		@param nextError: The error message if there are no more quick nav items of type itemType in this direction.
		@param prevDoc: The command description to bind to the script that yields the previous quick nav item.
		@param prevError: The error message if there are no more quick nav items of type itemType in this direction.
		@param readUnit: The unit (one of the textInfos.UNIT_* constants)
		to announce when moving to this type of item.
			For example, only the line is read when moving to tables to avoid reading a potentially massive table.
			If None, the entire item will be announced.
		"""
		scriptSuffix = itemType[0].upper() + itemType[1:]
		scriptName = "next%s" % scriptSuffix
		funcName = "script_%s" % scriptName
		script = lambda self, gesture: self._quickNavScript(gesture, itemType, "next", nextError, readUnit)
		script.__doc__ = nextDoc
		script.__name__ = funcName
		script.resumeSayAllMode = CURSOR.CARET
		setattr(cls, funcName, script)
		if key is not None:
			map["kb:%s" % key] = scriptName
		scriptName = "previous%s" % scriptSuffix
		funcName = "script_%s" % scriptName
		script = lambda self, gesture: self._quickNavScript(gesture, itemType, "previous", prevError, readUnit)
		script.__doc__ = prevDoc
		script.__name__ = funcName
		script.resumeSayAllMode = CURSOR.CARET
		setattr(cls, funcName, script)
		if key is not None:
			map["kb:shift+%s" % key] = scriptName


# Add quick navigation scripts.
BrowseModeTreeInterceptorEx._BrowseModeTreeInterceptorEx__gestures = (
	browseMode.BrowseModeTreeInterceptor._BrowseModeTreeInterceptor__gestures.copy())


from .npp_scriptDesc import (
	makeDesc,
	PRE_Line
)

qn = BrowseModeTreeInterceptorEx.addQuickNav
qn(
	"longLine",
	key="j",
	# Translators: Input help message for a quick navigation command in browse mode.
	nextDoc=makeDesc(PRE_Line, _("Go to next line that is exceeds the maximum line length")),
	# Translators: Message presented when the browse mode element is not found.
	nextError=_("no next long line"),
	# Translators: Input help message for a quick navigation command in browse mode.
	prevDoc=makeDesc(PRE_Line, _("Go to previous line that is exceeds the maximum line length")),
	# Translators: Message presented when the browse mode element is not found.
	prevError=_("no previous long line"))
del qn


class NPPDocumentTreeInterceptor (BrowseModeTreeInterceptorEx, browseMode.BrowseModeDocumentTreeInterceptor):

	ElementsListDialog = ElementsListDialog
	TextInfo = NPPDocumentBrowseModeTextInfo

	def __init__(self, obj):
		super(NPPDocumentTreeInterceptor, self).__init__(obj)

	def _caretMovementScriptHelper(
		self, gesture, unit, direction=None, posConstant=textInfos.POSITION_SELECTION,
		posUnit=None, posUnitEnd=False, extraDetail=False, handleSymbols=False):
		oldInfo = self.makeTextInfo(posConstant)
		info = oldInfo.copy()
		info.collapse(end=self.isTextSelectionAnchoredAtStart)
		if self.isTextSelectionAnchoredAtStart and not oldInfo.isCollapsed:
			info.move(textInfos.UNIT_CHARACTER, -1)
		if posUnit is not None:
			# expand and collapse to ensure that we are aligned with the end of the intended unit
			info.expand(posUnit)
			try:
				info.collapse(end=posUnitEnd)
			except RuntimeError:
				# MS Word has a "virtual linefeed" at the end of the document which can cause RuntimeError to be raised.
				# In this case it can be ignored.
				# See #7009
				pass
			if posUnitEnd:
				info.move(textInfos.UNIT_CHARACTER, -1)
		if direction is not None:
			info.expand(unit)
			info.collapse(end=posUnitEnd)
			if info.move(unit, direction) == 0 and isinstance(self, DocumentWithPageTurns):
				try:
					self.turnPage(previous=direction < 0)
				except RuntimeError:
					pass
				else:
					info = self.makeTextInfo(textInfos.POSITION_FIRST if direction > 0 else textInfos.POSITION_LAST)
		# #10343: Speak before setting selection because setting selection might
		# move the focus, which might mutate the document, potentially invalidating
		# info if it is offset-based.
		selection = info.copy()
		info.expand(unit)
		if not willSayAllResume(gesture):
			forPython.mySpeakTextInfo(info, unit=unit, reason=OutputReason.CARET)
		if not oldInfo.isCollapsed:
			speech.speakSelectionChange(oldInfo, selection)
		self.selection = selection

	def _get_isAlive(self):
		return winUser.isWindow(self.rootNVDAObject.windowHandle)

	def __contains__(self, obj):
		return obj == self.rootNVDAObject

	def _iterNodesByType(self, nodeType, direction="next", pos=None):
		if "heading" in nodeType:
			from .npp_quickNav import NPPDocumentHeadingsQuickNavIterator
			return NPPDocumentHeadingsQuickNavIterator(nodeType, self, direction, pos).iterate()
		elif nodeType == "link":
			from .npp_quickNav import NPPDocumentLinksQuickNavIterator
			return NPPDocumentLinksQuickNavIterator(nodeType, self, direction, pos).iterate()
		elif nodeType == "blockQuote":
			from .npp_quickNav import NPPDocumentBlockQuotesQuickNavIterator
			return NPPDocumentBlockQuotesQuickNavIterator(nodeType, self, direction, pos).iterate()
		elif nodeType == "longLine":
			from .npp_quickNav import NPPDocumentLongLinesQuickNavIterator
			return NPPDocumentLongLinesQuickNavIterator(nodeType, self, direction, pos).iterate()
		raise NotImplementedError

	def _iterNotLinkBlock(self, direction="next", pos=None):
		raise NotImplementedError

	def script_moveToStartOfContainer(self, gesture):
		ui.message(NVDAString("Not supported in this document"))

	def script_movePastEndOfContainer(self, gesture):
		ui.message(NVDAString("Not supported in this document"))
