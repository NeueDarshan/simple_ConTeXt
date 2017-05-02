import sublime
import sublime_plugin
import re
import os


PACKAGE = os.path.abspath(
    # os.path.join(sublime.packages_path(), "ConTeXtTools")
    os.path.dirname(__file__)
)


import sys
sys.path.insert(1, PACKAGE)
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

        refs = set()
        view = self.window.active_view()

        definite_refs = view.find_by_selector("meta.other.reference.context")
        for region in definite_refs:
            raw_ref = view.substr(region).strip()
            debraced_ref = re.match(r"\A{(.*?)}\Z", raw_ref)
            if debraced_ref:
                refs.add(debraced_ref.group(1).strip())
            else:
                refs.add(raw_ref.strip())

        potential_refs = view.find_by_selector(
            "meta.brackets.context - meta.other.value.context"
        )
        for region in potential_refs:
            raw_ref = view.substr(region)
            ref_match = re.match(
                r"\A\s*\[(" + current_ref_regex + r")\]\s*\Z", raw_ref
            )
            if ref_match:
                refs.add(ref_match.group(1).strip())

        self.references = sorted(refs)

    def run(self):
        if common.is_context(self.window.active_view()):
            self.reload_settings()
            self.window.show_quick_panel(
                self.references, self.select_reference
            )

    def select_reference(self, index):
        if 0 <= index < len(self.references):
            self.window.active_view().run_command(
                "contexttools_reference_insert",
                {"reference": self.references[index]}
            )

    def is_visible(self, *args):
        return common.is_context(self.window.active_view())


class ContexttoolsReferenceMacroEventListener(sublime_plugin.EventListener):
    def reload_settings(self):
        common.reload_settings(self)
        self.current_cmd_regex = self.current_profile.get(
            "references", {}).get("command_regex", "[a-zA-Z]*ref")

    def on_modified(self, view):
        self.reload_settings()

        end = view.sel()[0].end()
        cmd = common.last_command_in_view(view, begin=max(0, end-100), end=end)
        if not cmd:
            return

        name = view.substr(cmd)[1:]
        tail = view.substr(sublime.Region(cmd.end(), end))
        if (
            re.match(r"\A" + self.current_cmd_regex + r"\Z", name) and
            re.match(r"\A[^\S\n]*\[[^\S\n]*\Z", tail)
        ):
            view.window().run_command("contexttools_reference_selector")
