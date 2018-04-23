import threading

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

EXTENSIONS = ("tex", "mkii", "mkiv", "mkvi", "mkix", "mkxi")


class SimpleContextFileHoverListener(
    utilities.LocateSettings, sublime_plugin.ViewEventListener,
):
    extensions = ("",) + tuple(".{}".format(s) for s in EXTENSIONS)
    flags = files.CREATE_NO_WINDOW if sublime.platform() == "windows" else 0

    def is_visible(self):
        return self.is_visible_alt()

    def reload_settings(self):
        super().reload_settings()
        self.load_css()
        self.size = self.view.size()

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

        self.reload_settings()
        file_ = scopes.enclosing_block(
            self.view, point, scopes.FILE_NAME, end=self.size,
        )
        if file_:
            file_name = self.view.substr(sublime.Region(*file_))
            if file_name:
                file_name = file_name.strip()
                if file_name.startswith("{") and file_name.endswith("}"):
                    file_name = file_name[1:-1]
                self.view.show_popup(
                    TEMPLATE.format(file=file_name, style=self.style),
                    location=file_[0],
                    flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
                    on_navigate=self.on_navigate,
                )

    def on_navigate(self, href):
        threading.Thread(target=lambda: self.on_navigate_aux(href)).start()

    def on_navigate_aux(self, href):
        main = self.locate_file_main(href, extensions=self.extensions)
        if main:
            self.view.window().open_file(main)
            return
        other = self.locate_file_context(href, extensions=self.extensions)
        if other:
            self.view.window().open_file(other)
            return
        else:
            msg = (
                'Unable to locate file "{}".\n\nSearched around the '
                'current working directory, and in the TeX tree '
                'containing "{}".'
            )
            sublime.message_dialog(msg.format(href, self.context_path))
