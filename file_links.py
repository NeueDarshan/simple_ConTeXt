import os

import sublime
import sublime_plugin

from .scripts import utilities
from .scripts import html_css
from .scripts import scopes
from .scripts import files


TEMPLATE = """
<html>
    <style>
        {style}
    </style>
    <body id="simple-ConTeXt-file-link">
        <div class="outer">
            <div class="inner">
                <span class="message">
                    open file: <a href="{file}">{file}</a>
                </span>
            </div>
        </div>
    </body>
</html>
"""

EXTENSIONS = ["tex", "mkii", "mkiv", "mkvi", "mkix", "mkxi"]


class SimpleContextFileHoverListener(
    utilities.BaseSettings, sublime_plugin.ViewEventListener,
):
    extensions = [""] + [".{}".format(s) for s in EXTENSIONS]
    flags = files.CREATE_NO_WINDOW if sublime.platform() == "windows" else 0

    def is_visible(self):
        return self.is_visible_alt()

    def reload_settings_alt(self):
        self.reload_settings()
        self.load_css()
        self.size = self.view.size()
        try:
            file_name = self.view.file_name()
            self.base_dir = os.path.dirname(file_name) if file_name else None
        except AttributeError:
            self.base_dir = None

    def load_css(self):
        if not hasattr(self, "style"):
            self.style = html_css.strip_css_comments(
                sublime.load_resource(
                    "Packages/simple_ConTeXt/css/file_links.css"
                )
            )

    def on_hover(self, point, hover_zone):
        if hover_zone != sublime.HOVER_TEXT or not self.is_visible():
            return

        self.reload_settings_alt()
        file_ = scopes.enclosing_block(
            self.view, point, scopes.FILE_NAME, end=self.size,
        )
        if file_:
            file_name = self.view.substr(sublime.Region(*file_))
            if file_name:
                file_name = file_name.strip()
                if file_name.startswith("{") and file_name.endswith("}"):
                    file_name = file_name[1:-1]
            else:
                return
        else:
            return

        self.view.show_popup(
            TEMPLATE.format(file=file_name, style=self.style),
            location=file_[0],
            flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
            on_navigate=self.on_navigate,
        )

    def on_navigate(self, href):
        if self.base_dir:
            methods = [os.path.normpath(self.base_dir)]
            for f in os.listdir(os.path.normpath(self.base_dir)):
                path = os.path.normpath(os.path.join(self.base_dir, f))
                if os.path.isdir(path):
                    methods.append(path)
            methods.append(os.path.normpath(os.path.join(self.base_dir, "..")))

            file_ = files.fuzzy_locate(
                self.context_path,
                href,
                flags=self.flags,
                extensions=self.extensions,
                methods=reversed(methods),
            )
            if file_ and os.path.exists(file_):
                self.view.window().open_file(file_)
                return

        other = files.fuzzy_locate(
            self.context_path,
            href,
            flags=self.flags,
            extensions=self.extensions,
        )
        if other and os.path.exists(other):
            # For some reason, this is crashing Sublime Text on finishing the
            # dialogue \periods.
            #
            # msg = (
            #     'Unable to locate file "{}".\n\nSearched around the '
            #     'current working directory.\n\nFound a file with the same '
            #     'name in the TeX tree containing "{}", open instead?'
            # )
            # if sublime.ok_cancel_dialog(msg.format(href, self.context_path)):
            #     self.view.window().open_file(other)
            #
            # So instead let's just open the file.
            self.view.window().open_file(other)
        else:
            msg = (
                'Unable to locate file "{}".\n\nSearched around the '
                'current working directory, and in the TeX tree '
                'containing "{}".'
            )
            sublime.error_message(msg.format(href, self.context_path))
