import sublime
import subprocess
import time
import html
from . import build_base
from .scripts import utilities
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


class SimpleContextBuildContextCommand(
    build_base.SimpleContextBuildBaseCommand
):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("phantom_set_name", "ConTeXt")
        kwargs.setdefault("output_panel_name", "ConTeXt")
        kwargs.setdefault("output_category_len", 8)
        super().__init__(*args, **kwargs)
        self.set_idle()
        self.reload_settings()

    def set_idle(self):
        self._base_set_idle()

    def reload_settings(self):
        self._base_reload_settings()
        self.command_name = self._program.get("name", "context")
        if self._base_input:
            self.check_command = \
                ["mtxrun", "--script", "check", self._base_input]
            if self._base_file:
                self.main_command = utilities.process_options(
                    self.command_name,
                    self._program.get("options", {}),
                    self._base_input,
                    self._base_file
                )
        self.load_css()

    def load_css(self):
        if not hasattr(self, "style"):
            self.style = utilities.strip_css_comments(
                sublime.load_resource(
                    "Packages/simple_ConTeXt/css/phantom_error.css"
                )
            )

    def is_visible(self):
        return utilities.is_context(self._base_view)

    def run(self, *args, **kwargs):
        self.reload_settings()
        if not (
            hasattr(self, "check_command") and hasattr(self, "main_command")
        ):
            return
        commands = []
        do_check = self.setting_is_yes(kwargs.get("do_check"))
        do_main = self.setting_is_yes(kwargs.get("do_main"))
        if (
            do_check or (
                self.setting_is_maybe(kwargs.get("do_check")) and
                self.setting_is_yes(
                    self._check.get("check_syntax_before_build")
                )
            )
        ):
            commands.append(
                {"command": self.check_command, "handler": self.handle_checker}
            )
        if do_main:
            commands.append(
                {"command": self.main_command, "handler": self.handle_main}
            )

        just_check = do_check and not do_main
        self._base_run(
            commands,
            begin=lambda: self.handler_begin(just_check=just_check),
            end=lambda return_codes: self.handler_end(
                return_codes, just_check=just_check
            )
        )

    def setting_is_yes(self, obj):
        return obj in [1, "yes", "always", True]

    def setting_is_maybe(self, obj):
        return obj in [0, "maybe", "possibly", "depends"]

    def setting_is_no(self, obj):
        return obj in [-1, "no", "never", False]

    def handler_begin(self, just_check=False):
        self.start_time = time.time()
        self.add_to_output(
            "starting",
            "running ConTeXt" + (" syntax check" if just_check else "") + "..."
        )
        if self._options.get("show_path_in_builder"):
            path = self._settings.get("path")
            chars = 'using $PATH "{}"'.format(path)
            if path != self._path:
                chars += ' (i.e. "{}")'.format(self._path)
            self.add_to_output("starting", chars)
        if self._options.get("show_full_command_in_builder"):
            self.add_to_output(
                "starting",
                'full command "{}"'.format(" ".join(self.main_command))
            )

    def handler_end(self, return_codes, just_check=False):
        stop_time = time.time() - self.start_time
        if just_check:
            return

        if return_codes[-1] == 0:
            message = ", ".join([
                "success", "finished in {:.1f}s".format(stop_time)
            ])
            self.add_to_output("stopping", message, gap=True)
            if hasattr(self, "log_data"):
                pages = self.log_data.get("info", {}).get("pages")
                if (
                    self._options.get("show_pages_shipped_in_builder") and
                    pages
                ):
                    chars = "shipped {} page{}".format(
                        pages, "" if pages == 1 else "s"
                    )
                    self.add_to_output("stopping", chars)
            name = self._PDF.get("viewer")
            viewer = self._PDF_viewers.get(name)
            if viewer and self._PDF.get("open_after_build"):
                self.add_to_output(
                    "stopping", "opening PDF with {}".format(name)
                )
                subprocess.Popen(
                    [viewer, "{}.pdf".format(self._base_file)],
                    creationflags=self._base_flags
                )
        else:
            message = ", ".join([
                "failure", "finished in {:.1f}s".format(stop_time)
            ])
            self.add_to_output("stopping", message, gap=True)

    def handle_checker(self, text):
        result = utilities.parse_checker_output(text)
        passed = result.get("passed")
        head = result.get("head")
        main = result.get("main")
        if passed:
            self.add_to_output("check", "no syntax errors detected", gap=True)
        else:
            self.add_to_output("check", "failure", gap=True)
            if head:
                self.add_to_output("check", head)
            for i, line in enumerate(main.split("\n")):
                self.add_to_output(
                    "check", "snippet > {}".format(line), gap=not i
                )
            self._base_set_stopping()

    def handle_main(self, text):
        self.log_data = log.parse(text, decode=False)
        self.process_errors()
        self.do_phantoms()

    def process_errors(self):
        first = True
        if self._options.get("show_warnings_in_builder"):
            for type_, items in self.log_data.get("warnings", []).items():
                for e in items:
                    self.add_to_output(
                        "warning",
                        "{type} > {details}" .format(type=type_, **e),
                        gap=first
                    )
                    first = False
        if self._options.get("show_errors_in_builder"):
            for type_, items in self.log_data.get("errors", []).items():
                for e in items:
                    self.add_to_output(
                        "error", self.parse_error(type_, e), gap=first
                    )
                    first = False

    def do_phantoms(self):
        if self._base_view.settings().get("show_errors_inline"):
            self._base_update_phantoms([
                sublime.Phantom(
                    sublime.Region(
                        self._base_view.text_point(e.get("line", 1) - 1, 0)
                    ),
                    PHANTOM_ERROR_TEMPLATE.format(
                        message=html.escape(
                            self.parse_error(type_, e, verbose=False),
                            quote=False
                        ),
                        style=self.style
                    ),
                    sublime.LAYOUT_BLOCK,
                    on_navigate=self.hide_phantoms
                )
                for type_, list_ in self.log_data.get("errors", {}).items()
                for e in list_
            ])

    def hide_phantoms(self, *args, **kwargs):
        self._base_hide_phantoms()

    def parse_error(self, type_, e, verbose=True):
        if verbose:
            if e.get("line") and e.get("details"):
                return \
                    "{type} > line {line} > {details}".format(type=type_, **e)
            elif e.get("details"):
                return "{type} > {details}".format(type=type_, **e)
            elif e.get("line"):
                return "{type} > line {line}".format(type=type_, **e)
            else:
                return "{type} >".format(type=type_, **e)
        else:
            if e.get("details"):
                return "{type}: {details}".format(type=type_, **e)
            else:
                return type_

    def add_to_output(self, category, text, gap=False):
        self._base_add_to_output(category, text, gap=gap)
