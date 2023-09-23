# -*- coding: UTF-8 -*-

# Build customizations
# Change this file instead of sconstruct or manifest files, whenever possible.


# Since some strings in `addon_info` are translatable,
# we need to include them in the .po files.
# Gettext recognizes only strings given as parameters to the `_` function.
# To avoid initializing translations in this module we simply roll our own "fake" `_` function
# which returns whatever is given to it as an argument.
def _(arg):
	return arg


# Add-on information variables
addon_info = {
	# add-on Name, internal for nvda
	"addon_name": "notepadPlusPlusAccessEnhancement",
	# Add-on summary, usually the user visible name of the addon.
	# Translators: Summary for this add-on to be shown on installation and add-on information.
	"addon_summary": _("Notepad++ text's editor : accessibility enhancement"),
	# Add-on description
	# Translators: Long description to be shown for this add-on on add-on information from add-ons manager
	"addon_description": _(
		"""
1- Features #

This extension aims to improve the accessibility of the Notepad++ text editor and add functionalities """
		"""to facilitate the editing of files used in Python language and files written in markdown language.

It includes most of the additions made by NVDA_notepadPlusPlus add-on created by Derek Riemer and """
		"""Tuukka Ojala, then modified by Robert Hanggi and Andre9642 <https://github.com/derekriemer"""
		"""/nvda-notepadPlusPlus>.

To know:

* vocalization of the result of the "control + b" command which allows you to move to the symmetric delimiter,
* vocalization of the movement to the next or previous bookmark with "F2" or "capital letter + f2",
* reporting of lines that are too long,
* accessibility to autocomplete,
* accessibility to incremental search,
* Support for previous / next search function.


For Python files, it provides:

* move to the next class or method,
* importing the code from the editing window.


For Markdown or txt2tags files:

* preview of the result of the conversion to HTML in the virtual buffer of NVDA or in the default browser,
* added browse mode commands for title, link, blocquote.



And finally:

* Announcement of the number and indentation of each line,
* scripts to set the indentation,
* Focus movement displacement by "home" key,
* Comparison of the selected text with that of the clipboard,
* go to the next line ending with at least one tab or one space,
* format of the announcement of the name of the documents:
	* reduced file path announcement,
	* announcement of the name of the file before its path,
	* no diction of path's backslashs.


2- Compatibility
This extension has been tested with Notepad++ version 8.4.2.


3- Constraints
This extension uses and intercepts the shortcuts of Notepad++ configured by default. """
		"""It is therefore strongly advised, for its proper functioning, not to modify these shortcuts.
"""),
	# version
	"addon_version": "2.5.2",
	# Author(s)
	"addon_author": u"paulber19 (paulber19@laposte.net)",
	# URL for the add-on documentation support
	"addon_url": "https://github.com/paulber19/notepadPlusPlusAccessEnhancementNVDAAddon.git",
	# URL for the add-on repository where the source code can be found
	"addon_sourceURL": "https://github.com/paulber19/notepadPlusPlusAccessEnhancementNVDAAddon.git",
	# Documentation file name
	"addon_docFileName": "addonUserManual.html",
	# Minimum NVDA version supported (e.g. "2018.3")
	"addon_minimumNVDAVersion": "2022.1",
	# Last NVDA version supported/tested (e.g. "2018.4", ideally more recent than minimum version)
	"addon_lastTestedNVDAVersion": "2023.3",
	# Add-on update channel (default is stable or None)
	"addon_updateChannel": None,
	# Add-on license such as GPL 2
	"addon_license": "GPL v2",
	# URL for the license document the ad-on is licensed under
	"addon_licenseURL": "https://www.gnu.org/licenses/gpl-2.0.html",
}


import os.path

# Define the python files that are the sources of your add-on.
# You can use glob expressions here, they will be expanded.
pythonSources = [
	os.path.join("addon", "*.py"),
	os.path.join("addon", "shared", "*.py"),
	os.path.join("addon", "appModules", "notepadPlusPlus", "*.py"),
	os.path.join("addon", "appModules", "notepadPlusPlus", "forPython", "*.py"),
	os.path.join("addon", "globalPlugins", "notepadPlusPlusAccessEnhancement", "*.py"),
	os.path.join("addon", "globalPlugins", "notepadPlusPlusAccessEnhancement", "updateHandler", "*.py"),
]

# Files that contain strings for translation. Usually your python sources
i18nSources = pythonSources

# Files that will be ignored when building the nvda-addon file
# Paths are relative to the addon directory, not to the root directory of your addon sources.
excludedFiles = []

# Base language for the NVDA add-on
# If your add-on is written in a language other than english, modify this variable.
# For example, set baseLanguage to "es" if your add-on is primarily written in spanish.
baseLanguage = "en"

# Markdown extensions for add-on documentation
# Most add-ons do not require additional Markdown extensions.
# If you need to add support for markup such as tables, fill out the below list.
# Extensions string must be of the form "markdown.extensions.extensionName"
# e.g. "markdown.extensions.tables" to add tables.
markdownExtensions = []
