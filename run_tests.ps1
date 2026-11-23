Set-Location $PSScriptRoot
$Python = if (Test-Path .\.venv\Scripts\python.exe) { '.\.venv\Scripts\python.exe' } else { 'python' }
& $Python -m unittest discover -s tests -p 'test_*.py' -v
exit $LASTEXITCODE
