import sublime_plugin

from .scripts import utilities


#D A simple wrapper around the built||in \type{exec}. The only difference
#D is we provide some extra variables fetched from the simple ConTeXt settings.
class SimpleContextExecWrapperCommand(sublime_plugin.WindowCommand):
    def reload_settings(self):
        utilities.reload_settings(self)

    def run(self, **kwargs):
        self.reload_settings()
        self.window.run_command(
            "exec",
            utilities.expand_variables(
                self, kwargs, utilities.get_variables(self)
            )
        )
