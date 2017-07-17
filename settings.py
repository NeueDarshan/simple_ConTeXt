import sublime
import sublime_plugin
from .scripts import utilities


def simplify(obj):
    if isinstance(obj, str):
        return obj
    elif isinstance(obj, dict):
        return " ".join(sorted(obj))
    elif isinstance(obj, list):
        return " ".join(tup[0] for tup in sorted(obj))
    else:
        return str(obj)


class Choice:
    def __init__(self, options, choice=0):
        self.options = sorted(options)
        self.set(choice)

    def set(self, choice):
        if isinstance(choice, int):
            self.choice = choice
        else:
            try:
                self.choice = self.options.index(choice)
            except ValueError:
                self.choice = 0

    def get(self):
        return self.options[self.choice]

    def to_list(self, string=False):
        choice = self.get()
        if string:
            return [[k, str(k == choice)] for k in self.options]
        else:
            return [[k, k == choice] for k in self.options]

    def __str__(self):
        return " ".join(self.options)


class SimpleContextSettingsController(sublime_plugin.WindowCommand):
    def reload_settings(self):
        utilities.reload_settings(self)

    def run(self):
        self.reload_settings()
        self.encode_settings()
        self._last_scheme = None
        self._location = []
        self._history = {}
        self._run_panel()

    def _run_panel(self):
        self.window.show_quick_panel(
            self._flatten_current_level(),
            self._run_handle,
            selected_index=self.get_history()
        )

    def _run_handle(self, index, selected_index=None):
        if index < 0:
            return

        self.set_history(index)
        here = self._current_level()
        key = self._flatten_current_level()[index][0]

        if key == "..":
            self._location.pop()
            self._run_panel()

        elif key == "setting_groups":
            self._location.append(key)
            self._run_panel_scheme()

        else:
            value = here[key]
            self._location.append(key)

            if isinstance(value, bool):
                utilities.set_deep_safe(
                    self._encoded_settings, self._location, not value
                )
                self._location.pop()
                self._save()
                self._run_panel()

            elif isinstance(value, (int, float, str)) or value is None:
                self.window.show_input_panel(
                    "new value",
                    str(value),
                    self._on_done,
                    self._on_change,
                    self._on_cancel,
                )

            elif isinstance(value, Choice):
                self._run_panel_choice()

            else:
                self._run_panel()

    def _run_panel_scheme(self):
        self.window.show_quick_panel(
            self._flatten_current_level(),
            self._run_handle_scheme,
            selected_index=self.get_history()
        )

    def _run_handle_scheme(self, index):
        if index < 0:
            return

        self.set_history(index)
        here = self._current_level()
        key = self._flatten_current_level()[index][0]

        if key == "..":
            self._location.pop()
            self._run_panel()
        else:
            value = here[key]
            self._last_scheme = key
            self.decode_settings()
            for location, val in utilities.iter_deep(value):
                utilities.set_deep_safe(self.settings, location, val)
            self._save(decode=False)
            self._run_panel_scheme()

    def _run_panel_choice(self):
        self.window.show_quick_panel(
            self._flatten_current_level(),
            self._run_handle_choice,
            selected_index=self.get_history()
        )

    def _run_handle_choice(self, index, selected_index=None):
        if index < 0:
            return

        self.set_history(index)
        here = self._current_level()
        key = self._flatten_current_level()[index][0]

        if key == "..":
            self._location.pop()
            self._run_panel()
        else:
            here.set(key)
            utilities.set_deep_safe(
                self._encoded_settings, self._location, here
            )
            self._save()
            self._run_panel_choice()

    def _on_done(self, string):
        utilities.set_deep_safe(
            self._encoded_settings,
            self._location,
            utilities.guess_type(string)
        )
        self._location.pop()
        self._save()
        self._run_panel()

    def _on_change(self, string):
        pass

    def _on_cancel(self):
        self._location.pop()
        self._run_panel()

    def _current_level(self):
        return utilities.get_deep_safe(self._encoded_settings, self._location)

    def _flatten_current_level(self):
        if len(self._location) > 0 and self._location[-1] == "setting_groups":
            main = [
                [k, "[✓]" if k == self._last_scheme else "[ ]"]
                for k in sorted(self._current_level())
            ]
        elif isinstance(self._current_level(), Choice):
            main = self._current_level().to_list(string=True)
        else:
            main = [
                [k, simplify(self._current_level()[k])]
                for k in sorted(self._current_level())
            ]
        if len(self._location) > 0:
            if len(self._location) > 1:
                prev = "/" + "/".join(self._location[:-1])
            else:
                prev = "root"
            return [["..", '↑ go back to "{}"'.format(prev)]] + main
        else:
            return main

    def get_history(self):
        return self._history.get(len(self._location), 0)

    def set_history(self, index):
        self._history[len(self._location)] = index

    def _save(self, decode=True):
        if decode:
            self.decode_settings()
        self.sublime_settings.set("settings", self.settings)
        sublime.save_settings("simple_ConTeXt.sublime-settings")
        self.reload_settings()
        self.encode_settings()

    def encode_settings(self):
        self._encoded_settings = self.settings
        self._encoded_settings["path"] = Choice(
            self.paths, choice=self.settings.get("path")
        )
        self._encoded_settings["setting_groups"] = self.setting_groups

    def decode_settings(self):
        self.settings["path"] = self._encoded_settings["path"].get()
        del self.settings["setting_groups"]
