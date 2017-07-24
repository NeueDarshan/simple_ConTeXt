import sublime
import sublime_plugin
import subprocess
import threading
import time
import html
import os
from .scripts import utilities


CREATE_NO_WINDOW = 0x08000000

TEMPLATE = """
<html>
    <style>
        div.error {{
            padding: 0.5rem;
        }}
        div.error message {{
            color: var(--redish);
        }}
        div.error a {{
            font-weight: bold;
            text-decoration: none;
            background-color: var(--background);
            padding: 0.2rem;
            padding-left: 0.4rem;
            padding-right: 0.4rem;
        }}
    </style>
    <body id="simple-ConTeXt-phantom-error">
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
        self.state = 0
        self.cancel = False
        self.process = None
        self.base = ""

    def is_visible(self):
        return utilities.is_context(self.view)

    def reload_settings(self):
        utilities.reload_settings(self)

    def run(self):
        self.hide_phantoms()
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
        self.view = self.window.active_view()
        if self.view.is_dirty():
            self.view.run_command("save")
        self.setup_output_view()
        self.phantom_set = sublime.PhantomSet(self.view, "simple_context")
        input_ = os.path.split(self.view.file_name())[1]
        self.base = utilities.base_file(input_)

        program = self.settings.get("builder", {}).get("program", {})
        path = self.settings.get("path")
        if path in self.paths:
            path = self.paths[path]
        name = program.get("name", "context")
        self.command = utilities.process_options(
            name, program.get("options", {}), input_, self.base
        )

        chars = ""
        if self.settings.get("builder", {}).get(
                "show_program_path_in_builder"):
            chars += 'starting > using PATH "{}"'.format(
                self.settings.get("path")
            )
            if path != program.get("path"):
                chars += ' (i.e. "{}")'.format(path)
            chars += "\n"
        chars += 'starting > running "{}"'.format(name)
        if self.settings.get("builder", {}).get(
                "show_full_command_in_builder"):
            chars += ' (full command "{}")'.format(" ".join(self.command))
        chars += "\n"
        self.output_view.run_command("append", {"characters": chars})

        thread = threading.Thread(target=lambda: self.start_run_aux(path))
        thread.start()

    def start_run_aux(self, path):
        self.lock.acquire()
        if self.cancel:
            self.state = 0
            self.cancel = False
            return

        flags = CREATE_NO_WINDOW if sublime.platform() == "windows" else 0
        opts = {
            "creationflags": flags,
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE
        }
        if path:
            orig_path = os.environ["PATH"]
            os.environ["PATH"] = utilities.add_path(orig_path, path)
            opts["env"] = os.environ.copy()
            os.environ["PATH"] = orig_path

        self.state = 2
        self.process = subprocess.Popen(self.command, **opts)
        self.lock.release()

        result = self.process.communicate()
        self.elapsed = time.time() - self.start_time
        self.log = utilities.parse_log(result[0])
        self.builder = self.settings.get("builder", {})
        self.process_errors(flags)
        self.do_phantoms()
        self.process = None
        self.state = 0

    def do_phantoms(self):
        if self.builder.get("show_errors_in_main_view"):
            self.phantom_set.update([
                sublime.Phantom(
                    sublime.Region(
                        self.view.text_point(int(e["line"]) - 1, 0)
                    ),
                    TEMPLATE.format(
                        message=html.escape(
                            self.parse_error(e, verbose=False), quote=False
                        )
                    ),
                    sublime.LAYOUT_BLOCK,
                    on_navigate=self.hide_phantoms
                )
                for e in self.log["errors"]
            ])

    def hide_phantoms(self, *args, **kwargs):
        if hasattr(self, "view"):
            self.view.erase_phantoms("simple_context")

    def parse_error(self, e, verbose=True):
        if verbose:
            if e["line"] and e["details"]:
                return \
                    "error    > {error} > line {line}: {details}".format(**e)
            elif e["details"]:
                return "error    > {error} > {details}".format(**e)
            elif e["line"]:
                return "error    > {error} > line {line}".format(**e)
            else:
                return "error    > {error} >".format(**e)
        else:
            if e["details"]:
                return "{error}: {details}".format(**e)
            else:
                return e["error"]

    def process_errors(self, flags):
        chars = ""

        if self.builder.get("show_warnings_in_builder"):
            for d in self.log["warnings"]:
                chars += "\nwarning  > {type} > {message}".format(**d)

        if self.builder.get("show_errors_in_builder"):
            for e in self.log["errors"]:
                chars += "\n" + self.parse_error(e)

        if len(chars) > 0:
            self.output_view.run_command("append", {"characters": chars})
            chars = "\n"

        if self.process.returncode == 0:
            if self.builder.get(
                "show_pages_shipped_in_builder"
            ) and self.log.get("pages"):
                chars += (
                    "\nsuccess  > shipped {} page{}".format(
                        self.log["pages"],
                        "" if self.log["pages"] == 1 else "s"
                    )
                )
            viewer = self.builder.get("PDF", {}).get("PDF_viewer")
            if viewer and self.builder.get("PDF", {}).get("auto_open_PDF"):
                chars += "\nsuccess  > opening PDF with {}".format(viewer)
                subprocess.Popen(
                    [viewer, "{}.pdf".format(self.base)], creationflags=flags
                )
            chars += "\nsuccess  > finished in {:.1f}s".format(self.elapsed)
        else:
            chars += "\nfailure  > finished in {:.1f}s".format(self.elapsed)

        self.output_view.run_command("append", {"characters": chars})

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
        self.state = 0
        self.cancel = False
        self.process = None

    def reload_settings(self):
        utilities.reload_settings(self)

    def is_visible(self):
        return utilities.is_context(self.view)

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
        self.view = self.window.active_view()
        if self.view.is_dirty():
            self.view.run_command("save")
        self.setup_output_view()
        dir_, input_ = os.path.split(self.view.file_name())

        path = self.settings.get("path")
        if path in self.paths:
            path = self.paths[path]
        self.command = ["mtxrun", "--script", "check", input_]

        message = "starting > running ConTeXt syntax check"
        self.output_view.run_command("append", {"characters": message})

        thread = threading.Thread(target=lambda: self.run_aux(path))
        thread.start()

    def run_aux(self, path):
        self.lock.acquire()
        if self.cancel:
            self.state = 0
            self.cancel = False
            return

        flags = CREATE_NO_WINDOW if sublime.platform() == "windows" else 0
        opts = {
            "creationflags": flags,
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE
        }
        if path:
            orig_path = os.environ["PATH"]
            os.environ["PATH"] = utilities.add_path(orig_path, path)
            opts["env"] = os.environ.copy()
            os.environ["PATH"] = orig_path

        self.state = 2
        self.process = subprocess.Popen(self.command, **opts)
        self.lock.release()

        result = self.process.communicate()
        self.output_view.run_command(
            "append", {"characters": self.process_result(result)}
        )
        self.elapsed = time.time() - self.start_time
        self.builder = self.settings.get("builder", {})
        self.process = None
        self.state = 0

    def process_result(self, result):
        s = result[0].decode(encoding="utf-8", errors="replace").replace(
            "\r\n", "\n").replace("\r", "\n").strip()
        return "\n\nresult   > {}".format(s)

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
