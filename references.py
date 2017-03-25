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
            "references", {}).get(
                "reference_regex", r"[a-zA-Z]+\:[a-zA-Z]+")

        references = set()
        view = self.window.active_view()

        definite_references = view.find_by_selector(
            "text.tex.context meta.other.reference.context")
        for region in definite_references:
            raw_ref = view.substr(region).strip()
            debraced_ref = re.match(r"\A{(.*?)}\Z", raw_ref)
            if debraced_ref:
                references.add(debraced_ref.group(1).strip())
            else:
                references.add(raw_ref.strip())

        potential_references = view.find_by_selector(
            "text.tex.context meta.brackets.context"
            " - meta.other.value.context")
        for region in potential_references:
            raw_ref = view.substr(region)
            ref_match = re.match(
                r"\A\s*\[(" + current_ref_regex + r")\]\s*\Z", raw_ref)
            if ref_match:
                references.add(ref_match.group(1).strip())

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
        return self.window.active_view().match_selector(0, "text.tex.context")


class ContexttoolsReferenceMacroEventListener(sublime_plugin.EventListener):
    def reload_settings(self):
        common.reload_settings(self)
        self.current_cmd_regex = self.current_profile.get(
            "references", {}).get(
                "command_regex", "[a-zA-Z]*ref")

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
