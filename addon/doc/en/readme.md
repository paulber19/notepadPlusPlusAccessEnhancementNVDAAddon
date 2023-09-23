# Notepad++ text editor: accessibility enhancement #
* Author: PaulBer19 (paulber19@laposte.net)
* URL: [https://github.com/paulber19/notepadPlusPlusAccessEnhancementNVDAAddon.git] [3]
* Download:
 * [stable version] [1]
 * [development version] [2]


* Compatibility:
 * Minimum NVDA version required: 2022.1
 * Latest version of NVDA tested: 2023.3


# Features #

This extension aims to improve the accessibility of the Notepad++ text editor and add functionalities to facilitate the editing of files used in Python language and files written in markdown language.

It includes most of the additions made by the NVDA_notepadPlusPlus add-on created by Derek Riemer and Tuukka Ojala, then modified by Robert Hänggi and Andre9642 <https://github.com/derekriemer/nvda-notepadPlusPlus>.

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
* added navigation mode for titles, links, quotes.


For DSpellCheck Notepad++ plugin:

* reporting of spelling errors when moving from line to line


And the others complements:

* Announcement of the number and indentation of each line,
* scripts to set the indentation,
* Focus movement displacement by "home" key,
* Comparison of the selected text with that of the clipboard,
* go to the next line ending with at least one tab or one space,
* format of the announcement of the name of the documents:
	* reduced file path announcement,
	* announcement of the name of the file before its path,
	* no diction of path's backslashs,
	* reporting of spelling errors found by the DSpellCheck add-in (experimental).


# Compatibility #
This extension has been tested with Notepad++ version 8.4 and 8.5.6.



# Constraints #
This extension uses and intercepts the shortcuts of Notepad++ configured by default. It is therefore strongly advised, for its proper functioning, not to modify these shortcuts.



[1]: https://github.com/paulber007/AllMyNVDAAddons/raw/notepadPlusPlusAccessEnhancement/notepadPlusPlusAccessEnhancement/notepadPlusPlusAccessEnhancement-2.5.2.nvda-addon
[2]: https://github.com/paulber007/AllMyNVDAAddons/tree/master/notepadPlusPlusAccessEnhancement/dev
[3]: https://github.com/paulber19/notepadPlusPlusAccessEnhancementNVDAAddon.git
