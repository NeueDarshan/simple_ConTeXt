import sublime
import sublime_plugin

from .scripts import utilities
from .scripts import deep_dict


def simplify(obj):
    if isinstance(obj, str):
        return obj
    elif isinstance(obj, dict):
        return " ".join(sorted(obj))
    elif isinstance(obj, list):
        return " ".join(tup[0] for tup in sorted(obj))
    else:
        return str(obj)


class SimpleContextSettingsControllerCommand(sublime_plugin.WindowCommand):
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

            #D It's nice to be able to quickly toggle booleans, but we also
            #D want the option to change a boolean into, say, a string. So we
            #D do this compromise.
            if isinstance(value, bool):
                self.window.show_input_panel(
                    "new value:",
                    str(not value),
                    self.on_done,
                    self.on_change,
                    self.on_cancel,
                )

            elif isinstance(value, (int, float, str)) or value is None:
                self.window.show_input_panel(
                    "new value:",
                    str(value),
                    self.on_done,
                    self.on_change,
                    self.on_cancel,
                )

            elif isinstance(value, utilities.Choice):
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
            for location, val in deep_dict.iter_(value):
                deep_dict.set_safe(self._settings, location, val)
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
            deep_dict.set_safe(self.encoded_settings, self.location, here)
            self.save()
            self.run_panel_choice()

    def on_done(self, text):
        deep_dict.set_safe(
            self.encoded_settings, self.location, utilities.guess_type(text)
        )
        self.location.pop()
        self.save()
        self.run_panel()

    def on_change(self, text):
        pass

    def on_cancel(self):
        self.location.pop()
        self.run_panel()

    def current_level(self):
        return deep_dict.get_safe(self.encoded_settings, self.location)

    def flatten_current_level(self):
        if len(self.location) > 0 and self.location[-1] == "setting_groups":
            main = [
                [k, "[✓]" if k == self.last_scheme else "[ ]"]
                for k in sorted(self.current_level())
            ]
        elif isinstance(self.current_level(), utilities.Choice):
            main = self.current_level().to_list(string=True)
        else:
            main = [
                [k, simplify(self.current_level()[k])]
                for k in sorted(self.current_level())
            ]
        if len(self.location) > 0:
            return [["..", "in /{}/".format("/".join(self.location))]] + main
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
        self.encoded_settings["path"] = \
            utilities.Choice(self._paths, choice=self._settings.get("path"))
        viewer = utilities.Choice(
            self._PDF_viewers,
            choice=self._settings.get("PDF", {}).get("viewer")
        )
        self.encoded_settings.setdefault("PDF", {})["viewer"] = viewer
        self.encoded_settings["setting_groups"] = self._setting_groups

    def decode_settings(self):
        self._settings["path"] = self.encoded_settings["path"].get()
        self._settings.get("PDF", {})["viewer"] = \
            self.encoded_settings["PDF"]["viewer"].get()
        del self._settings["setting_groups"]


class SimpleContextEditSettingsCommand(sublime_plugin.WindowCommand):
    def run(self, *args, **kwargs):
        args = {
            "base_file":
                "${packages}/simple_ConTeXt/simple_ConTeXt.sublime-settings",
            "default": "{\n\t$0\n}\n"
        }
        sublime.run_command("edit_settings", args)
