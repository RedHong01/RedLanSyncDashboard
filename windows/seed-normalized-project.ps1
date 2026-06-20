param(
    [Parameter(Mandatory = $true)]
    [string]$Source,

    [Parameter(Mandatory = $true)]
    [string]$Destination,

    [string]$DashboardUrl = "",
    [string]$Token = "",
    [string]$MacProjectPath = "",
    [string]$FolderId = "",
    [string]$Label = "",
    [string]$RemotePath = ""
)

$ErrorActionPreference = "Stop"

function Assert-AbsoluteWindowsPath {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Name
    )

    if ($Path -notmatch "^[A-Za-z]:\\") {
        throw "$Name must be an absolute Windows drive path."
    }
}

if (-not (Test-Path -LiteralPath $Source)) {
    throw "Source does not exist: $Source"
}

Assert-AbsoluteWindowsPath -Path $Destination -Name "Destination"
if ([string]::IsNullOrWhiteSpace($RemotePath)) {
    $RemotePath = $Destination
}
Assert-AbsoluteWindowsPath -Path $RemotePath -Name "RemotePath"

New-Item -ItemType Directory -Path $Destination -Force | Out-Null

$robocopyArgs = @(
    $Source,
    $Destination,
    "/E",
    "/COPY:DAT",
    "/DCOPY:DAT",
    "/R:2",
    "/W:2",
    "/MT:16",
    "/XD",
    ".stfolder"
)

Write-Host "Seeding normalized project..."
Write-Host "  Source:      $Source"
Write-Host "  Destination: $Destination"
& robocopy @robocopyArgs
$copyCode = $LASTEXITCODE
if ($copyCode -gt 7) {
    throw "Robocopy failed with exit code $copyCode"
}

$stats = Get-ChildItem -LiteralPath $Destination -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum
Write-Host "Seed copy complete: $($stats.Count) files, $([Math]::Round($stats.Sum / 1GB, 2)) GB"

$canRegister = -not [string]::IsNullOrWhiteSpace($DashboardUrl) -and
    -not [string]::IsNullOrWhiteSpace($Token) -and
    -not [string]::IsNullOrWhiteSpace($MacProjectPath) -and
    -not [string]::IsNullOrWhiteSpace($FolderId)

if (-not $canRegister) {
    Write-Host "Dashboard registration skipped. Provide DashboardUrl, Token, MacProjectPath, and FolderId to register automatically."
    exit 0
}

if ([string]::IsNullOrWhiteSpace($Label)) {
    $Label = $FolderId
}

$payload = @{
    local_path = $MacProjectPath
    folder_id = $FolderId
    label = $Label
    remote_path = $RemotePath
} | ConvertTo-Json

$uri = $DashboardUrl.TrimEnd("/") + "/api/projects/register"
Write-Host "Registering project through dashboard: $uri"
$result = Invoke-RestMethod `
    -Uri $uri `
    -Method Post `
    -Headers @{ "X-LanSync-Token" = $Token } `
    -ContentType "application/json" `
    -Body $payload `
    -TimeoutSec 30

$result | ConvertTo-Json -Depth 20
