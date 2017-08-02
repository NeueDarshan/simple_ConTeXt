import sublime
import sublime_plugin
import subprocess
import threading
import time
import os
from .scripts import utilities


IDLE = 0

INITIALISING = 1

STARTED = 2

CREATE_NO_WINDOW = 0x08000000


class SimpleContextBuildMetapost(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock = threading.Lock()
        self.state = IDLE
        self.cancel = False
        self.process = None

    def reload_settings(self):
        utilities.reload_settings(self)
        self.flags = CREATE_NO_WINDOW if sublime.platform() == "windows" else 0
        self.view = self.window.active_view()
        self.dir, self.input = os.path.split(self.view.file_name())
        self.command = [self.cmd, self.input]
        self.has_output = False
        self.output_cache = ""

    def is_visible(self):
        return utilities.is_metapost(self.view)

    def run(self, cmd="mpost"):
        self.cmd = cmd
        if self.state == IDLE:
            self.start_run()
        else:
            self.stop_run()

    def stop_run(self):
        self.add_to_output("stopping > got request to stop builder", gap=True)

        if self.state == INITIALISING:
            self.cancel = True
        elif self.state == STARTED:
            try:
                if sublime.platform() == "windows":
                    kill = \
                        ["taskkill", "/t", "/f", "/pid", str(self.process.pid)]
                    subprocess.call(kill, creationflags=CREATE_NO_WINDOW)
                else:
                    self.process.kill()
            except Exception as e:
                chars = (
                    'stopping > encountered error "{}" while attempting to '
                    'stop builder'
                ).format(e)
                self.add_to_output(chars)

    def start_run(self):
        self.state = INITIALISING
        self.start_time = time.time()

        self.reload_settings()
        if self.view.is_dirty():
            self.view.run_command("save")
        self.setup_output_view()

        name = self._settings.get("path")
        chars = 'details  > using PATH "{}"'.format(name)
        if self._path != name:
            chars += ' (i.e. "{}")'.format(self._path)
        self.add_to_output(chars)

        thread = threading.Thread(target=lambda: self.run_aux(self._path))
        thread.start()

    def run_aux(self, path):
        self.lock.acquire()
        if self.cancel:
            self.state = IDLE
            self.cancel = False
            self.lock.release()
            return

        opts = {
            "creationflags": self.flags,
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE
        }
        if path:
            orig_path = os.environ["PATH"]
            os.environ["PATH"] = utilities.add_path(orig_path, path)
            opts["env"] = os.environ.copy()
            os.environ["PATH"] = orig_path

        os.chdir(self.dir)
        self.state = STARTED
        self.process = subprocess.Popen(self.command, **opts)
        self.lock.release()

        self.result = self.process.communicate()
        self.elapsed = time.time() - self.start_time
        self.add_result_to_output()
        self.process = None
        self.cancel = False
        self.state = IDLE

    def add_result_to_output(self):
        s = self.result[0].decode(encoding="utf-8", errors="replace").replace(
            "\r\n", "\n").replace("\r", "\n").strip()
        for i, line in enumerate(s.split("\n")):
            self.add_to_output("result   > {}".format(line), gap=not i)

    def add_to_output(self, s, gap=False):
        chars = \
            self.output_cache + ("\n" if self.has_output and gap else "") + s
        self.output_view.run_command("append", {"characters": chars})
        self.output_cache = "\n"
        self.has_output = True

    def setup_output_view(self):
        if not hasattr(self, "output_view"):
            self.output_view = \
                self.window.create_output_panel("simple_ConTeXt_MetaPost")

        self.output_view.settings().set("line_numbers", False)
        self.output_view.settings().set("gutter", False)
        self.output_view.settings().set("spell_check", False)
        self.output_view.settings().set("scroll_past_end", False)
        self.output_view.settings().set("word_wrap", False)
        self.output_view.assign_syntax(
            "Packages/simple_ConTeXt/build results.sublime-syntax"
        )
        self.output_view = self.window.create_output_panel(
            "simple_ConTeXt_MetaPost"
        )
        self.window.run_command(
            "show_panel", {"panel": "output.simple_ConTeXt_MetaPost"}
        )
