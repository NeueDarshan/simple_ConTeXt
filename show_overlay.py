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
    def run(self, scope="reference", scope_raw=None, on_choose=None):
        self.reload_settings()
        self.orig_sel = [(region.a, region.b) for region in self.view.sel()]
        self.on_choose = on_choose
        self.matches = sorted(
            self.view.find_by_selector(
                scope_raw if scope_raw is not None else
                self.scopes.get(scope, scopes.REFERENCE)
            ),
            key=lambda region: region.begin(),
        )
        clean = self.clean.get(scope, general_clean)
        self.window.show_quick_panel(
            [clean(self.view.substr(region)) for region in self.matches],
            self.on_done,
            on_highlight=self.on_highlight
        )

    def on_done(self, index):
        #D Consult \type{self.on_choose} \periods
        if 0 <= index < len(self.matches):
            self.set_selection(self.matches[index])
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
        bug = [s for s in self.view.sel()]
        self.view.add_regions(
            "bug", bug, "bug", "dot", sublime.HIDDEN | sublime.PERSISTENT
        )
        self.view.erase_regions("bug")
