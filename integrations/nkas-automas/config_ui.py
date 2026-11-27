"""Open the pinned NKAS Web UI for settings without resuming its scheduler."""

import sys
from pathlib import Path


def main():
    sys.path.insert(0, str(Path.cwd()))
    import gui
    from module.webui.process_manager import ProcessManager, list_mod_instance

    # This process only owns a configuration session. AUTO-MAS schedules the
    # finite runs, and the Hub installer manages the pinned NKAS release.
    def load_instances(*_args, **_kwargs):
        list_mod_instance()

    ProcessManager.restart_processes = staticmethod(load_instances)
    config = gui.State.deploy_config
    object.__setattr__(config, "AutoUpdate", False)
    object.__setattr__(config, "EnableRemoteAccess", False)
    gui.func(None)


if __name__ == "__main__":
    main()
