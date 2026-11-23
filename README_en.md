# Daily Clear Hub

Run seven games from one AUTO-MAS queue on Windows. Choose the supported daily and weekly jobs in each profile. The Princess Connect Bilibili CN profile uses pcr-script and its recognition resources.

- [Windows setup and commands (Chinese)](docs/windows.md)
- [Implementation review and upstream sources (Chinese)](docs/implementation-review.md)
- [Local template requirements (Chinese)](assets/README.md)

Follow the Windows guide to prepare the games and configure their saved profiles. From the repository root:

```powershell
& .\scripts\setup-windows.ps1 -Games honkai3,starrail,zzz,genshin,pcr,bhxy2,endfield
```

Create the profiles and add them to an AUTO-MAS scheduling queue, then select the queue and start it from the dispatch center. The [optional CLI](docs/windows.md) still supports `run --automas` and manual YAML configurations. The `native` backend uses [ok-script](https://github.com/ok-oldking/ok-script) and local templates.

On macOS or Linux, install PyYAML in a local virtual environment and run `./run_tests.sh` for portable tests.
