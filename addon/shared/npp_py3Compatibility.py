# shared/npp_py3Compatibility.py
# a part of notepadPlusPlusAccessEnhancement add-on
# Copyright 2020-2022 paulber19
# This file is covered by the GNU General Public License.


import addonHandler
import os
import sys

py3 = sys.version.startswith("3")


def getCommonUtilitiesPath():
	curAddonPath = getAddonPath()
	return os.path.join(curAddonPath, "utilities")


def getUtilitiesPath():
	curAddonPath = getAddonPath()
	return os.path.join(curAddonPath, "utilitiesPy3")


def getAddonPath(addon=None):
	if addon is None:
		addon = addonHandler.getCodeAddon()
	addonPath = addon.path
	return addonPath
