# Daily Clear Hub

Run daily jobs for seven games from one Windows queue. AUTO-MAS manages six games and Hub discovers their saved profiles. Princess Connect Bilibili CN uses pcr-script through the same command. Upstream engines include their recognition resources.

- [Windows setup and commands (Chinese)](docs/windows.md)
- [Implementation review and upstream sources (Chinese)](docs/implementation-review.md)
- [Local template requirements (Chinese)](assets/README.md)

Follow the Windows guide to prepare the games and configure their saved profiles. From the repository root:

```powershell
& .\scripts\setup-windows.ps1 -Games honkai3,starrail,zzz,genshin,pcr,bhxy2,endfield
& .\.venv\Scripts\python.exe .\main.py plan --automas
& .\.venv\Scripts\python.exe .\main.py check --automas
& .\.venv\Scripts\python.exe .\main.py run --automas
```

Pass game IDs to limit the queue, for example `run --automas endfield`. Existing manual YAML configurations still work with `run`. The optional `native` backend uses [ok-script](https://github.com/ok-oldking/ok-script) and local templates.

On macOS or Linux, install PyYAML in a local virtual environment and run `./run_tests.sh` for portable tests.
