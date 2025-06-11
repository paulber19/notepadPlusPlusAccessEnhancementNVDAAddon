# appModules\notepad++\npp_convert.py
# A part of the notepadPlusPlusAccessEnhancement add-on
# Copyright (C) 2020-2025 paulber19
# This file is covered by the GNU General Public License.

# some parts of code coms from notepad++ add-on created by 16 Tuukka Ojala, Derek Riemer but abandonned.

import addonHandler
from logHandler import log
import ui
import wx
from languageHandler import getLanguage
import gui
import os
import globalVars
import codecs
import sys
import speech.speech
from speech.priorities import SpeechPriority

_curAddon = addonHandler.getCodeAddon()
sharedPath = os.path.join(_curAddon.path, "shared")
sys.path.append(sharedPath)
from npp_py3Compatibility import getCommonUtilitiesPath
from npp_utils import isOpened
from messages import confirm_YesNo, alert, ReturnCode
del sys.path[-1]
del sys.modules["npp_py3Compatibility"]
del sys.modules["npp_utils"]
del sys.modules["messages"]

addonHandler.initTranslation()

DISP_BROWSER = 0
DISP_BROWSABLE_MESSAGE = 1
DISP_EDITOR = 2

# last convert type choice (0 for markdown,  1 for txt2tags)
_lastConvertTypeChoice = 0
# keep last display choice ( 0 for default browser, 1 for  browsable window, 2 for default editor)
_lastDisplayChoice = DISP_BROWSER
# last use default header choice
_lastUseDefaultHeader = True

# converters
_converters = ["markdown", "txt2tags"]

markdown_extensions = [
	"abbr",
	"admonition",
	"attr_list",
	# Codehilite requires Pygments Package included in NVDA from version 2025.1, but incomplete.
#	"codehilite",
	"def_list",
	# "extra",
	"fenced_code",
	"footnotes",
	# "legacy_attrs",
	"legacy_em",
	"md_in_html",
	"meta",
	"nl2br",
	"sane_lists",
	"smarty",
	"tables",
	"toc",
	"wikilinks",
]

EXTENSIONS_CONFIG = {
	"markdown_link_attr_modifier": {
		"new_tab": "external_only",
		"auto_title": "on",
	},
	"mdx_gh_links": {
		"user": "",
		"repo": "",
	},
}


RTL_LANG_CODES = frozenset({"ar", "fa", "he"})


def getStylesPath():
	docPath = os.path.join(_curAddon.path, "doc")
	lang = getLanguage()
	langPath = os.path.join(docPath, lang)
	if os.path.exists(langPath):
		return langPath
	elif "_" in lang:
		lang = lang.split("_")[0]
		langPath = os.path.join(docPath, lang)
		if os.path.exists(langPath):
			return langPath
	return docPath


_waitToRemoveFilesDelay = None
_filesToRemove = []


class ConvertToHTML(object):
	def __init__(self, document, documentPath=None):
		super(ConvertToHTML, self).__init__()
		self.document = document
		self.documentPath = documentPath
		userConfigPath = os.path.abspath(globalVars.appArgs.configPath)
		self.temporaryFolderPathForBrowserView = userConfigPath if documentPath is None else documentPath
		log.debug("temporaryFolderPathForBrowserView : %s" % self.temporaryFolderPathForBrowserView)
		global _waitToRemoveFilesDelay
		if _waitToRemoveFilesDelay is not None:
			_waitToRemoveFilesDelay .Stop()
		self.removeFiles()

	def showHtml(self, html, external):
		if external == DISP_EDITOR:
			ext = "txt"
		else:
			ext = "html"
		temporaryFile = os.path.join(self.temporaryFolderPathForBrowserView, "tmpBrowserView.%s" % ext)
		with codecs.open(temporaryFile, "w", "utf-8") as f:
			f.write(html)
			if _lastUseDefaultHeader:
				self.copyStyleSheets()
		# we assume that the default application for *.html is a browser and for .txt is an editor
		# the file is valid for one minute, should be enough even for long files to load
		source = f.name
		if external == DISP_EDITOR:
			try:
				os.startfile(source)
			except Exception:
				import shellapi
				from winUser import SW_SHOWNORMAL
				shellapi.ShellExecute(
					hwnd=None,
					operation="open",
					file="notepad.exe",
					parameters=source, directory=self.temporaryFolderPathForBrowserView, showCmd=SW_SHOWNORMAL,)
		else:
			os.startfile(source)

		_filesToRemove.append(source)
		global _waitToRemoveFilesDelay
		_waitToRemoveFilesDelay = wx.CallLater(60000, self.removeFiles)

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

	def removeFiles(self):
		global _filesToRemove, _waitToRemoveFilesDelay
		_waitToRemoveFilesDelay = None
		for file in _filesToRemove:
			try:
				os.remove(file)
			except Exception:
				pass
		_filesToRemove.clear()


class ConvertMarkdownToHtml(ConvertToHTML):
	# Translators: document Title
	title = _("Preview of MarkDown document")

	# html header header for markdown document
	HTML_HEADERS = """
<!DOCTYPE html>
<html lang="{lang}" dir="{dir}">
<head>
<meta charset="utf-8">
<title>{title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="stylesheet" href"styles-tmp.css">
<link rel="stylesheet" href="numberedHeadings-tmp.css">
</head>
""".strip()

	def formatHtmlText(self, htmlText, title):
		lang = getLanguage()
		htmlList = []
		htmlList.append(self.HTML_HEADERS.format(
			lang=lang,
			dir="rtl" if lang in RTL_LANG_CODES else "ltr",
			title=title,)
		)
		htmlList.append("<body>")
		htmlList.append(htmlText)
		htmlList.append("</body>")
		htmlList.append("</html>")
		htmlList.append("")
		return "\n".join(htmlList)

	def copyStyleSheets(self):
		import shutil
		# the default styles css files are in doc folder
		# but translators can adapte these files for convenience
		# so the file modified must be placed in the language folder.
		docPath = os.path.join(_curAddon.path, "doc")
		stylesPath = getStylesPath()
		stylesCss = "styles.css"
		stylesCss_tmp = os.path.join(self.temporaryFolderPathForBrowserView, "styles-tmp.css")
		numberedHeadingsCss = "numberedHeadings.css"
		numberedHeadingsCss_tmp = os.path.join(self.temporaryFolderPathForBrowserView, "numberedHeadings-tmp.css")
		if os.path.exists(os.path.join(stylesPath, stylesCss)):
			stylesCss = os.path.join(stylesPath, stylesCss)
		else:
			stylesCss = os.path.join(docPath, stylesCss)
		if os.path.exists(os.path.join(stylesPath, numberedHeadingsCss)):
			numberedHeadingsCss = os.path.join(stylesPath, numberedHeadingsCss)
		else:
			numberedHeadingsCss = os.path.join(docPath, numberedHeadingsCss)
		try:
			shutil.copy(stylesCss, stylesCss_tmp)
			_filesToRemove.append(stylesCss_tmp)
		except Exception:
			log.error(": %s file cannot be copiedto %s" % (stylesCss, stylesCss_tmp))
		try:
			shutil.copy(numberedHeadingsCss, numberedHeadingsCss_tmp)
			_filesToRemove.append(numberedHeadingsCss_tmp)
		except Exception:
			log.error(": %s file cannot be copied to %s" % (numberedHeadingsCss, numberedHeadingsCss_tmp))

	def convert(self, external=False):
		commonUtilitiesPath = getCommonUtilitiesPath()
		markdownExPath = os.path.join(commonUtilitiesPath, "markdownEx")
		sys.path.append(commonUtilitiesPath)
		sys.path.append(markdownExPath)
		# import htmlEx.parser
		# import markdown
		from markdownEx import markdown
		del sys.path[-1]
		del sys.modules["markdownEx"]

		mdText = self.document
		t2tTarget = self.getT2tTarget(mdText)
		if t2tTarget is not None:
			if confirm_YesNo(
				# Translators: the label of a message box dialog.
				_("It seems the document is a t2t document. Do you want to continue to treate as markdown ?"),
				# Translators: the title of a message box dialog.
				_("%s - warning") % _curAddon.manifest["summary"],
			) != ReturnCode.YES:
				return
		extensions = []
		for ext in markdown_extensions:
			extensions.append("markdownEx.markdown.extensions.%s" % ext)
		speech.speech.cancelSpeech()
		speech.speech.speakMessage(_("please wait"), priority=SpeechPriority.NOW)
		htmlText = markdown.markdown(mdText, extensions=extensions, extension_configs=EXTENSIONS_CONFIG)
		return htmlText

	def display(self, htmlText, external):
		if external == DISP_BROWSABLE_MESSAGE:
			ui.browseableMessage(htmlText, self.title, True)
			return
		html = htmlText
		if _lastUseDefaultHeader:
			html = self.formatHtmlText(htmlText, self.title)
		self.showHtml(html, external)

	def convertAndDisplay(self, external):
		htmlText = self.convert()
		self.display(htmlText, external)


class ConvertTxt2TagsToHtml(ConvertToHTML):
	# Translators: The title of the browseable message
	title = _("Preview of txt2tags  document")

	HTML_HEADERS = """
<!DOCTYPE html>
<html lang="{lang}" dir="{dir}">
<head>
<meta charset="utf-8">
<title>{title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="stylesheet" href"styles-t2t-tmp.css">
</head>
""".strip()

	def formatHtmlText(self, htmlText, title):
		lang = getLanguage()
		htmlList = []
		htmlList.append(self.HTML_HEADERS.format(
			lang=lang,
			dir="rtl" if lang in RTL_LANG_CODES else "ltr",
			title=title,)
		)
		htmlList.append(htmlText)
		htmlList.append("</html>")
		htmlList.append("")
		return "\n".join(htmlList)

	def copyStyleSheets(self):
		import shutil
		# the default styles css files are in doc folder
		# but translators can adapte these files for convenience
		# so the file modified must be placed in the language folder.
		docPath = os.path.join(_curAddon.path, "doc")
		stylesPath = getStylesPath()
		stylesCss = "style_t2t.css"
		stylesCss_tmp = os.path.join(self.temporaryFolderPathForBrowserView, "styles-t2t-tmp.css")
		if os.path.exists(os.path.join(stylesPath, stylesCss)):
			stylesCss = os.path.join(stylesPath, stylesCss)
		else:
			stylesCss = os.path.join(docPath, stylesCss)
		try:
			shutil.copy(stylesCss, stylesCss_tmp)
			_filesToRemove.append(stylesCss_tmp)
		except Exception:
			log.error(": %s file cannot be copiedto %s" % (stylesCss, stylesCss_tmp))

	def convert(self):
		txt2tagsModulePath = None
		if "txt2tags" in sys.modules:
			txt2tagsModulePath = sys.modules["txt2tags"]
			del sys.modules["txt2tags"]
		commonUtilitiesPath = getCommonUtilitiesPath()
		sys.path.append(commonUtilitiesPath)
		import txt2tags
		del sys.path[-1]
		del sys.modules["txt2tags"]
		if txt2tagsModulePath is not None:
			sys.modules["txt2tags"] = txt2tagsModulePath

		t2tText = self.document
		target = self.getT2tTarget(t2tText)
		if target is None:
			target = "html"
		elif target not in ["html"]:
			alert(
				# Translators: the label of a message box dialog.
				_("The target(%s) is not HTML" % target),
				# Translators: the title of a message box dialog.
				_("%s - warning") % _curAddon.manifest["summary"],
			)
			return
		speech.speech.cancelSpeech()
		speech.speech.speakMessage(_("please wait"), priority=SpeechPriority.NOW)
		temporaryFile = os.path.join(self.temporaryFolderPathForBrowserView, "tmpBrowserView.t2t")
		with codecs.open(temporaryFile, "w", "utf-8") as f:
			f.write(t2tText)
		source = temporaryFile
		cmd = ["-t", target, source]
		try:
			txt2tags.exec_command_line(cmd)
		except Exception:
			# cannot compile text
			log.warning("error: text or environnement is not good")
			alert(
				# Translators: the label of a message box dialog.
				_("Cannot compile text with txt2tags"),
				# Translators: the title of a message box dialog.
				_("%s - warning") % _curAddon.manifest["summary"],
			)
			return
		dest = source.replace(".t2t", ".%s" % target)
		_filesToRemove.append(source)
		self.removeFiles()
		return dest

	def getHtmlSource(self, htmlFile):
		tagsToBeRemoved = [
			"<META NAME=\"generator\"",
			"<!-- cmdline: txt2tags -t html",
			"<!-- html code generated by txt2tags ",
		]
		htmlList = []
		f = codecs.open(htmlFile, "r", "utf_8", errors="replace")
		for line in f:
			append = True
			for tag in tagsToBeRemoved:
				if tag in line:
					append = False
			if append:
				htmlList.append(line)
		f.close()
		html = "".join(htmlList)
		return html

	def getHtmlBody(self, htmlText):
		htmlList = htmlText.splitlines()
		startTag = "</head>"
		endTag = "</body>"
		appendLine = False
		textList = []
		for sLine in htmlList:
			line = sLine.lower()
			startTagFound = line.find(startTag)
			endTagFound = line.find(endTag)
			if startTagFound >= 0:
				appendLine = True
				sLine = sLine[startTagFound + len(startTag):]
				textList.append(sLine)
				continue
			elif endTagFound >= 0:
				sLine = sLine[: endTagFound]
				textList.append(sLine)
				break
			if appendLine:
				textList.append(sLine)
		textList.append("</body>")
		return "\n".join(textList)

	def display(self, htmlFile, external):
		global _waitToRemoveFilesDelay
		html = self.getHtmlSource(htmlFile)
		if external != DISP_BROWSABLE_MESSAGE:
			if _lastUseDefaultHeader:
				htmlText = self.getHtmlBody(html)
				html = self.formatHtmlText(htmlText, self.title)
			_filesToRemove.append(htmlFile)
			self.removeFiles()
			self.showHtml(html, external)
		else:
			ui.browseableMessage(html, self.title, True)
			_filesToRemove.append(htmlFile)
			self.removeFiles()

	def convertAndDisplay(self, external):
		htmlFile = self.convert()
		if htmlFile:
			self.display(htmlFile, external)


class ConvertToHTMLDialog(wx.Dialog):
	_instance = None
	# Translators: This is the title of convert to html dialog window
	title = _("Preview the document")

	def __new__(cls, *args, **kwargs):
		if ConvertToHTMLDialog._instance is not None:
			return ConvertToHTMLDialog._instance
		return super(ConvertToHTMLDialog, cls).__new__(cls, *args, **kwargs)

	def __init__(self, parent, document, documentPath):
		if ConvertToHTMLDialog._instance is not None:
			return
		super(ConvertToHTMLDialog, self).__init__(parent, -1, title=self.title, style=wx.CAPTION | wx.CLOSE_BOX)
		ConvertToHTMLDialog._instance = self
		self.document = document
		self.documentPath = documentPath
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
		# Translators: This is a label appearing on convert to html dialog
		labelText = _("&Display with:")
		self.displayWithChoices = [
			# Translators:  display converted document with default .html file viewer
			_("Default html documents viewer"),
			# display converted document withNVDA browsable message
			_("Browsable window"),
			# Translators: display converted document source with default .txt viewer
			_("Default txt document viewer")]
		self.displayWithListBox = sHelper.addLabeledControl(
			labelText,
			wx.ListBox,
			id=wx.ID_ANY,
			choices=self.displayWithChoices,
			style=wx.LB_SINGLE | wx.LB_ALWAYS_SB,
			size=(948, 130))
		self.displayWithListBox.SetSelection(_lastDisplayChoice)
		#  use default html header
		self.useDefaultHeaderBox = sHelper.addItem(wx.CheckBox(
			self,
			wx.ID_ANY,
			# Translators:  label of a check box.
			label=_("&Use of default HTML header")))
		self.useDefaultHeaderBox.SetValue(_lastUseDefaultHeader)
		bHelper = sHelper.addDialogDismissButtons(gui.guiHelper.ButtonHelper(wx.HORIZONTAL))
		labelText = _("&Preview")
		previewButton = wx.Button(self, label=labelText)
		sHelper.addItem(previewButton)
		previewButton .SetDefault()
		cancelButton = bHelper.addButton(self, wx.ID_CANCEL)
		mainSizer.Add(sHelper.sizer, border=gui.guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		mainSizer.Fit(self)
		self.SetSizer(mainSizer)
		# Events
		previewButton.Bind(wx.EVT_BUTTON, self.onPreviewButton)
		cancelButton.Bind(wx.EVT_BUTTON, lambda evt: self.Close())
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.SetEscapeId(wx.ID_CANCEL)

	def Destroy(self):
		ConvertToHTMLDialog._instance = None
		super(ConvertToHTMLDialog, self).Destroy()

	def onClose(self, evt):
		self.Destroy()
		evt.Skip()

	@classmethod
	def convertAndDisplay(cls, document, documentPath):
		if _lastConvertTypeChoice == 0:
			conv = ConvertMarkdownToHtml(document, documentPath)
		else:
			conv = ConvertTxt2TagsToHtml(document, documentPath)
		wx.CallLater(50, speech.speech.cancelSpeech)
		wx.CallLater(100, conv.convertAndDisplay, _lastDisplayChoice)

	def onPreviewButton(self, evt):
		global _lastDisplayChoice, _lastConvertTypeChoice, _lastUseDefaultHeader
		_lastConvertTypeChoice = self.converterBox.GetSelection()
		_lastDisplayChoice = self.displayWithListBox.GetSelection()
		_lastUseDefaultHeader = self.useDefaultHeaderBox.IsChecked()
		self.Close()
		ConvertToHTMLDialog.convertAndDisplay(self.document, self.documentPath)

	@classmethod
	def run(cls, document, documentPath):
		if isOpened(cls):
			return
		gui.mainFrame.prePopup()
		d = cls(gui.mainFrame, document, documentPath)
		d.CentreOnScreen()
		d.Show()
		gui.mainFrame.postPopup()
