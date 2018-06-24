import threading

import sublime
import sublime_plugin

from .scripts import utilities
from .scripts import html_css
from .scripts import scopes


TEMPLATE = """
<html>
    <style>
        {style}
    </style>
    <body id="simple-ConTeXt-file-link">
        <span class="message">
            open file: <a href="{file}">{file}</a>
        </span>
    </body>
</html>
"""

TEX_EXTENSIONS = ("tex", "mkii", "mkiv", "mkvi", "mkix", "mkxi")

BIB_EXTENSIONS = ("bib", "xml", "lua")


class SimpleContextFileHoverListener(
    utilities.LocateSettings, sublime_plugin.ViewEventListener,
):
    tex_extensions = ("",) + tuple(".{}".format(s) for s in TEX_EXTENSIONS)
    bib_extensions = ("",) + tuple(".{}".format(s) for s in BIB_EXTENSIONS)

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
        if not self.get_setting("file_links/on"):
            return

        main = scopes.enclosing_block(
            self.view, point, scopes.FILE_NAME, end=self.size,
        )
        if main:
            self.on_hover_aux(main, self.tex_extensions)
            return

        other = scopes.enclosing_block(
            self.view, point, scopes.MAYBE_CITATION, end=self.size,
        )
        if other:
            self.on_hover_aux(other, self.bib_extensions)
            return

    def on_hover_aux(self, word, extensions):
        file_name = self.view.substr(sublime.Region(*word))
        if file_name:
            file_name = file_name.strip()
            if file_name.startswith("{") and file_name.endswith("}"):
                file_name = file_name[1:-1].strip()
            self.view.show_popup(
                TEMPLATE.format(file=file_name, style=self.style),
                location=word[0],
                flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
                on_navigate=lambda href: self.on_navigate(href, extensions),
            )

    def on_navigate(self, href, extensions):
        threading.Thread(
            target=lambda: self.on_navigate_aux(href, extensions)
        ).start()

    def on_navigate_aux(self, name, extensions):
        main = self.locate_file_main(name, extensions=extensions)
        if main:
            self.view.window().open_file(main)
            return

        other = self.locate_file_context(name, extensions=extensions)
        if other:
            self.view.window().open_file(other)
            return

        sublime.message_dialog('Falied to locate file "{}".'.format(name))
