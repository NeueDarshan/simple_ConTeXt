import sublime
import sublime_plugin
import collections
from .scripts import utilities
from .scripts import scopes


class SimpleContextReferenceInsert(sublime_plugin.TextCommand):
    def run(self, edit, reference="ref"):
        to_add = []
        for region in self.view.sel():
            self.view.insert(edit, region.begin(), reference)
            len_ = region.begin() + len(reference) + 1
            to_add.append(sublime.Region(len_, len_))
        self.view.sel().clear()
        self.view.sel().add_all(to_add)


class SimpleContextReferenceSelector(sublime_plugin.WindowCommand):
    def reload_settings(self):
        utilities.reload_settings(self)
        self.references = collections.OrderedDict()
        view = self.window.active_view()
        for region in view.find_by_selector(scopes.REFERENCE):
            raw = view.substr(region).strip()
            if raw.startswith("{") and raw.endswith("}"):
                self.references[raw[1:-1]] = region
            else:
                self.references[raw] = region

    def is_visible(self):
        return scopes.is_context(self.window.active_view())

    def run(self):
        self.reload_settings()
        self.ref_init_point = self.window.active_view().sel()[0].end()
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
                "simple_context_reference_insert", {"reference": ref}
            )


class SimpleContextReferenceMacroEventListener(sublime_plugin.EventListener):
    def reload_settings(self):
        utilities.reload_settings(self)

    def on_modified_async(self, view):
        self.reload_settings()
        if not self._references.get("on"):
            return

        # end = view.sel()[0].end()
        # cmd = scopes.last_block_in_region(
        #     view,
        #     end - 500,
        #     end,
        #     scopes.CONTROL_WORD,
        #     skip=scopes.SKIP_ARGS_AND_SPACES
        # )
        # if cmd and view.match_selector(end - 1, scopes.BEGIN_BRACKET):
        #     view.window().run_command("simple_context_reference_selector")
