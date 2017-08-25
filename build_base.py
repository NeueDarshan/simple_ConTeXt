import sublime
import sublime_plugin
import subprocess
import threading
import os
from .scripts import utilities


CREATE_NO_WINDOW = 0x08000000


class SimpleContextBuildBaseCommand(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        self._base_kwargs = kwargs
        self._base_phantom_set_name = \
            self._base_set_init_default("phantom_set_name", "simple_ConTeXt")
        self._base_output_panel_name = \
            self._base_set_init_default("output_panel_name", "simple_ConTeXt")
        output_category_len = \
            self._base_set_init_default("output_category_len", 10)

        super().__init__(*args, **self._base_kwargs)
        self._base_output_settings = {
            "category_length": output_category_len,
            "output_cache": "",
            "has_output": False,
        }
        self._base_output_settings["template"] = \
            "{:%d} > {}" % self._base_output_settings["category_length"]

        self._base_set_idle()
        self._base_lock = threading.Lock()

    def _base_set_init_default(self, key, default):
        if key in self._base_kwargs:
            copy = self._base_kwargs[key]
            del self._base_kwargs[key]
            return copy
        else:
            return default

    def _base_reload_settings(self):
        utilities.reload_settings(self)

        self._base_window = self.window
        self._base_view = self._base_window.active_view()
        self._base_phantom_set = \
            sublime.PhantomSet(self._base_view, self._base_phantom_set_name)

        try:
            file_name = self._base_view.file_name()
            if file_name:
                self._base_dir, self._base_input = os.path.split(file_name)
                self._base_file = utilities.base_file(self._base_input)
        except AttributeError:
            self._base_dir, self._base_input = None, None

        self._base_flags = \
            CREATE_NO_WINDOW if sublime.platform() == "windows" else 0
        self._base_command_options = {
            "creationflags": self._base_flags,
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT
        }
        if self._path and os.path.exists(self._path):
            environ = os.environ.copy()
            environ["PATH"] = utilities.add_path(environ["PATH"], self._path)
            self._base_command_options["env"] = environ
        else:
            self._base_command_options["env"] = os.environ

    def _base_run(self, commands, begin=None, end=None):
        if self._base_is_idle():
            self._base_set_running()
            self._base_setup_output_view()
            self._base_run_start(commands, begin=begin, end=end)
        elif self._base_is_running():
            self._base_set_stopping()
            self._base_run_stop()
        elif self._base_is_stopping():
            pass

    def _base_is_idle(self):
        return self._base_state == 0

    def _base_set_idle(self):
        self._base_state = 0

    def _base_is_running(self):
        return self._base_state == 1

    def _base_set_running(self):
        self._base_state = 1

    def _base_is_stopping(self):
        return self._base_state == 2

    def _base_set_stopping(self):
        self._base_state = 2

    def _base_run_start(self, commands, begin=None, end=None):
        self._base_return_codes = [None] * len(commands)
        thread = threading.Thread(
            target=lambda: self._base_run_start_aux(
                commands, begin=begin, end=end
            )
        )
        thread.start()

    def _base_run_start_aux(self, commands, begin=None, end=None):
        if begin:
            begin()
        for index, command in enumerate(commands):
            if self._base_is_stopping():
                break
            else:
                self._base_run_start_aux_i(index, command)
        if end:
            end(self._base_return_codes)
        self._base_reset_output()
        self._base_set_idle()

    def _base_run_start_aux_i(self, index, command):
        self._base_lock.acquire()
        runner, handler = command["command"], command["handler"]
        os.chdir(self._base_dir)
        self._base_process = \
            subprocess.Popen(runner, **self._base_command_options)
        self._base_lock.release()

        result = self._base_process.communicate()
        self._base_return_codes[index] = self._base_process.returncode

        self._base_lock.acquire()
        if not self._base_is_stopping():
            handler(utilities.bytes_decode(result[0]))
        self._base_lock.release()

    def _base_run_stop(self):
        self._base_add_to_output(
            "stopping", "got request to stop builder", gap=True
        )
        try:
            if sublime.platform() == "windows":
                kill = [
                    "taskkill", "/t", "/f", "/pid", str(self._base_process.pid)
                ]
                subprocess.call(kill, creationflags=self._base_flags)
            else:
                self._base_process.kill()
        except Exception as e:
            chars = 'encountered error "{}" while attempting to stop builder'
            self._base_add_to_output("stopping", chars.format(e))

    def _base_update_phantoms(self, list_):
        self._base_phantom_set.update(list_)

    def _base_hide_phantoms(self):
        if hasattr(self, "_base_view"):
            self._base_view.erase_phantoms(self._base_phantom_set_name)

    def _base_add_to_output(self, category, text, gap=False):
        if self._options.get("compact_output"):
            gap = False
        chars = (
            self._base_output_settings["output_cache"] +
            (
                "\n" if self._base_output_settings["has_output"] and gap
                else ""
            ) +
            self._base_output_settings["template"].format(category, text)
        )
        self._base_output_view.run_command("append", {"characters": chars})
        self._base_output_settings["output_cache"] = "\n"
        self._base_output_settings["has_output"] = True

    def _base_reset_output(self):
        self._base_output_settings["output_cache"] = ""
        self._base_output_settings["has_output"] = False

    def _base_setup_output_view(self):
        if not hasattr(self, "_base_output_view"):
            self._base_output_view = self._base_window.create_output_panel(
                self._base_output_panel_name
            )

        self._base_output_view.settings().set("line_numbers", False)
        self._base_output_view.settings().set("gutter", False)
        self._base_output_view.settings().set("spell_check", False)
        self._base_output_view.settings().set("word_wrap", False)
        self._base_output_view.settings().set("scroll_past_end", False)
        self._base_output_view.assign_syntax(
            "Packages/simple_ConTeXt/build results.sublime-syntax"
        )
        self._base_output_view = self._base_window.create_output_panel(
            self._base_output_panel_name
        )
        self._base_window.run_command(
            "show_panel",
            {"panel": "output.{}".format(self._base_output_panel_name)}
        )
