import subprocess
import threading
import time
import os

import sublime
import sublime_plugin

from .scripts import utilities
from .scripts import files


IDLE = 0

RUNNING = 1


class SimpleContextRunScriptCommand(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        flags = \
            files.CREATE_NO_WINDOW if sublime.platform() == "windows" else 0
        self.options = {
            "creationflags": flags,
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
        }
        self.state = IDLE
        self.previous_script = "context --version"

    def reload_settings(self):
        utilities.reload_settings(self)
        if self.context_path and os.path.exists(self.context_path):
            environ = os.environ.copy()
            environ["PATH"] = \
                files.add_path(environ["PATH"], self.context_path)
            self.options["env"] = environ
        else:
            self.options["env"] = os.environ.copy()

    def run(self, user_input=None):
        self.reload_settings()
        self.setup_output_view()
        if self.state == IDLE:
            self.state = RUNNING
            if user_input is not None:
                self.on_done(user_input)
            else:
                self.window.show_input_panel(
                    "Run script:",
                    self.previous_script,
                    self.on_done,
                    self.on_change,
                    self.on_cancel,
                )

    def on_done(self, text):
        self.start_time = time.time()
        view = self.window.active_view()
        variables = self.window.extract_variables()
        if view:
            name = view.file_name()
            path = os.path.dirname(view.file_name()) if name else None
        else:
            path = None
        thread = threading.Thread(
            target=lambda: self.on_done_aux(text, variables, path=path)
        )
        thread.start()

    def on_done_aux(self, text, variables, path=None):
        if path and os.path.exists(path):
            os.chdir(path)

        cmd = sublime.expand_variables(text.split(), variables)
        print('Running: {}'.format(" ".join(cmd)))
        process = subprocess.Popen(cmd, **self.options)
        result = process.communicate()
        output = files.clean_output(files.decode_bytes(result[0]))
        self.show_output()
        self.add_to_output(output)
        self.add_to_output(
            "\n[Finished in {:.1f}s]".format(time.time() - self.start_time)
        )
        self.previous_script = text
        self.state = IDLE

    def on_change(self, text):
        pass

    def on_cancel(self):
        self.state = IDLE

    def show_output(self):
        self.window.run_command(
            "show_panel", {"panel": "output.ConTeXt_script"},
        )

    def add_to_output(self, text):
        self.output_view.run_command("append", {"characters": text})

    def setup_output_view(self):
        if not hasattr(self, "output_view"):
            self.output_view = \
                self.window.create_output_panel("ConTeXt_script")

        self.output_view.settings().set("line_numbers", False)
        self.output_view.settings().set("gutter", False)
        self.output_view.settings().set("spell_check", False)
        self.output_view.settings().set("word_wrap", False)
        self.output_view.settings().set("scroll_past_end", False)
        self.output_view.assign_syntax("Packages/Text/Plain text.tmLanguage")
        self.output_view = self.window.create_output_panel("ConTeXt_script")
        self.show_output()
