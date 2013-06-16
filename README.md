# CodeSearch

A plugin for [Sublime Text 3](http://www.sublimetext.com/).

## Synopsis

This plugin makes it possible to use [CodeSearch](https://code.google.com/p/codesearch/) within Sublime Text 3.

CodeSearch is a fast index-based searching tool. 

The plugin allows to index all folders of your project file and, after you created the index, to search for a custom string or regular expression.
It opens a quick selection panel to browse results and highlights matches inside files.

## Installation

* [Package Control](http://wbond.net/sublime_packages/package_control): install package **CodeSearch** (this is the recommended way), or

* Copy the folder into the Packages folder.

## Project Preparation

1. Edit your project file ('Project -> Edit Project') and add the following section:

	"code_search":
	{
		"csearchindex": "csearchindex"
	}

where csearchindex is the path to the desired index file (either absolute or relative to the project file).

2. Index your code by calling the "Code Search Index" command

## Searching

* Use the key binding (`Ctrl+Alt+Shift+S` on Windows), or
* Call the "Code Search" command;
* Enter the search query
* The status bar will show the progress. Most of the time, you should see the results immediate in the quick panel. Switching files opens the transient view and the search string will be highlighted.
* It is possible to cancel a search by just running the "Code Search" command again. In such a case, the current results will be shown.

## Configuration

Configuration is stored in a separate, user-specific `CodeSearch.sublime-settings` file. See the default file for configuration options; links to both can be
found in the main menu in `Preferences -> Package Settings -> Code Search`.

* * *

Based on [Search In Project](https://github.com/leonid-shevtsov/SearchInProject_SublimeText2)