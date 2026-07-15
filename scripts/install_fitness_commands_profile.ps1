param(
    [string]$ProfilePath = $PROFILE,
    [switch]$ReplaceProfileWithThinLoader
)

$ErrorActionPreference = "Stop"
$repoRoot = if ($env:FITNESS_WINDOWS_REPO) { $env:FITNESS_WINDOWS_REPO } else { "C:\projects\fitness_ai" }
$commandScript = Join-Path $repoRoot "scripts\fitness_commands.ps1"
$startMarker = "# >>> Health & Fitness Platform command menu >>>"
$endMarker = "# <<< Health & Fitness Platform command menu <<<"
$loader = @"
$startMarker
if (Test-Path -LiteralPath '$($commandScript.Replace("'", "''"))') {
    . '$($commandScript.Replace("'", "''"))'
}
$endMarker
"@

if (-not (Test-Path -LiteralPath $commandScript)) {
    throw "Command menu not found at $commandScript"
}

$profileDirectory = Split-Path -Parent $ProfilePath
if ($profileDirectory) { New-Item -ItemType Directory -Path $profileDirectory -Force | Out-Null }

$existing = if (Test-Path -LiteralPath $ProfilePath) { Get-Content -LiteralPath $ProfilePath -Raw } else { "" }
if (Test-Path -LiteralPath $ProfilePath) {
    $backup = "$ProfilePath.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss-fff')"
    Copy-Item -LiteralPath $ProfilePath -Destination $backup
    Write-Host "Profile backup created: $backup"
}

if ($ReplaceProfileWithThinLoader) {
    Set-Content -LiteralPath $ProfilePath -Value ($loader.Trim() + [Environment]::NewLine) -Encoding utf8
    Write-Host "Profile replaced with the repo-owned thin loader: $ProfilePath"
    return
}

$managedPatterns = @(
    '(?ms)^# >>> Health & Fitness Platform command menu >>>.*?^# <<< Health & Fitness Platform command menu <<<\s*',
    '(?ms)^# >>> AI Health Coach command menu >>>.*?^# <<< AI Health Coach command menu <<<\s*'
)
foreach ($pattern in $managedPatterns) { $existing = [regex]::Replace($existing, $pattern, "") }

$updated = $existing.TrimEnd()
if ($updated) { $updated += [Environment]::NewLine + [Environment]::NewLine }
$updated += $loader.Trim() + [Environment]::NewLine
Set-Content -LiteralPath $ProfilePath -Value $updated -Encoding utf8
Write-Host "Repo-owned Health & Fitness Platform command loader installed: $ProfilePath"
Write-Host "Existing non-managed profile content was preserved."
