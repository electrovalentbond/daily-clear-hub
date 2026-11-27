#Requires -Version 5.1
[CmdletBinding()]
param(
    [ValidateNotNullOrEmpty()]
    [ValidateSet('honkai3', 'starrail', 'zzz', 'genshin', 'pcr', 'bhxy2', 'endfield', 'nikke', 'gakumas', 'dotabyss')]
    [string[]]$Games = @('honkai3', 'starrail', 'zzz', 'genshin', 'pcr', 'bhxy2', 'endfield'),
    [ValidateNotNullOrEmpty()]
    [string]$ToolsRoot = (Join-Path $env:USERPROFILE 'Games\DailyAutomation')
)

$ErrorActionPreference = 'Stop'
$HubRoot = Split-Path -Parent $PSScriptRoot
$ToolsRoot = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($ToolsRoot)
$Downloads = Join-Path $ToolsRoot 'Downloads'
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

function Test-AssetHash([string]$Path, [string]$Sha256) {
    return (Test-Path -LiteralPath $Path -PathType Leaf) -and
        ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -eq $Sha256)
}

function Receive-Asset([string]$Url, [string]$Path, [string]$Sha256) {
    if (Test-Path -LiteralPath $Path -PathType Leaf) {
        if (-not (Test-AssetHash $Path $Sha256)) {
            throw "SHA-256 mismatch for $Path. Remove that file before trying again."
        }
        return
    }

    [IO.Directory]::CreateDirectory((Split-Path -Parent $Path)) | Out-Null
    $Partial = "$Path.part"
    if (Test-AssetHash $Partial $Sha256) {
        [IO.File]::Move($Partial, $Path)
        return
    }

    # Handle curl exit codes ourselves in both Windows PowerShell and PowerShell 7.
    $Curl = (Get-Command curl.exe -CommandType Application | Select-Object -First 1).Source
    $PSNativeCommandUseErrorActionPreference = $false
    $MaxAttempts = 4
    for ($Attempt = 1; $Attempt -le $MaxAttempts; $Attempt++) {
        $Resume = (Test-Path -LiteralPath $Partial -PathType Leaf) -and
            (Get-Item -LiteralPath $Partial).Length -gt 0
        $CurlArgs = @('--fail', '--location', '--connect-timeout', '30',
            '--output', $Partial, '--write-out', '%{http_code}')
        if ($Resume) {
            $CurlArgs += @('--continue-at', '-')
        }
        $HttpStatus = & {
            $ErrorActionPreference = 'Continue'
            & $Curl @CurlArgs $Url
        }
        $CurlCode = $LASTEXITCODE

        if ($CurlCode -eq 0 -or ($Resume -and $HttpStatus -eq '416')) {
            if (Test-AssetHash $Partial $Sha256) {
                [IO.File]::Move($Partial, $Path)
                return
            }
            Remove-Item -LiteralPath $Partial -ErrorAction SilentlyContinue
            if (-not $Resume -or $Attempt -eq $MaxAttempts) {
                throw "SHA-256 mismatch for $Path."
            }
            Write-Host 'The resumed download failed verification. Restarting from byte zero.'
            continue
        }

        if ($Resume -and $CurlCode -in @(33, 36)) {
            Remove-Item -LiteralPath $Partial -ErrorAction SilentlyContinue
            if ($Attempt -lt $MaxAttempts) {
                Write-Host 'The server refused the resume request. Restarting from byte zero.'
                continue
            }
        }

        $Retryable = $CurlCode -in @(5, 6, 7, 16, 18, 28, 35, 52, 55, 56, 92) -or
            $HttpStatus -in @('408', '429', '500', '502', '503', '504')
        if (-not $Retryable -or $Attempt -eq $MaxAttempts) {
            throw "Download failed for $Path (curl $CurlCode, HTTP $HttpStatus). Rerun setup to retry or resume."
        }
        Write-Host "Download interrupted (curl $CurlCode, HTTP $HttpStatus). Retrying ($($Attempt + 1)/$MaxAttempts)."
        Start-Sleep -Seconds (2 * $Attempt)
    }
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
    $Pending = Join-Path $Downloads "$($Release.Folder).extracting"
    $Resuming = Test-Path -LiteralPath $Pending -PathType Leaf
    if ((Test-Path -LiteralPath $Destination) -and -not $Resuming) {
        return (Find-ReleaseEntry $Destination $Release.Entry)
    }

    $Zip = Join-Path $Downloads ([IO.Path]::GetFileName($Release.Url))
    Receive-Asset $Release.Url $Zip $Release.Sha256
    # Record incomplete extraction before creating the destination so reruns can repair it.
    [IO.File]::WriteAllText($Pending, $Release.Sha256)
    Write-Host "Extracting $Zip to $Destination"
    try {
        Expand-Archive -LiteralPath $Zip -DestinationPath $Destination -Force:$Resuming -ErrorAction Stop
        $Entry = Find-ReleaseEntry $Destination $Release.Entry
    } catch {
        throw "Could not finish extracting $Zip to ${Destination}: $($_.Exception.Message) Rerun setup to reuse this ZIP."
    }
    Remove-Item -LiteralPath $Pending
    Remove-Item -LiteralPath $Zip -ErrorAction SilentlyContinue
    return $Entry
}

$PcrRevision = 'd1eb2120599a5bc42ce934657f7788e1a8f0bfc3'
$DotAbyssRevision = '8ec90d7b900b9feaaac35cd78498e928e2e2a067'
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
    pcr = @{
        Folder = 'pcr-script'
        Entry = 'daily_task.py'
        Url = "https://github.com/Gibberer/pcr-script/archive/$PcrRevision.zip"
        Sha256 = '12847c8dc80f99a3038d15cd1bc87e600f07c1454f9c28a4f2761774c3a18c16'
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
    nikke = @{
        Folder = 'MDA-v1.13.10'
        Entry = 'interface.json'
        Url = 'https://github.com/1204244136/MDA/releases/download/v1.13.10/MDA-win-x86_64-v1.13.10.zip'
        Sha256 = '9836b5dddad10b5697f5f391c93e3bee379b640d4323f2240ec695c38c3b7685'
    }
    gakumas = @{
        Folder = 'MaaGakumasu-v1.5.4'
        Entry = 'interface.json'
        Url = 'https://github.com/SuperWaterGod/MaaGakumasu/releases/download/v1.5.4/MaaGakumasu-win-x86_64-v1.5.4.zip'
        Sha256 = '0a622954a9bfb6becefa573c794193b03b70368c858ca17582dae3f3d598d29b'
    }
    dotabyss = @{
        Folder = 'MaaDotAbyss-v0.2.0'
        Entry = 'run_gui.py'
        Url = "https://github.com/Azure-Sora/MaaDotAbyss/archive/$DotAbyssRevision.zip"
        Sha256 = 'b511f075c4f4a972e3d90a259755b4acd77d2bf7f96e5fde1e421a58d71c6262'
    }
}

function Install-BetterGI {
    $Target = Join-Path $ToolsRoot 'BetterGI'
    if (Test-Path -LiteralPath (Join-Path $Target 'BetterGI.exe') -PathType Leaf) {
        Write-Host "genshin: $Target"
        return
    }

    $Installer = Join-Path $Downloads 'BetterGI.Install.0.67.0.exe'
    $Sha256 = 'b065a7301d44bb818a313e07513b5a90d356003a5115a83749246a4b03fa2308'
    Receive-Asset 'https://github.com/babalae/better-genshin-impact/releases/download/0.67.0/BetterGI.Install.0.67.0.exe' $Installer $Sha256
    Write-Host "genshin installer: $Installer"
    Write-Host "genshin suggested install directory: $Target"
}

function Prepare-Pcr {
    $Project = Join-Path $ToolsRoot $Releases.pcr.Folder
    if (Test-Path -LiteralPath (Join-Path $Project '.git')) {
        $Head = Invoke-CheckedNative 'git.exe' @('-C', $Project, 'rev-parse', 'HEAD')
        if ($Head -ne $PcrRevision) {
            throw "Preserved existing pcr-script checkout at $Project. Choose another -ToolsRoot for revision $PcrRevision."
        }
    } else {
        $Project = Split-Path -Parent (Install-ZipRelease $Releases.pcr)
    }

    $Python = Get-ProjectPython $Project
    Invoke-CheckedNative $Python @(
        '-m', 'pip', 'install', '--disable-pip-version-check', '-r', (Join-Path $Project 'requirements.txt')
    )

    $AdapterSource = Join-Path $HubRoot 'integrations\pcr-automas'
    $Adapter = Join-Path $ToolsRoot 'pcr-automas'
    [IO.Directory]::CreateDirectory($Adapter) | Out-Null
    foreach ($Item in @('agent.py', 'requirements.txt', 'interface.json', 'resource')) {
        Copy-Item -LiteralPath (Join-Path $AdapterSource $Item) -Destination $Adapter -Recurse -Force
    }
    $AdapterConfig = @{ hub_root = $HubRoot; pcr_root = $Project } | ConvertTo-Json
    [IO.File]::WriteAllText((Join-Path $Adapter 'local.json'), $AdapterConfig, [Text.UTF8Encoding]::new($false))

    Write-Host "pcr project: $Project"
    Write-Host "pcr Python: $Python"
    Write-Host "pcr AUTO-MAS project: $Adapter"
}

function Prepare-DotAbyss {
    $Project = Split-Path -Parent (Install-ZipRelease $Releases.dotabyss)
    $Python = Get-ProjectPython $Project
    Invoke-CheckedNative $Python @(
        '-m', 'pip', 'install', '--disable-pip-version-check', '-r', (Join-Path $Project 'requirements.txt'),
        'maafw==5.16.1'
    )

    $AdapterSource = Join-Path $HubRoot 'integrations\dotabyss-automas'
    $Adapter = Join-Path $ToolsRoot 'dotabyss-automas'
    [IO.Directory]::CreateDirectory($Adapter) | Out-Null
    foreach ($Item in @('agent.py', 'job.py', 'requirements.txt', 'interface.json', 'resource')) {
        Copy-Item -LiteralPath (Join-Path $AdapterSource $Item) -Destination $Adapter -Recurse -Force
    }
    $AdapterConfig = @{ hub_root = $HubRoot; dotabyss_root = $Project } | ConvertTo-Json
    [IO.File]::WriteAllText((Join-Path $Adapter 'local.json'), $AdapterConfig, [Text.UTF8Encoding]::new($false))

    Write-Host "dotabyss project: $Project"
    Write-Host "dotabyss Python: $Python"
    Write-Host "dotabyss AUTO-MAS project: $Adapter"
}

[IO.Directory]::CreateDirectory($ToolsRoot) | Out-Null
try {
    $SetupLock = [IO.File]::Open((Join-Path $ToolsRoot '.setup.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
} catch [IO.IOException] {
    throw "Could not lock $ToolsRoot. Check whether another setup is running or the directory is accessible."
}
try {
    $HubPython = Get-ProjectPython $HubRoot
    Invoke-CheckedNative $HubPython @('-m', 'pip', 'install', '--disable-pip-version-check', 'PyYAML==6.0.3')
    Write-Host "Hub Python: $HubPython"

    $MasExe = Install-ZipRelease $Releases.automas
    Write-Host "AUTO-MAS: $MasExe"
    foreach ($Game in $Games) {
        switch ($Game) {
            'genshin' { Install-BetterGI }
            'pcr' { Prepare-Pcr }
            'dotabyss' { Prepare-DotAbyss }
            default {
                $Entry = Install-ZipRelease $Releases[$Game]
                if ($Game -eq 'bhxy2') {
                    Invoke-CheckedNative $HubPython @((Join-Path $PSScriptRoot 'patch_maabh2.py'), $Entry)
                }
                Write-Host ("${Game}: " + (Split-Path -Parent $Entry))
            }
        }
    }
} finally {
    $SetupLock.Dispose()
}
