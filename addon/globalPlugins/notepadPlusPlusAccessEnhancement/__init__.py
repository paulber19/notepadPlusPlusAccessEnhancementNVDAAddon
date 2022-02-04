# globalPlugins\notepadPlusPlusAccessEnhancement\__init__.py
# a part of notepadPlusPlusAccessEnhancement add-on
# Copyright (C) 2020-2021 Paulber19
# This file is covered by the GNU General Public License.

import globalVars
import config

# this add-on is disabled when loading in the secure screen,
# as well as if NVDA is running as a Windows Store Desktop Bridge application.
if (globalVars.appArgs.secure or (
	hasattr(config, "isAppX") and config.isAppX)):
	import globalPluginHandler

	class GlobalPlugin (globalPluginHandler.GlobalPlugin):
		pass
else:
	from . import npp_globalPlugin

	class GlobalPlugin (npp_globalPlugin.NotepadPlusPlusGlobalPlugin):
		pass
