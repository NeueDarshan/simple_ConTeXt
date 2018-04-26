import sublime_plugin

from .scripts import utilities


class SimpleContextBuildOnSaveListener(
    utilities.BaseSettings, sublime_plugin.ViewEventListener,
):
    def on_post_save_async(self):
        self.reload_settings()
        if (
            self.is_visible_alt() and
            self.get_setting("builder/behaviour/auto/after_save")
        ):
            extra_opts_raw = self.get_setting(
                "builder/behaviour/auto/extra_opts_for_ConTeXt"
            )
            extra_opts = utilities.process_options(
                self, extra_opts_raw, utilities.get_variables(self),
            )
            cmd_context = ["context", "$simple_context_insert_options"]
            cmd_context += extra_opts + ["$file"]
            cmd_seq = [
                {
                    "cmd": cmd_context,
                    "env": {"PATH": "$simple_context_prefixed_path"},
                    "output": "context",
                },
                {
                    "cmd": [
                        "$simple_context_pdf_viewer", "$file_base_name.pdf"
                    ],
                    "output": "pdf",
                    "run_when": "$simple_context_open_pdf_after_build",
                },
            ]
            self.view.window().run_command(
                "simple_context_exec_main", {"cmd_seq": cmd_seq},
            )
