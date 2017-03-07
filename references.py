import sublime
import sublime_plugin
import re


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
    def reload_settings(self):
        common.reload_settings(self)
        current_ref_regex = self.current_profile.get(
            "references", {}).get("reference_regex", "[a-zA-Z]+:[a-zA-Z:-_]+")

        view = self.window.active_view()
        potential_references = view.find_by_selector(
            "text.tex.context meta.environment.list.context")

        references = set()
        for region in potential_references:
            potential_ref = view.substr(region)
            main_match = re.match(
                r"\[(" + current_ref_regex + r")\]", potential_ref)
            alt_match = re.match(
                r"\[.*?\breference=(" + current_ref_regex + r").*?\]",
                potential_ref)
            if alt_match:
                references.add(alt_match.group(1).strip())
            elif main_match:
                references.add(main_match.group(1).strip())

        self.references = sorted(references)

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
    def reload_settings(self):
        common.reload_settings(self)
        self.current_cmd_regex = self.current_profile.get(
            "references", {}).get("command_regex", "[a-zA-Z]*ref")

    def on_modified(self, view):
        self.reload_settings()

        command_name, tail = common.last_command_in_region(
            view, sublime.Region(0, view.sel()[0].end()))

        if (
            command_name and
            re.match(r"\A" + self.current_cmd_regex + r"\Z", command_name) and
            re.match(r"\A[^\S\n]*\[[^\S\n]*\Z", tail)
        ):
            view.window().run_command("contexttools_reference_selector")
