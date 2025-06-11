# -*- coding: UTF-8 -*-
# install.py
# a part of notepadAccessEnhancement add-on
# Copyright 2022-2025 paulber19
# This file is covered by the GNU General Public License.


import addonHandler
import os
from logHandler import log

addonHandler.initTranslation()

PREVIOUSCONFIGURATIONFILE_SUFFIX = ".prev"
DELETECONFIGURATIONFILE_SUFFIX = ".delete"


def renameFile(file, dest):
	try:
		if os.path.exists(dest):
			os.remove(dest)
		os.rename(file, dest)
		log.debug("current configuration file: %s renamed to : %s" % (file, dest))
	except Exception:
		log.error("current configuration file: %s  cannot be renamed to: %s" % (file, dest))


def keepPreviousSettingsConfirmation(addonSummary):
	import os
	import sys
	curPath = os.path.dirname(__file__)
	sharedPath = os.path.join(curPath, "shared")
	sys.path.append(curPath)
	sys.path.append(sharedPath)
	from messages import confirm_YesNo, ReturnCode
	del sys.path[-1]
	del sys.path[-1]
	del sys.modules["messages"]

	if confirm_YesNo(
		# Translators: the label of a message box dialog.
		_("Do you want to keep current add-on configuration settings ?"),
		# Translators: the title of a message box dialog.
		_("%s - installation") % addonSummary,
	) == ReturnCode.YES or confirm_YesNo(
		# Translators: the label of a message box dialog.
		_("Are you sure you don't want to keep the current add-on configuration settings?"),
		# Translators: the title of a message box dialog.
		_("%s - installation") % addonSummary,
	) != ReturnCode.YES:
		return True
	return False


def onInstall():
	import globalVars
	curPath = os.path.dirname(__file__)
	from addonHandler import _availableAddons
	addon = _availableAddons[curPath]
	addonName = addon.manifest["name"]
	addonSummary = addon.manifest["summary"]
	# save old configuration
	userConfigPath = globalVars.appArgs.configPath
	curConfigFileName = "%sAddon.ini" % addonName
	addonConfigFile = os.path.join(userConfigPath, curConfigFileName)
	if not os.path.exists(addonConfigFile):
		return
	extraAppArgs = globalVars.appArgsExtra if hasattr(globalVars, "appArgsExtra") else globalVars.unknownAppArgs
	keep = True if "addon-auto-update" in extraAppArgs else False
	if keep or keepPreviousSettingsConfirmation(addonSummary):
		dest = addonConfigFile + PREVIOUSCONFIGURATIONFILE_SUFFIX
		renameFile(addonConfigFile, dest)
	else:
		# add-on configuration should not be kept
		dest = addonConfigFile + DELETECONFIGURATIONFILE_SUFFIX
		renameFile(addonConfigFile, dest)


def deleteFile(theFile):
	if not os.path.exists(theFile):
		return
	os.remove(theFile)
	if os.path.exists(theFile):
		log.warning("Error on deletion of%s  file" % theFile)
	else:
		log.warning("%s file deleted" % theFile)


def deleteAddonConfig():
	import globalVars
	import sys
	curPath = os.path.dirname(__file__)
	sys.path.append(curPath)
	import buildVars
	addonName = buildVars.addon_info["addon_name"]
	del sys.path[-1]
	configFile = os.path.join(
		globalVars.appArgs.configPath, "%sAddon.ini" % addonName)
	deleteFile(configFile)


def onUninstall():
	deleteAddonConfig()
