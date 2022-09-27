# appModules\notepad++\npp_convert.py
# A part of the notepadPlusPlusAccessEnhancement add-on
# Copyright (C) 2020-2022 paulber19
# This file is covered by the GNU General Public License.

# some parts of code coms from notepad++ add-on created by 16 Tuukka Ojala, Derek Riemer but abandonned.

import addonHandler
from logHandler import log
import ui
import wx
import gui
import os
import re
import tempfile
import codecs
import sys

_curAddon = addonHandler.getCodeAddon()
sharedPath = os.path.join(_curAddon.path, "shared")
sys.path.append(sharedPath)
from npp_py3Compatibility import getCommonUtilitiesPath, getUtilitiesPath
from npp_utils import isOpened
del sys.path[-1]
addonHandler.initTranslation()

# keep last convert type choice (0 for markdown,  1 for txt2tags)
_lastConvertTypeChoice = 0
# keep last display choice ( true for browser or False for  virtual buffer)
_lastDisplayChoice = True
# converters
_converters = ["markdown", "txt2tags"]


class ConvertToHTML(object):
	def __init__(self, document):
		super(ConvertToHTML, self).__init__()
		self.document = document

	def mdToHTML(self, external=False):
		commonUtilitiesPath = getCommonUtilitiesPath()
		markdownPath = os.path.join(commonUtilitiesPath, "markdown")
		sys.path.append(markdownPath)
		from markdown2 import markdown
		del sys.path[-1]

		raw = self.getRaw()
		t2tTarget = self.getT2tTarget(raw)
		if t2tTarget is not None:
			if gui.messageBox(
				# Translators: the label of a message box dialog.
				_("It seems the document is a t2t document. Do you want to continue to treate as markdown ?"),
				# Translators: the title of a message box dialog.
				_("%s - warning") % _curAddon.manifest["summary"],
				wx.YES | wx.NO | wx.ICON_WARNING) == wx.NO:
				return
		html = markdown(raw)

		if not external:
			# Translators: The title of the browseable message
			title = _("Preview of MarkDown or HTML")
			ui.browseableMessage(html, title, True)
		else:
			if html.find('<head > ') == -1:
				# Translators: Title for the default browser, instead of the file name
				title = _("Preview of MarkDown or HTML")
				html = r'<head> <title>' + title + r'</title></head>' + r'<body>' + html + r'<body>'
			with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
				f.write(html.encode('utf-8'))
			# we assume that the default application for *.html is a browser
			# The webrowser module does not always open the file with the standard browser
			# the file is valid for one minute, should be enough even for long files to load
				source = f.name
			os.startfile(source)
			wx.CallLater(60000, self.removeFiles, [source, ])

	def getRaw(self):
		raw = self.document
		raw = re.sub(r'\[\[!meta title=\"(.*)\"\]\]', r'# \1 #', raw)
		return raw

	def getT2tTarget(self, document):
		target = None
		textList = document.splitlines()
		for line in textList:
			search = "%!target:"
			line = line.lower()
			if len(line) > len(search) and line[: len(search)] == search:
				target = line.replace(search, "")
				target = target.strip()
				target = target.lower()
				break
		return target

	def t2tToHTML(self, external=False):
		utilitiesPath = getUtilitiesPath()
		sys.path.append(utilitiesPath)
		import txt2tags
		del sys.path[-1]
		raw = self.getRaw()
		target = self.getT2tTarget(raw)
		if target is None:
			target = "html"
		elif target not in ["html"]:
			if gui.messageBox(
				# Translators: the label of a message box dialog.
				_("The target(%s) is not HTML" % target),
				# Translators: the title of a message box dialog.
				_("%s - warning") % _curAddon.manifest["summary"],
				wx.CLOSE | wx.ICON_WARNING):
				return
		with tempfile.NamedTemporaryFile(suffix='.t2t', delete=False) as f:
			f.write(raw.encode('utf-8'))
		source = f.name
		cmd = ["-t", target, source]
		try:
			txt2tags.exec_command_line(cmd)
		except Exception:
			# cannot compile text
			log.warning("error: text or environnement is not good")
			if gui.messageBox(
				# Translators: the label of a message box dialog.
				_("Cannot compile text with txt2tags"),
				# Translators: the title of a message box dialog.
				_("%s - warning") % _curAddon.manifest["summary"],
				wx.CLOSE | wx.ICON_WARNING):
				return
		dest = source.replace(".t2t", ".%s" % target)
		if external:
			# we assume that the default application for *.html is a browser
			# The webrowser module does not always open the file with the standard browser
			# the file is valid for one minute, should be enough even for long files to load
			os.startfile(dest)
			wx.CallLater(60000, self.removeFiles, [source, dest])
		else:
			html = ""
			f = codecs.open(dest, "r", "utf_8", errors="replace")
			for line in f:
				html = html + line + "\r\n"
			f.close()
			# Translators: The title of the browseable message
			title = _("Preview of txt2tags or HTML")
			ui.browseableMessage(html, title, True)
			self.removeFiles([source, dest])

	def removeFiles(self, files):
		for file in files:
			os.remove(file)

	def convertAndDisplay(self):
		external = _lastDisplayChoice
		converter = _converters[_lastConvertTypeChoice]
		if converter == "txt2tags":
			self.t2tToHTML(external)
		elif converter == "markdown":
			self.mdToHTML(external)


class ConvertToHTMLDialog(wx.Dialog):
	_instance = None
	# Translators: This is the title of convert to html dialog window
	title = _("Convert to HTML")

	def __new__(cls, *args, **kwargs):
		if ConvertToHTMLDialog._instance is not None:
			return ConvertToHTMLDialog._instance
		return super(ConvertToHTMLDialog, cls).__new__(cls, *args, **kwargs)

	def __init__(self, parent, document):
		if ConvertToHTMLDialog._instance is not None:
			return
		super(ConvertToHTMLDialog, self).__init__(parent, -1, title=self.title, style=wx.CAPTION | wx.CLOSE_BOX)
		ConvertToHTMLDialog._instance = self
		self.document = document
		self.doGui()

	def doGui(self):
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = gui.guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		# markdown or txt2tags
		# Translators: This is a label appearing on convert to html dialog
		labelText = _("&Treate with:")
		self.converters = ["markdown", "txt2tags"]
		self.converterBox = sHelper.addLabeledControl(
			labelText,
			wx.ListBox,
			id=wx.ID_ANY,
			choices=self.converters,
			style=wx.LB_SINGLE | wx.LB_ALWAYS_SB,
			size=(948, 130))
		self.converterBox.SetSelection(_lastConvertTypeChoice)
		# the display choice
		self.displayBox = sHelper.addItem(wx.CheckBox(
			self,
			wx.ID_ANY,
			# Translators:  label of a check box.
			label=_("&Display the result in the navigator")))
		self.displayBox.SetValue(_lastDisplayChoice)
		bHelper = sHelper.addDialogDismissButtons(gui.guiHelper.ButtonHelper(wx.HORIZONTAL))
		okButton = bHelper.addButton(self, wx.ID_OK)
		okButton .SetDefault()
		cancelButton = bHelper.addButton(self, wx.ID_CANCEL)
		mainSizer.Add(sHelper.sizer, border=gui.guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		mainSizer.Fit(self)
		self.SetSizer(mainSizer)
		# Events
		okButton.Bind(wx.EVT_BUTTON, self.onOk)
		cancelButton.Bind(wx.EVT_BUTTON, lambda evt: self.Close())
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.SetEscapeId(wx.ID_CANCEL)

	def Destroy(self):
		ConvertToHTMLDialog._instance = None
		super(ConvertToHTMLDialog, self).Destroy()

	def onClose(self, evt):
		self.Destroy()
		evt.Skip()

	def onOk(self, evt):
		global _lastConvertTypeChoice, _lastDisplayChoice
		_lastConvertTypeChoice = self.converterBox.GetSelection()
		_lastDisplayChoice = self.displayBox.IsChecked()
		self.Close()
		conv = ConvertToHTML(self.document)
		wx.CallLater(100, conv.convertAndDisplay, )

	@classmethod
	def run(cls, info):
		if isOpened(cls):
			return
		gui.mainFrame.prePopup()
		d = cls(gui.mainFrame, info)
		d.CentreOnScreen()
		d.Show()
		gui.mainFrame.postPopup()
