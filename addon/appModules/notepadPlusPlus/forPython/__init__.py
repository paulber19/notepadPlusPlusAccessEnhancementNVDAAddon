# appModules\notepad++\forPython\__init__.py
# A part of the notepadPlusPlusAccessEnhancement add-on
# Copyright (C) 2020-2023 paulber19
# This file is covered by the GNU General Public License.

import addonHandler

from logHandler import log
import speech
import api
import textInfos
import ui
from speech.speech import SpeakTextInfoState
import config
from speech.priorities import Spri
from speech.commands import (
	# Commands that are used in this file.
	SpeechCommand,
)
import os
import sys
_curAddon = addonHandler.getCodeAddon()
sharedPath = os.path.join(_curAddon.path, "shared")
sys.path.append(sharedPath)
from npp_addonConfigManager import _addonConfigManager
from npp_addonConfigManager import (
	Mode_SayIndent, Mode_SayLevel, Mode_SayLevelChange, Mode_SayIndentChange, Mode_SayNothing)
del sys.path[-1]
from controlTypes.outputReason import OutputReason


addonHandler.initTranslation()
# messages
msgUnknownLevel = _("Unknow level")
msgLevel = _("Level")

# constantes

# indent characters
C_INDENT = " "

GB_sLevelMark = "1T"
GB_LastIndentList = []
# timer
GB_Timer = None


def GetCurrentLine():
	obj = api.getFocusObject()
	treeInterceptor = obj.treeInterceptor
	if hasattr(treeInterceptor, 'TextInfo') and not treeInterceptor.passThrough:
		obj = treeInterceptor
	try:
		info = obj.makeTextInfo(textInfos.POSITION_CARET)
	except (NotImplementedError, RuntimeError):
		info = obj.makeTextInfo(textInfos.POSITION_FIRST)
	info.expand(textInfos.UNIT_LINE)
	return info.text


def GetIndentations(sLine):
	"""
	function to get the indents of line
	return a tuple indent string list and line without indent
	Each string give the number and type of the indent
	3T for 3 tab
	4E for four spaces
	0E for no indent
	"""
	if len(sLine) == 0:
		return (["0E"], sLine)

	sIndentCharacter = sLine[0]
	if sIndentCharacter == " ":
		sIndentMarque = "E"

	elif sIndentCharacter == "\t":
		sIndentMarque = "T"
	else:
		# no indent at start of line
		return (["0E"], sLine)
	sIndent = []
	iIndent = 1
	sTemp = sLine[1:]
	iStopBoucle = 150
	while (len(sTemp) > 0) and (iStopBoucle > 0):
		iStopBoucle = iStopBoucle - 1
		#
		sPremierChar = sTemp[0]

		#
		if (sPremierChar != " ")\
			and (sPremierChar != "\t"):
			#
			sIndent.append(str(iIndent) + sIndentMarque)
			#
			return sIndent, sTemp
		sTemp = sTemp[1:]
		if sPremierChar == sIndentCharacter:

			iIndent = iIndent + 1
		else:
			sIndent.append(str(iIndent) + sIndentMarque)
			iIndent = 1
			sIndentCharacter = sPremierChar
			if sIndentMarque == "E":
				sIndentMarque = "T"
			else:
				sIndentMarque = "E"

	if iIndent != 0:
		# one indent to add
		sIndent.append(str(iIndent) + sIndentMarque)

	if iStopBoucle == 0:
		# too many indents
		return([], sLine)

	return (sIndent, sTemp)


def CalculateLineLevel(sIndentList):
	if sIndentList == ["0E"]:
		# level 0
		return 0

	if len(sIndentList) != 1:
		# unknown level
		return -1

	sIndent = sIndentList[0]
	sTabOuEspace = sIndent[-1:]
	if sTabOuEspace != GB_sLevelMark[-1:]:
		# unattended level mark
		return -1

	sPas = int(sIndent[:-1])
	i = 1 + (sPas / int(GB_sLevelMark[:-1]))

	if sPas % int(GB_sLevelMark[:-1]):
		#
		return -1

	return int(i - 1)


def GetLineAndColumnNumber():
	obj = api.getFocusObject()
	start = obj.makeTextInfo(textInfos.POSITION_ALL)
	try:
		end = obj.makeTextInfo(textInfos.POSITION_CARET)
	except (NotImplementedError, RuntimeError):
		log.error("Position can not be reported")
		return
	start.setEndPoint(end, "endToStart")
	text = start.text
	line = len(text.split("\r"))
	start = end  # Caret position
	start.expand(textInfos.UNIT_LINE)
	end = obj.makeTextInfo(textInfos.POSITION_CARET)
	start.setEndPoint(end, "endToStart")
	column = len(start.text) + 1
	return (line, column)


def GetLevelToSay(sIndentList):
	i = CalculateLineLevel(sIndentList)
	text = ""
	if i < 0:
		text = msgUnknownLevel
	else:
		if GB_LastIndentList[:] != sIndentList[:]:
			text = msgLevel + str(i)
	return text


def GetIndentText(sIndentList):
	if len(sIndentList) == 0:
		# not possible to determinate
		return ""

	if sIndentList == ["0E"]:
		# no indent
		return ""
	sTemp = ""
	for sIndent in sIndentList:
		sTemp = sTemp + " " + sIndent[:-1]
		if sIndent[-1] == "E":
			sTemp = sTemp + " espaces"
		else:
			sTemp = sTemp + " Tab "

	return sTemp


def FormatLine(sLine):
	global GB_LastIndentList

	text = ""
	if _addonConfigManager.toggleReportLineNumberOption(False):
		(lineNumber, columnNumber) = GetLineAndColumnNumber()
		text = str(lineNumber) + " "
	(sIndentList, sLineWithoutIndent) = GetIndentations(sLine)
	CheckLineIndentType(sIndentList)
	indentReportMode = _addonConfigManager.getIndentReportMode()
	if indentReportMode == Mode_SayIndent:
		indentText = GetIndentText(sIndentList)
		text = text + indentText + " "
	elif indentReportMode == Mode_SayLevel:
		levelText = GetLevelToSay(sIndentList)
		text = text + levelText + " "
	elif indentReportMode == Mode_SayLevelChange:
		text = text + GetSayLevelChangeText(sIndentList)
	elif indentReportMode == Mode_SayIndentChange:
		text = text + GetSayIndentChangeText(sIndentList)
	GB_LastIndentList = sIndentList

	return text + sLineWithoutIndent


def GetIndentCount(sIndentList):

	iCount = 0

	for s in sIndentList:
		iCount = iCount + int(s[:-1])

	return iCount


def GetSayLevelChangeText(sIndentList):
	text = ""
	iCount = GetIndentCount(sIndentList)
	lastIndentCount = GetIndentCount(GB_LastIndentList)
	if iCount > lastIndentCount:
		text = _("Higher level") + " "
	elif iCount < lastIndentCount:
		text = _("Lower level") + " "

	return text


def GetSayIndentChangeText(indentList):
	global GB_LastIndentList
	text = ""

	if ",".join(indentList) != ",".join(GB_LastIndentList):
		if indentList == ["0E"]:
			text = _("No indent") + " "
		else:
			text = GetIndentText(indentList)

	return text


def CheckLineIndentType(indentList):
	type = indentList[0][-1:]
	for s in indentList:
		if s[-1:] != type:
			indentReportMode = _addonConfigManager.getIndentReportMode()
			if indentReportMode in [Mode_SayLevel, Mode_SayLevelChange]:
				speech.speakMessage(_("Attention, mixture of spaces and tab"))
				break


def setLevelMark(obj):
	global GB_sLevelMark
	sText = obj.windowText.split("\n")
	hasAnInstruction = False
	for sLine in sText:
		if len(sLine) <= 1:
			continue
		(sIndentList, sLineWithoutIndent) = GetIndentations(sLine[:-1])
		if IsInstruction(sLineWithoutIndent):
			hasAnInstruction = True
		if len(sIndentList) != 1 or sIndentList == ["0E"]:
			continue
		if hasAnInstruction:
			GB_sLevelMark = sIndentList[0]
			return


def IsInstruction(sLine):
	if sLine == "":
		return False
	sChar = sLine[-1]
	if sChar == ":" and (
		sLine[:4] == "def "
		or sLine[:3] == "if "
		or sLine[:4] == "try "
		or sLine[:6] == "while "
		or sLine[:4] == "for "):
		return True

	return False


def SayPosition():
	global GB_LastIndentList
	sLine = GetLineToCursor()
	(sIndentList, sLineWithoutIndent) = GetIndentations(sLine)
	if sIndentList == ["0E"]:
		ui.message(_("Start of line"))
		return
	indentReportMode = _addonConfigManager.getIndentReportMode()
	if len(sLineWithoutIndent) > 0:
		ui.message(_("column %s") % (len(sLine) + 1))
		info = api.getReviewPosition().copy()
		info.expand(textInfos.UNIT_CHARACTER)
		speech.speakTextInfo(info, unit=textInfos.UNIT_CHARACTER, reason=OutputReason.CARET)
	elif indentReportMode == Mode_SayNothing:
		ui.message(_("column %s") % (len(sLine) + 1))
	elif indentReportMode in [Mode_SayIndent, Mode_SayIndentChange, Mode_SayLevelChange]:
		text = GetIndentText(sIndentList)
		ui.message(_("After") + " " + text)
	elif indentReportMode in [Mode_SayLevel]:
		GB_LastIndentList = []
		ui.message(GetLevelToSay(sIndentList))
	GB_LastIndentList = sIndentList


def GetLineToCursor():
	obj = api.getFocusObject()
	start = obj.makeTextInfo(textInfos.POSITION_ALL)
	try:
		end = obj.makeTextInfo(textInfos.POSITION_CARET)
	except (NotImplementedError, RuntimeError):
		ui.message(_("Line cannot be reported"))
		return ""

	start = end  # Caret position
	start.expand(textInfos.UNIT_LINE)
	end = obj.makeTextInfo(textInfos.POSITION_CARET)
	start.setEndPoint(end, "endToStart")
	return start.text


from typing import (
	Optional,
	Dict,
	Union,
)


def splitTextIndentation(line):
	global GB_LastIndentList
	text = ""
	if _addonConfigManager.toggleReportLineNumberOption(False):
		(lineNumber, columnNumber) = GetLineAndColumnNumber()
		text = str(lineNumber) + " "
	(indentList, lineWithoutIndent) = GetIndentations(line)
	CheckLineIndentType(indentList)
	indentReportMode = _addonConfigManager.getIndentReportMode()
	if indentReportMode == Mode_SayIndent:
		text = text + GetIndentText(indentList)
	elif indentReportMode == Mode_SayLevel:
		text = text + GetLevelToSay(indentList)
	elif indentReportMode == Mode_SayLevelChange:
		text = text + GetSayLevelChangeText(indentList)
	elif indentReportMode == Mode_SayIndentChange:
		text = text + GetSayIndentChangeText(indentList)
	GB_LastIndentList = indentList
	if len(text) == 0:
		return ("", lineWithoutIndent)
	elif len(lineWithoutIndent) == 0:
		return ("", text)
	return ("", text + " " + lineWithoutIndent)


def mySpeakTextInfo(
	info: textInfos.TextInfo,
	useCache: Union[bool, SpeakTextInfoState] = True,
	formatConfig: Dict[str, bool] = None,
	unit: Optional[str] = None,
	reason: OutputReason = OutputReason.QUERY,
	_prefixSpeechCommand: Optional[SpeechCommand] = None,
	onlyInitialFields: bool = False,
	suppressBlanks: bool = False,
	priority: Optional[Spri] = None
) -> bool:
	if _addonConfigManager.toggleManageLineNumberAndIndentationAnnouncementOption(False) and (
		unit == textInfos.UNIT_LINE):
		NVDAReportLineIndentationOption = config.conf["documentFormatting"]["reportLineIndentation"]
		NVDAReportLineNumberOption = config.conf["documentFormatting"]["reportLineNumber"]
		NVDASpeechSplitTextIndentation = speech.speech.splitTextIndentation
		speech.speech.splitTextIndentation = splitTextIndentation
		config.conf["documentFormatting"]["reportLineIndentation"] = 1
		config.conf["documentFormatting"]["reportLineNumber"] = False
	res = speech.speakTextInfo(
		info,
		useCache,
		formatConfig,
		unit,
		reason,
		_prefixSpeechCommand,
		onlyInitialFields,
		suppressBlanks,
		priority
	)
	if _addonConfigManager.toggleManageLineNumberAndIndentationAnnouncementOption(False) and (
		unit == textInfos.UNIT_LINE):
		speech.speech.splitTextIndentation = NVDASpeechSplitTextIndentation
		config.conf["documentFormatting"]["reportLineIndentation"] = NVDAReportLineIndentationOption
		config.conf["documentFormatting"]["reportLineNumber"] = NVDAReportLineNumberOption
	return res
