import subprocess
import threading

import sublime
import sublime_plugin

from .scripts import utilities
from .scripts import files


DOCS = [
    ["bibTeX: The ConTeXt Way", "mkiv-publications"],
    ["Coloring ConTeXt", "colors-mkiv"],
    ["Columns", "columnsets"],
    ["ConTeXt Lua Documents", "cld-mkiv"],
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
    ["Nodes", "nodes"],
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


# Needs some work.
class SimpleContextFindDocsCommand(
    utilities.BaseSettings, sublime_plugin.WindowCommand,
):
    def reload_settings(self, force_reload_docs=False):
        super().reload_settings()
        self.viewer = self.get_setting("PDF/viewer")
        if force_reload_docs:
            self.reload_docs()
        else:
            if not hasattr(self, "docs"):
                self.reload_docs()

    def reload_docs(self):
        self.docs = []
        for name, file_ in DOCS:
            path = files.locate(
                self.context_path,
                "{}.pdf".format(file_),
                flags=self.flags,
                shell=self.shell,
            )
            if path:
                self.docs.append([name, file_, path])

    def run(self):
        self.reload_settings(force_reload_docs=True)
        threading.Thread(target=self.run_panel).start()

    def run_panel(self, selected_index=0):
        self.window.show_quick_panel(
            [tup[:2] for tup in self.docs] +
            [["...", "search for other files"]],
            self.run_handle,
            selected_index=selected_index,
        )

    def run_handle(self, index):
        if 0 <= index < len(self.docs):
            self.open_doc(self.docs[index][2])
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

    def open_doc(self, file_):
        subprocess.Popen(
            [self.viewer, file_], creationflags=self.flags, shell=self.shell,
        )
