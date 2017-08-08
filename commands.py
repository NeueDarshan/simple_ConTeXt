import sublime
import sublime_plugin
import subprocess
import threading
from .scripts import utilities


CREATE_NO_WINDOW = 0x08000000

DOCS = [
    # ["bibTeX: The ConTeXt Way", "mkiv-publications"],
    ["Coloring ConTeXt", "colors-mkiv"],
    ["Columns", "columnsets"],
    ["ConTeXt MkIV: An Excursion", "ma-cb-en"],
    ["Dealing With XML In ConTeXt", "xml-mkiv"],
    ["Exporting XML and EPUB from ConTeXt", "epub-mkiv"],
    ["Extreme Tables", "xtables-mkiv"],
    ["Flowcharts", "charts-mkiv"],
    ["Fonts Out Of ConTeXt", "fonts-mkiv"],
    ["It's In The Details", "details"],
    ["Languages in ConTeXt", "languages-mkiv"],
    ["LMX Templates", "templates-mkiv"],
    ["LuaTeX and ConTeXt", "about"],
    ["LuaTeX Reference Manual", "luatex"],
    ["Luatools, Mtxrun, Context", "tools-mkiv"],
    ["Math", "math-mkiv"],
    ["MathML Examples", "mmlexamp"],
    ["MathML", "mmlprime"],
    ["MetaPost: A User's Manual", "mpman"],
    ["MkIV Hybrid Technology", "hybrid"],
    ["README", "mreadme"],
    ["Rules", "rules-mkiv"],
    ["Simple Spreadsheets", "spreadsheets-mkiv"],
    ["Spacing in ConTeXt", "spacing-mkiv"],
    ["SQL", "sql-mkiv"],
    ["Steps", "steps-mkiv"],
    ["Still Going On", "still"],
    ["SwigLib Basics", "swiglib-mkiv"],
    ["The ConTeXt Libraries", "lua-mkiv"],
    ["The History of LuaTeX", "mk"],
    ["Tips and Tricks", "tiptrick"],
    ["Units", "units-mkiv"],
    ["Workflow Support In ConTeXt", "workflows-mkiv"],
]


class SimpleContextFindDocs(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def reload_settings(self):
        utilities.reload_settings(self)
        self.viewer = self._PDF.get("viewer")
        self.flags = CREATE_NO_WINDOW if sublime.platform() == "windows" else 0
        self.docs = DOCS

    def run(self):
        self.reload_settings()
        thread = threading.Thread(target=self.run_panel)
        thread.start()

    def run_panel(self, selected_index=0):
        self.window.show_quick_panel(
            self.docs + [["...", "search for other files"]],
            self.run_handle,
            selected_index=selected_index
        )

    def run_handle(self, index):
        if 0 <= index < len(self.docs):
            self.open_doc(self.docs[index][1])
        elif index == len(self.docs):
            self.window.show_input_panel(
                "name", "", self.on_done, self.on_change, self.on_cancel,
            )

    def on_done(self, text):
        self.open_doc(text)

    def on_change(self, text):
        pass

    def on_cancel(self):
        self.run_panel(selected_index=len(self.docs))

    def open_doc(self, name):
        file = utilities.locate(self._path, "{}.pdf".format(name))
        if self.viewer and file:
            subprocess.Popen([self.viewer, file], creationflags=self.flags)
        else:
            msg = (
                'Unable to locate file "{}.pdf".\n\nSearched in the TeX '
                'tree containing "{}".'
            )
            sublime.error_message(msg.format(name, self._path))


class SimpleContextEditSettings(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.args = {
            "base_file":
                "${packages}/simple_ConTeXt/simple_ConTeXt.sublime-settings",
            "default": "{\n\t$0\n}\n"
        }

    def run(self, *args, **kwargs):
        sublime.run_command("edit_settings", self.args)
