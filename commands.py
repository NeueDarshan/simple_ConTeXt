import sublime
import sublime_plugin
import collections
import threading
import json
import os


PACKAGE = os.path.abspath(
    # os.path.join(sublime.packages_path(), "simple_ConTeXt")
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


class Choice:
    def __init__(self, options, choice=0):
        self.options = sorted(options)
        self.set(choice)

    def set(self, choice):
        if isinstance(choice, int):
            self.choice = choice
        else:
            try:
                self.choice = self.options.index(choice)
            except ValueError:
                self.choice = 0

    def get(self):
        return self.options[self.choice]

    def list(self, string=False):
        choice = self.get()
        if string:
            return [[k, str(k == choice)] for k in self.options]
        else:
            return [[k, k == choice] for k in self.options]

    def __str__(self):
        return ", ".join(self.options)


class SimpleContextSettingsController(sublime_plugin.WindowCommand):
    def reload_settings(self):
        common.reload_settings(self)

    def run(self):
        self.reload_settings()
        self.encode_settings()
        self._location = []
        self._last_scheme = None
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

        elif key == "setting_schemes":
            self._location.append(key)
            self._run_panel_scheme()

        else:
            value = here[key]
            self._location.append(key)

            if isinstance(value, bool):
                common.set_deep_safe(
                    self._encoded_settings, self._location, not value
                )
                self._location.pop()
                self._save()
                self._run_panel()

            elif isinstance(value, (int, float, str)):
                self.window.show_input_panel(
                    "new " + common.type_as_str(value),
                    str(value),
                    self._on_done,
                    self._on_change,
                    self._on_cancel,
                )

            elif isinstance(value, Choice):
                self._run_panel_choice()

            else:
                self._run_panel()

    def _run_panel_scheme(self):
        self.window.show_quick_panel(
            self._flatten_current_level(),
            self._run_handle_scheme,
            selected_index=self._history.get(len(self._location), 0)
        )

    def _run_handle_scheme(self, index):
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
            self._last_scheme = key
            self.decode_settings()
            for location, val in common.iter_deep(value):
                common.set_deep_safe(self.settings, location, val)
            self._save(decode=False)
            self._run_panel_scheme()

    def _run_panel_choice(self):
        self.window.show_quick_panel(
            self._flatten_current_level(),
            self._run_handle_choice,
            selected_index=self._history.get(len(self._location), 0)
        )

    def _run_handle_choice(self, index, selected_index=None):
        if index < 0:
            return

        self._history[len(self._location)] = index
        here = self._current_level()
        key = self._flatten_current_level()[index][0]

        if key == "..":
            self._location.pop()
            self._run_panel()
        else:
            here.set(key)
            common.set_deep_safe(self._encoded_settings, self._location, here)
            self._save()
            self._run_panel_choice()

    def _on_done(self, string, type_="str"):
        common.set_deep_safe(
            self._encoded_settings, self._location, common.guess_type(string)
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
        return common.get_deep_safe(self._encoded_settings, self._location)

    def _flatten_current_level(self):
        if len(self._location) > 0 and self._location[-1] == "setting_schemes":
            main = sorted(
                [k, "done" if k == self._last_scheme else "..."]
                for k in self._current_level()
            )
        elif isinstance(self._current_level(), Choice):
            main = self._current_level().list(string=True)
        else:
            main = sorted(
                [k, simplify(self._current_level()[k])]
                for k in self._current_level()
            )
        if len(self._location) > 0:
            return [["..", "↑ go back"]] + main
        else:
            return main

    def _save(self, decode=True):
        if decode:
            self.decode_settings()
        self.sublime_settings.set("settings", self.settings)
        sublime.save_settings("simple_ConTeXt.sublime-settings")
        self.reload_settings()
        self.encode_settings()

    def encode_settings(self):
        self._encoded_settings = self.settings

        interface = self.settings.get("pop_ups", {}).get("interface")
        self._encoded_settings.setdefault("pop_ups", {})["interface"] = \
            Choice(self.interfaces, choice=interface)

        path = self.settings.get("program", {}).get("path")
        self._encoded_settings.setdefault("program", {})["path"] = \
            Choice(self.program_paths, choice=path)

        colour_scheme = self.settings.get("pop_ups", {}).get("colour_scheme")
        self._encoded_settings.setdefault("pop_ups", {})["colour_scheme"] = \
            Choice(self.colour_schemes, choice=colour_scheme)

        self._encoded_settings["setting_schemes"] = self.setting_schemes

    def decode_settings(self):
        self.settings["pop_ups"]["interface"] = \
            self._encoded_settings.get("pop_ups", {}).get("interface").get()
        self.settings["program"]["path"] = \
            self._encoded_settings.get("program", {}).get("path").get()
        self.settings["pop_ups"]["colour_scheme"] = \
            self._encoded_settings.get(
                "pop_ups", {}).get("colour_scheme").get()
        del self.settings["setting_schemes"]


class SimpleContextGenerateInterface(sublime_plugin.WindowCommand):
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
        if not (0 <= index < len(self.interfaces)):
            return

        self.name = sorted(self.interfaces)[index]
        interface = self.interfaces[self.name]
        main = interface.get("main")
        modules = interface.get("modules")
        if not main:
            return

        self.xml = parsing.collect(None, main)
        if modules:
            self.xml = parsing.collect(self.xml, modules)

        thread = threading.Thread(target=self._run)
        thread.start()

    def _run(self):
        parsing.fix_tree(self.xml.getroot())
        commands = parsing.parse_context_tree(self.xml)
        parsing.simplify_commands(commands)
        path = os.path.join(PACKAGE, "interface")
        os.makedirs(path, exist_ok=True)

        with open(
            os.path.join(path, "commands_{}.json".format(self.name)),
            mode="w",
            encoding="utf-8"
        ) as f:
            json.dump(commands, f, sort_keys=True)


class SimpleContextQueryInterfaceCommands(sublime_plugin.WindowCommand):
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
                "simple_context_interface_command_insert",
                {
                    "command": "\\{} {}".format(
                        var["name"],
                        " ".join(d["rendering"] for d in var["details"])
                    )
                }
            )


class SimpleContextInterfaceCommandInsert(sublime_plugin.TextCommand):
    def run(self, edit, command=""):
        for region in self.view.sel():
            self.view.insert(edit, region.begin(), command)
