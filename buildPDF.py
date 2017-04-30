import sublime
import sublime_plugin
import subprocess
import time
import os


PACKAGE = os.path.abspath(
    # os.path.join(sublime.packages_path(), "ConTeXtTools")
    os.path.dirname(__file__)
)


import sys
sys.path.insert(1, PACKAGE)
from scripts import common


class ContextBuildPdfCommand(sublime_plugin.WindowCommand):
    def reload_settings(self):
        common.reload_settings(self)

    def run(self):
        start_time = time.time()
        self.reload_settings()

        view = self.window.active_view()
        if not common.is_context(view):
            return

        if not hasattr(self, "output_view"):
            self.output_view = self.window.get_output_panel("ConTeXtTools")

        self.output_view.settings().set("line_numbers", False)
        self.output_view.settings().set("gutter", False)
        self.output_view.settings().set("scroll_past_end", False)
        self.output_view.assign_syntax(
            "Packages/ConTeXtTools/build results.sublime-syntax"
        )
        self.output_view = self.window.get_output_panel("ConTeXtTools")
        self.window.run_command("show_panel", {"panel": "output.ConTeXtTools"})

        dir_, input_ = os.path.split(view.file_name())
        base = common.file_with_ext(input_, "")
        os.chdir(dir_)

        general = self.current_profile.get("context_program", {})
        command = common.process_options(
            general.get("name", "context"),
            general.get("options", {}),
            input_,
            base
        )
        chars = "running command: '{}'\n\n".format(" ".join(command))
        self.output_view.run_command("append", {"characters": chars})

        with common.ModPath(general.get("path")):
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            process.communicate()
            elapsed = time.time() - start_time

            if process.returncode != 0:
                self.output_view.run_command("append", {"characters": "error"})
            else:
                chars = "\n\n".join(
                    ["Success!", "[Finished in {:.1f}s]".format(elapsed)]
                )
                self.output_view.run_command("append", {"characters": chars})
