# coding :utf-8
# appModules\notepad++\__init__.py
# a part of notepadPlusPlusAccessEnhancement add-on
# Copyright (C) 2020-2023 paulber19
# Released under GPL2


import addonHandler
import core
import wx
import os
from scriptHandler import script

from controlTypes.role import Role
import eventHandler
import speech
import ui
import api
import NVDAObjects
from . import npp_editWindow
from .npp_scriptDesc import PRE_Line, makeDesc
from . import npp_incrementalFind, npp_autocomplete
from . import forPython
from . import npp_application
import sys
_curAddon = addonHandler.getCodeAddon()
debugToolsPath = os.path.join(_curAddon.path, "debugTools")
sys.path.append(debugToolsPath)
try:
	from appModuleDebug import AppModuleDebug as AppModule
	from appModuleDebug import printDebug, toggleDebugFlag
except ImportError:
	from appModuleHandler import AppModule as AppModule

	def printDebug(msg):
		return

	def toggleDebugFlag():
		return
del sys.path[-1]
sharedPath = os.path.join(_curAddon.path, "shared")
sys.path.append(sharedPath)
from npp_addonConfigManager import _addonConfigManager, Mode_SayLevel, indentReportModeLabels
del sys.path[-1]


addonHandler.initTranslation()
_addonSummary = _curAddon.manifest['summary']
_addonVersion = _curAddon.manifest['version']
_addonName = _curAddon.manifest['name']
_scriptCategory = _addonSummary


class MainWindow(NVDAObjects.IAccessible.IAccessible):
	def initOverlayClass(self):
		self.tabs = npp_application.Tabs(self)

	def _get_name(self):
		name = super(MainWindow, self)._get_name()
		# name is often too long so reduce filename path in name
		name = npp_application.reducePath(name)
		return name

	def event_foreground(self, ):
		super(MainWindow, self).event_foreground()
		self.tabs.sayCurrentDocumentPosition()
		self.appModule.mainWindow = self


class ListItem (NVDAObjects.IAccessible.IAccessible):
	def _get_name(self):
		name = super(ListItem, self)._get_name()
		if hasattr(self, "reducedName") or name is None:
			return name
		# name is often too long so reduce filename path in name
		if not _addonConfigManager.toggleReduceFilePathOption(False):
			return name
		# to don't speak the path of an tabs item's list,
		# we must to know if it's an item of tabs list
		try:
			tabsList = self.appModule.mainWindow.tabs.getTabs(returnNames=True)
			for item in tabsList:
				if item == name[-1 * len(item):]:
					name = npp_application.reducePath(name)
					self.reducedName = True
					break
		except Exception:
			pass
		return name


class DocumentListItem (NVDAObjects.IAccessible.IAccessible):
	_lastFocusedObject = None
	delay = None

	def _get_name(self):
		name = super(DocumentListItem, self)._get_name()
		if name and chr(0x21f5) in name:
			name = name.replace("%s " % chr(0x21f5), "")
		path = self.firstChild.next.name
		tempList = path.split("\\")
		reducedPath = "\\".join(npp_application._reducePath(tempList))
		name = name.replace(path, reducedPath)
		columns = _addonConfigManager.getDocumentColumnsChoices()
		nameList = name.split(";")
		newList = [nameList[0]]
		i = 1
		for index in range(1, len(self.children)):
			childName = self.getChild(index).name
			if not childName:
				continue
			if (index - 1) in columns:
				newList.append(nameList[i])
			i += 1
		return ";".join(newList)

	def event_selection(self):
		pass

	def event_selectionRemove(self):
		pass

	def _gainFocus(self):
		if DocumentListItem.delay is not None:
			DocumentListItem.delay .Stop()
			DocumentListItem.delay = None
		self.reportFocus()

	def event_gainFocus(self):
		if DocumentListItem.delay is not None:
			DocumentListItem.delay .Stop()
		DocumentListItem.delay = wx.CallLater(10, self._gainFocus)

	def event_typedCharacter(self, ch):
		super(DocumentListItem, self).event_typedCharacter(ch)
		lastFocus = DocumentListItem ._lastFocusedObject
		index = lastFocus.IAccessibleChildID - 1
		objs = self.parent.children
		before = objs[:index]
		after = objs[index + 1:-1]
		choices = after + before
		from oleacc import SELFLAG_TAKESELECTION, SELFLAG_TAKEFOCUS
		for obj in choices:
			if obj.name.lower().startswith(ch):
				obj.IAccessibleObject.accSelect(SELFLAG_TAKEFOCUS, obj.IAccessibleChildID)
				obj.IAccessibleObject.accSelect(SELFLAG_TAKESELECTION, obj.IAccessibleChildID)
				return
		# after a typed character, the focus is put on the first item of the document list.
		# if there is no new document, we want that the focus don't move.
		lastFocus.IAccessibleObject.accSelect(SELFLAG_TAKEFOCUS, lastFocus.IAccessibleChildID)
		lastFocus.IAccessibleObject.accSelect(SELFLAG_TAKESELECTION, lastFocus.IAccessibleChildID)


import winInputHook
_winInputHookKeyDownCallback = None


def internal_keyDownEventEx(vkCode, scanCode, extended, injected):
	focus = api.getFocusObject()
	if focus.role == Role.LISTITEM and focus.windowControlID == 7001:
		DocumentListItem ._lastFocusedObject = focus
	return _winInputHookKeyDownCallback(vkCode, scanCode, extended, injected)


class AppModule(AppModule):
	scriptCategory = _scriptCategory

	def __init__(self, *args, **kwargs):
		super(AppModule, self).__init__(*args, **kwargs)
		toggleDebugFlag()
		printDebug("notePadPlusPlusAccessEnhancement appModule init")
		self.requestEvents()
		self.isAutocomplete = False

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		if obj.windowClassName == "Notepad++" and obj.role == Role.PANE:
			clsList.insert(0, MainWindow)
			self.mainWindow = obj
			return
		# code written by Tuukka Ojala, Derek Riemer
		if obj.windowClassName == "Scintilla" and obj.windowControlID == 0:
			clsList.insert(0, npp_editWindow.NPPDocument)
			return
		try:
			if obj.role == Role.LISTITEM and (
				obj.parent.windowClassName == "ListBox" and obj.parent.parent.parent.windowClassName == "ListBoxX"):
				clsList.insert(0, npp_autocomplete.AutocompleteList)
				return
		except AttributeError:
			pass
		if (
			(obj.windowControlID == 1682 and obj.role == Role.EDITABLETEXT)
			or (
				obj.role == Role.BUTTON and obj.windowControlID in (67220, 67219))
		):
			clsList.insert(0, npp_incrementalFind.IncrementalFind)
			return
		if obj.windowControlID == 1689 and obj.role == Role.STATICTEXT:
			clsList.insert(0, npp_incrementalFind.LiveTextControl)
			return
		if obj.role == Role.LISTITEM:
			if obj.windowControlID == 7001:
				# list item in document window
				clsList.insert(0, DocumentListItem)
			else:
				clsList.insert(0, ListItem)
			return

	def terminate(self):
		super(AppModule, self).terminate()

	# code written by Tuukka Ojala, Derek Riemer
	def requestEvents(self):
		# We need these for autocomplete
		eventHandler.requestEvents("show", self.processID, "ListBoxX")

	# code written by Tuukka Ojala, Derek Riemer
	def event_show(self, obj, nextHandler):
		if obj.role == Role.PANE:
			self.isAutocomplete = True
			core.callLater(100, self.waitforAndReportDestruction, obj)
			# get the edit field if the weak reference still has it.
			edit = self._edit() if hasattr(self, "_edit") else None
			if not edit:
				return
			eventHandler.executeEvent("suggestionsOpened", edit)
		nextHandler()

	# code written by Tuukka Ojala, Derek Riemer
	def waitforAndReportDestruction(self, obj):
		if obj.parent:
			core.callLater(100, self.waitforAndReportDestruction, obj)
			return
		# The object is dead.
		self.isAutocomplete = False
		# get the edit field if the weak reference still has it.
		edit = self._edit() if hasattr(self, "_edit") else None
		if not edit:
			return
		eventHandler.executeEvent("suggestionsClosed", edit)

	@script(
		# Translators: Input help mode message for toggle Manage Line Number And Indentation Announcement command.
		description=_("Toggle line number and indentation's announcement management by add-on")
	)
	def script_toggleManageLineNumberAndIndentationAnnouncement(self, gesture):
		if _addonConfigManager.toggleManageLineNumberAndIndentationAnnouncementOption():
			# Translators: message to user to report line number and indentation's announcement by add-on")
			speech.speakMessage(_("Line number and indentation's announcement by add-on"))
		else:
			# Translators: message to user to report line indentation 'sannouncement by NVDA.
			speech.speakMessage(_("Line number and indentation's announcement by NVDA"))

	def getSelectionInfo(self):
		import textInfos
		obj = api.getFocusObject()
		treeInterceptor = obj.treeInterceptor
		if hasattr(treeInterceptor, 'TextInfo') and not treeInterceptor.passThrough:
			obj = treeInterceptor
		try:
			info = obj.makeTextInfo(textInfos.POSITION_SELECTION)
		except (RuntimeError, NotImplementedError):
			info = None
		if not info or info.isCollapsed:
			return None
		return info

	def compareSelectionToClip1(self):
		clipDatas = api.getClipData()
		if len(clipDatas) == 0:
			speech.speakMessage(_("clipboard is empty"))
			return
		infos = self.getSelectionInfo()
		if infos is None:
			speech.speakMessage(_("no selection"))
			return
		textList = []
		f1 = infos.text.split()
		f2 = clipDatas.split()
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
				# Print a blank line
				textList.append("")
			# Read the next line from the file
			f1_line = f1[line_no] if line_no < len(f1) else None
			f2_line = f2[line_no] if line_no < len(f2) else None
			# Increment line counter
			line_no += 1

	@script(
		# Translators: Input help mode message for toggle Report Line Indentation command.
		description=makeDesc(PRE_Line, _("Toggle line indentation reporting")),
		gestures=("kb:windows+alt+f6",)
	)
	def script_toggleReportLineIndentation(self, gesture):
		if not _addonConfigManager.toggleManageLineNumberAndIndentationAnnouncementOption(False):
			# Translators: message to user to impossibility to do it
			speech.speakMessage(
				_("Impossible, the number and the indentation of the lines are not announced by the extension"))
			return
		_addonConfigManager.toggleReportLineIndentationOption(True)
		mode = _addonConfigManager.getIndentReportMode()
		msg = indentReportModeLabels[mode]
		speech.speakMessage(msg)

	@script(
		# Translators: Input help mode message for toggle Indent Report Mode command.
		description=makeDesc(PRE_Line, _("Choose line indentation announcement's format")),
		gestures=("kb:windows+control+f6",)
	)
	def script_toggleIndentReportMode(self, gesture):
		if not _addonConfigManager.toggleManageLineNumberAndIndentationAnnouncementOption(False):
			# Translators: message to user to impossibility to do it
			speech.speakMessage(
				_("Impossible, the number and the indentation of the lines are not announced by the extension"))
			return
		mode = _addonConfigManager.toggleIndentReportMode()
		msg = indentReportModeLabels[mode]
		speech.speakMessage(msg)
		if mode == Mode_SayLevel:
			if forPython.GB_sLevelMark[-1:] == "E":
				speech.speakMessage(_("The increment is %s spaces") % forPython.GB_sLevelMark[:-1])
			else:
				speech.speakMessage(_("The increment is %s Tab") % forPython.GB_sLevelMark[:-1])

	@script(
		# Translators: Input help mode message for toggle Report Line Number Option command.
		description=makeDesc(PRE_Line, _("Activate/desactivate the line number's announcement")),
		gestures=("kb:windows+control+f5",)
	)
	def script_toggleReportLineNumberOption(self, gesture):
		if not _addonConfigManager.toggleManageLineNumberAndIndentationAnnouncementOption(False):
			# Translators: message to user to impossibility to do it
			speech.speakMessage(
				_("Impossible, the number and the indentation of the lines are not announced by the extension"))
			return
		reportLineNumber = _addonConfigManager.toggleReportLineNumberOption()
		if reportLineNumber:
			# Translators: message to the user to report line number' announcement indicator state.
			ui.message(_("Say line number"))
		else:
			# Translators: message to the user to report line number' announcement indicator state.
			ui.message(_("Don't say line number"))

	@script(
		# Translators: Input help mode message for toggle report spelling errors option command.
		description=_("Toggle report spelling errors option")
	)
	def script_toggleReportSpellingErrorsOption(self, gesture):
		option = _addonConfigManager.toggleReportSpellingErrorsOption()
		if option:
			# Translators: message to the user to report spelling errors reporting.
			ui.message(_("Report spelling errors"))
		else:
			# Translators: message to the user to don't report spelling errors.
			ui.message(_("Don't report spelling errors"))

	def event_NVDAObject_init(self, obj):
		pass

	def event_appModule_gainFocus(self):
		printDebug("appModule notePadPlusPlus: event_appModulegainFocus")
		global _winInputHookKeyDownCallback
		_winInputHookKeyDownCallback = winInputHook.keyDownCallback
		winInputHook.setCallbacks(keyDown=internal_keyDownEventEx)

	def event_appModule_loseFocus(self):
		printDebug("appModule notepadPlusPlus: event_appModuleLoseFocus")
		if _winInputHookKeyDownCallback is not None:
			winInputHook.setCallbacks(keyDown=_winInputHookKeyDownCallback)

	def script_test(self, gesture):
		print("Notepad ++ test")
		ui.message("Notepad ++ test")

	__gestures = {
		"kb:alt+control+f10": "test",
	}
