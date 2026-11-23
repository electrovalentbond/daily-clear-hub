# Daily Clear Hub

Run daily jobs for seven games from one Windows queue. The built-in reward flows use [ok-script](https://github.com/ok-oldking/ok-script) for capture, recognition, and input. They confirm the reward page and distinguish a verified empty state from a failure. Star Rail can use March7thAssistant and Guns GirlZ can use HKA for a broader routine.

- [Windows setup and PowerShell commands (Chinese)](docs/windows.md)
- [Implementation review and upstream sources (Chinese)](docs/implementation-review.md)
- [Local template requirements (Chinese)](assets/README.md)

After setup, copy `config.local.yaml.example` to `config.local.yaml` and configure the games you want to use.

```powershell
& .\.venv\Scripts\python.exe .\main.py plan
& .\.venv\Scripts\python.exe .\main.py check
& .\.venv\Scripts\python.exe .\main.py run
```

Pass game IDs to check or run a specific selection, for example `run endfield`. Use `gui endfield --debug` to diagnose capture. All games are disabled initially. The built-in flows require local COCO templates and verification against the current game client. The external backends use their own resources and setup.

On macOS or Linux, install PyYAML in a local virtual environment and run `./run_tests.sh` for portable tests.
