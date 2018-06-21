import subprocess
import threading
import time
import os

import sublime
import sublime_plugin

from .scripts import utilities
from .scripts import html_css
from .scripts import files
from .scripts import log


PHANTOM_ERROR_TEMPLATE = """
<html>
    <style>
        {style}
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


class ExecMainSubprocess:
    platform = sublime.platform()
    flags = files.CREATE_NO_WINDOW if platform == "windows" else 0
    shell = True if platform == "windows" else False
    proc = None
    killed = False
    lock = threading.Lock()

    def __init__(
        self,
        sequence,
        root=None,
        working_dir=None,
        show_ConTeXt_path=None,
        show_full_command=None,
        show_errors=None,
        show_errors_inline=None,
    ):
        self.sequence = sequence[::-1]
        self.root = root
        self.working_dir = working_dir
        self.show_errors = False if show_errors is None else show_errors
        self.show_ConTeXt_path = \
            False if show_ConTeXt_path is None else show_ConTeXt_path
        self.show_full_command = \
            False if show_full_command is None else show_full_command
        self.show_errors_inline = \
            False if show_errors_inline is None else show_errors_inline

    def start(self):
        with self.lock:
            self.killed = False
            self.start_time = time.time()
            if self.working_dir:
                os.chdir(self.working_dir)
        self.proceed()

    def proceed(self):
        self.lock.acquire()
        if not self.sequence:
            self.lock.release()
            self.quit()
            return

        seq = self.sequence.pop()
        run_when = seq.get("run_when")
        if run_when is not None and not run_when:
            self.lock.release()
            self.proceed()
            return

        cmd = seq.get("cmd")
        if not cmd:
            self.lock.release()
            self.proceed()
            return
        if isinstance(cmd, str):
            cmd = cmd.split()

        shell = bool(seq.get("shell"))

        env = os.environ.copy()
        extra_env = seq.get("env")
        if extra_env:
            for k, v in extra_env.items():
                env[k] = v
        output = seq.get("output")

        # print("[simple_ConTeXt] Running: {}".format(" ".join(cmd)))
        print("Running {}".format(" ".join(cmd)))
        thread = threading.Thread(
            target=lambda: self.run_command(
                cmd,
                {
                    "env": env,
                    "shell": shell,
                    "creationflags": self.flags,
                    "stdin": subprocess.PIPE,
                    "stdout": subprocess.PIPE,
                    "stderr": subprocess.STDOUT,
                },
                output,
            )
        )
        self.lock.release()
        thread.start()

    def run_command(self, cmd, opts, output):
        self.proc = subprocess.Popen(cmd, **opts)
        if output == "context":
            self.root.add_to_output("- running ConTeXt\n")
            if self.show_ConTeXt_path:
                path = self.root.get_setting("path")
                if path:
                    self.root.add_to_output(
                        "  - ConTeXt path: {}\n".format(path)
                    )
            if self.show_full_command:
                self.root.add_to_output(
                    "  - full command: {}\n".format(" ".join(cmd))
                )
            result = self.proc.communicate()
            code = self.proc.returncode
        elif output == "pdf":
            code = 0
        else:
            code = 0

        with self.lock:
            if output == "context":
                self.output_context(result[0] if result else None, code)
            elif output == "pdf":
                self.output_context_pdf(cmd[0] if cmd else None)

        if code:
            self.quit()
        else:
            self.proceed()

    def output_context(self, data, code):
        if not self.root:
            return
        result = self.root.parse_log(data)
        errors = [] if result is None else result.get("errors", [])
        if errors:
            if self.show_errors:
                self.root.add_to_output(log.compile_errors(errors))
            self.root.add_to_output(
                "  - completed un-successfully\n",
                scroll_to_end=True,
                force=True,
            )
            if self.root.global_show_errors_inline and self.show_errors_inline:
                self.root.do_phantoms(errors)
            if self.root.show_output_on_errors:
                self.root.show_output()
        else:
            self.root.add_to_output(
                "  - completed successfully\n",
                scroll_to_end=True,
                force=True,
            )

    def parse_log(self, name):
        return log.parse(name, self.root.log_script, self.root.opts)

    def output_context_pdf(self, cmd):
        viewer = self.root.get_setting("PDF/viewer")
        if viewer:
            text = "- opening PDF with {}\n".format(viewer)
        else:
            text = "- opening PDF\n"
        self.root.add_to_output(text, scroll_to_end=True, force=True)

    def kill(self):
        # Hmm. When we run a process \type{context ...} and then do
        # \type{process.kill()} here, it doesn't seem to work as I would
        # naively expect. I think that's because \type{context} is a wrapper
        # around \LuaTeX, and so what we really wanted to kill was the
        # \type{luatex} process.
        with self.lock:
            if self.killed:
                return

            if self.proc:
                if self.platform == "windows":
                    subprocess.Popen(
                        ["taskkill", "/t", "/f", "/pid", str(self.proc.pid)],
                        creationflags=self.flags,
                        shell=self.shell,
                    )
                else:
                    self.proc.kill()

            self.killed = True
            self.sequence = []
            self.root.add_to_output(
                "- cancelled in {:.1f}s\n".format(
                    time.time() - self.start_time
                )
            )
            self.root.proc = None
            self.root = None

    def poll(self):
        if self.proc:
            return self.proc.poll() is None
        return None

    def exit_code(self):
        if self.proc:
            return self.proc.poll()
        return None

    def quit(self):
        if not self.root:
            return
        self.root.add_to_output(
            "- finished in {:.1f}s\n".format(time.time() - self.start_time)
        )
        self.root.proc = None


class SimpleContextExecMainCommand(
    utilities.BaseSettings, sublime_plugin.WindowCommand,
):
    proc = None
    output_panel_cache = ""

    def reload_settings(self):
        super().reload_settings()
        self.window.run_command("simple_context_unpack_lua_scripts")
        self.global_show_errors_inline = sublime.load_settings(
            "Preferences.sublime-settings").get("show_errors_inline", True)
        self.show_panel_on_build = sublime.load_settings(
            "Preferences.sublime-settings").get("show_panel_on_build", True)
        self.view = self.window.active_view()
        self.phantom_set = sublime.PhantomSet(self.view, key="simple_ConTeXt")
        self.opts = self.expand_variables(
            {
                "creationflags": self.flags,
                "shell": self.shell,
                "env": {"PATH": "${simple_context_prefixed_path}"},
            }
        )
        self.log_script = self.expand_variables(
            "${packages}/simple_ConTeXt/scripts/parse_log.lua"
        )
        if not hasattr(self, "style"):
            self.load_css()

    def load_css(self):
        self.style = html_css.strip_css_comments(
            sublime.load_resource(
                "Packages/simple_ConTeXt/css/phantom_error.css"
            )
        )

    def run(
        self,
        cmd_seq=None,
        show=None,
        show_ConTeXt_path=None,
        show_errors=None,
        show_errors_inline=None,
        show_full_command=None,
        encoding="utf-8",
        hide_phantoms_only=False,
        kill=False,
        quiet=False,
        syntax="Packages/Text/Plain text.tmLanguage",
        update_phantoms_only=False,
        word_wrap=True,
        working_dir=None,
        file_regex="",
        line_regex="",
        **kwargs
    ):
        cmd_seq = [] if cmd_seq is None else cmd_seq
        self.reload_settings()
        show = (
            self.get_setting("builder/normal/output/show")
            if show is None else show
        )
        show_ConTeXt_path = (
            self.get_setting("builder/normal/output/show_ConTeXt_path")
            if show_ConTeXt_path is None else show_ConTeXt_path
        )
        show_full_command = (
            self.get_setting("builder/normal/output/show_full_command")
            if show_full_command is None else show_full_command
        )
        show_errors = (
            self.get_setting("builder/normal/output/show_errors")
            if show_errors is None else show_errors
        )
        show_errors_inline = (
            self.get_setting("builder/normal/output/show_errors_inline")
            if show_errors_inline is None else show_errors_inline
        )

        if update_phantoms_only:
            if self.global_show_errors_inline:
                self.update_phantoms()
            return
        if hide_phantoms_only:
            self.hide_phantoms()
            return

        if kill:
            self.kill_proc()
            return

        # Building whilst a build is already in progress does nothing. If you
        # wish to cancel it, use the proper Sublime Text way of doing that:
        # \type{Ctrl+Shift+C} is bound to cancel build by default.
        #
        # TODO: add an option to opt||in to this behaviour, as it can be nice
        # and would be easy for us to do.
        if self.proc is not None:
            return

        self.proc = None
        self.encoding = encoding
        self.quiet = quiet
        self.word_wrap = word_wrap

        self.setup_output_view(
            syntax=syntax,
            word_wrap=word_wrap,
            working_dir=working_dir,
            file_regex=file_regex,
            line_regex=line_regex,
        )
        if not self.quiet:
            sublime.status_message("Building")

        self.hide_phantoms()
        if self.show_panel_on_build and show is True:
            self.show_output()
            self.show_output_on_errors = False
        else:
            # We can be (very) forgiving to spelling errors, as the other
            # options than \type{"when_there_are_errors"} are just \type{True}
            # and \type{False}.
            self.show_output_on_errors = isinstance(show, str)

        if not working_dir and self.view:
            file_ = self.view.file_name()
            if file_:
                working_dir = os.path.dirname(file_)
        if working_dir:
            os.chdir(working_dir)

        if cmd_seq:
            sequence = self.expand_variables(cmd_seq)
            try:
                self.proc = ExecMainSubprocess(
                    sequence,
                    root=self,
                    working_dir=working_dir,
                    show_ConTeXt_path=show_ConTeXt_path,
                    show_errors=show_errors,
                    show_errors_inline=show_errors_inline,
                    show_full_command=show_full_command,
                )
                self.proc.start()
            except Exception as e:
                # print("[simple_ConTeXt] {}".format(e))
                if not self.quiet:
                    text = "- encountered error of type {}\n- finished\n"
                    self.add_to_output(text.format(type(e)))

    def kill_proc(self):
        if self.proc:
            self.proc.kill()
        self.proc = None

    def is_enabled(self, kill=False, **kwargs):
        if kill:
            return (self.proc is not None) and self.proc.poll()
        return True

    def show_output(self):
        self.window.run_command("show_panel", {"panel": "output.ConTeXt"})

    def add_to_output(self, text, clean=False, **kwargs):
        cache = self.output_panel_cache
        dict_ = kwargs
        if clean:
            text = text.replace("\r\n", "\n").replace("\r", "\n")
        if text.endswith("\n"):
            self.output_panel_cache = "\n"
            text = text.rstrip("\n")
        else:
            self.output_panel_cache = ""
        dict_["characters"] = cache + text
        self.output_view.run_command("append", dict_)

    def setup_output_view(
        self,
        syntax="Packages/Text/Plain text.tmLanguage",
        word_wrap=True,
        working_dir="",
        file_regex="",
        line_regex="",
    ):
        if not hasattr(self, "output_view"):
            self.output_view = self.window.create_output_panel("ConTeXt")

        self.output_view.settings().set("result_file_regex", file_regex)
        self.output_view.settings().set("result_line_regex", line_regex)
        self.output_view.settings().set("result_base_dir", working_dir)
        self.output_view.settings().set("line_numbers", False)
        self.output_view.settings().set("gutter", False)
        self.output_view.settings().set("draw_indent_guides", False)
        self.output_view.settings().set("rulers", False)
        self.output_view.settings().set("spell_check", False)
        self.output_view.settings().set("scroll_past_end", False)
        if isinstance(word_wrap, bool):
            self.output_view.settings().set("word_wrap", word_wrap)
        else:
            self.output_view.settings().set("word_wrap", False)
        if syntax:
            self.output_view.assign_syntax(syntax)

        self.window.create_output_panel("ConTeXt")
        self.output_panel_cache = ""

    def parse_log(self, text):
        return log.parse(text, self.log_script, self.opts)

    def do_phantoms(self, errors):
        last_line = self.view.sel()[-1]
        phantoms = []
        for err in errors:
            if len(err) < 2:
                continue
            try:
                line = int(err[0])
                if line < 1:
                    line = last_line
                else:
                    line -= 1
            except ValueError:
                line = last_line
            phantoms.append(
                sublime.Phantom(
                    sublime.Region(self.view.text_point(line, 0)),
                    PHANTOM_ERROR_TEMPLATE.format(
                        style=self.style,
                        message=html_css.unescape("{}: {}".format(*err[1:])),
                    ),
                    sublime.LAYOUT_BLOCK,
                    on_navigate=lambda href: self.hide_phantoms(),
                )
            )
        self.phantom_set.update(phantoms)

    def update_phantoms(self):
        pass

    def hide_phantoms(self):
        if self.view:
            self.view.erase_phantoms("simple_ConTeXt")

    def on_phantom_navigate(self, href):
        self.hide_phantoms()
