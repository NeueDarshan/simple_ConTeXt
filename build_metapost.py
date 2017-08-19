import time
from . import build_base
from .scripts import utilities


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
        self.command = ["mpost", self._base_input]

    def is_visible(self):
        return utilities.is_metapost(self._base_view)

    def run(self, *args, **kwargs):
        self.reload_settings()
        self._base_run(
            [{"command": self.command, "handler": self.handler_main}],
            begin=self.handler_begin,
            end=self.handler_end
        )

    def handler_begin(self):
        self.start_time = time.time()
        self.add_to_output("starting", "running MetaPost...")

    def handler_end(self, return_codes):
        stop_time = time.time() - self.start_time
        self.add_to_output(
            "stopping",
            "success" if return_codes[0] == 0 else "failure",
            gap=True
        )
        self.add_to_output("stopping", "finished in {:.1f}s".format(stop_time))

    def handler_main(self, text):
        for i, line in enumerate(text.split("\n")):
            self.add_to_output("result", line, gap=not i)

    def add_to_output(self, category, text, gap=False):
        self._base_add_to_output(category, text, gap=gap)
