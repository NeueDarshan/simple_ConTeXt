from typing import Any, Dict, List, Optional  # noqa

import sublime
import sublime_plugin

from .scripts import deep_dict
from .scripts import utilities


# Bit ugly that we take this approach. We feel the need to do so because I
# can't see how to iterate over a ST settings object.
CURRENT_SETTINGS = {
    "buffer/on",
    "builder/auto/extra_opts_for_ConTeXt",
    "builder/auto/on",
    "builder/auto/open_PDF_after_build",
    "builder/auto/output/show",
    "builder/auto/output/show_ConTeXt_path",
    "builder/auto/output/show_errors",
    "builder/auto/output/show_errors_inline",
    "builder/auto/output/show_full_command",
    "builder/auto/return_focus_after_open_PDF",
    "builder/normal/open_PDF_after_build",
    "builder/normal/opts_for_ConTeXt",
    "builder/normal/output/show",
    "builder/normal/output/show_ConTeXt_path",
    "builder/normal/output/show_errors",
    "builder/normal/output/show_errors_inline",
    "builder/normal/output/show_full_command",
    "builder/normal/return_focus_after_open_PDF",
    "citations/command_regex",
    "citations/format",
    "citations/on",
    "file_links/on",
    "option_completions/on",
    "path",
    "PDF/viewer",
    "pop_ups/hang_indentation",
    "pop_ups/line_break",
    "pop_ups/match_indentation",
    "pop_ups/methods/on_hover",
    "pop_ups/methods/on_modified",
    "pop_ups/show_copy_pop_up",
    "pop_ups/show_source_files",
    "pop_ups/try_generate_on_demand",
    "references/command_regex",
    "references/on",
    "script/timeout",
}


def simplify(obj) -> str:
    if isinstance(obj, str):
        return obj
    elif isinstance(obj, dict):
        return "[" + "] [".join(sorted(obj)) + "]"
    elif isinstance(obj, list):
        return "[" + "] [".join(tup[0] for tup in sorted(obj) if tup) + "]"
    return str(obj)


# Would be nice to do the `quick_panel` in a better way, with a row for each
# sub-option. However, I'm not sure is that's possible at the moment: it seems
# that each entry is expected to have the same number of rows, which limits our
# options.
class SimpleContextSettingsControllerCommand(
    utilities.BaseSettings, sublime_plugin.WindowCommand,
):
    def reload_settings(self) -> None:
        super().reload_settings()
        self.context_paths = \
            utilities.get_setting_location(self, "ConTeXt_paths", default={})

    def update_settings(self) -> None:
        self.current_settings = {}  # type: Dict[str, Any]
        for k in CURRENT_SETTINGS:
            deep_dict.set_safe(
                self.current_settings, k.split("/"), self.get_setting(k),
            )

    def run(self) -> None:
        self.reload_settings()
        self.update_settings()
        self.encode_settings()
        self.last_scheme = None  # type: Optional[str]
        self.location = []  # type: List[str]
        self.history = {}  # type: Dict[int, int]
        self.run_panel()

    def run_panel(self) -> None:
        self.window.show_quick_panel(
            self.flatten_current_level(),
            self.run_handle,
            selected_index=self.get_history(),
        )

    def run_handle(self, index: int) -> None:
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

            # It's nice to be able to quickly toggle booleans, but we also want
            # the option to change a boolean into, say, a string. So we do this
            # compromise.
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

    def run_panel_scheme(self) -> None:
        self.window.show_quick_panel(
            self.flatten_current_level(),
            self.run_handle_scheme,
            selected_index=self.get_history(),
        )

    def run_handle_scheme(self, index: int) -> None:
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
                deep_dict.set_safe(self.encoded_settings, location, val)
            self.save(decode=False)
            self.run_panel_scheme()

    def run_panel_choice(self) -> None:
        self.window.show_quick_panel(
            self.flatten_current_level(),
            self.run_handle_choice,
            selected_index=self.get_history(),
        )

    def run_handle_choice(self, index: int) -> None:
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

    def on_done(self, text: str) -> None:
        deep_dict.set_safe(
            self.encoded_settings, self.location, utilities.guess_type(text),
        )
        self.location.pop()
        self.save()
        self.run_panel()

    def on_change(self, text: str) -> None:
        pass

    def on_cancel(self) -> None:
        self.location.pop()
        self.run_panel()

    def current_level(self) -> Any:
        return deep_dict.get_safe(self.encoded_settings, self.location)

    def flatten_current_level(self) -> List[List[str]]:
        current_level = self.current_level()
        if self.location and self.location[-1] == "setting_groups":
            main = [
                [k, "[✓]" if k == self.last_scheme else "[ ]"]
                for k in sorted(current_level)
            ]
        elif isinstance(current_level, utilities.Choice):
            main = current_level.to_list(string=True)
        else:
            main = [
                [k, simplify(current_level[k])] for k in sorted(current_level)
            ]
        if self.location:
            return [["..", "in /{}/".format("/".join(self.location))]] + main
        return main

    def get_history(self) -> int:
        return self.history.get(len(self.location), 0)

    def set_history(self, index: int) -> None:
        self.history[len(self.location)] = index

    def save(self, decode: bool = True) -> None:
        if decode:
            self.decode_settings()
        self.write_settings()
        for k, v in self.to_write.items():
            self.sublime_settings.set("current.{}".format(k), v)
        sublime.save_settings("simple_ConTeXt.sublime-settings")
        self.reload_settings()
        self.encode_settings()

    def encode_settings(self) -> None:
        """
        Load the settings on file into memory, and perform some simple
        transformations to them.
        """

        self.encoded_settings = self.current_settings
        self.encoded_settings["path"] = utilities.Choice(
            self.context_paths, choice=self.current_settings.get("path"),
        )
        viewer = utilities.Choice(
            utilities.get_setting_location(self, "PDF_viewers", default={}),
            choice=self.get_setting("PDF/viewer"),
        )
        self.encoded_settings.setdefault("PDF", {})["viewer"] = viewer
        self.encoded_settings["setting_groups"] = \
            self.sublime_settings.get("setting_groups", {})

    def decode_settings(self) -> None:
        """
        Write the settings in memory onto the appropriate file, undoing the
        transformations as appropriate.
        """

        self.current_settings["path"] = self.encoded_settings["path"].get()
        self.current_settings.get("PDF", {})["viewer"] = \
            self.encoded_settings["PDF"]["viewer"].get()
        del self.current_settings["setting_groups"]

    def write_settings(self) -> None:
        self.to_write = {}  # type: Dict[str, Any]
        for k, v in deep_dict.iter_(self.current_settings):
            for opt in {"extra_opts_for_ConTeXt", "opts_for_ConTeXt"}:
                if opt in k:
                    i = k.index(opt) + 1
                    deep_dict.set_safe(
                        self.to_write, ["/".join(k[:i])] + k[i:], v,
                    )
                    break
            else:
                self.to_write["/".join(k)] = v


class SimpleContextEditSettingsCommand(sublime_plugin.WindowCommand):
    def run(self, *args, **kwargs) -> None:
        base_file = \
            "${packages}/simple_ConTeXt/simple_ConTeXt.sublime-settings"
        dict_ = {"base_file": base_file, "default": "{\n\t$0\n}\n"}
        sublime.run_command("edit_settings", dict_)
