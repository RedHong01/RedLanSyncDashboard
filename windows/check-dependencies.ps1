$ErrorActionPreference = "Stop"

. "$PSScriptRoot\DependencyScan.ps1"

Get-LanSyncDependencyInventory | ConvertTo-Json -Depth 12
