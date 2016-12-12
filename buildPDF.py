import sublime_plugin
import subprocess
import time
import os
import re


def is_context(view):
    try:
        return view.match_selector(
            view.sel()[0].begin(), "text.tex.context")
    except:
        return False


def file_with_ext(file, ext):
    return os.path.splitext(os.path.basename(file))[0] + ext


def parse_log_for_error(file_str):
    def is_error(line):
        return re.match(
            r"^.*?>\s*(.*?) error\s+on\s+line\s+([0-9]+).*?! (.*?)$",
            line
        )

    def is_code_snippet(line):
        return re.match(r"^\s*[0-9]+", line)

    def is_blank_line(line):
        return (len(line) == 0 or re.match(r"^\s*$", line))

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

    return "\n".join([error_summary, ""] + log[start_of_error:end_of_error-1])


class ContextBuildPdfCommand(sublime_plugin.WindowCommand):

    # def __init__(self, *args, **kwargs):
    #     sublime_plugin.WindowCommand.__init__(self, *args, **kwargs)

    def run(self):
        start_time = time.time()

        active_view = self.window.active_view()

        if not is_context(active_view):
            return

        # setup the 'build panel'/'output view'
        #  |-- initialize if needed
        if not hasattr(self, "output_view"):
            self.output_view = self.window.get_output_panel("contexttools")

        #  |-- define various settings
        self.output_view.settings().set("line_numbers", False)
        self.output_view.settings().set("gutter", False)
        self.output_view.settings().set("scroll_past_end", False)
        self.output_view.assign_syntax(
            "Packages/ConTeXtTools/build results.sublime-syntax")

        #  |-- this is needed to 'refresh' the view
        self.output_view = self.window.get_output_panel("contexttools")

        #  |-- make the `output_view` visible
        self.window.run_command("show_panel", {"panel": "output.contexttools"})

        try:
            # identity the file to compile, and its location
            input_file_dir, input_file_name = os.path.split(
                active_view.file_name())
            # change dir to the target files dir, so any output is put there
            os.chdir(input_file_dir)
            # decide on the output name
          # output_file_name = file_with_ext(input_file_name, ".pdf")

            # run `context` on the input file
            context_process = subprocess.Popen(
                [
                    "context",
                    "--run",
                    input_file_name,
                  # "--autogenerate",
                  # "--result={}".format(output_file_name),
                    "--synctex=1",
                  # "--noconsole=1",
                    "--interface=en",
                    "--jit",
                  # "--autopdf",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )

            out, _ = context_process.communicate()
            if context_process.returncode != 0:
                raise Exception()

            # report our success
            elapsed = time.time() - start_time
            characters = "Success!\n\nFinished in {:.1f}s".format(elapsed)
            self.output_view.run_command(
                "append",
                {
                    "characters": characters,
                  # "force": True,
                }
            )

        except Exception as e:
            # report our failure
            #  |-- parse the log for the error message
            err_message = parse_log_for_error(out)
            #  |-- construct a suitable error message
            characters = "Failure!\n\n{}".format(err_message)
            #  |-- print that message to the build panel
            self.output_view.run_command(
                "append",
                {
                    "characters": characters,
                  # "force": True,
                }
            )
