param(
    [string]$InstallDir = "$env:ProgramData\RedLanSyncAgent",
    [string]$BundleConfig = "$PSScriptRoot\agent-config.generated.json",
    [switch]$SkipStartupFallback
)

$ErrorActionPreference = "Stop"

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "请右键 PowerShell，以管理员身份运行此安装脚本。"
}

if (-not (Test-Path -LiteralPath $BundleConfig)) {
    throw "缺少配对配置：$BundleConfig"
}

$bundle = Get-Content -LiteralPath $BundleConfig -Raw | ConvertFrom-Json
if ([string]::IsNullOrWhiteSpace([string]$bundle.Token)) {
    throw "配对配置中没有 Token"
}

New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
Copy-Item -LiteralPath "$PSScriptRoot\LanSyncAgent.ps1" -Destination "$InstallDir\LanSyncAgent.ps1" -Force
Copy-Item -LiteralPath "$PSScriptRoot\DependencyScan.ps1" -Destination "$InstallDir\DependencyScan.ps1" -Force
Copy-Item -LiteralPath $BundleConfig -Destination "$InstallDir\agent-config.json" -Force

$ruleName = "Red LAN Sync Companion 8766"
if (-not (Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule `
        -DisplayName $ruleName `
        -Direction Inbound `
        -Action Allow `
        -Protocol TCP `
        -LocalPort ([int]$bundle.Port) `
        -Profile Any | Out-Null
}

foreach ($adapter in @(Get-NetAdapter -Physical -ErrorAction SilentlyContinue)) {
    try {
        Set-NetAdapterPowerManagement `
            -Name $adapter.Name `
            -WakeOnMagicPacket Enabled `
            -WakeOnPattern Enabled `
            -NoRestart `
            -ErrorAction Stop | Out-Null
    }
    catch {
        Write-Warning "无法自动启用 $($adapter.Name) 的 Wake-on-LAN；请在网卡属性中确认 Magic Packet 设置。"
    }
}

$scriptPath = "$InstallDir\LanSyncAgent.ps1"
$configPath = "$InstallDir\agent-config.json"
$arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`" -ConfigPath `"$configPath`""

$taskName = "Red LAN Sync Companion"
$taskInstalled = $false
try {
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arguments
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $identity.Name
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 10 -RestartInterval (New-TimeSpan -Minutes 1)
    $taskPrincipal = New-ScheduledTaskPrincipal -UserId $identity.Name -LogonType Interactive -RunLevel Highest

    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $taskPrincipal `
        -Force | Out-Null

    Start-ScheduledTask -TaskName $taskName
    $taskInstalled = $true
}
catch {
    Write-Warning "计划任务创建或启动失败，将依赖当前用户 Startup 兜底启动项。错误：$($_.Exception.Message)"
}

$startupFallbackPath = ""
if (-not $SkipStartupFallback) {
    $startupDir = [Environment]::GetFolderPath("Startup")
    New-Item -ItemType Directory -Path $startupDir -Force | Out-Null
    $startupFallbackPath = Join-Path $startupDir "RedLanSyncCompanion.vbs"
    $startupCommand = "powershell.exe $arguments"
    $startupCommand = $startupCommand.Replace('"', '""')
    @"
Set WshShell = CreateObject(""WScript.Shell"")
WshShell.Run "$startupCommand", 0, False
"@ | Set-Content -LiteralPath $startupFallbackPath -Encoding ASCII
    try {
        icacls $startupFallbackPath /grant "$($identity.Name):RX" | Out-Null
    }
    catch {
        Write-Warning "无法调整 Startup 兜底启动项权限；如果登录后代理未启动，请手动检查：$startupFallbackPath"
    }
}

if (-not $taskInstalled) {
    Start-Process powershell.exe -WindowStyle Hidden -ArgumentList $arguments
}

$shortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "Wake RedM3Max.url"
@"
[InternetShortcut]
URL=http://127.0.0.1:$($bundle.Port)/
IconFile=%SystemRoot%\System32\shell32.dll
IconIndex=27
"@ | Set-Content -LiteralPath $shortcutPath -Encoding ASCII

$dashboardShortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "Red LAN Sync Dashboard.url"
@"
[InternetShortcut]
URL=$($bundle.DashboardUrl)/
IconFile=%SystemRoot%\System32\shell32.dll
IconIndex=13
"@ | Set-Content -LiteralPath $dashboardShortcutPath -Encoding ASCII

$startMenuDir = Join-Path ([Environment]::GetFolderPath("Programs")) "Red LAN Sync"
New-Item -ItemType Directory -Path $startMenuDir -Force | Out-Null
Copy-Item -LiteralPath $dashboardShortcutPath -Destination (Join-Path $startMenuDir "Red LAN Sync Dashboard.url") -Force

Write-Host ""
Write-Host "Red LAN Sync Companion 已安装并启动。" -ForegroundColor Green
Write-Host "安装目录: $InstallDir"
Write-Host "监听端口: $($bundle.Port)"
Write-Host "任务计划: $(if ($taskInstalled) { $taskName } else { '未创建，使用 Startup 兜底' })"
if ($startupFallbackPath) {
    Write-Host "Startup 兜底: $startupFallbackPath"
}
Write-Host "桌面入口: $shortcutPath"
Write-Host "网页管理入口: $dashboardShortcutPath"
