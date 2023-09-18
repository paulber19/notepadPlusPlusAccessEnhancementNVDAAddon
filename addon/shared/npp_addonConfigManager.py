# shared\npp_addonConfigManager.py
# a part of notepadPlusPlusAccessEnhancement add-on
# Copyright 2020-2022,paulber19
# This file is covered by the GNU General Public License.

from logHandler import log
import addonHandler
import os
import wx
import gui
import globalVars
import config
from configobj import ConfigObj
from configobj.validate import Validator, ValidateError, VdtTypeError
from io import StringIO

addonHandler.initTranslation()

# config section
SCT_General = "General"
SCT_Options = "Options"
SCT_DSpellCheck = "DSpellCheck"

# general section items
ID_ConfigVersion = "ConfigVersion"
ID_AutoUpdateCheck = "AutoUpdateCheck"
ID_UpdateReleaseVersionsToDevVersions = "UpdateReleaseVersionsToDevVersions"
# options section
ID_MaxLineLength = "MaxLineLength"
ID_BrailleAutocompleteSuggestions = "brailleAutocompleteSuggestions"
ID_LineLengthIndicator = "lineLengthIndicator"
ID_ReportLineNumber = "ReportLineNumber"
ID_ManageLineNumberAndIndentationAnnouncement = "ManageLineNumberAndIndentationAnnouncement"
ID_ReportLineIndentation = "ReportLineIndentation"
ID_IndentReportMode = "IndentReportMode"
ID_ReduceFilePath = "ReduceFilePath"
ID_PreviousHierarchicalLevelToKeep = "PreviousHierarchicalLevelToKeep"
ID_SayFileNameBeforePath = "SayFileNameBeforePath"
ID_NoSayFilePathBackslashs = "NoSayFilePathBackslashs"
ID_ReversePath = "reversePath"
ID_ReportReversedPathWithNoLevel = "ID_ReversedPathWithNoLevel"
ID_DocumentColumnsChoices = "DocumentColumnsChoices"
ID_ReportSpellingErrors = "ReportSpellingErrors"

# header line mode
Mode_SayIndent = 0
Mode_SayIndentChange = 1
Mode_SayLevel = 2
Mode_SayLevelChange = 3
Mode_SayNothing = 4
indentReportModeLabels = [
	# labels for indent report mode: order is important
	# Translators: say indents.
	_("Say indent"),  # Mode_SayIndent:
	# Translators: say indent changes.
	_("Say indent changes"),  # Mode_SayIndentChange
	# Translators: say level.
	_("Say level"),  # Mode_SayLevel
	# Translators: say indent changes.
	_("Say level changes"),  # Mode_SayLevelChange
	# Translators: no indent report.
	_("Say nothing"),  # Mode_SayNothing
]
# DSpellCheck section
ID_CopyAllMisspelledWordsToClipboardShortCut = "CopyAllMisspelledWordsToClipboardShortCut"

# document columns ID
documentColumnIDs = [
	"path",
	"type",
	"size",
]
ID_PathColumn = 0
ID_TypeColumn = 1
ID_SizeColumn = 2
# documentColumnLabels
documentColumnLabels = [
	# Translators: path column name
	_("Path"),
	# Translators: type column name
	_("Type"),
	# Translators: size column name
	_("Size")
]


_curAddon = addonHandler.getCodeAddon()
_addonName = _curAddon.manifest["name"]


class BaseAddonConfiguration(ConfigObj):
	_version = ""
	""" Add-on configuration file. It contains metadata about add-on . """
	_GeneralConfSpec = """[{section}]
	{idConfigVersion} = string(default = " ")
	""".format(section=SCT_General, idConfigVersion=ID_ConfigVersion)

	configspec = ConfigObj(StringIO("""# addon Configuration File
	{general}""".format(general=_GeneralConfSpec)
	), list_values=False, encoding="UTF-8")

	def __init__(self, input):
		""" Constructs an L{AddonConfiguration} instance from manifest string data
		@param input: data to read the addon configuration information
		@type input: a fie-like object.
		"""
		super(BaseAddonConfiguration, self).__init__(
			input, configspec=self.configspec, encoding='utf-8', default_encoding='utf-8')
		self.newlines = "\r\n"
		self._errors = []
		val = Validator()
		result = self.validate(val, copy=True, preserve_errors=True)
		if type(result) == dict:
			self._errors = self.getValidateErrorsText(result)
		else:
			self._errors = None

	def getValidateErrorsText(self, result):
		textList = []
		for name, section in result.items():
			if section is True:
				continue
			textList.append("section [%s]" % name)
			for key, value in section.items():
				if isinstance(value, ValidateError):
					textList.append(
						'key "{}": {}'.format(
							key, value))
		return "\n".join(textList)

	@property
	def errors(self):
		return self._errors


class AddonConfiguration10(BaseAddonConfiguration):
	_version = "1.0"
	_GeneralConfSpec = """[{section}]
	{configVersion} = string(default = {version})
	{autoUpdateCheck} = boolean(default=True)
	{updateReleaseVersionsToDevVersions} = boolean(default=False)
	""".format(
		section=SCT_General,
		configVersion=ID_ConfigVersion,
		version=_version,
		autoUpdateCheck=ID_AutoUpdateCheck,
		updateReleaseVersionsToDevVersions=ID_UpdateReleaseVersionsToDevVersions)

	_OptionsConfSpec = """[{section}]
	{maxLineLength} = integer(default=80)
	{lineLengthIndicator} = boolean(default=False)
	{brailleAutocompleteSuggestions} = boolean(default=False)
	{reportLineNumber} = boolean(default=False)
	{manageLineNumberAndIndentationAnnouncement} = boolean(default=True)
	{reportLineIndentation} = boolean(default=True)
	{indentReportMode} = integer(default=0)
	{reduceFilePath} = boolean(default=False)
	{previousHierarchicalLevelToKeep} = integer(default=0)
	{sayFileNameBeforePath} = boolean(default=True)
	{noSayFilePathBackslashs} = boolean(default=False)
	{reportSpellingErrors} = boolean(default=False)
	""".format(
		section=SCT_Options,
		maxLineLength=ID_MaxLineLength,
		lineLengthIndicator=ID_LineLengthIndicator,
		brailleAutocompleteSuggestions=ID_BrailleAutocompleteSuggestions,
		reportLineNumber=ID_ReportLineNumber,
		reportLineIndentation=ID_ReportLineIndentation,
		manageLineNumberAndIndentationAnnouncement=ID_ManageLineNumberAndIndentationAnnouncement,
		indentReportMode=ID_IndentReportMode,
		reduceFilePath=ID_ReduceFilePath,
		previousHierarchicalLevelToKeep=ID_PreviousHierarchicalLevelToKeep,
		sayFileNameBeforePath=ID_SayFileNameBeforePath,
		noSayFilePathBackslashs=ID_NoSayFilePathBackslashs,
		reportSpellingErrors=ID_ReportSpellingErrors)
	_DSpellCheckConfSpec = """[{section}]
	{copyAllMisspelledWordsToClipboardShortCut} = string(default = "control+shift+alt+space")
	""".format(
		section=SCT_DSpellCheck,
		copyAllMisspelledWordsToClipboardShortCut=ID_CopyAllMisspelledWordsToClipboardShortCut
	)

	#: The configuration specification
	configspec = ConfigObj(StringIO("""# addon Configuration File
	{general}{options}{DspellCheck}
	""".format(
		general=_GeneralConfSpec,
		options=_OptionsConfSpec,
		DspellCheck=_DSpellCheckConfSpec)
	), list_values=False, encoding="UTF-8")


S_DefaultColumns = "path,type,size"


class AddonConfiguration11(BaseAddonConfiguration):
	_version = "1.1"
	_GeneralConfSpec = """[{section}]
	{configVersion} = string(default = {version})
	{autoUpdateCheck} = boolean(default=True)
	{updateReleaseVersionsToDevVersions} = boolean(default=False)
	""".format(
		section=SCT_General,
		configVersion=ID_ConfigVersion,
		version=_version,
		autoUpdateCheck=ID_AutoUpdateCheck,
		updateReleaseVersionsToDevVersions=ID_UpdateReleaseVersionsToDevVersions)

	_OptionsConfSpec = """[{section}]
	{maxLineLength} = integer(default=80)
	{lineLengthIndicator} = boolean(default=False)
	{brailleAutocompleteSuggestions} = boolean(default=False)
	{reportLineNumber} = boolean(default=False)
	{manageLineNumberAndIndentationAnnouncement} = boolean(default=True)
	{reportLineIndentation} = boolean(default=True)
	{indentReportMode} = integer(default=0)
	{reduceFilePath} = boolean(default=False)
	{previousHierarchicalLevelToKeep} = integer(default=2)
	{sayFileNameBeforePath} = boolean(default=True)
	{noSayFilePathBackslashs} = boolean(default=False)
	{reversePath} = boolean(default=False)
	{reportReversedPathWithNoLevel} = boolean(default=False)
	{reportSpellingErrors} = boolean(default=False)
	{documentColumnsChoices} =  string(default="path")
	""".format(
		section=SCT_Options,
		maxLineLength=ID_MaxLineLength,
		lineLengthIndicator=ID_LineLengthIndicator,
		brailleAutocompleteSuggestions=ID_BrailleAutocompleteSuggestions,
		reportLineNumber=ID_ReportLineNumber,
		reportLineIndentation=ID_ReportLineIndentation,
		manageLineNumberAndIndentationAnnouncement=ID_ManageLineNumberAndIndentationAnnouncement,
		indentReportMode=ID_IndentReportMode,
		reduceFilePath=ID_ReduceFilePath,
		previousHierarchicalLevelToKeep=ID_PreviousHierarchicalLevelToKeep,
		sayFileNameBeforePath=ID_SayFileNameBeforePath,
		noSayFilePathBackslashs=ID_NoSayFilePathBackslashs,
		reversePath=ID_ReversePath,
		reportReversedPathWithNoLevel=ID_ReportReversedPathWithNoLevel,
		documentColumnsChoices=ID_DocumentColumnsChoices,
		reportSpellingErrors=ID_ReportSpellingErrors)

	_DSpellCheckConfSpec = """[{section}]
	{copyAllMisspelledWordsToClipboardShortCut} = string(default = "control+shift+alt+space")
""".format(
		section=SCT_DSpellCheck,
		copyAllMisspelledWordsToClipboardShortCut=ID_CopyAllMisspelledWordsToClipboardShortCut
	)

	#: The configuration specification
	configspec = ConfigObj(StringIO(
		"""# addon Configuration File
{general}{options}{DspellCheck}
	""".format(
			general=_GeneralConfSpec,
			options=_OptionsConfSpec,
			DspellCheck=_DSpellCheckConfSpec)
	), list_values=False, encoding="UTF-8")


class AddonConfigurationManager():
	_currentConfigVersion = "1.1"
	_versionToConfiguration = {
		"1.0": AddonConfiguration10,
		"1.1": AddonConfiguration11,
	}

	def __init__(self):
		self.configFileName = "%sAddon.ini" % _addonName
		self.loadSettings()
		config.post_configSave.register(self._handlePostConfigSave)

	def warnConfigurationReset(self):
		wx.CallLater(
			100,
			gui.messageBox,
			# Translators: A message warning configuration reset.
			_(
				"The configuration file of the add-on contains errors. "
				"The configuration has been  reset to factory defaults"),
			# Translators: title of message box
			"{addon} - {title}" .format(addon=_curAddon.manifest["summary"], title=_("Warning")),
			wx.OK | wx.ICON_WARNING
		)

	def loadSettings(self):
		addonConfigFile = os.path.join(
			globalVars.appArgs.configPath, self.configFileName)
		doMerge = True
		if os.path.exists(addonConfigFile):
			# there is allready a config file
			try:
				baseConfig = BaseAddonConfiguration(addonConfigFile)
				if baseConfig.errors:
					e = Exception("Error parsing configuration file:\n%s" % baseConfig.errors)
					raise e
				if baseConfig[SCT_General][ID_ConfigVersion] != self._currentConfigVersion:
					# it's an old config, but old config file must not exist here.
					# Must be deleted
					os.remove(addonConfigFile)
					log.warning("%s: Old configuration version found. Config file is removed: %s" % (
						_addonName, addonConfigFile))
				else:
					# it's the same version of config, so no merge
					doMerge = False
			except Exception as e:
				log.warning(e)
				# error on reading config file, so delete it
				os.remove(addonConfigFile)
				self.warnConfigurationReset()
				log.warning(
					"%s Addon configuration file error: configuration reset to factory defaults" % _addonName)

		if os.path.exists(addonConfigFile):
			self.addonConfig =\
				self._versionToConfiguration[self._currentConfigVersion](addonConfigFile)
			if self.addonConfig.errors:
				log.warning(self.addonConfig.errors)
				log.warning(
					"%s Addon configuration file error: configuration reset to factory defaults" % _addonName)
				os.remove(addonConfigFile)
				self.warnConfigurationReset()
				# reset configuration to factory defaults
				self.addonConfig =\
					self._versionToConfiguration[self._currentConfigVersion](None)
				self.addonConfig.filename = addonConfigFile
				doMerge = False
		else:
			# no add-on configuration file found
			self.addonConfig =\
				self._versionToConfiguration[self._currentConfigVersion](None)
			self.addonConfig.filename = addonConfigFile
		# merge step
		oldConfigFile = os.path.join(_curAddon.path, self.configFileName)
		if os.path.exists(oldConfigFile):
			if doMerge:
				self.mergeSettings(oldConfigFile)
			os.remove(oldConfigFile)
		if not os.path.exists(addonConfigFile):
			self.saveSettings(True)

	def mergeSettings(self, oldConfigFile):
		log.warning("Merge settings with old configuration")
		baseConfig = BaseAddonConfiguration(oldConfigFile)
		version = baseConfig[SCT_General][ID_ConfigVersion]
		if version not in self._versionToConfiguration:
			log.warning("Configuration merge error: unknown configuration version")
			return
		oldConfig = self._versionToConfiguration[version](oldConfigFile)
		for sect in self.addonConfig.sections:
			for k in self.addonConfig[sect]:
				if sect == SCT_General and k == ID_ConfigVersion:
					continue
				if sect in oldConfig.sections and k in oldConfig[sect]:
					self.addonConfig[sect][k] = oldConfig[sect][k]

	def saveSettings(self, force=False):
		# We never want to save config if runing securely
		if globalVars.appArgs.secure:
			return
		if not force and not config.conf['general']['saveConfigurationOnExit']:
			return
		if self.addonConfig is None:
			return
		val = Validator()
		try:
			self.addonConfig.validate(val, copy=True)
		except VdtTypeError:
			# error in configuration file
			log.warning("saveSettings: validator error: %s" % self.addonConfig.errors)
			return
		try:
			self.addonConfig.write()
			log.warning("add-on configuration saved")
		except Exception:
			log.warning("Could not save configuration - probably read only file system")

	def _handlePostConfigSave(self):
		self.saveSettings(True)

	def terminate(self):
		self.saveSettings()
		config.post_configSave.unregister(self._handlePostConfigSave)
		log.warning("addonConfigManager terminate")

	def toggleGeneralOption(self, id, toggle):
		conf = self.addonConfig
		if toggle:
			conf[SCT_General][id] = not conf[SCT_General][id]
			self.saveSettings()
		return conf[SCT_General][id]

	def toggleAutoUpdateCheck(self, toggle=True):
		return self.toggleGeneralOption(ID_AutoUpdateCheck, toggle)

	def toggleUpdateReleaseVersionsToDevVersions(self, toggle=True):
		return self.toggleGeneralOption(ID_UpdateReleaseVersionsToDevVersions, toggle)

	def toggleOption(self, id, toggle=True):
		conf = self.addonConfig
		if toggle:
			conf[SCT_Options][id] = not conf[SCT_Options][id]
			self.saveSettings()
		return conf[SCT_Options][id]

	def toggleLineLengthIndicator(self, toggle=True):
		return self.toggleOption(ID_LineLengthIndicator, toggle)

	def toggleBrailleAutocompleteSuggestionsOption(self, toggle=True):
		return self.toggleOption(ID_BrailleAutocompleteSuggestions, toggle)

	def toggleReportLineNumberOption(self, toggle=True):
		return self.toggleOption(ID_ReportLineNumber, toggle)

	def getMaxLineLength(self):
		conf = self.addonConfig
		return conf[SCT_Options][ID_MaxLineLength]

	def setMaxLineLength(self, maxLineLength):
		conf = self.addonConfig
		conf[SCT_Options][ID_MaxLineLength] = int(maxLineLength)

	def toggleReportLineIndentationOption(self, toggle=True):
		return self.toggleOption(ID_ReportLineIndentation, toggle)

	def toggleManageLineNumberAndIndentationAnnouncementOption(self, toggle=True):
		return self.toggleOption(ID_ManageLineNumberAndIndentationAnnouncement, toggle)

	def toggleIndentReportMode(self, toggle=True):
		conf = self.addonConfig
		mode = conf[SCT_Options][ID_IndentReportMode]
		if toggle:
			mode = mode + 1
			if mode == Mode_SayNothing:
				mode = Mode_SayIndent
			conf[SCT_Options][ID_IndentReportMode] = mode
		return mode

	def setIndentReportMode(self, mode):
		conf = self.addonConfig
		conf[SCT_Options][ID_IndentReportMode] = mode

	def getIndentReportMode(self):
		conf = self.addonConfig
		if not self.toggleReportLineIndentationOption(False):
			return Mode_SayNothing
		return conf[SCT_Options][ID_IndentReportMode]

	def toggleReduceFilePathOption(self, toggle=True):
		return self.toggleOption(ID_ReduceFilePath, toggle)

	def setPreviousHierarchicalLevelToKeep(self, level):
		conf = self.addonConfig
		conf[SCT_Options][ID_PreviousHierarchicalLevelToKeep] = level

	def getPreviousHierarchicalLevelToKeep(self):
		conf = self.addonConfig
		return conf[SCT_Options][ID_PreviousHierarchicalLevelToKeep]

	def toggleSayFileNameBeforePathOption(self, toggle=True):
		return self.toggleOption(ID_SayFileNameBeforePath, toggle)

	def toggleNoSayFilePathBackslashsOption(self, toggle=True):
		return self.toggleOption(ID_NoSayFilePathBackslashs, toggle)

	def toggleReversePathOption(self, toggle=True):
		return self.toggleOption(ID_ReversePath, toggle)

	def toggleReportReversedPathWithNoLevelOption(self, toggle=True):
		return self.toggleOption(ID_ReportReversedPathWithNoLevel, toggle)

	def toggleReportSpellingErrorsOption(self, toggle=True):
		return self.toggleOption(ID_ReportSpellingErrors, toggle)

	def getDocumentColumnsChoices(self):
		conf = self.addonConfig
		documentColumns = conf[SCT_Options][ID_DocumentColumnsChoices]
		columns = []
		if len(documentColumns) == 0:
			return columns
		for column in documentColumns .split(","):
			columns.append(documentColumnIDs.index(column))
		return columns

	def setDocumentColumnsChoices(self, columns):
		conf = self.addonConfig
		choices = []
		for column in columns:
			choices.append(documentColumnIDs[column])
		conf[SCT_Options][ID_DocumentColumnsChoices] = ",".join(choices)

	def getCopyAllMisspelledWordsToClipboardShortCut(self):
		conf = self.addonConfig
		return conf[SCT_DSpellCheck][ID_CopyAllMisspelledWordsToClipboardShortCut]


# singleton for addon config manager
_addonConfigManager = AddonConfigurationManager()
