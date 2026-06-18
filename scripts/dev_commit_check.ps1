param(
    [ValidateSet("docs-only", "code", "full")]
    [string]$Mode = "docs-only",

    [string[]]$PytestArgs = @()
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

function Write-Section {
    param([string]$Message)
    Write-Host ""
    Write-Host "== $Message ==" -ForegroundColor Cyan
}

function Get-ToolPath {
    param(
        [string]$CommandName,
        [string]$VenvRelativePath
    )

    $candidate = Join-Path $ProjectRoot $VenvRelativePath
    if (Test-Path $candidate) {
        return $candidate
    }

    return $CommandName
}

function Invoke-Tool {
    param(
        [string]$Label,
        [string]$FilePath,
        [string[]]$Arguments
    )

    Write-Section $Label
    & $FilePath @Arguments

    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

function Get-ChangedFiles {
    $files = @()

    $files += git diff --name-only
    if ($LASTEXITCODE -ne 0) {
        throw "git diff --name-only failed"
    }

    $files += git diff --cached --name-only
    if ($LASTEXITCODE -ne 0) {
        throw "git diff --cached --name-only failed"
    }

    $files += git ls-files --others --exclude-standard
    if ($LASTEXITCODE -ne 0) {
        throw "git ls-files --others --exclude-standard failed"
    }

    return $files |
        Where-Object { $_ -and $_.Trim().Length -gt 0 } |
        Sort-Object -Unique
}

function Show-ChangedFiles {
    param([string[]]$Files)

    Write-Section "Visible git changes"
    if (-not $Files -or $Files.Count -eq 0) {
        Write-Host "No changed or untracked files visible to git."
        return
    }

    $Files | ForEach-Object { Write-Host "  $_" }
}

function Test-ProjectMemoryFiles {
    $requiredPaths = @(
        "docs/project_memory/current_state.md",
        "docs/project_memory/product_vision.md",
        "docs/project_memory/architecture_principles.md",
        "docs/project_memory/backend_truth_contract.md",
        "docs/project_memory/ai_boundaries.md",
        "docs/project_memory/section_registry_summary.md",
        "docs/project_memory/handoffs"
    )

    $missing = @()

    foreach ($path in $requiredPaths) {
        if (-not (Test-Path (Join-Path $ProjectRoot $path))) {
            $missing += $path
        }
    }

    if ($missing.Count -gt 0) {
        Write-Host "Missing required project memory paths:" -ForegroundColor Red
        $missing | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        throw "Project memory check failed"
    }

    Write-Section "Project memory check"
    Write-Host "Required project memory files/directories found."
}

function Test-ArtifactRisk {
    param([string[]]$Files)

    $blocked = @()

    foreach ($file in $Files) {
        $normalized = $file -replace "\\", "/"

        if (
            $normalized -like "*.patch" -or
            $normalized -like "*.zip" -or
            $normalized -like "artifacts/*" -or
            $normalized -like "*/artifacts/*" -or
            $normalized -like "_backup_before_*" -or
            $normalized -like "*/_backup_before_*" -or
            $normalized -like "_patched_*" -or
            $normalized -like "*/_patched_*" -or
            $normalized -eq "patch_check_output.txt" -or
            $normalized -like "*/patch_check_output.txt"
        ) {
            $blocked += $file
        }
    }

    if ($blocked.Count -gt 0) {
        Write-Host "Patch/snapshot/artifact files are visible to git:" -ForegroundColor Red
        $blocked | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        Write-Host ""
        Write-Host "Do not stage these. Add them to .git/info/exclude or move them outside the repo." -ForegroundColor Yellow
        throw "Artifact staging risk detected"
    }
}

function Test-DocsOnlyChangeSet {
    param([string[]]$Files)

    $notDocsOnly = @()

    foreach ($file in $Files) {
        $normalized = $file -replace "\\", "/"

        if ($normalized -like "docs/*") {
            continue
        }

        if ($normalized -like "*.md") {
            continue
        }

        if ($normalized -eq "scripts/dev_commit_check.ps1") {
            continue
        }

        $notDocsOnly += $file
    }

    if ($notDocsOnly.Count -gt 0) {
        Write-Host "Docs-only mode found non-doc/tooling changes:" -ForegroundColor Red
        $notDocsOnly | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        Write-Host ""
        Write-Host "Use -Mode code or inspect these files before committing." -ForegroundColor Yellow
        throw "Docs-only check failed"
    }
}

$ruff = Get-ToolPath "ruff" ".venv\Scripts\ruff.exe"
$black = Get-ToolPath "black" ".venv\Scripts\black.exe"
$python = Get-ToolPath "python" ".venv\Scripts\python.exe"

Write-Section "Developer commit check"
Write-Host "Mode: $Mode"
Write-Host "Project root: $ProjectRoot"

$changedFiles = @(Get-ChangedFiles)
Show-ChangedFiles -Files $changedFiles
Test-ArtifactRisk -Files $changedFiles

Invoke-Tool "git diff --check" "git" @("diff", "--check")
Test-ProjectMemoryFiles

switch ($Mode) {
    "docs-only" {
        Test-DocsOnlyChangeSet -Files $changedFiles
        Write-Section "Docs-only validation complete"
        Write-Host "No Ruff/Black/pytest run in docs-only mode."
    }

    "code" {
        Invoke-Tool "ruff check . --fix" $ruff @("check", ".", "--fix")
        Invoke-Tool "black ." $black @(".")

        if ($PytestArgs.Count -gt 0) {
            Invoke-Tool "focused pytest" $python (@("-m", "pytest") + $PytestArgs)
        }
        else {
            $touchedTests = @(
                $changedFiles |
                    Where-Object { ($_ -replace "\\", "/") -match "^tests/.+\.py$" }
            )

            if ($touchedTests.Count -gt 0) {
                Invoke-Tool "touched pytest files" $python (@("-m", "pytest") + $touchedTests + @("-q"))
            }
            else {
                Write-Section "Focused pytest"
                Write-Host "No touched test files detected."
                Write-Host "Run a focused pytest command manually if code behavior changed, or use -Mode full."
            }
        }

        Invoke-Tool "git diff --check after formatting" "git" @("diff", "--check")
        Write-Section "Code validation complete"
    }

    "full" {
        Invoke-Tool "ruff check . --fix" $ruff @("check", ".", "--fix")
        Invoke-Tool "black ." $black @(".")
        Invoke-Tool "pytest -q" $python @("-m", "pytest", "-q")
        Invoke-Tool "git diff --check after full validation" "git" @("diff", "--check")
        Write-Section "Full validation complete"
    }
}

Write-Host ""
Write-Host "Next:" -ForegroundColor Cyan
Write-Host "  git status --short"
Write-Host "  git add <intended files only>"
Write-Host "  git diff --cached --name-only"
