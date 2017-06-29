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


def _flatten(s, k, v):
    if k == "interface":
        return [k, ", ".join(sorted(s.get("interfaces", {})))]
    elif k == "path":
        return [k, ", ".join(sorted(s.get("program_paths", {})))]
    elif k == "colour_schemes":
        return [k, ", ".join(sorted(s.get("colour_schemes", {})))]
    elif isinstance(v, str):
        return [k, v]
    elif hasattr(v, "__iter__"):
        return [k, ", ".join(sorted(v))]
    else:
        return [k, str(v)]


class ContexttoolsSettingsController(sublime_plugin.WindowCommand):
    def reload_settings(self):
        common.reload_settings(self)

    def run(self):
        self.reload_settings()
        self.choices = {}
        self._run_zero()

    def _run_zero(self, selected_index=0):
        self.window.show_quick_panel(
            sorted(
                _flatten(self.sublime_settings, k, v)
                for k, v in self.settings.items()
            ),
            self._run_one,
            selected_index=selected_index,
        )

    def _run_one(self, index, selected_index=0):
        dict_ = self.settings
        if not 0 <= index < len(dict_):
            return

        key = sorted(dict_)[index]
        val = dict_[key]
        self.choices[0] = [index, key]

        if key == "interface":
            return self.window.show_quick_panel(
                [["..", "↑ go back"]] +
                sorted(
                    [k, str(k == self.settings.get("interface"))]
                    for k in self.interfaces
                ),
                self._run_two_interface,
                selected_index=selected_index
            )

        self.window.show_quick_panel(
            [["..", "↑ go back"]] +
            sorted(
                _flatten(self.sublime_settings, k, v) for k, v in val.items()
            ),
            self._run_two,
            selected_index=selected_index
        )

    def _run_two_interface(self, index, selected_index=0):
        if index == 0:
            return self._run_zero(selected_index=self.choices[0][0])

        index -= 1
        dict_ = self.interfaces
        if not 0 <= index < len(dict_):
            return

        key = sorted(dict_)[index]
        self.choices[1] = [index, key]

        self.settings["interface"] = key
        self.sublime_settings.set("settings", self.settings)
        sublime.save_settings("ConTeXtTools.sublime-settings")
        self.reload_settings()
        return self._run_one(self.choices[0][0], selected_index=index+1)

    def _run_two(self, index, selected_index=0):
        if index == 0:
            return self._run_zero(selected_index=self.choices[0][0])

        index -= 1
        dict_ = self.settings[self.choices[0][1]]
        if not 0 <= index < len(dict_):
            return

        key = sorted(dict_)[index]
        val = dict_[key]
        self.choices[1] = [index, key]

        if isinstance(val, bool):
            self.settings[self.choices[0][1]][key] = not val
            self.sublime_settings.set("settings", self.settings)
            sublime.save_settings("ConTeXtTools.sublime-settings")
            self.reload_settings()
            return self._run_one(self.choices[0][0], selected_index=index+1)

        elif isinstance(val, str):
            if key == "path":
                path = self.settings.get("program", {}).get("path")
                return self.window.show_quick_panel(
                    [["..", "↑ go back"]] +
                    sorted([k, str(k == path)] for k in self.program_paths),
                    self._run_three_path,
                    selected_index=selected_index
                )
            else:
                captions = {
                    "name": "new program name",
                    "command_regex": "new regex",
                    "reference_regex": "new regex",
                    "default": "new string"
                }
                return self.window.show_input_panel(
                    captions.get(key, "default"),
                    val,
                    lambda string: self._run_three_str_done(
                        string, selected_index=index+1
                    ),
                    self._run_three_str_change,
                    lambda: self._run_three_str_cancel(selected_index=index+1),
                )

        self.window.show_quick_panel(
            [["..", "↑ go back"]] +
            sorted(
                _flatten(self.sublime_settings, k, v) for k, v in val.items()
            ),
            self._run_three,
            selected_index=selected_index
        )

    def _run_three_path(self, index, selected_index=0):
        if index == 0:
            return self._run_one(
                1 + self.choices[1][0], selected_index=1+self.choices[1][0]
            )

        index -= 1
        dict_ = self.program_paths
        if not 0 <= index < len(dict_):
            return

        key = sorted(dict_)[index]
        self.choices[2] = [index, key]

        self.settings["program"]["path"] = key
        self.sublime_settings.set("settings", self.settings)
        sublime.save_settings("ConTeXtTools.sublime-settings")
        self.reload_settings()
        return self._run_two(1 + self.choices[1][0], selected_index=index+1)

    def _run_three_str_change(self, string):
        pass

    def _run_three_str_cancel(self, selected_index=0):
        return self._run_one(self.choices[0][0], selected_index=selected_index)

    def _run_three_str_done(self, string, selected_index=0):
        self.settings[self.choices[0][1]][self.choices[1][1]] = string
        self.sublime_settings.set("settings", self.settings)
        sublime.save_settings("ConTeXtTools.sublime-settings")
        self.reload_settings()
        return self._run_one(
            self.choices[0][0], selected_index=selected_index
        )

    def _run_three(self, index, selected_index=0):
        if index == 0:
            return self._run_one(1 + self.choices[1][0])

        index -= 1
        dict_ = self.settings[self.choices[0][1]][self.choices[1][1]]
        if not 0 <= index < len(dict_):
            return

        key = sorted(dict_)[index]
        val = dict_[key]
        self.choices[2] = [index, key]

        if isinstance(val, bool):
            self.settings[self.choices[0][1]][self.choices[1][1]][key] = \
                not val
            self.sublime_settings.set("settings", self.settings)
            sublime.save_settings("ConTeXtTools.sublime-settings")
            self.reload_settings()
            return self._run_two(
                1 + self.choices[1][0], selected_index=index+1
            )

        # elif isinstance(val, str):
        #     if key == "path":
        #         path = self.settings.get("program", {}).get("path")
        #         return self.window.show_quick_panel(
        #             [["..", "↑ go back"]] +
        #             sorted([k, str(k == path)] for k in self.program_paths),
        #             self._run_three_path,
        #             selected_index=selected_index
        #         )
        #     else:
        #         captions = {
        #             "name": "new program name",
        #             "command_regex": "new regex",
        #             "reference_regex": "new regex",
        #             "default": "new string"
        #         }
        #         return self.window.show_input_panel(
        #             captions.get(key, "default"),
        #             val,
        #             lambda string: self._run_three_str_done(
        #                 string, selected_index=index+1
        #             ),
        #             self._run_three_str_change,
        #             lambda: self._run_three_str_cancel(selected_index=index+1),
        #         )

        # self.window.show_quick_panel(
        #     [["..", "↑ go back"]] +
        #     sorted(
        #         _flatten(self.sublime_settings, k, v) for k, v in val.items()
        #     ),
        #     self._run_three,
        #     selected_index=selected_index
        # )


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
