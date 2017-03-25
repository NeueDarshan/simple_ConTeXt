import sublime
import sublime_plugin
import subprocess
import time
import os


import sys
sys.path.insert(1, os.path.abspath(os.path.dirname(__file__)))
from scripts import common


def process_options(name, options, input_, input_base):
    if isinstance(options, str):
        command = [name] + options.split(" ") + [input_]

    elif isinstance(options, dict):
        command = [name]

        if options.get("result"):
            output_file_name = sublime.expand_variables(
                options["result"], {"name": input_base})
            command.append("--result={}".format(output_file_name))
            del options["result"]

        for option, value in options.items():
            if isinstance(value, bool):
                if value:
                    command.append("--{}".format(option))
            elif isinstance(value, dict):
                normalized_value = " ".join(
                    "{}={}".format(k, v) for k, v in value.items())
                command.append("--{}={}".format(option, normalized_value))
            else:
                if option == "script":
                    command.insert(1, "--{}".format(option))
                    command.insert(2, "{}".format(value))
                else:
                    command.append("--{}={}".format(option, value))

        command.append(input_)

    else:
        command = [name, input_]

    return command


class ContextBuildPdfCommand(sublime_plugin.WindowCommand):
    def reload_settings(self):
        common.reload_settings(self)
        common.prep_environ_path(
            self.current_profile.get("context_program", {}).get("path"))

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

        input_dir, input_name = os.path.split(active_view.file_name())
        input_base_name = common.file_with_ext(input_name, "")
        os.chdir(input_dir)

        context_program = self.current_profile.get("context_program", {})
        command_name = context_program.get("name", "context")
        command_line_options = context_program.get("options", {})
        command = process_options(
            command_name, command_line_options, input_name, input_base_name)

        chars = "running command: '{}'\n\n".format(" ".join(command))
        self.output_view.run_command("append", {"characters": chars})
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

        # try:
        #     err_message = common.parse_log_for_error(result[0])
        # except UnboundLocalError as err:
        #     err_message = repr(err)
        # elapsed = time.time() - start_time
        # characters = "\n\n".join([
        #     "Failure!",
        #     err_message,
        #     "[Finished in {time:.1f}s]".format(time=elapsed)])
        # self.output_view.run_command("append", {"characters": characters})
