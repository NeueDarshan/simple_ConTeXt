import sublime
import sublime_plugin
import collections
import json
import os


PACKAGE = os.path.abspath(
    # os.path.join(sublime.packages_path(), "ConTeXtTools")
    os.path.dirname(__file__)
)


import sys
sys.path.insert(1, PACKAGE)
from scripts import common
from scripts import parsing


def simplify(obj):
    if isinstance(obj, str):
        return obj
    elif isinstance(obj, dict):
        return ", ".join(obj)
    elif isinstance(obj, list):
        return ", ".join(tup[0] for tup in obj)
    else:
        return str(obj)


def _true_entry(list_):
    for tup in list_:
        if tup[1]:
            return tup[0]


class ContexttoolsSettingsController(sublime_plugin.WindowCommand):
    def reload_settings(self):
        common.reload_settings(self)

    def run(self):
        self.reload_settings()
        self.encode_settings()
        self._location = []
        self._history = {}
        self._run_panel()

    def _run_panel(self):
        self.window.show_quick_panel(
            self._flatten_current_level(),
            self._run_handle,
            selected_index=self._history.get(len(self._location), 0)
        )

    def _run_handle(self, index, selected_index=None):
        if index < 0:
            return

        self._history[len(self._location)] = index
        here = self._current_level()
        key = self._flatten_current_level()[index][0]

        if key == "..":
            self._location.pop()
            self._run_panel()
        else:
            value = here[key]
            self._location.append(key)

            if isinstance(value, bool):
                common.set_deep(
                    self._encoded_settings, self._location, not value
                )
                self._location.pop()
                self._save()
                self._run_panel()

            elif isinstance(value, int):
                self.window.show_input_panel(
                    "new integer",
                    str(value),
                    self._on_done,
                    self._on_change,
                    self._on_cancel,
                )

            elif isinstance(value, str):
                self.window.show_input_panel(
                    "new str",
                    str(value),
                    self._on_done,
                    self._on_change,
                    self._on_cancel,
                )

            elif isinstance(value, list):
                self._run_panel_special()

            else:
                self._run_panel()

    def _run_panel_special(self):
        self.window.show_quick_panel(
            self._flatten_current_level(),
            self._run_handle_special,
            selected_index=self._history.get(len(self._location), 0)
        )

    def _run_handle_special(self, index, selected_index=None):
        if index < 0:
            return

        self._history[len(self._location)] = index
        here = self._current_level()
        key = self._flatten_current_level()[index][0]

        if key == "..":
            self._location.pop()
            self._run_panel()
        else:
            common.set_deep(
                self._encoded_settings,
                self._location,
                sorted((tup[0], tup[0] == key) for tup in here)
            )
            self._save()
            self._run_panel_special()

    def _on_done(self, string):
        common.set_deep(
            self._encoded_settings, self._location, string
        )
        self._location.pop()
        self._save()
        self._run_panel()

    def _on_change(self, string):
        pass

    def _on_cancel(self):
        self._location.pop()
        self._run_panel()

    def _current_level(self):
        return common.get_deep(self._encoded_settings, self._location)

    def _flatten_current_level(self):
        if isinstance(self._current_level(), list):
            main = sorted(
                [tup[0], str(tup[1])] for tup in self._current_level()
            )
        else:
            main = sorted(
                [k, simplify(self._current_level()[k])]
                for k in self._current_level()
            )
        if len(self._location) > 0:
            return [["..", "↑ go back"]] + main
        else:
            return main

    def _save(self):
        self.decode_settings()
        self.sublime_settings.set("settings", self.settings)
        sublime.save_settings("ConTeXtTools.sublime-settings")
        self.reload_settings()
        self.encode_settings()

    def encode_settings(self):
        self._encoded_settings = self.settings

        interface = self.settings.get("interface")
        self._encoded_settings["interface"] = \
            [(k, k == interface) for k in self.interfaces]

        path = self.settings.get("program", {}).get("path")
        self._encoded_settings.setdefault("program", {})["path"] = \
            [(k, k == path) for k in self.program_paths]

        colour_scheme = self.settings.get(
            "pop_ups", {}).get("visuals", {}).get("colour_scheme")
        self._encoded_settings.setdefault(
            "pop_ups", {}).setdefault(
                "visuals", {})["colour_scheme"] = \
            [(k, k == colour_scheme) for k in self.colour_schemes]

        self._encoded_settings["setting_schemes"] = self.setting_schemes

    def decode_settings(self):
        self.settings["interface"] = \
            _true_entry(self._encoded_settings.get("interface"))
        self.settings["program"]["path"] = \
            _true_entry(self._encoded_settings.get("program", {}).get("path"))
        self.settings["pop_ups"]["visuals"]["colour_scheme"] = _true_entry(
            self._encoded_settings.get(
                "pop_ups", {}).get("visuals", {}).get("colour_scheme")
        )

class ContexttoolsGenerateInterface(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def reload_settings(self):
        common.reload_settings(self)

    def run(self):
        self.reload_settings()
        self.window.show_quick_panel(
            sorted(self.interfaces), self.generate_interface
        )

    def generate_interface(self, index):
        if not (0 <= index < len(self.interface_names)):
            return

        name = sorted(s for s in self.interfaces)[index]
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
            if file.startswith("commands ") and file.endswith(".json"):
                names.append(file[9:-5])
        names = sorted(names)
        for name in sorted(names):
            self.json_files[name] = []

        self.window.show_quick_panel(
            list(self.json_files.keys()), self._run_choose
        )

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
                    "\\{} {}".format(
                        var["name"],
                        " ".join(d["rendering"] for d in var["details"])
                    )
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
                    "command": "\\{} {}".format(
                        var["name"],
                        " ".join(d["rendering"] for d in var["details"])
                    )
                }
            )


class ContexttoolsInterfaceCommandInsert(sublime_plugin.TextCommand):
    def run(self, edit, command=""):
        for region in self.view.sel():
            self.view.insert(edit, region.begin(), command)
