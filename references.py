import sublime
import sublime_plugin
import collections
import re
import os


PACKAGE = os.path.abspath(
    # os.path.join(sublime.packages_path(), "ConTeXtTools")
    os.path.dirname(__file__)
)


import sys
sys.path.insert(1, PACKAGE)
from scripts import common


DEFINITE_REF_SELECTOR = "meta.other.reference.context"

POSSIBLE_REF_SELECTOR = (
    "meta.brackets.context - (meta.other.reference.context, "
    "punctuation.section.brackets.begin.context, "
    "punctuation.section.brackets.end.context, variable.parameter.context, "
    "keyword.operator.assignment.context, meta.other.value.context)"
)


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

        regex = self.settings.get("references", {}).get(
            "reference_regex", r"[a-zA-Z_\.\-\:]+")
        cmd_regex = self.settings.get("references", {}).get(
            "command_regex", r"(in|at|about|[a-zA-Z]*ref)")

        self.references = collections.OrderedDict()
        view = self.window.active_view()

        for region in view.find_by_selector(DEFINITE_REF_SELECTOR):
            raw = view.substr(region).strip()
            if raw.startswith("{") and raw.endswith("}"):
                self.references[raw[1:-1]] = region
            else:
                self.references[raw] = region

        for region in view.find_by_selector(POSSIBLE_REF_SELECTOR):
            raw = view.substr(region).strip()
            ref_match = re.match(r"\A" + regex + r"\Z", raw)

            cmd = common.last_command_in_view(
                view, end=region.end()+1, skip=common._skip_args
            )
            if cmd:
                cmd_match = \
                    re.match(r"\A" + cmd_regex + r"\Z", view.substr(cmd)[1:])
            else:
                cmd_match = False

            if ref_match and not cmd_match:
                self.references[raw] = region

    def run(self):
        view = self.window.active_view()
        if common.is_context(view):
            self.reload_settings()
            self.ref_init_point = view.sel()[0].end()
            self.window.show_quick_panel(
                list(self.references.keys()),
                self.select_reference,
                on_highlight=self.highlight_reference
            )

    def highlight_reference(self, index):
        if 0 <= index < len(self.references):
            view = self.window.active_view()
            region = list(self.references.values())[index]
            view.sel().clear()
            view.sel().add(region)
            view.show(region)

    def select_reference(self, index):
        view = self.window.active_view()
        view.sel().clear()
        view.sel().add(self.ref_init_point)
        view.show(self.ref_init_point)
        if 0 <= index < len(self.references):
            ref = view.substr(list(self.references.values())[index])
            view.run_command(
                "contexttools_reference_insert", {"reference": ref}
            )

    def is_visible(self, *args):
        return common.is_context(self.window.active_view())


class ContexttoolsReferenceMacroEventListener(sublime_plugin.EventListener):
    def reload_settings(self):
        common.reload_settings(self)
        self.current_cmd_regex = self.settings.get(
            "references", {}).get("command_regex", r"[a-zA-Z]*ref")

    def on_modified_async(self, view):
        self.reload_settings()
        if not self.settings.get("references", {}).get("on"):
            return

        end = view.sel()[0].end()
        cmd = \
            common.last_command_in_view(view, end=end, skip=common._skip_args)
        if not cmd:
            return

        name = view.substr(cmd)[1:]
        if (
            view.match_selector(
                end-1, "punctuation.section.brackets.begin.context"
            ) and
            re.match(r"\A" + self.current_cmd_regex + r"\Z", name)
        ):
            view.window().run_command("contexttools_reference_selector")
