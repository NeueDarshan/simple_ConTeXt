import sublime_plugin

from .scripts import utilities


class SimpleContextExecWrapperCommand(sublime_plugin.WindowCommand):
    """
    A simple wrapper around the built||in \\type{exec}. The only difference is
    we provide some extra variables fetched from the simple ConTeXt settings.
    """

    def reload_settings(self):
        utilities.reload_settings(self)

    def run(self, **kwargs):
        self.reload_settings()
        self.window.run_command(
            "exec",
            utilities.expand_variables(
                self, kwargs, utilities.get_variables(self),
            ),
        )
