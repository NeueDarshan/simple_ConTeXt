import sublime
import sublime_plugin
import subprocess
import threading
import time
import os


PACKAGE = os.path.abspath(
    # os.path.join(sublime.packages_path(), "ConTeXtTools")
    os.path.dirname(__file__)
)


import sys
sys.path.insert(1, PACKAGE)
from scripts import common


CREATE_NO_WINDOW = 0x08000000


class ContextBuildPdfCommand(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock = threading.Lock()
        self.state = 0
        self.cancel = False
        self.process = None

    def reload_settings(self):
        common.reload_settings(self)

    def run(self):
        if self.state == 0:
            self.start_run()
        else:
            self.stop_run()

    def stop_run(self):
        stop = "\nstopping > got request to stop complication\n"
        self.output_view.run_command("append", {"characters": stop})

        if self.state == 1:
            self.cancel = True
        elif self.state == 2:
            try:
                if sublime.platform() == "windows":
                    kill = \
                        ["taskkill", "/t", "/f", "/pid", str(self.process.pid)]
                    subprocess.call(kill, creationflags=CREATE_NO_WINDOW)
                else:
                    self.process.kill()
            except Exception as e:
                chars = (
                    'stopping > encountered error "{}" while attempting to '
                    'stop compilation\n'
                ).format(e)
                self.output_view.run_command("append", {"characters": chars})

    def start_run(self):
        self.state = 1
        self.start_time = time.time()

        self.reload_settings()
        view = self.window.active_view()
        if not common.is_context(view):
            return

        if view.is_dirty():
            view.run_command("save")

        self.setup_output_view()

        dir_, input_ = os.path.split(view.file_name())
        base = common.file_with_ext(input_, "")
        os.chdir(dir_)

        program = self.settings.get("program", {})
        path = program.get("path")
        if path in self.program_paths:
            path = self.program_paths[path]

        self.command = common.process_options(
            program.get("name", "context"),
            program.get("options", {}),
            input_,
            base
        )

        chars = ""
        if self.settings.get("builder", {}).get("show_path"):
            chars += 'starting > using $PATH "{}"'.format(program.get("path"))
            if path != program.get("path"):
                chars += ' (i.e. "{}")'.format(path)
            chars += "\n"
        chars += 'starting > running "context"'
        if self.settings.get("builder", {}).get("show_full_command"):
            chars += ' (full command "{}")'.format(" ".join(self.command))
        chars += "\n"
        self.output_view.run_command("append", {"characters": chars})

        thread = threading.Thread(target=lambda: self._run(path))
        thread.start()

    def _run(self, path):
        self.lock.acquire()
        if self.cancel:
            self.state = 0
            self.cancel = False
            return

        self.state = 2
        flags = CREATE_NO_WINDOW if sublime.platform() == "windows" else 0

        with common.ModPath(path):
            self.process = subprocess.Popen(
                self.command,
                creationflags=flags,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.lock.release()

        result = self.process.communicate()
        elapsed = time.time() - self.start_time
        log = common.parse_log(result[0])
        builder = self.settings.get("builder", {})
        chars = ""

        if builder.get("show_warnings"):
            for d in log["warnings"]:
                chars += "\nwarning  > {type} > {message}".format(**d)

        if builder.get("show_errors"):
            for e in log["errors"]:
                if e["line"] and e["details"]:
                    chars += (
                        "\nerror    > {error} > line {line}: {details}"
                        .format(**e)
                    )
                elif e["details"]:
                    chars += "\nerror    > {error} > {details}".format(**e)
                elif e["line"]:
                    chars += "\nerror    > {error} > line {line}".format(**e)
                else:
                    chars += "\nerror    > {error} >".format(**e)

        if len(chars) > 0:
            chars += "\n"
        if self.process.returncode == 0:
            if builder.get("show_pages") and log.get("pages"):
                chars += (
                    "\nsuccess  > shipped {} page{}"
                    .format(log["pages"], "" if log["pages"] == 1 else "s")
                )
            chars += "\nsuccess  > finished in {:.1f}s".format(elapsed)
        else:
            chars += "\nfailure  > finished in {:.1f}s".format(elapsed)

        self.output_view.run_command("append", {"characters": chars})
        self.process = None
        self.state = 0

    def setup_output_view(self):
        if not hasattr(self, "output_view"):
            self.output_view = self.window.get_output_panel("ConTeXtTools")

        self.output_view.settings().set("line_numbers", False)
        self.output_view.settings().set("gutter", False)
        self.output_view.settings().set("spell_check", False)
        self.output_view.settings().set("scroll_past_end", False)
        self.output_view.assign_syntax(
            "Packages/ConTeXtTools/build results.sublime-syntax"
        )
        self.output_view = self.window.get_output_panel("ConTeXtTools")
        self.window.run_command("show_panel", {"panel": "output.ConTeXtTools"})
