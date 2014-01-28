import sublime, sublime_plugin
import subprocess, os
import threading
from queue import Queue

class CodeSearchIndexCommand(sublime_plugin.WindowCommand):
	def __init__(self, window):
		sublime_plugin.WindowCommand.__init__(self, window)
		self.path_cindex = None
		self.indexing = False

	def run(self):
		data = self.window.project_data()
		self.folders = []
		for folder in data["folders"]:
			self.folders.append(os.path.expanduser(folder["path"]))

		if "code_search" in data:
			if "csearchindex" in data["code_search"]:
				self.csearchindex = os.path.expanduser(data["code_search"]["csearchindex"])
				settings = sublime.load_settings('CodeSearch.sublime-settings')
				self.path_cindex = settings.get("path_cindex")
				indexThread = threading.Thread(target=self.runIndexing)
				indexThread.start()
				return

		sublime.error_message("Please add 'code_search':{ 'csearchindex': '<path-to-the-index-file>'} to your project!")

	def runIndexing(self):
		csearchdir = os.path.abspath(os.path.dirname(self.csearchindex))
		if not os.path.isdir(csearchdir):
			os.makedirs(csearchdir)
		self.indexing = True
		project_file_name = self.window.project_file_name()
		working_dir = os.path.dirname(project_file_name)

		self.total_files = 0
		self.num_files = 0
		for folder in self.folders:
			dir = os.path.join(working_dir, folder)
			self.total_files += self.getNumberOfFiles(dir)

		self.updateStatus()

		my_env = os.environ.copy()
		my_env["CSEARCHINDEX"] = self.csearchindex
		commandLine = [self.path_cindex, "-verbose"]
		try:
			startupinfo = subprocess.STARTUPINFO()
			startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		except:
			startupinfo = None
		self.popen = subprocess.Popen(commandLine + self.folders, cwd=working_dir, env=my_env, startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
		self.indexing = False
		self.window.active_view().erase_status("CodeSearch")

	def getNumberOfFiles(self, folder):
		numberOfFiles = 0
		for root, dirs, files in os.walk(folder):
			numberOfFiles += len(files)
		return numberOfFiles

	def readStdout(self, out, queue):
		# stdout doesn't seem to be used
		# even the verbose output goes to stderr
		for line in iter(out.readline, b''):
			pass
		out.close()

	def readStderr(self, out, queue):
		self.num_files = 0
		for line in iter(out.readline, b''):
			self.num_files += 1
		out.close()

	def updateStatus(self):
		if self.indexing:
			percent = 100.0
			if self.total_files > 0:
				percent = self.num_files / self.total_files * 100
			self.window.active_view().set_status(
				"CodeSearch",
				"CodeSearch indexing {} of {} files ({} %)". format(self.num_files, self.total_files, int(percent)))
			sublime.set_timeout(self.updateStatus, 2000)
