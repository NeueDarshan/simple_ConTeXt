import sublime
import sublime_plugin
import subprocess
import time
import os


import sys
sys.path.insert(1, os.path.abspath(os.path.dirname(__file__)))
from scripts import common


class ContextBuildPdfCommand(sublime_plugin.WindowCommand):
    def reload_settings(self):
        common.reload_settings(self)

    def run(self):
        start_time = time.time()
        self.reload_settings()

        active_view = self.window.active_view()
        if not common.is_context(active_view):
            return

        if not hasattr(self, "output_view"):
            self.output_view = self.window.get_output_panel("ConTeXtTools")
        self.output_view.settings().set("line_numbers", False)
        self.output_view.settings().set("gutter", False)
        self.output_view.settings().set("scroll_past_end", False)
        self.output_view.assign_syntax(
            "Packages/ConTeXtTools/build results.sublime-syntax")
        self.output_view = self.window.get_output_panel("ConTeXtTools")
        self.window.run_command("show_panel", {"panel": "output.ConTeXtTools"})

        dir_, input_ = os.path.split(active_view.file_name())
        base = common.file_with_ext(input_, "")
        os.chdir(dir_)

        context = self.current_profile.get("context_program", {})
        command = context.get("name", "context")
        options = context.get("options", {})
        command = common.process_options(command, options, input_, base)

        chars = "running command: '{}'\n\n".format(" ".join(command))
        self.output_view.run_command("append", {"characters": chars})

        path = self.current_profile.get("context_program", {}).get("path")
        with common.ModPath(path):
            context_process = subprocess.Popen(
                command,
                **{
                    "std" + opt: subprocess.PIPE
                    for opt in ["in", "out", "err"]
                }
            )

            context_process.communicate()
            elapsed = time.time() - start_time

            if context_process.returncode != 0:
                self.output_view.run_command("append", {"characters": "error"})
            else:
                chars = "\n\n".join(
                    ["Success!", "[Finished in {:.1f}s]".format(elapsed)])
                self.output_view.run_command("append", {"characters": chars})
