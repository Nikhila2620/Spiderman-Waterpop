# Create Desktop and Start Menu Shortcuts for Spider-Man Waterpop v2.0
# Shortcuts always target START_APP.bat so a copied .venv cannot silently fail.
$ErrorActionPreference = "SilentlyContinue"

$ProjectDir = Split-Path -Parent $PSScriptRoot
$DesktopDir = [Environment]::GetFolderPath("Desktop")
$StartMenuDir = [System.IO.Path]::Combine([Environment]::GetFolderPath("StartMenu"), "Programs")

$IconPath = Join-Path $ProjectDir "assets\images\app_icon.ico"
$BatPath = Join-Path $ProjectDir "START_APP.bat"

$WshShell = New-Object -ComObject WScript.Shell

function Make-Shortcut($lnkPath, $desc) {
    $Shortcut = $WshShell.CreateShortcut($lnkPath)
    $Shortcut.TargetPath = $BatPath
    $Shortcut.Arguments = ""
    $Shortcut.WorkingDirectory = $ProjectDir
    if (Test-Path $IconPath) {
        $Shortcut.IconLocation = "$IconPath, 0"
    }
    $Shortcut.Description = $desc
    $Shortcut.Save()
    Write-Host "[OK] Created shortcut: $lnkPath"
}

Make-Shortcut (Join-Path $DesktopDir "Spider-Man Waterpop.lnk") "Spider-Man Waterpop v2.0"
Make-Shortcut (Join-Path $StartMenuDir "Spider-Man Waterpop.lnk") "Spider-Man Waterpop v2.0"
Make-Shortcut (Join-Path $StartMenuDir "Spider-Man Water Buddy.lnk") "Spider-Man Water Buddy v2.0"

Write-Host "`nAll shortcuts successfully configured in Windows Start Menu and Desktop!"
