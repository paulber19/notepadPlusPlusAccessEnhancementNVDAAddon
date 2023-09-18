# appModules\notepad++\npp_application.py
# A part of notepadPlusPlusAccessEnhancement addon
# Copyright (C) 2020-2023 paulber19
# This file is covered by the GNU General Public License.

import addonHandler
import api
import speech
from controlTypes.role import Role
from controlTypes.state import State
import queueHandler
import os
import sys
_curAddon = addonHandler.getCodeAddon()
sharedPath = os.path.join(_curAddon.path, "shared")
sys.path.append(sharedPath)
from npp_addonConfigManager import _addonConfigManager
del sys.path[-1]
addonHandler.initTranslation()


class Tabs (object):
	def __init__(self, foreground=None):
		super(Tabs, self).__init__()
		self.obj = self.getNVDAObject(foreground)

	def getNVDAObject(self, foreground):
		if foreground is None:
			desktop = api.getDesktopObject()
			for o in desktop.children:
				if o.windowClassName == "Notepad++":
					foreground = o.getChild(3)
					break
		if foreground is None:
			return None
		for o in foreground.children:
			if o.role == Role.TABCONTROL:
				return o

		return None

	def getTabs(self, returnNames=False):
		if self.obj is None:
			return []
		tabs = []
		for index in range(0, self.obj.childCount):
			o = self.obj.getChild(index)
			if o is None or o.role != Role.TAB:
				continue
			if returnNames:
				tabs.append(o.name)
			else:
				tabs.append(o)
		return tabs

	def getDocumentCount(self):
		if self.obj is None:
			return None
		tabs = self.getTabs()
		return len(tabs)

	def getCurrentDocumentIndex(self):
		if self.obj is None:
			return None
		tabsList = self.getTabs()
		for o in tabsList:
			if State.SELECTED in o.states:
				return tabsList.index(o) + 1
		return None

	def sayCurrentDocumentPosition(self):
		count = self.getDocumentCount()
		if count and count > 1:
			index = self.getCurrentDocumentIndex()
			# Translators: message to user to report document position
			queueHandler.queueFunction(
				queueHandler.eventQueue,
				speech.speakMessage, _("Documents {index} on {total}").format(index=index, total=count))


def reducePath(filePathAndName):
	if not filePathAndName or "\\" not in filePathAndName:
		# no path so return filename
		return filePathAndName
	nameList = filePathAndName.split("\\")
	filename = nameList[-1]
	pathList = nameList[:-1]
	pathList = _reducePath(nameList[:-1])
	if not pathList:
		return filename
	sep = "\\"
	sayFileNameBeforePathOption = _addonConfigManager.toggleSayFileNameBeforePathOption(False)
	if _addonConfigManager.toggleReversePathOption(False):
		pathList = reversePath(pathList)
		sep = "/"
		sayFileNameBeforePathOption = True
	if sayFileNameBeforePathOption:
		path = sep.join(pathList)
		name = "%s (%s)" % (filename, path)
	else:
		pathList.append(filename)
		name = sep.join(pathList)
	if _addonConfigManager.toggleNoSayFilePathBackslashsOption(False):
		name = name.replace("\\", " ")
	return name


def _reducePath(pathList):
	if not _addonConfigManager.toggleReduceFilePathOption(False):
		return pathList
	previousHierarchicalLevelToKeep = _addonConfigManager.getPreviousHierarchicalLevelToKeep()
	if previousHierarchicalLevelToKeep:
		if len(pathList) > previousHierarchicalLevelToKeep + 1:
			tempList = [pathList[0], "..."]
			tempList.extend(pathList[(-1) * (previousHierarchicalLevelToKeep):])
			return tempList
		else:
			return pathList
	return []


def reversePath(pathList):
	if not _addonConfigManager.toggleReversePathOption(False):
		return pathList
	withLevel = not _addonConfigManager.toggleReportReversedPathWithNoLevelOption(False)
	nb = len(pathList)
	textList = []
	for index in range(nb - 1, -1, -1):
		level = nb - index
		item = pathList[-level]
		if withLevel and item != "..." and index:
			levelText = "(n-%s)" % str(level - 1) if level - 1 else "(n)"
			textList.append("{name} {levelText}" .format(name=item, levelText=levelText))
		else:
			textList.append(" %s" % item)
	return textList
