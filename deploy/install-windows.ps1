param(
  [switch]$InstallWatcherTask,
  [switch]$InstallStyle
)

$ErrorActionPreference = "Stop"
$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Python = Join-Path $ProjectDir ".venv\Scripts\python.exe"
$PythonW = Join-Path $ProjectDir ".venv\Scripts\pythonw.exe"
$EnvFile = Join-Path $ProjectDir ".env"

if (-not (Test-Path $Python)) {
  py -3 -m venv (Join-Path $ProjectDir ".venv")
}
& $Python -m pip install -e $ProjectDir

if (-not (Test-Path $EnvFile)) {
  Copy-Item (Join-Path $ProjectDir ".env.example") $EnvFile
  Write-Host "Created $EnvFile. Fill it before starting the watcher."
}

if ($InstallStyle) {
  $StyleDir = Join-Path $env:USERPROFILE ".claude\output-styles"
  $StylePath = Join-Path $StyleDir "看清自己.md"
  New-Item -ItemType Directory -Force -Path $StyleDir | Out-Null
  if (Test-Path $StylePath) {
    Write-Warning "$StylePath already exists; left untouched."
  } else {
    Copy-Item (Join-Path $ProjectDir "templates\看清自己.md") $StylePath
    Write-Host "Installed style template: $StylePath"
  }
}

if ($InstallWatcherTask) {
  if (-not (Test-Path $PythonW)) { throw "pythonw.exe was not installed." }
  $Action = New-ScheduledTaskAction -Execute $PythonW -Argument "-m thought_bridge.watcher" -WorkingDirectory $ProjectDir
  $Trigger = New-ScheduledTaskTrigger -AtLogOn
  $Settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Days 3650) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
  Register-ScheduledTask -TaskName "ClaudeThoughtBridgeWatcher" -Action $Action -Trigger $Trigger -Settings $Settings -Description "Follow Claude Code transcript and publish process events" -Force | Out-Null
  Write-Host "Installed current-user logon task: ClaudeThoughtBridgeWatcher"
}

Write-Host "Installation complete. Run: $Python -m thought_bridge.cli doctor"
