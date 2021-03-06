import os
import subprocess
import threading
import time

from typing import Optional

# import sublime
import sublime_plugin

from .scripts import files
from .scripts import utilities


IDLE = 0

RUNNING = 1


class SimpleContextRunScriptCommand(
    utilities.BaseSettings, sublime_plugin.WindowCommand,
):
    state = IDLE
    previous_script = "mtxrun --autogenerate --script context --version"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.options = {
            "creationflags": self.flags,
            "shell": self.shell,
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
        }

    def reload_settings(self) -> None:
        super().reload_settings()
        self.options["env"] = utilities.get_path_var(self)

    def run(self, user_input: Optional[str] = None) -> None:
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

    def on_done(self, text: str) -> None:
        self.start_time = time.time()
        view = self.window.active_view()
        if view:
            name = view.file_name()
            path = os.path.dirname(view.file_name()) if name else None
        else:
            path = None
        threading.Thread(
            target=lambda: self.on_done_aux(text, path=path)
        ).start()

    def on_done_aux(self, text: str, path: Optional[str] = None) -> None:
        if path and os.path.exists(path):
            os.chdir(path)

        cmd = self.expand_variables(text.split())
        print("[simple_ConTeXt] Running: {}".format(" ".join(cmd)))
        process = subprocess.Popen(cmd, **self.options)
        try:
            result = process.communicate(
                timeout=self.get_setting("script/timeout")
            )
        except subprocess.TimeoutExpired:
            result = None
        if result:
            output = files.clean_output(files.decode_bytes(result[0]))
            self.add_to_output(output)
        self.show_output()
        self.add_to_output(
            "\n[Finished in {:.1f}s]".format(time.time() - self.start_time)
        )
        self.previous_script = text
        self.state = IDLE

    def on_change(self, text: str) -> None:
        pass

    def on_cancel(self) -> None:
        self.state = IDLE

    def show_output(self) -> None:
        self.window.run_command(
            "show_panel", {"panel": "output.ConTeXt_script"},
        )

    def add_to_output(self, text: str) -> None:
        self.output_view.run_command("append", {"characters": text})

    def setup_output_view(self) -> None:
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
