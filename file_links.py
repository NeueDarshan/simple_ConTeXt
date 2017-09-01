import sublime
import sublime_plugin
import os
from .scripts import utilities


CREATE_NO_WINDOW = 0x08000000

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
        self.flags = CREATE_NO_WINDOW if sublime.platform() == "windows" else 0
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
            self.style = utilities.strip_css_comments(
                sublime.load_resource(
                    "Packages/simple_ConTeXt/css/file_links.css"
                )
            )

    def is_visible(self):
        return utilities.is_context(self.view)

    def on_hover(self, point, hover_zone):
        if hover_zone != sublime.HOVER_TEXT or not self.is_visible():
            return

        self.reload_settings()
        file = utilities.match_enclosing_block(
            self.view, point, "meta.other.file.context"
        )
        if file:
            block = utilities.match_last_block_in_region(
                self.view, file[0], file[1], "meta.other.file.name.context"
            )
            if block:
                file_name = self.view.substr(sublime.Region(*block))
                if not file_name:
                    return
            else:
                return
        else:
            return

        self.view.show_popup(
            TEMPLATE.format(file=file_name, style=self.style),
            location=block[0],
            flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
            on_navigate=self.on_navigate,
            on_hide=self.on_hide
        )

    def on_navigate(self, href):
        if not self.base_dir:
            return

        methods = [os.path.normpath(self.base_dir)]
        for f in os.listdir(os.path.normpath(self.base_dir)):
            path = os.path.normpath(os.path.join(self.base_dir, f))
            if os.path.isdir(path):
                methods.append(path)
        methods.append(os.path.normpath(os.path.join(self.base_dir, "..")))

        file = utilities.fuzzy_locate(
            self._path,
            href,
            flags=self.flags,
            extensions=self.extensions,
            methods=reversed(methods)
        )
        if file and os.path.exists(file):
            self.view.window().open_file(file)
        else:
            other = utilities.fuzzy_locate(
                self._path,
                href,
                flags=self.flags,
                extensions=self.extensions,
            )
            if other and os.path.exists(other):
                # # For some reason, this is crashing ST on finishing the
                # # dialogue \periods
                # msg = (
                #     'Unable to locate file "{}".\n\nSearched around the '
                #     'current working directory.\n\nFound a file with the same '
                #     'name in the TeX tree containing "{}", open instead?'
                # ).format(href, self._path)
                # if sublime.ok_cancel_dialog(msg):
                #     self.view.window().open_file(other)
                self.view.window().open_file(other)
            else:
                msg = (
                    'Unable to locate file "{}".\n\nSearched around the '
                    'current working directory, and in the TeX tree '
                    'containing "{}".'
                ).format(href, self._path)
                sublime.error_message(msg.format(file, self._path))

    def on_hide(self):
        pass
