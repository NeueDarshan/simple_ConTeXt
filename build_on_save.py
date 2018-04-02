import sublime_plugin

from .scripts import utilities
from .scripts import scopes


class SimpleContextBuildOnSaveListener(sublime_plugin.ViewEventListener):
    def reload_settings(self):
        utilities.reload_settings(self)

    def is_visible(self):
        return scopes.is_context(self.view)

    def on_post_save_async(self):
        self.reload_settings()
        if (
            self.is_visible() and
            self._behaviour.get("auto_build", {}).get("after_save")
        ):
            self.view.window().run_command("build")
