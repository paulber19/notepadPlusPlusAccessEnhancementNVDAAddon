# appModules\notepad++\npp_quickNav.py
# A part of the notepadPlusPlusAccessEnhancement add-on
# Copyright (C) 2020-2025 paulber19
# This file is covered by the GNU General Public License.


import addonHandler
import browseMode
import speech
import re
import textInfos
import os
import sys
_curAddon = addonHandler.getCodeAddon()
sharedPath = os.path.join(_curAddon.path, "shared")
sys.path.append(sharedPath)
from npp_addonConfigManager import _addonConfigManager
del sys.path[-1]

addonHandler.initTranslation()


class NPPDocumentNodeQuickNavItem(browseMode.TextInfoQuickNavItem):
	def __init__(self, itemType, document, textInfo):
		self.itemType = itemType
		super(NPPDocumentNodeQuickNavItem, self).__init__(itemType, document, textInfo)
		self.level = self.getLevel()

	def isChild(self, parent):
		if not isinstance(parent, NPPDocumentNodeQuickNavItem):
			return False
		if all(hasattr(x, "level") for x in (self, parent)):
			return self.level > parent.level

	def getLevel(self):
		return 0

	@property
	def label(self):
		if self.itemType == "blockQuote":
			return self.textInfo.text.replace(">", "").strip()
		if self.itemType == "link":
			return self.textInfo.text.split("[")[1].split("]")[0]


class NPPDocumentHeadingQuickNavItem(NPPDocumentNodeQuickNavItem):
	def getLevel(self):
		documentType = self.textInfo.documentType
		if documentType == "markdown":
			level = re.split(r"[\s\t]", self.textInfo.text)[0].count("#")
		elif documentType == "txt2tags":
			level = re.split(r"[\s\t]", self.textInfo.text)[0].count("+")
		else:
			raise NotImplementedError
		return level

	@property
	def label(self):
		documentType = self.textInfo.documentType
		if documentType == "markdown":
			return self.textInfo.text.replace("#", "").strip()
		else:
			return self.textInfo.text.replace("+", "").strip()


class NPPDocumentLinkQuickNavItem(NPPDocumentNodeQuickNavItem):
	@property
	def label(self):
		info = self.textInfo.copy()
		info.expand(textInfos.UNIT_LINE)
		text = info.text
		if "[" in text:
			return info.text.split("[")[1].split("]")[0]
		elif "[" in text:
			return info.text.split("<")[1].split(">")[0]
		return text


class NPPDocumentBlockQuoteQuickNavItem(NPPDocumentNodeQuickNavItem):
	@property
	def label(self):
		info = self.textInfo.copy()
		info.expand(textInfos.UNIT_LINE)
		if ">" in info.text:
			return info.text.split(">")[1][1:max(80, len(info.text))]
		return info.text

	def getLevel(self):
		if ">" in self.textInfo.text:
			return self.textInfo.text.count(">")
		return 0


class NPPDocumentLongLineQuickNavItem(NPPDocumentNodeQuickNavItem):
	@property
	def label(self):
		info = self.textInfo.copy()
		info.expand(textInfos.UNIT_LINE)
		return info.text


class NPPDocumentNodesQuickNavIterator (object):
	NodeClass = NPPDocumentNodeQuickNavItem

	def __init__(self, nodeType, document, direction, info):
		self.nodeType = nodeType
		self.document = document
		self.reverse = True if direction == "previous" else False
		self.elementsList = False
		if info:
			self.searchArea = info.copy()
		else:
			self.searchArea = document.makeTextInfo(textInfos.POSITION_FIRST)
			self.elementsList = True
		self.isHeading = "heading" in nodeType
		self.isLink = nodeType == "link"
		self.isBlockQuote = nodeType == "blockQuote"
		self.isList = nodeType == "list"
		self.isListItem = nodeType == "listItem"
		self.levelToFind = 0
		if self.nodeType[-1].isdigit():
			self.levelToFind = int(self.nodeType[-1])
		self.documentType = self.getDocumentType()

	def getDocumentType(self):
		info = self.searchArea.copy()
		info.expand(textInfos.UNIT_STORY)
		markdown = re.search(
			r"^#+[\s\t]",
			info.text,
			(re.IGNORECASE) | re.UNICODE | re.DOTALL | re.MULTILINE)
		txt2tags = re.search(
			r"^\++[\s\t]",
			info.text,
			(re.IGNORECASE) | re.UNICODE | re.DOTALL | re.MULTILINE)
		if markdown and txt2tags:
			speech.speakMessage(_("Unable to determine document type: markdown or txt2tags"))
			return "unknown"
		if markdown:
			documentType = "markdown"
		elif txt2tags:
			documentType = "txt2tags"
		else:
			documentType = "unknown"
		return documentType

	def getSearchPattern(self):
		pattern = ""
		if self.isBlockQuote:
			pattern = r"> "
		elif self.isLink:
			pattern = r"\[\\w+\]"
		elif self.isListItem:
			pattern = "* "
		pattern = self.adjustPattern(pattern)
		return pattern

	def adjustPattern(self, searchPattern):
		pattern = searchPattern
		reverse = self.reverse
		if reverse:
			pattern = searchPattern[::-1] if not self.isLink else (
				"%s%s%s" % (searchPattern[-1], searchPattern[2:-1], searchPattern[1]))
		if self.isListItem:
			pattern = r"%s" % searchPattern if reverse else "%s" % searchPattern
			pattern = pattern.replace("*", r"[\*\+-]")
		elif self.isList:
			pattern = r" *(?=[\r\n][\r\n][\r\n])" if reverse else r"(?<=[\r\n][\r\n][\r\n])* "
		pattern = pattern.replace(
			" ", r"[\s\t]") if not self.isBlockQuote else pattern.replace(" ", r"[\s\t]?(?=\w)")
		return pattern

	def isValid(self, item):
		return True

	def iterate(self):
		pattern = self.getSearchPattern()
		while self.searchArea.find(pattern, reverse=self.reverse, elementsList=self.elementsList):
			info = self.searchArea.copy()
			info.expand(textInfos.UNIT_LINE)
			info.documentType = self.documentType
			item = self.NodeClass(self.nodeType, self.document, info)
			if not self.isValid(item):
				continue
			yield item


class NPPDocumentHeadingsQuickNavIterator(NPPDocumentNodesQuickNavIterator):
	NodeClass = NPPDocumentHeadingQuickNavItem

	def getSearchPattern(self):
		level = self.levelToFind
		documentType = self.documentType
		if documentType == "markdown":
			if self.reverse:
				pattern = r"[\s\t]#{1,}$" if not level else r"[\s\t]#{%s}$" % level
			else:
				pattern = r"(?<!#)#+[\s\t]" if not level else r"(?<!#)#{%s}[\s\t]" % level
				pattern = r"^#{1,}[\s\t]" if not level else r"^#{%s}[\s\t]" % level
		elif documentType == "txt2tags":
			if self.reverse:
				pattern = r"[\s\t]\+{1,}$" if not level else r"[\s\t]\+{%s}$" % level
			else:
				pattern = r"^\+{1,}[\s\t]" if not level else r"^\+{%s}[\s\t]" % level
		else:
			return None

		return pattern

	def isValid(self, item):
		level = item.level
		levelToFind = self.levelToFind
		if (not self.elementsList and (
			levelToFind and (
			level == 0 or (levelToFind < level or level < levelToFind)))
			or not levelToFind and level == 0) or (self.elementsList and level == 0):
			return False
		return True


class NPPDocumentLinksQuickNavIterator(NPPDocumentNodesQuickNavIterator):
	NodeClass = NPPDocumentLinkQuickNavItem

	def getSearchPattern(self):
		if self.documentType == "markdown":
			# for synthaxe <... >
			pattern1 = r"<[^<>]+>" if not self.reverse else r">{1}[^<>]+<{1}"
			return pattern1
		return None


class NPPDocumentBlockQuotesQuickNavIterator(NPPDocumentNodesQuickNavIterator):
	NodeClass = NPPDocumentBlockQuoteQuickNavItem

	def getSearchPattern(self):
		if self.reverse:
			pattern = r"\s+>(?=\s)+"
		else:
			pattern = r"(?<=\s)+>\s"
		return pattern

	def isValid(self, item):
		level = item.level
		if level == 0:
			return False
		return True


class NPPDocumentLongLinesQuickNavIterator(NPPDocumentNodesQuickNavIterator):
	NodeClass = NPPDocumentLongLineQuickNavItem

	def getSearchPattern(self):
		if self.reverse:
			return r"\s+>(?=\s)+"
		else:
			return r"^^."

	def isValid(self, item):
		info = item.textInfo.copy()
		info.expand(textInfos.UNIT_LINE)
		text = info.text
		if len(text) > _addonConfigManager.getMaxLineLength():
			return True
		return False
