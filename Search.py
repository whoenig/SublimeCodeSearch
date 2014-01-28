import sublime, sublime_plugin
import subprocess, os
import threading
from queue import Queue

class CodeSearchEvents(sublime_plugin.EventListener):
	LastSearchString = ""
	SearchActive = False

	def on_load_async(self, view):
		if CodeSearchEvents.SearchActive:
			regions = view.find_all(CodeSearchEvents.LastSearchString)
			if len(regions) > 0:
				view.add_regions("code_search", regions, "entity.name.filename.find-in-files", "circle", sublime.DRAW_OUTLINED)
				view.show(regions[0])
				view.set_status("CodeSearchNumRegions", "NumRegions: " + str(len(regions)))
		else:
			view.erase_status("CodeSearchNumRegions")
			view.erase_status("CodeSearch")

class CodeSearchCommand(sublime_plugin.WindowCommand):
	def __init__(self, window):
		sublime_plugin.WindowCommand.__init__(self, window)
		self.searching = False
		self.searchFor = ""
		self.csearchindex = ""
		self.result = []
		self.popen = None
		pass

	def run(self):
		if self.popen:
			self.popen.terminate()
		view = self.window.active_view()
		selectionText = view.substr(view.sel()[0])
		data = self.window.project_data()
		if "code_search" in data:
			if "csearchindex" in data["code_search"]:
				self.csearchindex = os.path.expanduser(data["code_search"]["csearchindex"])
				settings = sublime.load_settings('CodeSearch.sublime-settings')
				self.path_csearch = settings.get("path_csearch")
				self.window.show_input_panel(
					"CodeSearch:",
					selectionText or self.searchFor,
					self.search, None, None)
				return

		sublime.error_message("Please add 'code_search':{ 'csearchindex': '<path-to-the-index-file>'} to your project!")

	def search(self, searchFor):
		print("start search for: " + searchFor + " in " + self.csearchindex)
		self.searching = True
		self.result = []
		self.searchFor = searchFor
		CodeSearchEvents.LastSearchString = searchFor
		CodeSearchEvents.SearchActive = True
		self.updateStatus()
		codeSearchThread = threading.Thread(target=self.runCodeSearch)
		codeSearchThread.start()

	def runCodeSearch(self):
		project_file_name = self.window.project_file_name()
		working_dir = os.path.dirname(project_file_name)
		my_env = os.environ.copy()
		my_env["CSEARCHINDEX"] = self.csearchindex
		commandLine = [self.path_csearch, "-l", self.searchFor]
		try:
			startupinfo = subprocess.STARTUPINFO()
			startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		except:
			startupinfo = None
		self.popen = subprocess.Popen(commandLine, cwd=working_dir, env=my_env, startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdoutQueue = Queue()
		readStdOutThread = threading.Thread(target=self.readStdout, args=(self.popen.stdout, stdoutQueue))
		readStdOutThread.daemon = True
		readStdOutThread.start()
		stderrQueue = Queue()
		readStdErrThread = threading.Thread(target=self.readStderr, args=(self.popen.stderr, stderrQueue))
		readStdErrThread.daemon = True
		readStdErrThread.start()
		self.popen.wait()
		self.popen = None
		self.updateStatus()
		self.searching = False

		self.currentView = self.window.active_view()
		if len(self.result) > 0:
			self.window.show_quick_panel(self.result, self.onDone, 0, 0, self.onHighlighted)
		else:
			self.window.show_quick_panel(["No results"], self.onDoneNoResults)

	def onDone(self, index):
		CodeSearchEvents.SearchActive = False
		if index == -1:
			self.window.focus_view(self.currentView)
			self.currentView.erase_status("CodeSearch")
		else:
			entry = self.result[index]
			fileName = os.path.join(entry[1], entry[0])
			view = self.window.open_file(fileName)

	def onDoneNoResults(self, index):
		CodeSearchEvents.SearchActive = False
		self.currentView.erase_status("CodeSearch")

	def onHighlighted(self, index):
		if index != -1:
			entry = self.result[index]
			fileName = os.path.join(entry[1], entry[0])
			view = self.window.open_file(fileName, sublime.TRANSIENT)
			view.set_status("CodeSearch", "CodeSearch for " + self.searchFor + " found: " + str(len(self.result)) + " files")
		else:
			self.window.focus_view(self.currentView)


	def readStdout(self, out, queue):
		for line in iter(out.readline, b''):
			path = line.decode('utf-8').strip()
			(directory, fileName) = os.path.split(path)
			self.result.append([fileName, directory])
		out.close()

	def readStderr(self, out, queue):
		for line in iter(out.readline, b''):
			error = line.decode('utf-8').strip()
			print("CodeSearch Error: " + error)
		out.close()

	def updateStatus(self):
		if self.searching:
			self.window.active_view().set_status("CodeSearch", "CodeSearch for " + self.searchFor + " found: " + str(len(self.result)) + " files")
			sublime.set_timeout(self.updateStatus, 2000)

