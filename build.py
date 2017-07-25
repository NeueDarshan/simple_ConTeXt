import sublime
import sublime_plugin
import subprocess
import threading
import time
import html
import os
from .scripts import utilities
from .scripts import parse_log


IDLE = 0
CHK_INITIALISING = 1
CHK_STARTED = 2
BLD_STARTED = 3

CREATE_NO_WINDOW = 0x08000000

TEMPLATE = """
<html>
    <style>
        div.hook {{
            border-left: 0.5rem solid
                color(var(--redish) blend(var(--background) 30%));
            border-top: 0.4rem solid transparent;
            height: 0;
            width: 0;
        }}
        div.error {{
            background-color:
                color(var(--redish) blend(var(--background) 30%));
            border-radius: 0 0.2rem 0.2rem 0.2rem;
            margin: 0 0 0.2rem;
            padding: 0.4rem 0 0.4rem 0.7rem;
        }}
        div.error span.message {{
            padding-right: 0.7rem;
        }}
        div.error a {{
            text-decoration: inherit;
            border-radius: 0 0.2rem 0.2rem 0;
            bottom: 0.05rem;
            font-weight: bold;
            padding: 0.35rem 0.7rem 0.45rem 0.8rem;
            position: relative;
        }}
        html.light div.error a {{
            background-color: #ffffff18;
        }}
        html.dark div.error a {{
            background-color: #00000018;
        }}
    </style>
    <body id="simple-ConTeXt-phantom-error">
        <div class="hook"></div>
        <div class="error">
            <span class="message">{message}</span>
            <a href="hide">×</a>
        </div>
    </body>
</html>
"""


class SimpleContextBuildCommand(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock = threading.Lock()
        self.state = IDLE
        self.cancel = False
        self.process = None
        self.base = ""

    def is_visible(self):
        return utilities.is_context(self.view)

    def reload_settings(self):
        utilities.reload_settings(self)
        self.view = self.window.active_view()
        self._phantom_set = sublime.PhantomSet(self.view, "simple_context")
        self._dir, self._input = os.path.split(self.view.file_name())
        self._base = utilities.base_file(self._input)
        self._builder = self.settings.get("builder", {})
        self._program = self._builder.get("program", {})
        self._check = self._builder.get("check", {})
        self._flags = \
            CREATE_NO_WINDOW if sublime.platform() == "windows" else 0
        self._name = self._program.get("name", "context")
        self._command = utilities.process_options(
            self._name,
            self._program.get("options", {}),
            self._input,
            self._base
        )

        self._path = self.settings.get("path")
        if self._path in self.paths:
            self._path = self.paths[self._path]

    def run(self):
        self.hide_phantoms()
        if self.state == IDLE:
            self.start_run()
        else:
            self.stop_run()

    def stop_run(self):
        self.add_to_output("\nstopping > got request to stop builder\n")

        if self.state == CHK_INITIALISING:
            self.cancel = True
        elif self.state in [CHK_STARTED, BLD_STARTED]:
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
                    'stop builder\n'
                ).format(e)
                self.add_to_output(chars)

    def start_run(self):
        self.state = CHK_INITIALISING
        self.start_time = time.time()

        self.reload_settings()
        if self.view.is_dirty():
            self.view.run_command("save")
        self.setup_output_view()

        thread = threading.Thread(
            target=lambda: self.start_run_aux(self._path)
        )
        thread.start()

    def start_run_aux(self, path):
        self.lock.acquire()
        if self.cancel:
            self.state = IDLE
            self.cancel = False
            self.lock.release()
            return

        self.state = CHK_STARTED
        if self._builder.get("show_path_in_builder"):
            chars = 'details  > using PATH "{}"'.format(
                self.settings.get("path")
            )
            if path != self._program.get("path"):
                chars += ' (i.e. "{}")'.format(path)
            self.add_to_output(chars)

        os.chdir(self._dir)

        if self._check.get("check_syntax_before_build"):
            self.add_to_output("\nchecking > doing ConTeXt syntax check")

            opts = {
                "creationflags": self._flags,
                "stdin": subprocess.PIPE,
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE
            }
            if path:
                orig_path = os.environ["PATH"]
                os.environ["PATH"] = utilities.add_path(orig_path, path)
                opts["env"] = os.environ.copy()
                os.environ["PATH"] = orig_path
            self.process = subprocess.Popen(
                ["mtxrun", "--script", "check", self._input], **opts
            )
            self.lock.release()

            self.result = self.process.communicate()
            elapsed = time.time()
            if self.process.returncode == 0:
                done = self.add_result_to_output()
                if not done and self._check.get("stop_build_if_check_fails"):
                    self.add_to_output("\nfailure  > stopping builder")
                    self.add_to_output("failure  > finished in {:.1f}s".format(
                        elapsed - self.start_time
                    ))
                    self.state = IDLE
                    return

        else:
            self.lock.release()

        self.start_run_aux_i(path)

    def start_run_aux_i(self, path):
        self.lock.acquire()
        if self.cancel:
            self.state = IDLE
            self.cancel = False
            self.lock.release()
            return

        chars = '\nstarting > running "{}"'.format(self._name)
        if self._builder.get("show_full_command_in_builder"):
            chars += ' (full command "{}")'.format(" ".join(self._command))
        self.add_to_output(chars)

        opts = {
            "creationflags": self._flags,
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE
        }
        if path:
            orig_path = os.environ["PATH"]
            os.environ["PATH"] = utilities.add_path(orig_path, path)
            opts["env"] = os.environ.copy()
            os.environ["PATH"] = orig_path

        self.state = BLD_STARTED
        self.process = subprocess.Popen(self._command, **opts)
        self.lock.release()

        result = self.process.communicate()
        self.elapsed = time.time() - self.start_time
        self.log = parse_log.parse_log(result[0])
        self.process_errors()
        self.do_phantoms()
        self.process = None
        self.state = IDLE

    def do_phantoms(self):
        if self._builder.get("show_errors_in_main_view"):
            self._phantom_set.update([
                sublime.Phantom(
                    sublime.Region(
                        self.view.text_point(e.get("line", 1) - 1, 0)
                    ),
                    TEMPLATE.format(
                        message=html.escape(
                            self.parse_error(type_, e, verbose=False),
                            quote=False
                        )
                    ),
                    sublime.LAYOUT_BLOCK,
                    on_navigate=self.hide_phantoms
                )
                for type_, list_ in self.log.get("errors", {}).items()
                for e in list_
            ])

    def hide_phantoms(self, *args, **kwargs):
        if hasattr(self, "view"):
            self.view.erase_phantoms("simple_context")

    def parse_error(self, type_, e, verbose=True):
        if verbose:
            if e.get("line") and e.get("details"):
                return "error    > {type} > line {line}: {details}".format(
                    type=type_, **e
                )
            elif e.get("details"):
                return "error    > {type} > {details}".format(type=type_, **e)
            elif e.get("line"):
                return \
                    "error    > {type} > line {line}".format(type=type_, **e)
            else:
                return "error    > {type} >".format(type=type_, **e)
        else:
            if e.get("details"):
                return "{type}: {details}".format(type=type_, **e)
            else:
                return type_

    def process_errors(self):
        self.add_to_output("")
        extra = False

        if self._builder.get("show_warnings_in_builder"):
            for type_, items in self.log.get("warnings", []).items():
                for e in items:
                    extra = True
                    self.add_to_output("warning  > {type} > {details}".format(
                        type=type_, **e
                    ))
        if self._builder.get("show_errors_in_builder"):
            for type_, items in self.log.get("errors", []).items():
                for e in items:
                    extra = True
                    self.add_to_output(self.parse_error(type_, e))
        if extra:
            self.add_to_output("")

        if self.process.returncode == 0:
            pages = self.log.get("info", {}).get("pages")
            if self._builder.get("show_pages_shipped_in_builder") and pages:
                chars = "success  > shipped {} page{}".format(
                    pages, "" if pages == 1 else "s"
                )
                self.add_to_output(chars)

            viewer = self._builder.get("PDF", {}).get("PDF_viewer")
            if viewer and self._builder.get("PDF", {}).get("auto_open_PDF"):
                self.add_to_output(
                    "success  > opening PDF with {}".format(viewer)
                )
                subprocess.Popen(
                    [viewer, "{}.pdf".format(self._base)],
                    creationflags=self._flags
                )
            self.add_to_output(
                "success  > finished in {:.1f}s".format(self.elapsed)
            )
        else:
            self.add_to_output(
                "failure  > finished in {:.1f}s".format(self.elapsed)
            )

    def add_result_to_output(self):
        s = self.result[0].decode(encoding="utf-8", errors="replace").replace(
            "\r\n", "\n").replace("\r", "\n").strip()
        if s == "no error":
            self.add_to_output("checking > success")
            return True
        else:
            parts = s.split("  ", maxsplit=2)
            self.add_to_output("checking > failure > line {} > {}".format(
                1 + int(parts[0]), parts[1]
            ))
            self.add_to_output("checking > failure > {}".format(parts[2]))
            return False

    def add_to_output(self, s):
        self.output_view.run_command("append", {"characters": s + "\n"})

    def setup_output_view(self):
        if not hasattr(self, "output_view"):
            self.output_view = \
                self.window.create_output_panel("simple_ConTeXt")

        self.output_view.settings().set("line_numbers", False)
        self.output_view.settings().set("gutter", False)
        self.output_view.settings().set("spell_check", False)
        self.output_view.settings().set("scroll_past_end", False)
        self.output_view.assign_syntax(
            "Packages/simple_ConTeXt/build results.sublime-syntax"
        )
        self.output_view = self.window.create_output_panel("simple_ConTeXt")
        self.window.run_command(
            "show_panel", {"panel": "output.simple_ConTeXt"}
        )


class SimpleContextCheckCommand(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock = threading.Lock()
        self.state = IDLE
        self.cancel = False
        self.process = None

    def reload_settings(self):
        utilities.reload_settings(self)
        self.flags = CREATE_NO_WINDOW if sublime.platform() == "windows" else 0
        self.view = self.window.active_view()
        self.dir_, self.input_ = os.path.split(self.view.file_name())
        self.command = ["mtxrun", "--script", "check", self.input_]
        self.path_ = self.settings.get("path")
        if self.path_ in self.paths:
            self.path_ = self.paths[self.path_]

    def is_visible(self):
        return utilities.is_context(self.view)

    def run(self):
        if self.state == IDLE:
            self.start_run()
        else:
            self.stop_run()

    def stop_run(self):
        self.add_to_output("stopping > got request to stop builder")

        if self.state == CHK_INITIALISING:
            self.cancel = True
        elif self.state == CHK_STARTED:
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
                    'stop builder'
                ).format(e)
                self.add_to_output(chars)

    def start_run(self):
        self.state = CHK_INITIALISING
        self.start_time = time.time()

        self.reload_settings()
        if self.view.is_dirty():
            self.view.run_command("save")
        self.setup_output_view()

        self.add_to_output("starting > running ConTeXt syntax check")
        thread = threading.Thread(target=lambda: self.run_aux(self.path_))
        thread.start()

    def run_aux(self, path):
        self.lock.acquire()
        if self.cancel:
            self.state = IDLE
            self.cancel = False
            self.lock.release()
            return

        opts = {
            "creationflags": self.flags,
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE
        }
        if path:
            orig_path = os.environ["PATH"]
            os.environ["PATH"] = utilities.add_path(orig_path, path)
            opts["env"] = os.environ.copy()
            os.environ["PATH"] = orig_path

        os.chdir(self.dir_)
        self.state = CHK_STARTED
        self.process = subprocess.Popen(self.command, **opts)
        self.lock.release()

        self.result = self.process.communicate()
        self.elapsed = time.time() - self.start_time
        self.add_result_to_output()
        self.process = None
        self.state = IDLE

    def add_result_to_output(self):
        s = self.result[0].decode(encoding="utf-8", errors="replace").replace(
            "\r\n", "\n").replace("\r", "\n").strip()
        if s == "no error":
            self.add_to_output("\nsuccess  > no error")
            self.add_to_output(
                "success  > finished in {:.1f}s".format(self.elapsed)
            )
        else:
            parts = s.split("  ", maxsplit=2)
            self.add_to_output("\nfailure  > line {} > {}".format(
                1 + int(parts[0]), parts[1]
            ))
            self.add_to_output("failure  > {}".format(parts[2]))
            self.add_to_output(
                "\nfailure  > finished in {:.1f}s".format(self.elapsed)
            )

    def add_to_output(self, s):
        self.output_view.run_command("append", {"characters": s + "\n"})

    def setup_output_view(self):
        if not hasattr(self, "output_view"):
            self.output_view = \
                self.window.create_output_panel("simple_ConTeXt_check")

        self.output_view.settings().set("line_numbers", False)
        self.output_view.settings().set("gutter", False)
        self.output_view.settings().set("spell_check", False)
        self.output_view.settings().set("scroll_past_end", False)
        self.output_view.assign_syntax(
            "Packages/simple_ConTeXt/build results.sublime-syntax"
        )
        self.output_view = self.window.create_output_panel(
            "simple_ConTeXt_check"
        )
        self.window.run_command(
            "show_panel", {"panel": "output.simple_ConTeXt_check"}
        )
