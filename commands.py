import sublime
import sublime_plugin
import subprocess
import threading
import time
import json
import os
from .scripts import utilities
from .scripts import interface_reading as reading
from .scripts import interface_writing as writing


CREATE_NO_WINDOW = 0x08000000

DOCS = [
    "about",
    "charts-mkiv",
    "colors-mkiv",
    "columnsets",
    "details",
    "epub-mkiv",
    "epub-mkiv-demo",
    "hybrid",
    "languages-mkiv",
    "lua-mkiv",
    "luatex",
    "ma-cb-en",
    "math-mkiv",
    "mk",
    "mmlexamp",
    "mmlprime",
    "mreadme",
    "rules-mkiv",
    "spacing-mkiv",
    "spreadsheets-mkiv",
    "sql-mkiv",
    "steps-mkiv",
    "still",
    "swiglib-mkiv",
    "templates-mkiv",
    "tiptrick",
    "tools-mkiv",
    "units-mkiv",
    "workflows-mkiv",
    "xml-mkiv",
    "xtables-mkiv",
]


class SimpleContextForceBuildInterface(sublime_plugin.WindowCommand):
    def reload_settings(self):
        utilities.reload_settings(self)
        self.name = utilities.file_as_slug(self._path)

    def run(self):
        self.reload_settings()
        thread = threading.Thread(target=self.build_interface)
        thread.start()

    def build_interface(self):
        print(
            "simple_ConTeXt: force building interface (warning: is slow) ..."
        )
        start_time = time.time()
        loader = reading.InterfaceLoader()
        loader.load(self._path, passes=3, modules=True)
        file = os.path.join(
            sublime.packages_path(),
            "simple_ConTeXt",
            "interface",
            "commands_{}.json".format(self.name)
        )
        with open(file, encoding="utf-8", mode="w") as f:
            json.dump(loader.encode(), f)
        print(
            "simple_ConTeXt: done building interface, took {:.1f}s"
            .format(time.time() - start_time)
        )


class SimpleContextTestPopUps(sublime_plugin.WindowCommand):
    def reload_settings(self):
        utilities.reload_settings(self)
        self.name = utilities.file_as_slug(self._path)

    def run(self):
        self.reload_settings()
        thread = threading.Thread(target=self.test_pop_ups)
        thread.start()

    def test_pop_ups(self):
        print("simple_ConTeXt: testing pop-ups ...")
        start_time = time.time()
        pop_ups = self.settings.get("pop_ups", {})
        file = os.path.join(
            sublime.packages_path(),
            "simple_ConTeXt",
            "interface",
            "commands_{}.json".format(self.name)
        )
        with open(file, encoding="utf-8") as f:
            j = json.load(f)
            details = j["details"]
            files = j["files"]
        write = writing.InterfaceWriter()
        n = 0
        for name, cmd in details.items():
            n += 1
            write.render(name, cmd, files, **pop_ups)
        print(
            "simple_ConTeXt: done testing {} pop-ups, took {:.1f}s"
            .format(n, time.time() - start_time)
        )


class SimpleContextFindDocs(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.docs = DOCS

    def reload_settings(self):
        utilities.reload_settings(self)
        self.viewer = self._PDF.get("viewer")
        self.flags = CREATE_NO_WINDOW if sublime.platform() == "windows" else 0

    def run(self):
        self.reload_settings()
        thread = threading.Thread(target=self.run_panel)
        thread.start()

    def run_panel(self, selected_index=0):
        self.window.show_quick_panel(
            self.docs + ["... look for other file"],
            self.run_handle,
            selected_index=selected_index
        )

    def run_handle(self, index):
        if 0 <= index < len(self.docs):
            self.open_doc(self.docs[index])
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
        print()
        if self.viewer:
            subprocess.Popen([self.viewer, file], creationflags=self.flags)
