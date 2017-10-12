import sublime
import sublime_plugin
import re
from .scripts import utilities
from .scripts import scopes


#D Strip braces and whitespace
def general_clean(text):
    match = re.match(r"^\s*{\s*(.*?)\s*}\s*", text)
    if match:
        return match.group(1)
    else:
        return text.strip()


#D Strip leading slash from command name
def definition_clean(text):
    text = general_clean(text)
    if text.startswith("\\"):
        return text[1:]
    else:
        return text


class SimpleContextInsertTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, text=""):
        offset = 0
        for region in self.view.sel():
            offset += self.view.insert(edit, region.begin() + offset, text)


class SimpleContextShowOverlayCommand(sublime_plugin.WindowCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scopes = {
            "reference": scopes.REFERENCE,
            "heading": scopes.HEADING,
            "definition": scopes.DEFINE,
            "file_name": scopes.FILE_NAME,
        }
        self.clean = {
            "reference": general_clean,
            "heading": general_clean,
            "definition": definition_clean,
            "file_name": general_clean,
        }

    def reload_settings(self):
        utilities.reload_settings(self)
        self.view = self.window.active_view()

    def is_visible(self):
        return scopes.is_context(self.view)

    #D For our use, we give a descriptive name as a \type{scope}. But you can
    #D override this by providing a \type{scope_raw} instead.
    def run(
        self,
        scope="reference",
        scope_raw=None,
        on_choose=None,
        selected_index=0
    ):
        self.reload_settings()
        self.orig_sel = [(region.a, region.b) for region in self.view.sel()]
        self.on_choose = on_choose
        self.matches = sorted(
            [
                region for region in self.view.find_by_selector(
                    scope_raw if scope_raw is not None else
                    self.scopes.get(scope, scopes.REFERENCE)
                )
                if region is not None
            ],
            key=lambda region: region.begin(),
        )
        clean = self.clean.get(scope, general_clean)

        if selected_index in ["closest", "previous", "next"]:
            sel = self.view.sel()
            num_matches = len(self.matches)
            num_regions = len(sel)
            if num_regions > 0 and num_matches > 0:
                middle_region = sel[num_regions // 2]
                #D Include the \type{[0]} to avoid taking \type{max} on an
                #D empty sequence
                index = max(
                    [0] + [
                        i for i in range(num_matches)
                        if self.filter(
                            self.matches[i].begin() - middle_region.begin(),
                            selected_index,
                        )
                    ],
                    key=self.key_function(middle_region),
                )
            else:
                index = 0
        else:
            index = selected_index

        self.window.show_quick_panel(
            [clean(self.view.substr(region)) for region in self.matches],
            self.on_done,
            on_highlight=self.on_highlight,
            selected_index=index,
        )

    def filter(self, delta, mode):
        if mode == "closest":
            return True
        elif mode == "previous":
            return delta <= 0
        elif mode == "next":
            return delta >= 0

    def key_function(self, region):
        return lambda i: -abs(region.begin() - self.matches[i].begin())

    def on_done(self, index):
        if 0 <= index < len(self.matches):
            region = self.matches[index]
            if self.on_choose == "insert":
                text = self.view.substr(region)
                self.set_selection(
                    *[sublime.Region(*tup) for tup in self.orig_sel]
                )
                self.view.window().run_command(
                    "simple_context_insert_text", {"text": text}
                )
            else:
                self.set_selection(region)

        else:
            self.set_selection(
                *[sublime.Region(*tup) for tup in self.orig_sel]
            )

    def on_highlight(self, index):
        if 0 <= index < len(self.matches):
            region = self.matches[index]
            self.set_selection(region)

    def set_selection(self, *regions):
        #D How should we handle multiple selections? Let's just jump to the
        #D modal/middle selection.
        middle_region = regions[len(regions) // 2]
        self.view.sel().clear()
        self.view.sel().add_all(regions)
        self.view.show_at_center(middle_region)
        self.bug_work_around()

    #D Work||around for a known Sublime Text bug, where caret position doesn't
    #D always refresh properly.
    def bug_work_around(self):
        self.view.add_regions(
            "simple_context_bug",
            self.view.sel(),
            flags=sublime.HIDDEN | sublime.PERSISTENT
        )
        self.view.erase_regions("simple_context_bug")
