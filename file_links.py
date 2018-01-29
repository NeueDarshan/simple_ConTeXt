import sublime
import sublime_plugin

import os

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


class SimpleContextFileHoverListener(sublime_plugin.ViewEventListener):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        exts = ["tex", "mkii", "mkiv", "mkvi", "mkix", "mkxi"]
        self.extensions = [""] + [".{}".format(s) for s in exts]

    def reload_settings(self):
        utilities.reload_settings(self)
        self.load_css()
        self.size = self.view.size()
        self.flags = \
            files.CREATE_NO_WINDOW if sublime.platform() == "windows" else 0
        try:
            file_name = self.view.file_name()
            if file_name:
                self.base_dir, _ = os.path.split(file_name)
            else:
                self.base_dir = None
        except AttributeError:
            self.base_dir = None

    def load_css(self):
        if not hasattr(self, "style"):
            self.style = html_css.strip_css_comments(
                sublime.load_resource(
                    "Packages/simple_ConTeXt/css/file_links.css"
                )
            )

    def is_visible(self):
        return scopes.is_context(self.view)

    def on_hover(self, point, hover_zone):
        if hover_zone != sublime.HOVER_TEXT or not self.is_visible():
            return

        self.reload_settings()
        file = scopes.enclosing_block(
            self.view, point, self.size, scopes.FILE_NAME
        )
        if file:
            file_name = self.view.substr(sublime.Region(*file))
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
            location=file[0],
            flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
            on_navigate=self.on_navigate,
            on_hide=self.on_hide
        )

    def on_navigate(self, href):
        if self.base_dir:
            methods = [os.path.normpath(self.base_dir)]
            for f in os.listdir(os.path.normpath(self.base_dir)):
                path = os.path.normpath(os.path.join(self.base_dir, f))
                if os.path.isdir(path):
                    methods.append(path)
            methods.append(os.path.normpath(os.path.join(self.base_dir, "..")))

            file = files.fuzzy_locate(
                self._path,
                href,
                flags=self.flags,
                extensions=self.extensions,
                methods=reversed(methods)
            )
            if file and os.path.exists(file):
                self.view.window().open_file(file)
                return

        other = files.fuzzy_locate(
            self._path, href, flags=self.flags, extensions=self.extensions
        )
        if other and os.path.exists(other):
            #D For some reason, this is crashing Sublime Text on finishing the
            #D dialogue \periods.
            # msg = (
            #     'Unable to locate file "{}".\n\nSearched around the '
            #     'current working directory.\n\nFound a file with the same '
            #     'name in the TeX tree containing "{}", open instead?'
            # ).format(href, self._path)
            # if sublime.ok_cancel_dialog(msg):
            #     self.view.window().open_file(other)
            #D So instead let's just open the file.
            self.view.window().open_file(other)
        else:
            msg = (
                'Unable to locate file "{}".\n\nSearched around the '
                'current working directory, and in the TeX tree '
                'containing "{}".'
            ).format(href, self._path)
            sublime.error_message(msg)

    def on_hide(self):
        pass
