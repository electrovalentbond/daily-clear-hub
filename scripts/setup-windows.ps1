#Requires -Version 5.1
[CmdletBinding()]
param(
    [ValidateNotNullOrEmpty()]
    [ValidateSet('honkai3', 'starrail', 'zzz', 'genshin', 'pcr', 'bhxy2', 'endfield')]
    [string[]]$Games = @('honkai3', 'starrail', 'zzz', 'genshin', 'bhxy2', 'endfield'),
    [ValidateNotNullOrEmpty()]
    [string]$ToolsRoot = (Join-Path $env:USERPROFILE 'Games\DailyAutomation')
)

$ErrorActionPreference = 'Stop'
$HubRoot = Split-Path -Parent $PSScriptRoot
$ToolsRoot = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($ToolsRoot)
$Games = @($Games | ForEach-Object { $_.ToLowerInvariant() } | Select-Object -Unique)

function Invoke-CheckedNative([string]$Command, [string[]]$Arguments) {
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Command exited with code $LASTEXITCODE."
    }
}

function Get-ProjectPython([string]$Project) {
    $Venv = Join-Path $Project '.venv'
    $Python = Join-Path $Venv 'Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
        $Launcher = Get-Command py.exe -CommandType Application -ErrorAction SilentlyContinue
        if (-not $Launcher) {
            throw 'Install Python 3.12 x64 with the Windows Python launcher first.'
        }
        Invoke-CheckedNative $Launcher.Source @('-3.12', '-m', 'venv', $Venv) | Out-Host
    }
    Invoke-CheckedNative $Python @(
        '-c', 'import struct, sys; sys.exit(0 if sys.version_info[:2] == (3, 12) and struct.calcsize(chr(80)) == 8 else 1)'
    ) | Out-Host
    return $Python
}

function Confirm-AssetHash([string]$Path, [string]$Sha256) {
    if ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ne $Sha256) {
        throw "SHA-256 mismatch for $Path."
    }
}

function Receive-Asset([string]$Url, [string]$Path, [string]$Sha256) {
    Invoke-CheckedNative 'curl.exe' @('--fail', '--location', '--retry', '2', '--output', $Path, $Url)
    Confirm-AssetHash $Path $Sha256
}

function Find-ReleaseEntry([string]$Root, [string]$Filename) {
    $Direct = Join-Path $Root $Filename
    if (Test-Path -LiteralPath $Direct -PathType Leaf) {
        return $Direct
    }
    $Entries = @(Get-ChildItem -LiteralPath $Root -Filter $Filename -File -Recurse | Select-Object -First 2)
    if ($Entries.Count -ne 1) {
        throw "Expected one $Filename under $Root. Check the existing installation or choose another -ToolsRoot."
    }
    return $Entries[0].FullName
}

function Install-ZipRelease([hashtable]$Release) {
    $Destination = Join-Path $ToolsRoot $Release.Folder
    if (Test-Path -LiteralPath $Destination) {
        return (Find-ReleaseEntry $Destination $Release.Entry)
    }

    $Staging = Join-Path $ToolsRoot ('.setup-' + [guid]::NewGuid().ToString('N'))
    [IO.Directory]::CreateDirectory($Staging) | Out-Null
    try {
        $Zip = Join-Path $Staging 'release.zip'
        $Payload = Join-Path $Staging 'payload'
        Receive-Asset $Release.Url $Zip $Release.Sha256
        Expand-Archive -LiteralPath $Zip -DestinationPath $Payload
        Find-ReleaseEntry $Payload $Release.Entry | Out-Null
        [IO.Directory]::Move($Payload, $Destination)
    } finally {
        Remove-Item -LiteralPath $Staging -Recurse -Force -ErrorAction SilentlyContinue
    }
    return (Find-ReleaseEntry $Destination $Release.Entry)
}

$Releases = @{
    automas = @{
        Folder = 'AUTO-MAS-v5.8.0'
        Entry = 'AUTO-MAS.exe'
        Url = 'https://github.com/AUTO-MAS-Project/AUTO-MAS/releases/download/v5.8.0/AUTO-MAS-v5.8.0-x64.zip'
        Sha256 = '884a7b74da42ef837ca8ec8a1897f817839c77c201769155da18d870ccf73740'
    }
    honkai3 = @{
        Folder = 'Maa_bbb-v1.13.22'
        Entry = 'interface.json'
        Url = 'https://github.com/miaojiuqing/Maa_bbb/releases/download/v1.13.22/Maa_bbb-win-x86_64-v1.13.22.zip'
        Sha256 = '5e8a297ea2775617b2274110f79af66bc37f5cb65ddbcb8ba4ed1600367ef935'
    }
    starrail = @{
        Folder = 'March7thAssistant-v2026.11.22'
        Entry = 'March7th Assistant.exe'
        Url = 'https://github.com/moesnow/March7thAssistant/releases/download/v2026.11.22/March7thAssistant_full.zip'
        Sha256 = '526779bf643e244af6af172658601a77e5e2fc7da80f1b3fe09ae1efed5d1a49'
    }
    zzz = @{
        Folder = 'ZZZ-OD-v2.6.1'
        Entry = 'OneDragon-RuntimeLauncher.exe'
        Url = 'https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon/releases/download/v2.6.1/ZenlessZoneZero-OneDragon-v2.6.1-WithRuntime-Full.zip'
        Sha256 = 'c83607cf8966db4b440e1e1d4f38fad47099b1977cf41f7381ba85857779ce57'
    }
    bhxy2 = @{
        Folder = 'MaaBH2-v0.3.6'
        Entry = 'interface.json'
        Url = 'https://github.com/freeze-12/MaaBH2/releases/download/v0.3.6/MaaBH2-v0.3.6-win-x64.zip'
        Sha256 = '64e97957ea448b0b9505b2882e33c4e63b9a537d91c2d3c4d42154941c867f2e'
    }
    endfield = @{
        Folder = 'MaaEnd-v3.2.0'
        Entry = 'interface.json'
        Url = 'https://github.com/MaaEnd/MaaEnd/releases/download/v3.2.0/MaaEnd-win-x86_64-v3.2.0.zip'
        Sha256 = '2314044246733df849b7bc87c7fd99b8264f349eb947873701dea498d279b6b6'
    }
}

function Install-BetterGI {
    $Target = Join-Path $ToolsRoot 'BetterGI'
    if (Test-Path -LiteralPath (Join-Path $Target 'BetterGI.exe') -PathType Leaf) {
        Write-Host "genshin: $Target"
        return
    }

    $Downloads = Join-Path $ToolsRoot 'Downloads'
    $Installer = Join-Path $Downloads 'BetterGI.Install.0.67.0.exe'
    $Sha256 = 'b065a7301d44bb818a313e07513b5a90d356003a5115a83749246a4b03fa2308'
    if (Test-Path -LiteralPath $Installer -PathType Leaf) {
        Confirm-AssetHash $Installer $Sha256
    } else {
        [IO.Directory]::CreateDirectory($Downloads) | Out-Null
        $Partial = Join-Path $Downloads ('.setup-' + [guid]::NewGuid().ToString('N'))
        try {
            Receive-Asset 'https://github.com/babalae/better-genshin-impact/releases/download/0.67.0/BetterGI.Install.0.67.0.exe' $Partial $Sha256
            [IO.File]::Move($Partial, $Installer)
        } finally {
            Remove-Item -LiteralPath $Partial -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "genshin installer: $Installer"
    Write-Host "genshin suggested install directory: $Target"
}

function Prepare-Pcr {
    $Project = Join-Path $ToolsRoot 'pcr-script'
    $Revision = 'd1eb2120599a5bc42ce934657f7788e1a8f0bfc3'
    if (Test-Path -LiteralPath $Project) {
        if (-not (Test-Path -LiteralPath (Join-Path $Project '.git'))) {
            throw "Expected a pcr-script Git checkout at $Project."
        }
        $Head = Invoke-CheckedNative 'git.exe' @('-C', $Project, 'rev-parse', 'HEAD')
        if ($Head -ne $Revision) {
            throw "Preserved existing pcr-script checkout at $Project. Choose another -ToolsRoot for revision $Revision."
        }
    } else {
        $Staging = Join-Path $ToolsRoot ('.setup-' + [guid]::NewGuid().ToString('N'))
        try {
            Invoke-CheckedNative 'git.exe' @('clone', '--no-checkout', 'https://github.com/Gibberer/pcr-script.git', $Staging)
            Invoke-CheckedNative 'git.exe' @('-C', $Staging, 'checkout', '--detach', $Revision)
            [IO.Directory]::Move($Staging, $Project)
        } finally {
            Remove-Item -LiteralPath $Staging -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    $Python = Get-ProjectPython $Project
    Invoke-CheckedNative $Python @(
        '-m', 'pip', 'install', '--disable-pip-version-check', '-r', (Join-Path $Project 'requirements.txt')
    )
    Write-Host "pcr project: $Project"
    Write-Host "pcr Python: $Python"
}

$HubPython = Get-ProjectPython $HubRoot
Invoke-CheckedNative $HubPython @('-m', 'pip', 'install', '--disable-pip-version-check', 'PyYAML==6.0.3')
Write-Host "Hub Python: $HubPython"
[IO.Directory]::CreateDirectory($ToolsRoot) | Out-Null

if ($Games | Where-Object { $_ -ne 'pcr' }) {
    $MasExe = Install-ZipRelease $Releases.automas
    Write-Host "AUTO-MAS: $MasExe"
}
foreach ($Game in $Games) {
    switch ($Game) {
        'genshin' { Install-BetterGI }
        'pcr' { Prepare-Pcr }
        default {
            $Entry = Install-ZipRelease $Releases[$Game]
            Write-Host ("${Game}: " + (Split-Path -Parent $Entry))
        }
    }
}
