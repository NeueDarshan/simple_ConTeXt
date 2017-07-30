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
        self.last_scheme = None
        self.location = []
        self.history = {}
        self.run_panel()

    def run_panel(self):
        self.window.show_quick_panel(
            self.flatten_current_level(),
            self.run_handle,
            selected_index=self.get_history()
        )

    def run_handle(self, index):
        if index < 0:
            return

        self.set_history(index)
        here = self.current_level()
        key = self.flatten_current_level()[index][0]

        if key == "..":
            self.location.pop()
            self.run_panel()

        elif key == "setting_groups":
            self.location.append(key)
            self.run_panel_scheme()

        else:
            value = here[key]
            self.location.append(key)

            if isinstance(value, bool):
                utilities.set_deep_safe(
                    self.encoded_settings, self.location, not value
                )
                self.location.pop()
                self.save()
                self.run_panel()

            elif isinstance(value, (int, float, str)) or value is None:
                self.window.show_input_panel(
                    "new value",
                    str(value),
                    self.on_done,
                    self.on_change,
                    self.on_cancel,
                )

            elif isinstance(value, Choice):
                self.run_panel_choice()

            else:
                self.run_panel()

    def run_panel_scheme(self):
        self.window.show_quick_panel(
            self.flatten_current_level(),
            self.run_handle_scheme,
            selected_index=self.get_history()
        )

    def run_handle_scheme(self, index):
        if index < 0:
            return

        self.set_history(index)
        here = self.current_level()
        key = self.flatten_current_level()[index][0]

        if key == "..":
            self.location.pop()
            self.run_panel()
        else:
            value = here[key]
            self.last_scheme = key
            self.decode_settings()
            for location, val in utilities.iter_deep(value):
                utilities.set_deep_safe(self._settings, location, val)
            self.save(decode=False)
            self.run_panel_scheme()

    def run_panel_choice(self):
        self.window.show_quick_panel(
            self.flatten_current_level(),
            self.run_handle_choice,
            selected_index=self.get_history()
        )

    def run_handle_choice(self, index):
        if index < 0:
            return

        self.set_history(index)
        here = self.current_level()
        key = self.flatten_current_level()[index][0]

        if key == "..":
            self.location.pop()
            self.run_panel()
        else:
            here.set(key)
            utilities.set_deep_safe(
                self.encoded_settings, self.location, here
            )
            self.save()
            self.run_panel_choice()

    def on_done(self, string):
        utilities.set_deep_safe(
            self.encoded_settings,
            self.location,
            utilities.guess_type(string)
        )
        self.location.pop()
        self.save()
        self.run_panel()

    def on_change(self, string):
        pass

    def on_cancel(self):
        self.location.pop()
        self.run_panel()

    def current_level(self):
        return utilities.get_deep_safe(self.encoded_settings, self.location)

    def flatten_current_level(self):
        if len(self.location) > 0 and self.location[-1] == "setting_groups":
            main = [
                [k, "[✓]" if k == self.last_scheme else "[ ]"]
                for k in sorted(self.current_level())
            ]
        elif isinstance(self.current_level(), Choice):
            main = self.current_level().to_list(string=True)
        else:
            main = [
                [k, simplify(self.current_level()[k])]
                for k in sorted(self.current_level())
            ]
        if len(self.location) > 0:
            if len(self.location) > 1:
                prev = "/" + "/".join(self.location[:-1])
            else:
                prev = "root"
            return [["..", '↑ go back to "{}"'.format(prev)]] + main
        else:
            return main

    def get_history(self):
        return self.history.get(len(self.location), 0)

    def set_history(self, index):
        self.history[len(self.location)] = index

    def save(self, decode=True):
        if decode:
            self.decode_settings()
        self._sublime_settings.set("settings", self._settings)
        sublime.save_settings("simple_ConTeXt.sublime-settings")
        self.reload_settings()
        self.encode_settings()

    def encode_settings(self):
        self.encoded_settings = self._settings
        self.encoded_settings["path"] = Choice(
            self._paths, choice=self._settings.get("path")
        )
        self.encoded_settings.setdefault("PDF", {})["viewer"] = Choice(
            self._PDF_viewers,
            choice=self._settings.get("PDF", {}).get("viewer")
        )
        self.encoded_settings["setting_groups"] = self._setting_groups

    def decode_settings(self):
        self._settings["path"] = self.encoded_settings["path"].get()
        self._settings.get("PDF", {})["viewer"] = \
            self.encoded_settings["PDF"]["viewer"].get()
        del self._settings["setting_groups"]
