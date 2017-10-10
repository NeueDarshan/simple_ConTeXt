import sublime
import sublime_plugin
import threading
import json
import os
from .scripts import utilities
from .scripts import files
from .scripts import save


IDLE = 0

RUNNING = 1


class SimpleContextRegenerateInterfaceFilesCommand(
    sublime_plugin.WindowCommand
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = IDLE

    def reload_settings(self):
        utilities.reload_settings(self)
        self.flags = \
            files.CREATE_NO_WINDOW if sublime.platform() == "windows" else 0

    def run(
        self,
        paths=[],
        each=False,
        threaded=True,
        overwrite=False,
        file_min=20000,
    ):
        self.reload_settings()
        self.file_min = file_min
        if self.state == IDLE:
            self.state = RUNNING

            def f():
                self.run_aux(self._paths if each else paths, overwrite)
            if threaded:
                thread = threading.Thread(target=f)
                thread.start()
            else:
                f()

    def run_aux(self, paths, overwrite):
        for path in paths:
            self.run_aux_i(path, overwrite)

    def run_aux_i(self, path, overwrite):
        if path in self._paths:
            path = self._paths[path]

        slug = files.file_as_slug(path)
        dir_ = os.path.join(
            sublime.packages_path(), "simple_ConTeXt", "interface", slug
        )
        if overwrite:
            self.run_aux_ii(path, dir_)
        else:
            self.run_aux_iii(path, dir_)

        self.state = IDLE

    def run_aux_ii(self, path, dir_):
        if os.path.exists(dir_):
            for f in os.listdir(dir_):
                os.remove(os.path.join(dir_, f))
        else:
            os.makedirs(dir_)
        self.run_aux_iv(path, dir_)

    def run_aux_iii(self, path, dir_):
        if not os.path.exists(dir_):
            os.makedirs(dir_)

        commands = os.path.join(dir_, "_commands.json")
        if not os.path.exists(commands):
            self.run_aux_iv(path, dir_)

    def run_aux_iv(self, path, dir_):
        saver = save.InterfaceSaver(flags=self.flags)
        saver.save(path, modules=True, tolerant=True)
        cmds = saver.encode()
        cache, key, size = {}, None, 0
        for name in sorted(cmds):
            key = name
            val = cmds[key]
            size += len(str(val))
            cache[key] = val
            if size > self.file_min:
                file = os.path.join(dir_, "{}.json".format(key))
                with open(file, encoding="utf-8", mode="w") as f:
                    json.dump(cache, f)
                cache.clear()
                size = 0
        if cache:
            file = os.path.join(dir_, "{}.json".format(key))
            with open(file, encoding="utf-8", mode="w") as f:
                json.dump(cache, f)
        file = os.path.join(dir_, "_commands.json")
        with open(file, encoding="utf-8", mode="w") as f:
            json.dump(sorted(cmds), f)
