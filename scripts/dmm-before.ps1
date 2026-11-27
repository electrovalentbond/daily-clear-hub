#Requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('gakumas', 'dotabyss')]
    [string]$Game,
    [string]$OptionsJson,
    [switch]$WaitOnly
)

$ErrorActionPreference = 'Stop'
$DmmGames = @{
    gakumas = @{
        Name = '学園アイドルマスター'
        Names = @('学園アイドルマスター', '学园偶像大师', '学マス', 'gakumas')
        Product = 'gakumas'
        Class = 'UnityWndClass'
        Title = 'gakumas'
    }
    dotabyss = @{
        Name = 'ドットアビスX'
        Names = @('ドットアビスX', 'Dot Abyss X', 'dotabyss')
        Product = 'dotabyss_x_cl'
        Class = '^UnityWndClass$'
        Title = '^ドットアビスX$'
    }
}

function Get-DmmLaunchUri([IO.FileInfo]$Shortcut) {
    # Only resolve the DMM protocol URI. The shortcut itself may contain arbitrary commands.
    $Uri = $null
    if ($Shortcut.Extension -ieq '.url') {
        $Urls = @(Select-String -LiteralPath $Shortcut.FullName -Pattern '^\s*URL\s*=\s*(\S+)\s*$')
        if ($Urls.Count -eq 1) {
            $Uri = $Urls[0].Matches[0].Groups[1].Value
        }
    } elseif ($Shortcut.Extension -ieq '.lnk') {
        $Shell = New-Object -ComObject WScript.Shell
        $Link = $Shell.CreateShortcut($Shortcut.FullName)
        $Target = [string]$Link.TargetPath
        $Arguments = ([string]$Link.Arguments).Trim()
        if ($Target -match '^dmmgameplayer://') {
            $Uri = $Target
        } elseif ([IO.Path]::GetFileName($Target) -ieq 'rundll32.exe' -and
            $Arguments -match '^url\.dll,FileProtocolHandler\s+("[^"]+"|\S+)$') {
            $Uri = $Matches[1].Trim('"')
        } elseif ([IO.Path]::GetFileName($Target) -ieq 'explorer.exe') {
            $Uri = $Arguments.Trim('"')
        }
    }

    $Protocol = '^dmmgameplayer://(?:play/[a-z0-9_-]+/(?<Product>[a-z0-9_-]+)/cl/win|(?<Product>[a-z0-9_-]+)/cl/general(?:/[a-z0-9_-]+)?)/?$'
    if ($Uri -match $Protocol -and $Matches['Product'] -ieq $DmmGames[$Game].Product) {
        return $Uri
    }
}

function Resolve-DmmLaunchUri([hashtable]$Details, [string]$ConfiguredShortcut) {
    if ($ConfiguredShortcut) {
        $Shortcut = [Environment]::ExpandEnvironmentVariables($ConfiguredShortcut.Trim().Trim('"'))
        if ($Shortcut -notmatch '^[a-z]:\\' -or -not (Test-Path -LiteralPath $Shortcut -PathType Leaf)) {
            throw "找不到 DMM 快捷方式：$Shortcut。请填写已有的 .url 或 .lnk 文件完整路径。"
        }
        $Uri = Get-DmmLaunchUri (Get-Item -LiteralPath $Shortcut)
        if (-not $Uri) {
            throw "无法从快捷方式读取 $($Details.Name) 的 DMM 启动链接。请在 DMM GAMES PLAYER 重新创建游戏快捷方式。"
        }
        return $Uri
    }

    $Desktops = @(
        [Environment]::GetFolderPath([Environment+SpecialFolder]::DesktopDirectory)
        [Environment]::GetFolderPath([Environment+SpecialFolder]::CommonDesktopDirectory)
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Container) } | Select-Object -Unique
    $LaunchUris = @(
        foreach ($Desktop in $Desktops) {
            foreach ($Candidate in Get-ChildItem -LiteralPath $Desktop -File) {
                if ($Candidate.Extension -in '.url', '.lnk' -and
                    $Candidate.BaseName.Normalize([Text.NormalizationForm]::FormKC) -in $Details.Names) {
                    Get-DmmLaunchUri $Candidate
                }
            }
        }
    )
    $LaunchUris = @($LaunchUris | Select-Object -Unique)
    if ($LaunchUris.Count -eq 1) {
        return $LaunchUris[0]
    }
    if ($LaunchUris.Count -gt 1) {
        throw "桌面有多个 $($Details.Name) 的 DMM 启动链接。请填写要用的快捷方式完整路径。"
    }
    throw "桌面找不到 $($Details.Name) 的 DMM 启动链接。请在 DMM GAMES PLAYER 的「マイゲーム」中创建游戏快捷方式，或填写已有快捷方式路径。"
}

function Write-DmmLog([string]$Message) {
    if ([Console]::IsOutputRedirected) {
        # AUTO-MAS starts PowerShell without a console and reads the pipe as UTF-8.
        $Bytes = [Text.Encoding]::UTF8.GetBytes($Message + [Environment]::NewLine)
        $Output = [Console]::OpenStandardOutput()
        $Output.Write($Bytes, 0, $Bytes.Length)
        $Output.Flush()
    } else {
        Write-Output $Message
    }
}

try {
    $Options = if ($OptionsJson) { ConvertFrom-Json -InputObject $OptionsJson }
    $ConfiguredShortcut = ([string]$Options.DailyClearHubDmmLaunchSettings.shortcut).Trim()
    $Details = $DmmGames[$Game]

    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;

public static class DailyClearHubDmmWindow
{
    private delegate bool EnumWindowsCallback(IntPtr window, IntPtr parameter);

    [DllImport("user32.dll")]
    private static extern bool EnumWindows(EnumWindowsCallback callback, IntPtr parameter);

    [DllImport("user32.dll")]
    private static extern bool IsWindowVisible(IntPtr window);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int GetClassName(IntPtr window, StringBuilder value, int capacity);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int GetWindowText(IntPtr window, StringBuilder value, int capacity);

    [DllImport("user32.dll")]
    private static extern bool IsIconic(IntPtr window);

    [DllImport("user32.dll")]
    private static extern bool ShowWindowAsync(IntPtr window, int command);

    public static IntPtr Find(string classPattern, string titlePattern)
    {
        IntPtr match = IntPtr.Zero;
        var name = new StringBuilder(512);
        EnumWindows(delegate(IntPtr window, IntPtr parameter)
        {
            if (!IsWindowVisible(window) ||
                GetClassName(window, name, name.Capacity) == 0 ||
                !Regex.IsMatch(name.ToString(), classPattern) ||
                GetWindowText(window, name, name.Capacity) == 0 ||
                !Regex.IsMatch(name.ToString(), titlePattern))
                return true;

            match = window;
            return false;
        }, IntPtr.Zero);
        return match;
    }

    public static void Restore(IntPtr window)
    {
        if (IsIconic(window))
            ShowWindowAsync(window, 9); // SW_RESTORE
    }
}
'@

    $Window = [DailyClearHubDmmWindow]::Find($Details.Class, $Details.Title)
    if ($Window -ne [IntPtr]::Zero) {
        [DailyClearHubDmmWindow]::Restore($Window)
        Write-DmmLog "DMM：沿用已打开的 $($Details.Name) 游戏窗口。"
        exit 0
    }

    if ($WaitOnly) {
        Write-DmmLog "DMM：UU 已请求启动 $($Details.Name)，等待游戏窗口。"
    } else {
        $Uri = Resolve-DmmLaunchUri $Details $ConfiguredShortcut
        Write-DmmLog "DMM：通过官方启动器请求启动 $($Details.Name)，等待游戏窗口。"
        Start-Process -FilePath $Uri
    }

    $Wait = [Diagnostics.Stopwatch]::StartNew()
    while ($Wait.Elapsed.TotalSeconds -lt 120) {
        Start-Sleep -Seconds 1
        $Window = [DailyClearHubDmmWindow]::Find($Details.Class, $Details.Title)
        if ($Window -ne [IntPtr]::Zero) {
            [DailyClearHubDmmWindow]::Restore($Window)
            Start-Sleep -Seconds 2
            if ([DailyClearHubDmmWindow]::Find($Details.Class, $Details.Title) -ne [IntPtr]::Zero) {
                Write-DmmLog "DMM：已找到 $($Details.Name) 游戏窗口，交给 AUTO-MAS。"
                exit 0
            }
        }
    }
    $Source = if ($WaitOnly) { 'UU 的「启动游戏」' } else { 'DMM 快捷方式' }
    throw "等待 $($Details.Name) 游戏窗口超时（窗口类匹配 $($Details.Class)，标题匹配 $($Details.Title)）。请检查 $Source 是否能打开游戏、DMM 是否已登录，以及游戏是否正在更新。"
} catch {
    Write-DmmLog "DMM 前置任务失败：$($_.Exception.Message)"
    exit 1
}
