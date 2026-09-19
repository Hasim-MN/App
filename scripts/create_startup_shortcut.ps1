# Creates MediaFlow_AlwaysOn.lnk in Windows Startup folder
$WshShell = New-Object -ComObject WScript.Shell
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$appDir = Split-Path -Parent $scriptDir
$targetVbs = Join-Path $scriptDir "start_always_on_background.vbs"

$startupDir = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startupDir "MediaFlow_AlwaysOn.lnk"

$shortcut = $WshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "wscript.exe"
$shortcut.Arguments = "`"$targetVbs`""
$shortcut.WorkingDirectory = $appDir
$shortcut.Description = "MediaFlow 24/7 Always-On Server"
$shortcut.Save()

if (Test-Path $shortcutPath) {
    Write-Host "[SUCCESS] MediaFlow Auto-Start shortcut installed at: $shortcutPath" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Failed to create shortcut." -ForegroundColor Red
}
