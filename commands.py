import sublime
import sublime_plugin
import threading
import time
import json
import os
from .scripts import utilities
from .scripts import interface_reading as reading
from .scripts import interface_writing as writing


class SimpleContextForceBuildInterface(sublime_plugin.WindowCommand):
    def reload_settings(self):
        utilities.reload_settings(self)
        self._path = self.settings.get("path")
        if self._path in self.paths:
            self._path = self.paths[self._path]
        self._name = utilities.file_as_slug(self._path)

    def run(self):
        self.reload_settings()
        thread = threading.Thread(target=self.build_interface)
        thread.start()

    def build_interface(self):
        print(
            "simple_ConTeXt: force building interface (warning: is slow) ..."
        )
        start_time = time.time()
        self.loader = reading.InterfaceLoader()
        self.loader.load(self._path, passes=3, modules=True)
        file = os.path.join(
            sublime.packages_path(),
            "simple_ConTeXt",
            "interface",
            "commands_{}.json".format(self._name)
        )
        with open(file, encoding="utf-8", mode="w") as f:
            json.dump(self.loader.encode(), f)
        print(
            "simple_ConTeXt: done building interface, took {:.1f}s"
            .format(time.time() - start_time)
        )


class SimpleContextTestPopUps(sublime_plugin.WindowCommand):
    def reload_settings(self):
        utilities.reload_settings(self)
        self._path = self.settings.get("path")
        if self._path in self.paths:
            self._path = self.paths[self._path]
        self._name = utilities.file_as_slug(self._path)

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
            "commands_{}.json".format(self._name)
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
