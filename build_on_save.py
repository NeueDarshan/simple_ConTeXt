import sublime_plugin

from .scripts import utilities


class SimpleContextBuildOnSaveListener(
    utilities.BaseSettings, sublime_plugin.ViewEventListener,
):
    def on_post_save_async(self):
        self.reload_settings()
        if not (self.is_visible_alt() and self.get_setting("builder/auto/on")):
            return

        extra_opts_raw = \
            self.get_setting("builder/auto/extra_opts_for_ConTeXt")
        extra_opts = utilities.process_options(
            self, extra_opts_raw, utilities.get_variables(self),
        )
        cmd_context = \
            ["context", "$simple_context_insert_options"] + extra_opts + \
            ["$file"]
        cmd_seq = [
            {
                "cmd": cmd_context,
                "env": {"PATH": "$simple_context_prefixed_path"},
                "output": "context",
            },
            {
                "cmd": ["$simple_context_pdf_viewer", "$file_base_name.pdf"],
                "output": "pdf",
                "run_when": "$simple_context_open_pdf_after_build",
            },
        ]

        self.view.window().run_command(
            "simple_context_exec_main",
            {
                "cmd_seq": cmd_seq,
                "show": self.get_setting("builder/auto/output/show"),
                "show_ConTeXt_path":
                    self.get_setting("builder/auto/output/show_ConTeXt_path"),
                "show_full_command":
                    self.get_setting("builder/auto/output/show_full_command"),
            },
        )
