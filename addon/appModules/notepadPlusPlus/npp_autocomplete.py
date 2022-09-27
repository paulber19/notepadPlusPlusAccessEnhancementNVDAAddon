# coding: utf-8
# appModules\notepad++\npp_autocomplete.py
# A part of notepadPlusPlusAccessEnhancement addon
# Copyright (C) 2016-2022 Tuukka Ojala, Derek Riemer, paulber19
# This file is covered by the GNU General Public License.

import addonHandler
from NVDAObjects.IAccessible import IAccessible
import speech
import braille
import os
import sys
_curAddon = addonHandler.getCodeAddon()
sharedPath = os.path.join(_curAddon.path, "shared")
sys.path.append(sharedPath)
from npp_addonConfigManager import _addonConfigManager
del sys.path[-1]


class AutocompleteList(IAccessible):

	def event_selection(self):
		speech.cancelSpeech()
		speech.speakText(self.name)
		if _addonConfigManager.toggleBrailleAutocompleteSuggestionsOption(False):
			braille.handler.message(u'? %s ?' % self.name)
