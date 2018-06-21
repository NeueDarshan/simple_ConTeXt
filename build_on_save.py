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
            self.get_setting("builder/auto/extra_opts_for_ConTeXt", {})
        extra_opts = utilities.process_options(
            self, extra_opts_raw, utilities.get_variables(self),
        )
        cmd_context = \
            ["context", "${simple_context_insert_options}"] + extra_opts + \
            ["${file}"]
        run_when = self.get_setting("builder/auto/open_PDF_after_build", False)
        cmd_seq = [
            {
                "cmd": cmd_context,
                "env": {"PATH": "${simple_context_prefixed_path}"},
                "output": "context",
            },
            {
                "cmd": [
                    "${simple_context_pdf_viewer}", "${file_base_name}.pdf",
                ],
                "output": "pdf",
                "run_when": run_when,
            },
        ]

        show = self.get_setting(
            "builder/auto/output/show", "when_there_are_errors",
        )
        show_ConTeXt_path = \
            self.get_setting("builder/auto/output/show_ConTeXt_path", False)
        show_full_command = \
            self.get_setting("builder/auto/output/show_full_command", False)
        show_errors = \
            self.get_setting("builder/auto/output/show_errors", False)
        show_errors_inline = \
            self.get_setting("builder/auto/output/show_errors_inline", False)
        self.view.window().run_command(
            "simple_context_exec_main",
            {
                "cmd_seq": cmd_seq,
                "show": show,
                "show_ConTeXt_path": show_ConTeXt_path,
                "show_errors": show_errors,
                "show_errors_inline": show_errors_inline,
                "show_full_command": show_full_command,
            },
        )
