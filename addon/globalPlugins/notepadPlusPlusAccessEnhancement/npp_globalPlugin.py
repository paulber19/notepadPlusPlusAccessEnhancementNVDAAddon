# globalPlugins\notepadPlusPlusAccessEnhancement\npp_globalPlugin.py
# a part of notepadPlusPlusAccessEnhancement add-on
# Copyright (C) 2020-2025 Paulber19
# This file is covered by the GNU General Public License.


import addonHandler
import globalPluginHandler
import gui
import wx
import os
import sys
addon = addonHandler.getCodeAddon()
sharedPath = os.path.join(addon.path, "shared")
sys.path.append(sharedPath)
from npp_addonConfigManager import _addonConfigManager
del sys.path[-1]

addonHandler.initTranslation()


class NotepadPlusPlusGlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self, *args, **kwargs):
		super(NotepadPlusPlusGlobalPlugin, self).__init__(*args, **kwargs)
		self.installSettingsMenu()
		from .updateHandler.update_check import setCheckForUpdate
		setCheckForUpdate(_addonConfigManager.toggleAutoUpdateCheck(False))
		from . updateHandler import autoUpdateCheck
		autoUpdateCheck(releaseToDev=_addonConfigManager.toggleUpdateReleaseVersionsToDevVersions(False))

	def installSettingsMenu(self):
		self.preferencesMenu = gui.mainFrame.sysTrayIcon.preferencesMenu
		from .npp_configGui import AddonSettingsDialog
		self.menu = self.preferencesMenu.Append(
			wx.ID_ANY,
			AddonSettingsDialog.title + " ...",
			"")
		gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.onMenu, self.menu)

	def deleteSettingsMenu(self):
		try:
			self.preferencesMenu.Remove(self.menu)
		except Exception:
			pass

	def terminate(self):
		self.deleteSettingsMenu()
		_addonConfigManager.terminate()
		super(NotepadPlusPlusGlobalPlugin, self).terminate()

	def onMenu(self, evt):
		from .npp_configGui import AddonSettingsDialog
		gui.mainFrame._popupSettingsDialog(AddonSettingsDialog)
