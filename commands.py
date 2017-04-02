import sublime
import sublime_plugin
import subprocess
import json


import sys
import os
sys.path.insert(1, os.path.abspath(os.path.dirname(__file__)))
from scripts import common
from scripts import parsing


class ContexttoolsProfileSelector(sublime_plugin.WindowCommand):
    def reload_settings(self):
        common.reload_settings(self)

    def run(self):
        self.reload_settings()
        self.window.show_quick_panel(
            [name for name in self.profile_names],
            self.select_profile,
            0,
            self.current_profile_index
        )

    def select_profile(self, index):
        if 0 <= index < len(self.profile_names):
            self.settings.set("current_profile", self.profile_names[index])
            sublime.save_settings("ConTeXtTools.sublime-settings")


class ContexttoolsGenerateInterface(sublime_plugin.WindowCommand):
    def reload_settings(self):
        common.reload_settings(self)

    def run(self):
        self.reload_settings()
        self.window.show_quick_panel(
            [name for name in self.profile_names],
            self.generate_interface)

    def generate_interface(self, index):
        if not (0 <= index < len(self.profile_names)):
            return

        name = self.profile_names[index]
        self.settings.set("current_profile", name)
        self.reload_settings()

        context = self.current_profile.get("context_program", {})
        command = context.get("name", "context")
        options = context.get("options", {})
        version = self.current_profile.get(
            "command_popups", {}).get("version", name)
        common.deep_update(
            options,
            {
                "extra": "setups",
                "overview": True,
                "save": True
            }
        )
        command = common.process_options(command, options, None, None)
        os.chdir(os.path.join(
            sublime.packages_path(), "ConTeXtTools", "interface"))

        path = self.current_profile.get("context_program", {}).get("path")
        with common.ModPath(path):
            subprocess.call(command)
            os.remove("context-extra.pdf")
            os.rename("context-en.xml", "context-en-{}.xml".format(version))

            structured_commands = parsing.parse_context_tree(
                "context-en-{}.xml".format(version),
                pre_process=parsing.fix_tree)
            parsing.simplify_commands(structured_commands)
            flat_commands = parsing.rendered_command_dict(structured_commands)
            with open("commands-en-{}.json".format(version), mode="w") as f:
                json.dump(flat_commands, f, sort_keys=True, indent=2)
