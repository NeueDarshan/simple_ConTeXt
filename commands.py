import sublime
import sublime_plugin
import subprocess
import json


import sys
import os
sys.path.insert(1, os.path.abspath(os.path.dirname(__file__)))
# from scripts import parsing
from scripts import common


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

        return

        # name_ = self.profile_names[index]
        # chosen_profile = {}
        # for profile in self.settings.get("profiles", {}):
        #     if profile.get("name") == name_:
        #         chosen_profile = profile
        #         break
        # name = "context-en-{}.xml".format(name_)

        # os.chdir(os.path.join(
        #     sublime.packages_path(), "ConTeXtTools", "scripts"))
        # common.prep_environ_path(chosen_profile)

        # subprocess.call(["context", "--extra=setups", "--overview", "--save"])
        # os.remove("context-extra.pdf")
        # os.rename("context-en.xml", name)

        # structured_commands = parsing.parse_context_tree(
        #     name, pre_process=parsing.fix_context_tree_2016)
        # os.remove(name)

        # parsing.simplify_commands(structured_commands)
        # flat_commands = parsing.rendered_command_dict(structured_commands)
        # with open("commands {}.json".format(name_), mode="w") as f:
        #     json.dump(flat_commands, f, sort_keys=True, indent=2)
