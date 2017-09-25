import sublime
import time
import os
from . import build_base
from .scripts import scopes
from .scripts import files


class SimpleContextBuildLuaCommand(
    build_base.SimpleContextBuildBaseCommand
):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("phantom_set_name", "LuaTeX")
        kwargs.setdefault("output_panel_name", "LuaTeX")
        kwargs.setdefault("output_category_len", 8)
        super().__init__(*args, **kwargs)
        self.set_idle()
        self.reload_settings()

    def set_idle(self):
        self._base_set_idle()

    def reload_settings(self):
        self._base_reload_settings()

    def is_visible(self):
        return scopes.is_lua(self._base_view)

    def run(self, *args, **kwargs):
        self.reload_settings()
        if "cmd" in kwargs:
            self.command = kwargs.get("cmd")
        else:
            self.command = ["texlua", self._base_input]
        raw = kwargs.get("output", "fancy") == "raw"
        if raw:
            begin = self.handler_begin_raw
            main = self.handler_main_raw
            end = self.handler_end_raw
        else:
            begin = self.handler_begin
            main = self.handler_main
            end = self.handler_end
        self._base_run(
            [{"command": self.command, "handler": main}],
            begin=begin,
            end=end,
            syntax=not raw
        )

    def handler_begin(self):
        self.start_time = time.time()
        self.add_to_output("starting", "running Lua...")

    def handler_main(self, text):
        if text.strip():
            for i, line in enumerate(text.split("\n")):
                self.add_to_output("result", line, gap=not i)

    def handler_end(self, return_codes):
        stop_time = time.time() - self.start_time
        message = ", ".join([
            "success" if return_codes[0] == 0 else "failure",
            "finished in {:.1f}s".format(stop_time)
        ])
        self.add_to_output("stopping", message, gap=True)

    def handler_begin_raw(self):
        self.start_time = time.time()

    def handler_main_raw(self, text):
        self.raw_add_to_output(text)

    def handler_end_raw(self, return_codes):
        stop_time = time.time() - self.start_time
        if return_codes[0] == 0:
            message = "\n[Finished in {:.1f}s]".format(stop_time)
        else:
            message = "\n[Finished in {:.1f}s with exit code {}]".format(
                stop_time, return_codes[0]
            )
        self.raw_add_to_output(message)

    def add_to_output(self, category, text, gap=False):
        self._base_add_to_output(category, text, gap=gap)

    def raw_add_to_output(self, text):
        self._base_add_to_output_raw(text)


#D Why doesn't this work?
class SimpleContextBuildLuaAltCommand(
    build_base.SimpleContextBuildBaseCommand
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reload_settings()

    def reload_settings(self):
        self._base_reload_settings()

    def is_visible(self):
        return scopes.is_lua(self._base_view)

    def run(self, *args, **kwargs):
        self.reload_settings()
        env = os.environ.copy()
        if self._path and os.path.exists(self._path):
            env["PATH"] = files.add_path(env["PATH"], self._path)
        kwargs["env"] = env
        sublime.run_command("exec", kwargs)
