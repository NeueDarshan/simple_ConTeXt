import sublime
import sublime_plugin
import subprocess
import time
import os


import sys
sys.path.insert(1, os.path.abspath(os.path.dirname(__file__)))
from scripts import common


class ContextBuildPdfCommand(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_profile = {}
        self.reload_settings()

    def reload_settings(self):
        self.settings = sublime.load_settings("ConTeXtTools.sublime-settings")
        profile_name = self.settings.get("current_profile")

        for profile in self.settings.get("profiles", {}):
            if profile.get("name") == profile_name:
                self.current_profile = profile
                break

        common.prep_environ_path(self.current_profile)

    def run(self):
        start_time = time.time()
        self.reload_settings()

        active_view = self.window.active_view()
        if not common.is_context(active_view):
            return

        # setup the 'build panel'/'output view'
        #  |-- initialize if needed
        if not hasattr(self, "output_view"):
            self.output_view = self.window.get_output_panel("ConTeXtTools")

        #  |-- define various settings
        self.output_view.settings().set("line_numbers", False)
        self.output_view.settings().set("gutter", False)
        self.output_view.settings().set("scroll_past_end", False)
        self.output_view.assign_syntax(
            "Packages/ConTeXtTools/build results.sublime-syntax")

        #  |-- this is needed to 'refresh' the view
        self.output_view = self.window.get_output_panel("ConTeXtTools")

        #  |-- make the `output_view` visible
        self.window.run_command("show_panel", {"panel": "output.ConTeXtTools"})

        try:
            # identity the file to compile, and its location
            input_dir, input_name = os.path.split(
                active_view.file_name())
            input_base_name = common.file_with_ext(input_name, "")
            # change dir to the target files dir, so any output is put there
            os.chdir(input_dir)

            # decide what command to invoke, we take advantage of the fact that
            # subprocess will accept a list or a string
            command_line_options = self.current_profile.get(
                "context_executable", {}).get("options", {})

            if isinstance(command_line_options, str):
                command = ["context"] + command_line_options.split(" ") \
                    + [input_name]

            elif isinstance(command_line_options, dict):
                command = ["context"]

                if command_line_options.get("result"):
                    output_file_name = sublime.expand_variables(
                        command_line_options["result"],
                        {"name": input_base_name})
                    command.append("--result={name}".format(
                        name=output_file_name))
                    del command_line_options["result"]

                for option, value in command_line_options.items():
                    if isinstance(value, bool) and value:
                        command.append("--{option}".format(option=option))
                    elif isinstance(value, dict):
                        normalized_value = ", ".join(
                            "{opt}={val}".format(opt=k, val=v)
                            for k, v in value.items())
                        command.append("--{option}={value}".format(
                            value=normalized_value, option=option))
                    else:
                        command.append("--{option}={value}".format(
                            value=value, option=option))

                command.append(input_name)

            else:
                command = ["context", input_name]

            # run `context`
            context_process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)

            result = context_process.communicate()
            if context_process.returncode != 0:
                raise Exception()

            # report our success
            elapsed = time.time() - start_time
            characters = "\n\n".join([
                "Success!",
                "[Finished in {time:.1f}s]".format(time=elapsed)])
            self.output_view.run_command("append", {"characters": characters})

        except:
            # report our failure
            #  |-- parse the log for the error message
            try:
                err_message = common.parse_log_for_error(result[0])
            except UnboundLocalError as err:
                err_message = repr(err)
            #  |-- construct a suitable error message
            elapsed = time.time() - start_time
            characters = "\n\n".join([
                "Failure!",
                err_message,
                "[Finished in {time:.1f}s]".format(time=elapsed)])
            #  |-- print that message to the build panel
            self.output_view.run_command("append", {"characters": characters})
