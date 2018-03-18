import subprocess
import threading
import time
# import html
import os

import sublime
import sublime_plugin

from .scripts import utilities
# from .scripts import html_css
# from .scripts import scopes
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
    def __init__(self, sequence, root=None, working_dir=None):
        self.platform = sublime.platform()
        self.flags = \
            files.CREATE_NO_WINDOW if self.platform == "windows" else 0
        self.sequence = list(reversed(sequence))
        self.root = root
        self.working_dir = working_dir
        self.lock = threading.Lock()
        self.proc = None
        self.killed = False

    def start(self):
        with self.lock:
            self.killed = False
            self.start_time = time.time()
            if self.working_dir:
                os.chdir(self.working_dir)
        self.proceed()

    def proceed(self):
        with self.lock:
            if not self.sequence:
                self.quit()
                return

            seq = self.sequence.pop()
            cmd = seq.get("cmd")
            if not cmd:
                self.proceed()
                return
            if isinstance(cmd, str):
                cmd = cmd.split()

            env = os.environ.copy()
            extra_env = seq.get("env")
            if extra_env:
                for k, v in extra_env.items():
                    env[k] = v
            output = seq.get("output")

            print('Running: {}'.format(" ".join(cmd)))
            thread = threading.Thread(
                target=lambda: self.run_command(
                    cmd,
                    {
                        "env": env,
                        "creationflags": self.flags,
                        "stdin": subprocess.PIPE,
                        "stdout": subprocess.PIPE,
                        "stderr": subprocess.STDOUT,
                    },
                    output
                )
            )
        thread.start()

    def run_command(self, cmd, opts, output):
        self.proc = subprocess.Popen(cmd, **opts)
        if output == "context":
            self.root.add_to_output("running context:\n")
            result = self.proc.communicate()
            code = self.proc.returncode
        else:
            code = 0

        with self.lock:
            if output == "context":
                self.output_context(result[0] if result else None, code)
            elif output == "pdf":
                self.output_context_pdf(cmd[0] if cmd else None)

        if code == 0:
            self.proceed()
        else:
            self.quit()

    def output_context(self, data, code):
        self.root.add_to_output(
            log.parse(data, code),
            scroll_to_end=True,
            force=True
        )

    def output_context_pdf(self, cmd):
        text = "opening pdf with {}\n".format(cmd) if cmd else "opening pdf\n"
        self.root.add_to_output(text, scroll_to_end=True, force=True)

    def kill(self):
        with self.lock:
            if self.killed:
                return

            if self.proc:
                if self.platform == "windows":
                    subprocess.Popen(
                        ["taskkill", "/t", "/f", "/pid", str(self.proc.pid)],
                        creationflags=self.flags,
                    )
                else:
                    #D Doing \type{process.kill()} doesn't seem to work as it
                    #D should. Not sure why, maybe something to do with calls
                    #D to \type{context} invoking child processes, and then
                    #D killing the parent process not affecting the children.
                    #D Hmm \periods
                    self.proc.kill()

            self.killed = True
            self.sequence = []
            self.root.add_to_output(
                "[Cancelled in {:.1f}s]\n".format(
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
        self.root.add_to_output(
            "[Finished in {:.1f}s]\n".format(time.time() - self.start_time)
        )
        self.root.proc = None


class SimpleContextExecMainCommand(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.proc = None

    def reload_settings(self):
        utilities.reload_settings(self)
        self.show_errors_inline = sublime.load_settings(
            "Preferences.sublime-settings").get("show_errors_inline", True)
        self.show_panel_on_build = sublime.load_settings(
            "Preferences.sublime-settings").get("show_panel_on_build", True)
        self.view = self.window.active_view()

    def run(
        self,
        cmd_seq=[],
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
        self.reload_settings()

        if update_phantoms_only:
            if self.show_errors_inline:
                self.update_phantoms()
            return
        if hide_phantoms_only:
            self.hide_phantoms()
            return

        #D Building whilst a build is already in progress cancels it.
        if kill or self.proc is not None:
            self.kill_proc()
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
            line_regex=line_regex
        )
        if not self.quiet:
            sublime.status_message("Building")

        self.hide_phantoms()
        if self.show_panel_on_build:
            self.show_output()

        if not working_dir and self.view:
            file_ = self.view.file_name()
            working_dir = os.path.dirname(file_)
        if working_dir:
            os.chdir(working_dir)

        if cmd_seq:
            sequence = utilities.expand_variables(
                self, cmd_seq, utilities.get_variables(self)
            )

            try:
                self.proc = ExecMainSubprocess(
                    sequence, root=self, working_dir=working_dir,
                )
                self.proc.start()
            except Exception as e:
                print(str(e))
                if not self.quiet:
                    text = "encountered error of type {}\n[Finished]\n"
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
        dict_ = kwargs
        if clean:
            text = text.replace("\r\n", "\n").replace("\r", "\n")
        dict_["characters"] = text
        self.output_view.run_command("append", dict_)

    def setup_output_view(
        self,
        syntax="Packages/Text/Plain text.tmLanguage",
        word_wrap=True,
        working_dir="",
        file_regex="",
        line_regex=""
    ):
        if not hasattr(self, "output_view"):
            self.output_view = self.window.create_output_panel("ConTeXt")

        self.output_view.settings().set("result_file_regex", file_regex)
        self.output_view.settings().set("result_line_regex", line_regex)
        self.output_view.settings().set("result_base_dir", working_dir)
        self.output_view.settings().set("line_numbers", False)
        self.output_view.settings().set("gutter", False)
        self.output_view.settings().set("spell_check", False)
        self.output_view.settings().set("scroll_past_end", False)
        if isinstance(word_wrap, bool):
            self.output_view.settings().set("word_wrap", word_wrap)
        else:
            self.output_view.settings().set("word_wrap", False)
        if syntax:
            self.output_view.assign_syntax(syntax)

        self.window.create_output_panel("ConTeXt")  # this line is important

    def update_phantoms(self):
        pass  # TODO

    def hide_phantoms(self):
        if self.view:
            self.view.erase_phantoms("ConTeXt")

    def on_phantom_navigate(self, href):
        self.hide_phantoms()
