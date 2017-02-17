import sublime
import sublime_plugin


class ContexttoolsProfileSelector(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def reload_settings(self):
        self.settings = sublime.load_settings("ConTeXtTools.sublime-settings")
        self.profile_names = [
            profile.get("name")
            for profile in self.settings.get("profiles", {})
        ]

    def run(self):
        self.reload_settings()
        self.window.show_quick_panel(
            [name for name in self.profile_names],
            self.select_profile,
            sublime.MONOSPACE_FONT & sublime.KEEP_OPEN_ON_FOCUS_LOST
        )

    def select_profile(self, index):
        if 0 <= index < len(self.profile_names):
            self.settings.set("current_profile", self.profile_names[index])
            sublime.save_settings("ConTeXtTools.sublime-settings")
