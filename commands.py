import sublime
import sublime_plugin
import xml.etree.ElementTree as ET
import json


import sys
import os
sys.path.insert(1, os.path.abspath(os.path.dirname(__file__)))
from scripts import common
from scripts import parsing


def _collect(xml, path):
    for f_ in os.listdir(os.path.abspath(os.path.normpath(path))):
        with open(os.path.join(path, f_), encoding="utf-8") as f:

            try:
                if not f_.endswith(".xml"):
                    pass
                elif f_ in ["i-context.xml", "i-common-definitions.xml"]:
                    pass
                elif xml is None:
                    xml = ET.parse(f)
                else:
                    root = xml.getroot()
                    for e in ET.parse(f).getroot():
                        if f_.startswith("i-common"):
                            root.append(e)
                        elif e.attrib.get("file") is not None:
                            root.append(e)
                        else:
                            e.set("file", f_)
                            root.append(e)

            except ET.ParseError as err:
                msg = "error '{}' occurred whilst processing file '{}'" \
                    " located at '{}'"
                print(msg.format(err, f_, path))

    return xml


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
            self.interface_names, self.generate_interface)

    def generate_interface(self, index):
        if not (0 <= index < len(self.interface_names)):
            return

        name = self.interface_names[index]
        interface = self.interfaces[name]

        main = interface.get("main")
        modules = interface.get("modules")
        if not main:
            return

        xml = _collect(None, main)
        if modules:
            xml = _collect(xml, modules)

        parsing.fix_tree(xml.getroot())
        commands = parsing.parse_context_tree(xml)
        parsing.simplify_commands(commands)

        out_file = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "interface",
            "commands {}.json".format(name))
        with open(out_file, mode="w", encoding="utf-8") as f:
            json.dump(commands, f, sort_keys=True)


class ContexttoolsQueryInterfaceCommands(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.json_names = []
        self.json_commands = []

    def reload_settings(self):
        common.reload_settings(self)

    def run(self):
        self.reload_settings()

        self.json_names = []
        for file in os.listdir(os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "interface"
        )):
            if file.endswith(".json") and file.startswith("commands "):
                self.json_names.append(file[9:-5])
        self.json_names = sorted(self.json_names)
        self.window.show_quick_panel(self.json_names, self._run_choose)

    def _run_choose(self, index):
        if not (0 <= index < len(self.json_names)):
            return

        with open(
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                "interface",
                "commands {}.json".format(self.json_names[index])
            )
        ) as f:
            set_ = set()
            for name, details in json.load(f).items():
                for var in details["syntax_variants"]:
                    set_.add(
                        "\\{} ".format(name) +
                        " ".join(arg["rendering"] for arg in var)
                    )
            self.json_commands = sorted(set_)
            self.window.show_quick_panel(
                self.json_commands,
                self._run_print,
                flags=sublime.MONOSPACE_FONT | sublime.KEEP_OPEN_ON_FOCUS_LOST
            )

    def _run_print(self, index):
        if (0 <= index < len(self.json_commands)):
            self.window.run_command(
                "contexttools_interface_command_insert",
                {"command": self.json_commands[index]}
            )


class ContexttoolsInterfaceCommandInsert(sublime_plugin.TextCommand):
    def run(self, edit, command):
        for region in self.view.sel():
            self.view.insert(edit, region.begin(), command)


# class ContexttoolsQueryReferences(sublime_plugin.WindowCommand):
#     ...
