import sublime
import time
import os
from . import build_base
from .scripts import scopes
from .scripts import files


class SimpleContextBuildMetapostCommand(
    build_base.SimpleContextBuildBaseCommand
):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("phantom_set_name", "MetaPost")
        kwargs.setdefault("output_panel_name", "MetaPost")
        kwargs.setdefault("output_category_len", 8)
        super().__init__(*args, **kwargs)
        self.set_idle()
        self.reload_settings()

    def set_idle(self):
        self._base_set_idle()

    def reload_settings(self):
        self._base_reload_settings()

    def is_visible(self):
        return scopes.is_metapost(self._base_view)

    def run(self, *args, **kwargs):
        self.reload_settings()
        if "cmd" in kwargs:
            self.command = kwargs.get("cmd")
        else:
            self.command = ["mpost", self._base_input]
        self._base_run(
            [{"command": self.command, "handler": self.handler_main}],
            begin=self.handler_begin,
            end=self.handler_end
        )

    def handler_begin(self):
        self.start_time = time.time()
        self.add_to_output("starting", "running MetaPost...")

    def handler_main(self, text):
        # for i, line in enumerate(text.split("\n")):
        #     self.add_to_output("result", line, gap=not i)
        pass

    def handler_end(self, return_codes):
        stop_time = time.time() - self.start_time
        message = ", ".join([
            "success" if return_codes[0] == 0 else "failure",
            "finished in {:.1f}s".format(stop_time)
        ])
        self.add_to_output("stopping", message, gap=True)

    def add_to_output(self, category, text, gap=False):
        self._base_add_to_output(category, text, gap=gap)


#D Why doesn't this work?
class SimpleContextBuildMetapostAltCommand(
    build_base.SimpleContextBuildBaseCommand
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reload_settings()

    def reload_settings(self):
        self._base_reload_settings()

    def is_visible(self):
        return scopes.is_metapost(self._base_view)

    def run(self, *args, **kwargs):
        self.reload_settings()
        env = os.environ.copy()
        if self._path and os.path.exists(self._path):
            env["PATH"] = files.add_path(env["PATH"], self._path)
        kwargs["env"] = env
        sublime.run_command("exec", kwargs)
