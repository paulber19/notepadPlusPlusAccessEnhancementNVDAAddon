# globalPlugins\notepadPlusPlusAccessEnhancement\npp_configGui.py
# a part of notepadPlusPlusAccessEnhancement add-on
# Copyright 2020-2023 paulber19
# This file is covered by the GNU General Public License.

# manage add-on configuration dialog

import addonHandler
import wx
import gui
from gui.settingsDialogs import MultiCategorySettingsDialog, SettingsPanel
import os
from gui.guiHelper import BoxSizerHelper
import gui.nvdaControls
import sys
_curAddon = addonHandler.getCodeAddon()
_addonSummary = _curAddon.manifest['summary']
sharedPath = os.path.join(_curAddon.path, "shared")
sys.path.append(sharedPath)
from npp_addonConfigManager import _addonConfigManager
from npp_addonConfigManager import indentReportModeLabels
del sys.path[-1]
addonHandler.initTranslation()


class NPPGeneralOptionsPanel(SettingsPanel):
	# Translators: This is the label for the notepadPlusPlus general options panel
	title = _("General")

	def makeSettings(self, settingsSizer):
		sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		# Translators: A setting for enabling/disabling autocomplete suggestions in braille.
		labelText = _("Show autocomplete &suggestions in braille")
		self.brailleAutocompleteSuggestionsCheckBox = sHelper.addItem(wx.CheckBox(self, wx.ID_ANY, label=labelText))
		self.brailleAutocompleteSuggestionsCheckBox .SetValue(
			_addonConfigManager.toggleBrailleAutocompleteSuggestionsOption(False))
		# Translators: This is the label for a group of editing options in the settings panel.
		groupText = _("Documents's name")
		groupSizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, label=groupText)
		groupBox = groupSizer.GetStaticBox()
		group = BoxSizerHelper(self, sizer=groupSizer)
		sHelper.addItem(group)
		# Translators: A setting to activate saying file name before file path.
		labelText = _("&Say file name before path")
		self.sayFileNameBeforePathCheckBox = group.addItem(wx.CheckBox(groupBox, wx.ID_ANY, label=labelText))
		self.sayFileNameBeforePathCheckBox.SetValue(_addonConfigManager.toggleSayFileNameBeforePathOption(False))
		# Translators: A option to reverse path before reporting
		labelText = _("Say the path &going up the folder tree")
		self.reversePathCheckBox = group.addItem(wx.CheckBox(groupBox, wx.ID_ANY, label=labelText))
		self.reversePathCheckBox .SetValue(_addonConfigManager.toggleReversePathOption(False))
		# Translators: A setting for enabling/disabling file path reduction.
		labelText = _("&Reduce path")
		self.reduceFilePathCheckBox = group.addItem(wx.CheckBox(groupBox, wx.ID_ANY, label=labelText))
		self.reduceFilePathCheckBox.SetValue(_addonConfigManager.toggleReduceFilePathOption(False))
		# Translators: A option to not to mention the backslashs.
		labelText = _("&Don't say backslash of path")
		self.NoSayBackslashCheckBox = group.addItem(wx.CheckBox(groupBox, wx.ID_ANY, label=labelText))
		self.NoSayBackslashCheckBox.SetValue(_addonConfigManager.toggleNoSayFilePathBackslashsOption(False))
		# Translators: This is the label for a group of editing options in the settings panel.
		groupText = _("Reduced path announcement")
		groupSizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, label=groupText)
		groupBox = groupSizer.GetStaticBox()
		group = BoxSizerHelper(self, sizer=groupSizer)
		sHelper.addItem(group)
		# Translators: Setting for previous hieararchical level to keep.
		labelText = _("&Previous hierarchical levels to keep")
		self.previousHierarchicalLevelToKeep = group.addLabeledControl(
			labelText, wx.Choice, choices=["-%s" % str(x)if x > 0 else str(x) for x in range(0, 11)])
		self.previousHierarchicalLevelToKeep.SetSelection(_addonConfigManager.getPreviousHierarchicalLevelToKeep())
		# Translators: This is the label for a group of editing options in the settings panel.
		groupText = _("Reversed file path announcement")
		groupSizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, label=groupText)
		groupBox = groupSizer.GetStaticBox()
		group = BoxSizerHelper(self, sizer=groupSizer)
		sHelper.addItem(group)
		# Translators: A option to reverse path with no level
		labelText = _("Do not say the &hierarchical levels")
		self.reportReversedPathWithNoLevelCheckBox = group.addItem(
			wx.CheckBox(groupBox, wx.ID_ANY, label=labelText))
		self.reportReversedPathWithNoLevelCheckBox .SetValue(
			_addonConfigManager.toggleReportReversedPathWithNoLevelOption(False))
		# Translators: This is the label for a group of editing options in the settings panel.
		groupText = _("Documents dialog")
		groupSizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, label=groupText)
		groupBox = groupSizer.GetStaticBox()
		group = BoxSizerHelper(self, sizer=groupSizer)
		sHelper.addItem(group)
		# Translators: This is the label for a list of checkboxes
		# controlling which columns of the document name should not be spoken
		labelText = _("&Select elements of the document that should be spoken with its name:")
		from npp_addonConfigManager import documentColumnLabels
		self.maskedColumnsChoices = documentColumnLabels
		self.maskedColumnsList = group.addLabeledControl(
			labelText, gui.nvdaControls.CustomCheckListBox, choices=self.maskedColumnsChoices)
		columns = _addonConfigManager.getDocumentColumnsChoices()
		self.maskedColumnsList.SetCheckedItems(columns)
		self.maskedColumnsList.Select(0)

	def postInit(self):
		self.brailleAutocompleteSuggestionsCheckBox .SetFocus()

	def saveSettingChanges(self):
		if self.brailleAutocompleteSuggestionsCheckBox.IsChecked() != (
			_addonConfigManager.toggleBrailleAutocompleteSuggestionsOption(False)):
			_addonConfigManager.toggleBrailleAutocompleteSuggestionsOption(True)
		if self.reduceFilePathCheckBox.IsChecked() != _addonConfigManager.toggleReduceFilePathOption(False):
			_addonConfigManager.toggleReduceFilePathOption(True)
		previousHierarchicalLevelToKeep = self.previousHierarchicalLevelToKeep.GetSelection()
		_addonConfigManager.setPreviousHierarchicalLevelToKeep(previousHierarchicalLevelToKeep)
		if self.sayFileNameBeforePathCheckBox.IsChecked() != (
			_addonConfigManager.toggleSayFileNameBeforePathOption(False)):
			_addonConfigManager.toggleSayFileNameBeforePathOption(True)
		if self.NoSayBackslashCheckBox.IsChecked() != (
			_addonConfigManager.toggleNoSayFilePathBackslashsOption(False)):
			_addonConfigManager.toggleNoSayFilePathBackslashsOption(True)
		if self.reversePathCheckBox.IsChecked() != (
			_addonConfigManager.toggleReversePathOption(False)):
			_addonConfigManager.toggleReversePathOption(True)
		if self.reportReversedPathWithNoLevelCheckBox.IsChecked() != (
			_addonConfigManager.toggleReportReversedPathWithNoLevelOption(False)):
			_addonConfigManager.toggleReportReversedPathWithNoLevelOption(True)
		checkedColumns = self.maskedColumnsList.GetCheckedItems()
		_addonConfigManager.setDocumentColumnsChoices(checkedColumns)

	def onSave(self):
		self.saveSettingChanges()


class NPPLineOptionsPanel(SettingsPanel):
	# Translators: This is the label for the notepadPlusPlus settings dialog.
	title = _("Line")

	def makeSettings(self, settingsSizer):
		sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		# Translators: A setting for enabling/disabling line and Number indentation announcement management.
		labelText = _("&Let NVDA announce the line number and indentations")
		self.manageLineNumberAndIndentationAnnouncementCheckBox = sHelper.addItem(
			wx.CheckBox(self, wx.ID_ANY, label=labelText))
		self.manageLineNumberAndIndentationAnnouncementCheckBox.SetValue(
			not _addonConfigManager.toggleManageLineNumberAndIndentationAnnouncementOption(False))
		self.manageLineNumberAndIndentationAnnouncementCheckBox .Bind(
			wx.EVT_CHECKBOX, self.onManageLineNumberAndIndentationAnnouncementCheck)
		# Translators: A setting for enabling/disabling report line number
		labelText = _("&Report line number")
		self.reportLineNumberCheckBox = sHelper.addItem(wx.CheckBox(self, wx.ID_ANY, label=labelText))
		self.reportLineNumberCheckBox.SetValue(_addonConfigManager.toggleReportLineNumberOption(False))
		# Translators: This is the label for a group of editing options in the settings panel.
		groupText = _("Line indentation")
		groupSizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, label=groupText)
		groupBox = groupSizer.GetStaticBox()
		self.LineIndentationAnnouncementGroup = BoxSizerHelper(self, sizer=groupSizer)
		sHelper.addItem(self.LineIndentationAnnouncementGroup)
		# Translators: A setting for enabling/disabling line indentation announcement.
		labelText = _("Report line &indentation")
		self.reportLineIndentationCheckBox = self.LineIndentationAnnouncementGroup.addItem(
			wx.CheckBox(groupBox, wx.ID_ANY, label=labelText))
		self.reportLineIndentationCheckBox.SetValue(_addonConfigManager.toggleReportLineIndentationOption(False))
		# Translators: Setting for indent report mode.
		labelText = _("St&yle:")
		choice = indentReportModeLabels[:]
		self.indentReportMode = self.LineIndentationAnnouncementGroup.addLabeledControl(
			labelText,
			wx.Choice,
			choices=[str(x) for x in choice])
		self.indentReportMode.SetSelection(_addonConfigManager.toggleIndentReportMode(False))
		self.updateLineNumberAndIndentationAnnouncementBox()
		# Translators: This is the label for a group of editing options in the settings panel.
		groupText = _("Long line")
		groupSizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, label=groupText)
		groupBox = groupSizer.GetStaticBox()
		group = BoxSizerHelper(self, sizer=groupSizer)
		sHelper.addItem(group)
		# Translators: A setting for enabling/disabling line length indicator.
		labelText = _("Rep&ort long lines")
		self.lineLengthIndicatorCheckBox = group.addItem(wx.CheckBox(groupBox, wx.ID_ANY, label=labelText))
		self.lineLengthIndicatorCheckBox.SetValue(_addonConfigManager.toggleLineLengthIndicator(False))
		# Translators: Setting for maximum line length used by line length indicator
		labelText = _("&Minimum line length:")
		choice = [x for x in range(0, 500, 5)]
		choice = list(reversed(choice))
		self.maxLineLengthEdit = group.addLabeledControl(labelText, wx.Choice, choices=[str(x) for x in choice])
		self.maxLineLengthEdit.SetSelection(choice.index(_addonConfigManager.getMaxLineLength()))

	def updateLineNumberAndIndentationAnnouncementBox(self):
		if not self.manageLineNumberAndIndentationAnnouncementCheckBox .IsChecked():
			# enable box
			self.reportLineNumberCheckBox .Show()
			for item in range(0, self.LineIndentationAnnouncementGroup.sizer.GetItemCount()):
				self.LineIndentationAnnouncementGroup.sizer.Show(item)
		else:
			# disable box
			self.reportLineNumberCheckBox .Hide()
			for item in range(0, self.LineIndentationAnnouncementGroup.sizer.GetItemCount()):
				self.LineIndentationAnnouncementGroup.sizer.Hide(item)

	def onManageLineNumberAndIndentationAnnouncementCheck(self, evt):
		self.updateLineNumberAndIndentationAnnouncementBox()

		evt.Skip()

	def postInit(self):
		self.lineLengthIndicatorCheckBox.SetFocus()

	def saveSettingChanges(self):
		if self.reportLineNumberCheckBox .IsChecked() != _addonConfigManager.toggleReportLineNumberOption(False):
			_addonConfigManager.toggleReportLineNumberOption(True)
		if self.reportLineIndentationCheckBox .IsChecked() != (
			_addonConfigManager.toggleReportLineIndentationOption(False)):
			_addonConfigManager.toggleReportLineIndentationOption(True)
		if self.manageLineNumberAndIndentationAnnouncementCheckBox .IsChecked() != (
			not _addonConfigManager.toggleManageLineNumberAndIndentationAnnouncementOption(False)):
			_addonConfigManager.toggleManageLineNumberAndIndentationAnnouncementOption(True)
		indentReportMode = self.indentReportMode.GetSelection()
		_addonConfigManager.setIndentReportMode(indentReportMode)
		if self.lineLengthIndicatorCheckBox.IsChecked() != _addonConfigManager.toggleLineLengthIndicator(False):
			_addonConfigManager.toggleLineLengthIndicator(True)
		maxLineLength = int(self.maxLineLengthEdit.GetString(self.maxLineLengthEdit.GetSelection()))
		_addonConfigManager.setMaxLineLength(maxLineLength)

	def onSave(self):
		self.saveSettingChanges()


class NPPUpdatePanel(SettingsPanel):
	# Translators: This is the label for the Update panel.
	title = _("Update")

	def makeSettings(self, settingsSizer):
		sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		# Translators: This is the label for a checkbox in the update settings panel.
		labelText = _("Automatically check for &updates ")
		self.autoCheckForUpdatesCheckBox = sHelper.addItem(wx.CheckBox(self, wx.ID_ANY, label=labelText))
		self.autoCheckForUpdatesCheckBox.SetValue(_addonConfigManager.toggleAutoUpdateCheck(False))
		# Translators: This is the label for a checkbox in the update settings panel.
		labelText = _("Update also release versions to &developpement versions")
		self.updateReleaseVersionsToDevVersionsCheckBox = sHelper.addItem(
			wx.CheckBox(self, wx.ID_ANY, label=labelText))
		self.updateReleaseVersionsToDevVersionsCheckBox.SetValue(
			_addonConfigManager.toggleUpdateReleaseVersionsToDevVersions(False))
		# translators: label for a button in update settings panel.
		labelText = _("&Check for update")
		checkForUpdateButton = wx.Button(self, label=labelText)
		sHelper.addItem(checkForUpdateButton)
		checkForUpdateButton.Bind(wx.EVT_BUTTON, self.onCheckForUpdate)
		# translators: this is a label for a button in update settings panel.
		labelText = _("View &history")
		seeHistoryButton = wx.Button(self, label=labelText)
		sHelper.addItem(seeHistoryButton)
		seeHistoryButton.Bind(wx.EVT_BUTTON, self.onSeeHistory)

	def onCheckForUpdate(self, evt):
		from .updateHandler import addonUpdateCheck
		releaseToDevVersion = self.updateReleaseVersionsToDevVersionsCheckBox.IsChecked()
		wx.CallAfter(addonUpdateCheck, auto=False, releaseToDev=releaseToDevVersion)
		self.Close()

	def onSeeHistory(self, evt):
		addon = addonHandler.getCodeAddon()
		from languageHandler import getLanguage
		curLang = getLanguage()
		theFile = os.path.join(addon.path, "doc", curLang, "changes.html")
		if not os.path.exists(theFile):
			lang = curLang.split("_")[0]
			theFile = os.path.join(addon.path, "doc", lang, "changes.html")
			if not os.path.exists(theFile):
				lang = "en"
				theFile = os.path.join(addon.path, "doc", lang, "changes.html")
		os.startfile(theFile)

	def saveSettingChanges(self):
		if self.autoCheckForUpdatesCheckBox.IsChecked() != _addonConfigManager .toggleAutoUpdateCheck(False):
			_addonConfigManager .toggleAutoUpdateCheck(True)
		if self.updateReleaseVersionsToDevVersionsCheckBox.IsChecked() != (
			_addonConfigManager .toggleUpdateReleaseVersionsToDevVersions(False)):
			_addonConfigManager .toggleUpdateReleaseVersionsToDevVersions(True)

	def postSave(self):
		pass

	def onSave(self):
		self.saveSettingChanges()


class AddonSettingsDialog(MultiCategorySettingsDialog):
	title = "%s -%s" % (_curAddon.manifest["summary"], _("Settings"))
	INITIAL_SIZE = (1000, 480)
	MIN_SIZE = (470, 240)  # Min height required to show the OK, Cancel, Apply buttons

	categoryClasses = [
		NPPGeneralOptionsPanel,
		NPPLineOptionsPanel,
		NPPUpdatePanel
	]

	def __init__(self, parent, initialCategory=None):
		curAddon = addonHandler.getCodeAddon()
		# Translators: title of add-on parameters dialog.
		dialogTitle = _("Settings")
		self.title = "%s - %s" % (curAddon.manifest["summary"], dialogTitle)
		super(AddonSettingsDialog, self).__init__(parent, initialCategory)
