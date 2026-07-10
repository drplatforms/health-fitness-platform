<#
.SYNOPSIS
Print read-only milestone and Git safety status for the Fitness AI repository.

.DESCRIPTION
Run from the repository root:
  powershell -ExecutionPolicy Bypass -File .\tools\milestone_status.ps1

The script never stages, restores, cleans, switches branches, commits, pushes,
merges, or modifies repository files. Normal feature work is reported without a
nonzero exit. Whitespace errors or changed tracked database files are blocking.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"
$blockingFailure = $false

function Write-Section {
    param([string]$Title)

    Write-Host ""
    Write-Host "== $Title ==" -ForegroundColor Cyan
}

function Write-Result {
    param(
        [ValidateSet("PASS", "WARN", "FAIL")]
        [string]$Status,
        [string]$Message
    )

    $color = switch ($Status) {
        "PASS" { "Green" }
        "WARN" { "Yellow" }
        "FAIL" { "Red" }
    }
    Write-Host "[$Status] $Message" -ForegroundColor $color
}

function Write-LinesOrPass {
    param(
        [string[]]$Lines,
        [string]$EmptyMessage
    )

    if ($Lines.Count -eq 0) {
        Write-Result -Status "PASS" -Message $EmptyMessage
        return
    }

    $Lines | ForEach-Object { Write-Host $_ }
}

function ConvertTo-RepositoryRelativePath {
    param(
        [string]$FullPath,
        [string]$RepositoryRoot
    )

    return $FullPath.Substring($RepositoryRoot.Length + 1).Replace('\', '/')
}

function Test-IsReparsePoint {
    param([System.IO.FileSystemInfo]$Item)

    return [bool](
        $Item.Attributes -band [System.IO.FileAttributes]::ReparsePoint
    )
}

function Get-GeneratedDirectoryPaths {
    param(
        [string]$Root,
        [int]$MaximumDepth = 6
    )

    $generatedNames = @('.next', 'node_modules')
    $skipNames = @('.git', '.venv', '.cache', '__pycache__')
    $pending = [System.Collections.Generic.Stack[object]]::new()
    $pending.Push([pscustomobject]@{ Path = $Root; Depth = 0 })
    $generatedPaths = @()

    while ($pending.Count -gt 0) {
        $current = $pending.Pop()
        $directories = @(
            Get-ChildItem -LiteralPath $current.Path -Directory -Force -ErrorAction SilentlyContinue
        )

        foreach ($directory in $directories) {
            if ($directory.Name -in $generatedNames) {
                $generatedPaths += ConvertTo-RepositoryRelativePath `
                    -FullPath $directory.FullName `
                    -RepositoryRoot $Root
                continue
            }

            $childDepth = $current.Depth + 1
            if (
                (Test-IsReparsePoint -Item $directory) -or
                $directory.Name -in $skipNames -or
                $childDepth -ge $MaximumDepth
            ) {
                continue
            }

            $pending.Push(
                [pscustomobject]@{
                    Path = $directory.FullName
                    Depth = $childDepth
                }
            )
        }
    }

    return @($generatedPaths | Sort-Object -Unique)
}

function Get-TemporaryArtifactPaths {
    param(
        [string]$TemporaryRoot,
        [string]$RepositoryRoot,
        [int]$MaximumDepth = 6
    )

    if (-not (Test-Path -LiteralPath $TemporaryRoot)) {
        return @()
    }

    $excludedNames = @(
        '.git',
        '.venv',
        '.cache',
        '__pycache__',
        '.next',
        'node_modules'
    )
    $pending = [System.Collections.Generic.Stack[object]]::new()
    $pending.Push([pscustomobject]@{ Path = $TemporaryRoot; Depth = 0 })
    $temporaryPaths = @()

    while ($pending.Count -gt 0) {
        $current = $pending.Pop()
        $items = @(
            Get-ChildItem -LiteralPath $current.Path -Force -ErrorAction SilentlyContinue
        )

        foreach ($item in $items) {
            $relativePath = ConvertTo-RepositoryRelativePath `
                -FullPath $item.FullName `
                -RepositoryRoot $RepositoryRoot

            if ($item.PSIsContainer) {
                if ($item.Name -eq '__pycache__') {
                    $temporaryPaths += $relativePath
                    continue
                }

                $childDepth = $current.Depth + 1
                if (
                    (Test-IsReparsePoint -Item $item) -or
                    $item.Name -in $excludedNames -or
                    $childDepth -ge $MaximumDepth
                ) {
                    continue
                }

                $pending.Push(
                    [pscustomobject]@{
                        Path = $item.FullName
                        Depth = $childDepth
                    }
                )
                continue
            }

            if (Test-IsReparsePoint -Item $item) {
                continue
            }

            if (
                $item.Name -match '(?i)\.(db|sqlite|sqlite3|zip|pyc)$' -or
                $item.Name -match '(?i)(smoke|report)'
            ) {
                $temporaryPaths += $relativePath
            }
        }
    }

    return @($temporaryPaths | Sort-Object -Unique)
}

function Test-ForbiddenArtifactPath {
    param([string]$Path)

    $normalizedPath = $Path.Replace('\', '/')
    return (
        $normalizedPath -match '(?i)\.(db|sqlite|sqlite3|zip)$' -or
        $normalizedPath -match '(?i)(^|/)(\.next|node_modules)(/|$)' -or
        $normalizedPath -match '(?i)(^|/)tmp/.*/?__pycache__(/|$)' -or
        $normalizedPath -match '(?i)(^|/)tmp/.*\.pyc$' -or
        $normalizedPath -match '(?i)(^|/)tmp/.*(smoke|report)'
    )
}

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
Push-Location -LiteralPath $repositoryRoot

try {
    $gitRootOutput = @(& git rev-parse --show-toplevel)
    $gitRootExit = $LASTEXITCODE
    $gitRoot = $gitRootOutput | Select-Object -First 1
    if ($gitRootExit -ne 0) {
        Write-Result -Status "FAIL" -Message "Repository root could not be resolved by Git."
        exit 1
    }

    Write-Section "Repository"
    Write-Host "Repository root: $gitRoot"
    $branchOutput = @(& git branch --show-current)
    $branchExit = $LASTEXITCODE
    $branch = $branchOutput | Select-Object -First 1
    if ($branchExit -ne 0 -or [string]::IsNullOrWhiteSpace($branch)) {
        Write-Result -Status "FAIL" -Message "Current branch could not be determined."
        $blockingFailure = $true
    } else {
        Write-Host "Current branch: $branch"
    }

    Write-Section "Short Git Status"
    [string[]]$shortStatus = @(& git status --short --untracked-files=all)
    Write-LinesOrPass -Lines $shortStatus -EmptyMessage "Working tree is clean."

    Write-Section "Modified Tracked Files"
    [string[]]$modifiedTracked = @(& git diff --name-status 2>$null)
    Write-LinesOrPass -Lines $modifiedTracked -EmptyMessage "No unstaged tracked-file changes."

    Write-Section "Untracked Files"
    [string[]]$untrackedFiles = @(& git ls-files --others --exclude-standard)
    Write-LinesOrPass -Lines $untrackedFiles -EmptyMessage "No untracked files."

    Write-Section "Staged Files"
    [string[]]$stagedFiles = @(& git diff --cached --name-status 2>$null)
    Write-LinesOrPass -Lines $stagedFiles -EmptyMessage "No staged files."

    Write-Section "Recent Commits"
    & git log -5 --oneline
    if ($LASTEXITCODE -ne 0) {
        Write-Result -Status "FAIL" -Message "Recent commits could not be read."
        $blockingFailure = $true
    }

    Write-Section "Diff Check"
    $workingDiffCheck = @(& git diff --check 2>$null)
    $workingDiffExit = $LASTEXITCODE
    $stagedDiffCheck = @(& git diff --cached --check 2>$null)
    $stagedDiffExit = $LASTEXITCODE
    if ($workingDiffExit -eq 0 -and $stagedDiffExit -eq 0) {
        Write-Result -Status "PASS" -Message "Working and staged diffs pass git diff --check."
    } else {
        $workingDiffCheck | ForEach-Object { Write-Host $_ }
        $stagedDiffCheck | ForEach-Object { Write-Host $_ }
        Write-Result -Status "FAIL" -Message "Whitespace errors were found."
        $blockingFailure = $true
    }

    Write-Section "Possible Forbidden Artifacts"
    $changedPaths = @()
    foreach ($line in $shortStatus) {
        if ($line.Length -ge 4) {
            $changedPaths += $line.Substring(3).Trim('"')
        }
    }
    $temporaryRoot = Join-Path $repositoryRoot "tmp"
    [string[]]$temporaryArtifacts = @(
        Get-TemporaryArtifactPaths `
            -TemporaryRoot $temporaryRoot `
            -RepositoryRoot $repositoryRoot
    )
    [string[]]$generatedDirectories = @(
        Get-GeneratedDirectoryPaths -Root $repositoryRoot
    )
    [string[]]$forbiddenArtifacts = @(
        @(
            $changedPaths | Where-Object { Test-ForbiddenArtifactPath -Path $_ }
            $generatedDirectories
            $temporaryArtifacts
        ) | Sort-Object -Unique
    )
    if ($forbiddenArtifacts.Count -eq 0) {
        Write-Result -Status "PASS" -Message "No forbidden artifacts appear in Git status."
    } else {
        $forbiddenArtifacts | ForEach-Object { Write-Host $_ }
        Write-Result -Status "WARN" -Message "Generated or temporary local artifacts are present. This is nonfatal unless an artifact is tracked or staged."
    }

    Write-Section "Tracked Or Staged Forbidden Artifacts"
    [string[]]$trackedPaths = @(& git ls-files)
    [string[]]$stagedPaths = @(
        & git diff --cached --name-only --diff-filter=ACMRT 2>$null
    )
    [string[]]$trackedOrStagedForbidden = @(
        @($trackedPaths; $stagedPaths) |
            Where-Object { Test-ForbiddenArtifactPath -Path $_ } |
            Sort-Object -Unique
    )
    if ($trackedOrStagedForbidden.Count -eq 0) {
        Write-Result -Status "PASS" -Message "No forbidden artifacts are tracked or staged."
    } else {
        $trackedOrStagedForbidden | ForEach-Object { Write-Host $_ }
        Write-Result -Status "FAIL" -Message "Tracked or staged forbidden artifacts are blocking."
        $blockingFailure = $true
    }

    Write-Section "Tracked Database Changes"
    [string[]]$trackedDatabaseChanges = @(
        & git diff --name-only -- '*.db' '*.sqlite' '*.sqlite3' 2>$null
        & git diff --cached --name-only -- '*.db' '*.sqlite' '*.sqlite3' 2>$null
    ) | Sort-Object -Unique
    if ($trackedDatabaseChanges.Count -eq 0) {
        Write-Result -Status "PASS" -Message "No tracked database files changed."
    } else {
        $trackedDatabaseChanges | ForEach-Object { Write-Host $_ }
        Write-Result -Status "FAIL" -Message "Tracked database changes are blocking."
        $blockingFailure = $true
    }
} finally {
    Pop-Location
}

if ($blockingFailure) {
    exit 1
}

exit 0
