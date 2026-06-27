function Get-LanSyncFontInventory {
    param([int]$Limit = 5000)

    $roots = @(
        (Join-Path $env:WINDIR "Fonts"),
        (Join-Path $env:LOCALAPPDATA "Microsoft\Windows\Fonts")
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique

    $items = New-Object System.Collections.Generic.List[object]
    foreach ($root in $roots) {
        $files = Get-ChildItem -LiteralPath $root -Recurse -File -Include *.ttf, *.otf, *.ttc, *.woff, *.woff2 -ErrorAction SilentlyContinue
        foreach ($file in $files) {
            $name = [IO.Path]::GetFileNameWithoutExtension($file.Name) -replace "[-_](Regular|Bold|Italic|Medium|Light)$", ""
            $items.Add([PSCustomObject]@{
                name = $name
                file = $file.Name
                path = $file.FullName
                extension = $file.Extension.ToLowerInvariant()
            })
            if ($items.Count -ge $Limit) {
                return @($items)
            }
        }
    }
    return @($items | Sort-Object name)
}

function Get-LanSyncAdobePluginInventory {
    param([int]$Limit = 1000)

    $roots = New-Object System.Collections.Generic.List[string]
    foreach ($base in @($env:ProgramFiles, ${env:ProgramFiles(x86)})) {
        if ([string]::IsNullOrWhiteSpace($base)) { continue }
        $roots.Add((Join-Path $base "Adobe\Common\Plug-ins\7.0\MediaCore"))
        $roots.Add((Join-Path $base "Common Files\Adobe\Plug-Ins\CC"))
        Get-ChildItem -LiteralPath (Join-Path $base "Adobe") -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like "Adobe After Effects*" -or $_.Name -like "Adobe Photoshop*" -or $_.Name -like "Adobe Premiere Pro*" } |
            ForEach-Object {
                $roots.Add((Join-Path $_.FullName "Support Files\Plug-ins"))
                $roots.Add((Join-Path $_.FullName "Plug-ins"))
            }
    }
    $roots.Add((Join-Path $env:APPDATA "Adobe\Common\Plug-ins"))
    $roots.Add((Join-Path $env:LOCALAPPDATA "Adobe\Common\Plug-ins"))

    $items = New-Object System.Collections.Generic.List[object]
    foreach ($root in @($roots | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique)) {
        foreach ($item in Get-ChildItem -LiteralPath $root -ErrorAction SilentlyContinue) {
            $items.Add([PSCustomObject]@{
                name = if ($item.PSIsContainer) { $item.Name } else { [IO.Path]::GetFileNameWithoutExtension($item.Name) }
                path = $item.FullName
                root = $root
                type = if ($item.PSIsContainer) { "folder" } else { "file" }
                extension = $item.Extension.ToLowerInvariant()
            })
            if ($items.Count -ge $Limit) {
                return @($items)
            }
        }
    }
    return @($items | Sort-Object name)
}

function Get-LanSyncAdobeAppInventory {
    $items = New-Object System.Collections.Generic.List[object]
    foreach ($base in @($env:ProgramFiles, ${env:ProgramFiles(x86)})) {
        if ([string]::IsNullOrWhiteSpace($base)) { continue }
        $adobeRoot = Join-Path $base "Adobe"
        if (-not (Test-Path -LiteralPath $adobeRoot)) { continue }
        Get-ChildItem -LiteralPath $adobeRoot -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like "Adobe *" } |
            ForEach-Object {
                $items.Add([PSCustomObject]@{
                    name = $_.Name
                    path = $_.FullName
                })
            }
    }
    return @($items | Sort-Object name)
}

function Get-LanSyncUnityAppInventory {
    $items = New-Object System.Collections.Generic.List[object]
    $seen = New-Object System.Collections.Generic.HashSet[string]

    function Add-UnityEditor {
        param([string]$Path, [string]$Version = "")
        if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path -LiteralPath $Path)) { return }
        $key = $Path.ToLowerInvariant()
        if (-not $seen.Add($key)) { return }
        $items.Add([PSCustomObject]@{
            name = [IO.Path]::GetFileName($Path)
            version = $Version
            path = $Path
        })
    }

    foreach ($base in @($env:ProgramFiles, ${env:ProgramFiles(x86)}, $env:LOCALAPPDATA)) {
        if ([string]::IsNullOrWhiteSpace($base)) { continue }
        foreach ($editor in @(
            (Join-Path $base "Unity\Hub\Editor"),
            (Join-Path $base "Programs\Unity\Hub\Editor")
        )) {
            if (-not (Test-Path -LiteralPath $editor)) { continue }
            Get-ChildItem -LiteralPath $editor -Directory -ErrorAction SilentlyContinue | ForEach-Object {
                Add-UnityEditor -Path (Join-Path $_.FullName "Editor\Unity.exe") -Version $_.Name
            }
        }
        Get-ChildItem -LiteralPath $base -Directory -Filter "Unity*" -ErrorAction SilentlyContinue | ForEach-Object {
            Add-UnityEditor -Path (Join-Path $_.FullName "Editor\Unity.exe") -Version $_.Name
        }
    }
    return @($items | Sort-Object version, name)
}

function Get-LanSyncDependencyInventory {
    return [PSCustomObject]@{
        hostname = $env:COMPUTERNAME
        platform = "Windows"
        timestamp = [DateTime]::Now.ToString("o")
        fonts = @(Get-LanSyncFontInventory)
        adobe_plugins = @(Get-LanSyncAdobePluginInventory)
        adobe_apps = @(Get-LanSyncAdobeAppInventory)
        unity_apps = @(Get-LanSyncUnityAppInventory)
    }
}
