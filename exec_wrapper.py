import sublime_plugin

from .scripts import utilities


class SimpleContextExecWrapperCommand(
    utilities.BaseSettings, sublime_plugin.WindowCommand,
):
    """
    A simple wrapper around the built||in \\type{exec}. The only difference is
    we provide some extra variables fetched from the simple ConTeXt settings.
    """

    def run(self, **kwargs):
        self.reload_settings()
        self.window.run_command("exec", self.expand_variables(kwargs))
