import sublime_plugin

from .scripts import utilities


class SimpleContextBuildOnSaveListener(
    utilities.BaseSettings, sublime_plugin.ViewEventListener,
):
    def on_post_save_async(self):
        self.reload_settings()
        if (
            self.is_visible_alt() and
            self.get_setting("builder/behaviour/auto/after_save")
        ):
            self.view.window().run_command(
                "simple_context_exec_main",
                {},
            )
