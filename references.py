import sublime
import sublime_plugin
import re
import copy


import sys
import os
sys.path.insert(1, os.path.abspath(os.path.dirname(__file__)))
from scripts import common


class ContexttoolsReferenceInsert(sublime_plugin.TextCommand):
    def run(self, edit, reference="ref"):
        to_add = []
        for region in self.view.sel():
            self.view.insert(edit, region.begin(), reference)
            len_ = region.begin() + len(reference) + 1
            to_add.append(sublime.Region(len_, len_))
        self.view.sel().clear()
        self.view.sel().add_all(to_add)


class ContexttoolsReferenceSelector(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_ref_regex = ""

    def reload_settings(self):
        try:
            self.settings = sublime.load_settings(
                "ConTeXtTools.sublime-settings")
            profile_name = self.settings.get("current_profile")

            for profile in self.settings.get("profiles", {}):
                if profile.get("name") == profile_name:
                    self.current_ref_regex = profile.get(
                        "references", {}).get("reference_regex")
                    break

        except TypeError:
            pass

        view = self.window.active_view()
        potential_references = view.find_by_selector(
            "text.tex.context meta.environment.list.context")

        refs = set()
        for region in potential_references:
            str_ = view.substr(region)
            main_match = re.match(
                r"\[(" + self.current_ref_regex + r")\]", str_)
            alt_match = re.match(
                r"\[.*?\breference=(" + self.current_ref_regex + r").*?\]",
                str_)
            if alt_match:
                refs.add(alt_match.group(1).strip())
            elif main_match:
                refs.add(main_match.group(1).strip())
        self.references = sorted(refs)

    def run(self):
        if common.is_context(self.window.active_view()):
            self.reload_settings()
            self.window.show_quick_panel(
                self.references, self.select_reference)

    def select_reference(self, index):
        if 0 <= index < len(self.references):
            self.window.active_view().run_command(
                "contexttools_reference_insert",
                {"reference": self.references[index]}
            )

    def is_visible(self, *args):
        return self.window.active_view().match_selector(
            0, "text.tex.context")


class ContexttoolsReferenceMacroEventListener(sublime_plugin.EventListener):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_cmd_regex = ""

    def on_modified(self, view):
        self.reload_settings()

        command_name, tail = common.last_command_in_region(
            view, sublime.Region(0, view.sel()[0].end()))

        if not command_name:
            return

        if (
            re.match(r"\A" + self.current_cmd_regex + r"\Z", command_name) and
            re.match(r"\A[^\S\n]*" + r"\[" + r"[^\S\n]*\Z", tail)
        ):
            view.window().run_command("contexttools_reference_selector")

    def reload_settings(self):
        try:
            self.settings = sublime.load_settings(
                "ConTeXtTools.sublime-settings")
            profile_name = self.settings.get("current_profile")

            for profile in self.settings.get("profiles", {}):
                if profile.get("name") == profile_name:
                    self.current_cmd_regex = profile.get(
                        "references", {}).get("command_regex")
                    break

        except TypeError:
            pass
