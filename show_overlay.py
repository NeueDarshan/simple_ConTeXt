import sublime_plugin
from .scripts import utilities
from .scripts import scopes


class SimpleContextShowOverlayCommand(sublime_plugin.WindowCommand):
    def reload_settings(self):
        utilities.reload_settings(self)
        self.view = self.window.active_view()
        self.scopes = {
            "reference": scopes.REFERENCE,
            "definition": scopes.DEFINE,
            "file_name": scopes.FILE_NAME,
        }

    def is_visible(self):
        return scopes.is_context(self.view)

    def run(self, scope="reference", scope_raw=None):
        self.reload_settings()
        self.matches = sorted(
            self.view.find_by_selector(
                scope_raw if scope_raw is not None else
                self.scopes.get(scope, scopes.REFERENCE)
            ),
            key=lambda region: region.begin(),
        )
        self.window.show_quick_panel(
            [self.view.substr(region) for region in self.matches],
            self.on_done,
            on_highlight=self.on_highlight
        )

    def on_done(self, index):
        pass

    def on_highlight(self, index):
        if 0 <= index < len(self.matches):
            print(self.matches[index])
            # pass

    def select_reference(self, index):
        pass
