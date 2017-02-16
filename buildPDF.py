import sublime_plugin
import sublime
import subprocess
import time
import os
import re


def file_with_ext(file, ext):
    return os.path.splitext(os.path.basename(file))[0] + ext


def is_context(view):
    try:
        return view.match_selector(
            view.sel()[0].begin(), "text.tex.context")
    except:
        return False


def prep_environ_path():
    settings = sublime.load_settings("ConTeXtTools.sublime-settings")
    context_path = settings.get("context_executable", {}).get("path")
    if not context_path:
        return
    context_path = os.path.normpath(context_path)
    passes_initial_check = isinstance(context_path, str) \
        and os.path.exists(context_path)
    if passes_initial_check:
        PATH = os.environ["PATH"].split(os.pathsep)
        if context_path not in PATH:
            PATH.insert(0, context_path)
        else:
            PATH.remove(context_path)
            PATH.insert(0, context_path)
        os.environ["PATH"] = os.pathsep.join(PATH)


def parse_log_for_error(file_bytes):
    file_str = file_bytes.decode(encoding="utf-8")
    file_str = file_str.replace("\r\n", "\n").replace("\r", "\n")

    def is_error(line):
        return re.match(
            r"^.*?>\s*(.*?)\s+error\s+on\s+line\s+([0-9]+).*?!\s*(.*?)$",
            line)

    def is_code_snippet(line):
        return re.match(r"^\s*[0-9]+", line)

    def is_blank_line(line):
        return (len(line) == 0 or re.match(r"^\s*$", line))

    start_of_error = 0
    log = file_str.split("\n")
    for i, line in enumerate(log):
        error = is_error(line)
        if error:
            error_summary = "{} error on line {}: {}".format(*error.groups())
            start_of_error = i + 1
            break

    while is_blank_line(log[start_of_error]):
        start_of_error += 1

    cur_line = start_of_error
    while not is_code_snippet(log[cur_line]):
        cur_line += 1
    end_of_error = cur_line

    while is_blank_line(log[end_of_error]):
        end_of_error -= 1

    return "\n\n".join([error_summary] + log[start_of_error:end_of_error - 1])


class ContextBuildPdfCommand(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reload_settings()

    def reload_settings(self):
        self.settings = sublime.load_settings("ConTeXtTools.sublime-settings")
        prep_environ_path()

    def run(self):
        start_time = time.time()
        self.reload_settings()

        active_view = self.window.active_view()
        if not is_context(active_view):
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
            input_base_name = file_with_ext(input_name, "")
            # change dir to the target files dir, so any output is put there
            os.chdir(input_dir)

            # decide what command to invoke, we take advantage of the fact that
            # subprocess will accept a list or a string
            command_line_options = \
                self.settings.get("context_executable", {}).get("options", {})

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
                err_message = parse_log_for_error(result[0])
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
