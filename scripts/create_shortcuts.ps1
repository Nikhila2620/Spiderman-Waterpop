# Create Desktop and Start Menu Shortcuts for Spider-Man Water Buddy v2.0
$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $PSScriptRoot
$DesktopDir = [Environment]::GetFolderPath("Desktop")
$StartMenuDir = [System.IO.Path]::Combine([Environment]::GetFolderPath("StartMenu"), "Programs")

$IconPath = Join-Path $ProjectDir "assets\images\app_icon.ico"
$BatPath = Join-Path $ProjectDir "START_APP.bat"
$VenvPython = Join-Path $ProjectDir ".venv\Scripts\pythonw.exe"
$RunScript = Join-Path $ProjectDir "run.py"

# Choose target: pythonw run.py directly if venv exists, else START_APP.bat
$WshShell = New-Object -ComObject WScript.Shell

function Make-Shortcut($lnkPath) {
    $Shortcut = $WshShell.CreateShortcut($lnkPath)
    if (Test-Path $VenvPython) {
        $Shortcut.TargetPath = $VenvPython
        $Shortcut.Arguments = "`"$RunScript`""
    } else {
        $Shortcut.TargetPath = $BatPath
    }
    $Shortcut.WorkingDirectory = $ProjectDir
    if (Test-Path $IconPath) {
        $Shortcut.IconLocation = "$IconPath, 0"
    }
    $Shortcut.Description = "Spider-Man Water Buddy v2.0 - Desktop Hydration Companion"
    $Shortcut.Save()
    Write-Host "[OK] Created shortcut: $lnkPath"
}

# 1. Desktop Shortcut
$DesktopLnk = Join-Path $DesktopDir "Spider-Man Water Buddy.lnk"
Make-Shortcut $DesktopLnk

# 2. Start Menu Shortcut
$StartMenuLnk = Join-Path $StartMenuDir "Spider-Man Water Buddy.lnk"
Make-Shortcut $StartMenuLnk

Write-Host "`nAll shortcuts successfully configured!"
