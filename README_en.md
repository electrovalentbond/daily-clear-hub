# Daily Clear Hub

Run daily jobs for seven games from one Windows queue. The upstream engines supply their own recognition resources. AUTO-MAS dispatches Maa_bbb, MaaEnd, BetterGI, and Zenless Zone Zero OneDragon. The China Bilibili release of Princess Connect uses pcr-script. Star Rail uses March7thAssistant and Guns GirlZ uses HKA.

- [Windows setup and PowerShell commands (Chinese)](docs/windows.md)
- [Implementation review and upstream sources (Chinese)](docs/implementation-review.md)
- [Local template requirements (Chinese)](assets/README.md)

After setup, copy `config.local.yaml.example` to `config.local.yaml` and configure the games you want to use.

```powershell
& .\.venv\Scripts\python.exe .\main.py plan
& .\.venv\Scripts\python.exe .\main.py check
& .\.venv\Scripts\python.exe .\main.py run
```

Pass game IDs to check or run a specific selection, for example `run endfield`. All games are disabled initially. The sample configuration selects the upstream engines. You can also choose `backend: native` and use `gui endfield --debug` to diagnose capture and annotate templates for the built-in [ok-script](https://github.com/ok-oldking/ok-script) reward flows.

On macOS or Linux, install PyYAML in a local virtual environment and run `./run_tests.sh` for portable tests.
