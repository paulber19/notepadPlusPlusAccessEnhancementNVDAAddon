# shared\npp_NVDAStrings.py
# a part of notepadPlusPlusAccessEnhancement add-on
# Author: paulber19
# Copyright 2020-2021 paulber19
# This file is covered by the GNU General Public License.


def NVDAString(s):
	""" A simple function to bypass the addon translation system,
	so it can take advantage from the NVDA translations directly.
	Based on implementation made by Alberto Buffolino
	https://github.com/nvaccess/nvda/issues/4652 """
	return _(s)
