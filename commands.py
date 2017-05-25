import sublime
import sublime_plugin
import xml.etree.ElementTree as ET
import json
import collections
import os


PACKAGE = os.path.abspath(
    # os.path.join(sublime.packages_path(), "ConTeXtTools")
    os.path.dirname(__file__)
)


import sys
sys.path.insert(1, PACKAGE)
from scripts import common
from scripts import parsing


class ContexttoolsProfileSelector(sublime_plugin.WindowCommand):
    def reload_settings(self):
        common.reload_settings(self)

    def run(self):
        self.reload_settings()
        self.window.show_quick_panel(
            self.profile_names,
            self.select_profile,
            0,
            self.current_profile_index
        )

    def select_profile(self, index):
        if 0 <= index < len(self.profile_names):
            self.settings.set("current_profile", self.profile_names[index])
            sublime.save_settings("ConTeXtTools.sublime-settings")


class ContexttoolsGenerateInterface(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interface_names = []

    def reload_settings(self):
        common.reload_settings(self)
        self.interface_names = sorted(self.interfaces)

    def run(self):
        self.reload_settings()
        self.window.show_quick_panel(
            self.interface_names, self.generate_interface
        )

    def generate_interface(self, index):
        if not (0 <= index < len(self.interface_names)):
            return

        name = self.interface_names[index]
        interface = self.interfaces[name]

        main = interface.get("main")
        modules = interface.get("modules")
        if not main:
            return

        xml = parsing.collect(None, main)
        if modules:
            xml = parsing.collect(xml, modules)

        parsing.fix_tree(xml.getroot())
        commands = parsing.parse_context_tree(xml)
        parsing.simplify_commands(commands)

        path = os.path.join(PACKAGE, "interface")
        os.makedirs(path, exist_ok=True)

        with open(
            os.path.join(path, "commands {}.json".format(name)),
            mode="w",
            encoding="utf-8"
        ) as f:
            json.dump(commands, f, sort_keys=True)


class ContexttoolsQueryInterfaceCommands(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.json_files = collections.OrderedDict()
        self.choice = 0

    def reload_settings(self):
        common.reload_settings(self)

    def run(self):
        self.reload_settings()

        names = []
        for file in os.listdir(os.path.join(PACKAGE, "interface")):
            if file.endswith(".json") and file.startswith("commands "):
                names.append(file[9:-5])
        names = sorted(names)
        for name in sorted(names):
            self.json_files[name] = []

        self.window.show_quick_panel(
            list(self.json_files.keys()), self._run_choose)

    def _run_choose(self, index):
        if not (0 <= index < len(self.json_files)):
            return

        name = list(self.json_files.keys())[index]
        self.choice = name

        with open(
            os.path.join(PACKAGE, "interface", "commands {}.json".format(name))
        ) as f:
            f_ = json.load(f, object_pairs_hook=collections.OrderedDict)
            for cmd, details in f_.items():
                for var in details["syntax_variants"]:
                    self.json_files[name].append({"details": var, "name": cmd})
            self.window.show_quick_panel(
                [
                    "\\{} ".format(var["name"]) +
                    " ".join(d["rendering"] for d in var["details"])
                    for var in self.json_files[name]
                ],
                self._run_print,
                flags=sublime.MONOSPACE_FONT | sublime.KEEP_OPEN_ON_FOCUS_LOST
            )

    def _run_print(self, index):
        if (0 <= index < len(self.json_files[self.choice])):
            var = self.json_files[self.choice][index]
            self.window.run_command(
                "contexttools_interface_command_insert",
                {
                    "command":
                        "\\{} ".format(var["name"]) +
                        " ".join(d["rendering"] for d in var["details"])
                }
            )


class ContexttoolsInterfaceCommandInsert(sublime_plugin.TextCommand):
    def run(self, edit, command=""):
        for region in self.view.sel():
            self.view.insert(edit, region.begin(), command)
