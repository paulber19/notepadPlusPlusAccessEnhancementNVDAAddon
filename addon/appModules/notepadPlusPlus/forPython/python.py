# appModules\notepad++\forPython\python.py
# A part of the notepadPlusPlusAccessEnhancement add-on
# Copyright (C) 2020-2022 paulber19
# This file is covered by the GNU General Public License.


import addonHandler
from logHandler import log
import speech
import re
import textInfos
import os
import sys
import traceback

_curAddon = addonHandler.getCodeAddon()
sharedPath = os.path.join(_curAddon.path, "shared")
sys.path.append(sharedPath)
from npp_addonConfigManager import _addonConfigManager
del sys.path[-1]

addonHandler.initTranslation()


def printDebug(s):
	return


class InterpreterError(Exception):
	pass


def my_exec(cmd, globals=None, locals=None, description='source string'):
	try:
		exec(cmd, globals, locals)
	except SyntaxError as err:
		error_class = err.__class__.__name__
		detail = err.args[0]
		line_number = err.lineno
	except Exception as err:
		error_class = err.__class__.__name__
		detail = err.args[0]
		cl, exc, tb = sys.exc_info()
		line_number = traceback.extract_tb(tb)[-1][1]
	else:
		return
	interpreterError = InterpreterError("%s at line %d %s: %s" % (error_class, line_number, description, detail))
	interpreterError.lineNumber = line_number
	raise interpreterError


class PythonDocument(object):
	msgNoOtherClass = _("No other class")
	msgNoOtherMethod = _("No other method")
	msgNoOtherClassOrMethod = _("No other class or method")

	@classmethod
	def importCode(self, code, name, add_to_sys_modules=0):
		""" code can be any object containing code -- string, file object, or
		compiled code object. Returns a new module object initialized
		by dynamically importing the given code and optionally adds it
		to sys.modules under the given name.
		"""
		import imp
		module = imp.new_module(name)
		if add_to_sys_modules:
			sys.modules[name] = module
		try:
			my_exec(code)
		except InterpreterError as e:
			raise e
		return module

	@classmethod
	def goToLongLine(self, info, next=True):
		info.expand(textInfos.UNIT_STORY)
		document = info._getStoryText()
		textList = document.splitlines()
		if len(textList) == 0:
			return
		currentLine = info.getCurrentLineNumber()
		if next:
			r = range(currentLine, len(textList) - 1)
			dec = 1
		else:
			r = range(currentLine, 0, -1)
			dec = -1
		for id in r:
			lineID = id + dec
			line = textList[lineID]
			temp = line.replace("\t", "")
			temp = temp.replace(" ", "")
			if len(temp) > _addonConfigManager.getMaxLineLength():
				info.goToLine(lineID)
				return
		# Translators: message to user to say there no more long line
		speech.speakMessage(_("No more long line"))

	@classmethod
	def moveToLineWithOnlyTabOrSpace(cls, info, next=True):
		info.expand(textInfos.UNIT_STORY)
		document = info._getStoryText()
		textList = document.splitlines()
		if len(textList) == 0:
			log.error("error: text list empty")
			return
		currentLine = info.getCurrentLineNumber()
		if next:
			rng = list(range(currentLine + 1, len(textList)))
		else:
			rng = list(range(currentLine - 1, -1, -1))
		for lineID in rng:
			line = textList[lineID]
			if len(line) == 0:
				continue
			temp = line.replace("\t", "")
			temp = temp.replace(" ", "")
			if len(temp):
				continue
			info.goToLine(lineID)
			return
		speech.speakMessage(_("No more line with only tab or space"))

	@classmethod
	def moveToLineEndingWithTabOrspace(cls, info, next=True):
		info.expand(textInfos.UNIT_STORY)
		document = info._getStoryText()
		textList = document.splitlines()
		if len(textList) == 0:
			log.error("error: text list empty")
			return
		currentLine = info.getCurrentLineNumber()
		if next:
			rng = list(range(currentLine + 1, len(textList)))
		else:
			rng = list(range(currentLine - 1, -1, -1))
		for lineID in rng:
			line = textList[lineID]
			if len(line) == 0:
				continue
			if len(line.replace("\t", "")) == 0:
				continue
			if len(line.replace(" ", "")) == 0:
				continue
			if line[-1] not in ["\t", " "]:
				continue
			info.goToLine(lineID)
			return
		speech.speakMessage(_("No more line ending with tab or space"))

	@classmethod
	def moveToNextOrPrevious(cls, info, regElement, regStop=None, noElementText="", previous=False):
		info.expand(textInfos.UNIT_STORY)
		document = info._getStoryText()
		textList = document.splitlines()
		if len(textList) == 0:
			return
		if previous:
			start = info.getCurrentLineNumber() - 1
			rng = list(range(start, -1, -1))
		else:
			start = info.getCurrentLineNumber() + 1
			rng = list(range(start, len(textList)))
		for lineID in rng:
			if regElement.match(textList[lineID]):
				info.goToLine(lineID)
				return
			if regStop and regStop.match(textList[lineID]):
				break
		speech.speakMessage(noElementText)
		return

	@classmethod
	def nextClass(cls, info):
		noElementText = PythonDocument.msgNoOtherClass
		regElement = re.compile("^[ \t]*((?:class ).*$)", re.MULTILINE)
		regStop = None
		cls.moveToNextOrPrevious(info, regElement, regStop, noElementText)

	@classmethod
	def previousClass(cls, info):
		noElementText = PythonDocument.msgNoOtherClass
		regElement = re.compile("^[ \t]*((?:class ).*$)", re.MULTILINE)
		regStop = None
		cls.moveToNextOrPrevious(info, regElement, regStop, noElementText, previous=True)

	@classmethod
	def nextMethod(cls, info):
		noElementText = PythonDocument.msgNoOtherMethod
		regElement = re.compile("^[ \t]*((?:def ).*$)", re.MULTILINE)
		regStop = re.compile("^[ \t]*((?:class).*?:.*$)", re.MULTILINE)
		cls.moveToNextOrPrevious(info, regElement, regStop, noElementText)

	@classmethod
	def previousMethod(cls, info):
		noElementText = PythonDocument.msgNoOtherMethod
		regElement = re.compile("^[ \t]*((?:def ).*$)", re.MULTILINE)
		regStop = re.compile("^[ \t]*((?:class).*?:.*$)", re.MULTILINE)
		cls.moveToNextOrPrevious(info, regElement, regStop, noElementText, previous=True)

	@classmethod
	def nextClassOrMethod(cls, info):
		noElementText = PythonDocument.msgNoOtherClassOrMethod
		regElement = re.compile("^[ \t]*((?:class |def ).*$)", re.MULTILINE)
		regStop = None
		cls.moveToNextOrPrevious(info, regElement, regStop, noElementText)

	@classmethod
	def previousClassOrMethod(cls, info):
		noElementText = PythonDocument.msgNoOtherClassOrMethod
		regElement = re.compile("^[ \t]*((?:class |def ).*$)", re.MULTILINE)
		regStop = None
		cls.moveToNextOrPrevious(info, regElement, regStop, noElementText, previous=True)
