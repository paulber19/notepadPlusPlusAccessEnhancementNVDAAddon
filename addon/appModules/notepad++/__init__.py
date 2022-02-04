# coding :utf-8
# appModules\notepad++\__init__.py
# a part of notepadPlusPlusAccessEnhancement add-on
# Copyright (C) 2020-2022 paulber19
# Released under GPL2


import addonHandler
import core
import os
from scriptHandler import script
try:
	# for nvda version >= 2021.2
	from controlTypes.role import Role
	ROLE_LISTITEM = Role.LISTITEM
	ROLE_EDITABLETEXT = Role.EDITABLETEXT
	ROLE_PANE = Role.PANE
	ROLE_BUTTON = Role.BUTTON
	ROLE_STATICTEXT = Role.STATICTEXT
except ImportError:
	from controlTypes import (
		ROLE_PANE, ROLE_LISTITEM, ROLE_EDITABLETEXT, ROLE_BUTTON, ROLE_STATICTEXT)
import eventHandler
import speech
import ui
import api
import NVDAObjects
from . import npp_editWindow
from .npp_editWindow import PRE_Line, makeDesc
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


class AppModule(AppModule):
	scriptCategory = _scriptCategory

	def __init__(self, *args, **kwargs):
		super(AppModule, self).__init__(*args, **kwargs)
		# toggleDebugFlag()
		printDebug("notePadPlusPlusAccessEnhancement appModule init")
		self.requestEvents()
		self.isAutocomplete = False

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		if obj.windowClassName == "Notepad++" and obj.role == ROLE_PANE:
			clsList.insert(0, MainWindow)
			self.mainWindow = obj
			return
		# code written by Tuukka Ojala, Derek Riemer
		if obj.windowClassName == "Scintilla" and obj.windowControlID == 0:
			clsList.insert(0, npp_editWindow.NPPDocument)
			return
		try:
			if obj.role == ROLE_LISTITEM and (
				obj.parent.windowClassName == "ListBox" and obj.parent.parent.parent.windowClassName == "ListBoxX"):
				clsList.insert(0, npp_autocomplete.AutocompleteList)
				return
		except AttributeError:
			pass
		if (
			(obj.windowControlID == 1682 and obj.role == ROLE_EDITABLETEXT)
			or (
				obj.role == ROLE_BUTTON and obj.windowControlID in (67220, 67219))
		):
			clsList.insert(0, npp_incrementalFind.IncrementalFind)
			return
		if obj.windowControlID == 1689 and obj.role == ROLE_STATICTEXT:
			clsList.insert(0, npp_incrementalFind.LiveTextControl)
			return

		if obj.role == ROLE_LISTITEM:
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
		if obj.role == ROLE_PANE:
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

	def script_test(self, gesture):
		print("Notepad ++ test")
		ui.message("Notepad ++ test")

	__gestures = {
		# "kb:alt+control+f10": "test",
	}
