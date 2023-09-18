# appModules\notepad++\npp_scriptDesc.py
# A part of the notepadPlusPlusAccessEnhancement add-on
# Copyright (C) 2023 paulber19
# This file is covered by the GNU General Public License.


# script prefix
PRE_Line = _("Line")
PRE_Document = _("Document")
PRE_Python = _("Python")
PRE_Markdown = _("Markdown")


def makeDesc(pre, description):
	return "%s: %s" % (pre, description)
