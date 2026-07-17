# Health & Fitness Platform developer command menu.
# Repo-owned command logic: the PowerShell profile should only dot-source this file.

$script:FitnessWindowsRepo = if ($env:FITNESS_WINDOWS_REPO) { $env:FITNESS_WINDOWS_REPO } else { "C:\projects\fitness_ai" }
$script:FitnessFrontendDir = Join-Path $script:FitnessWindowsRepo "frontend"
$script:FitnessLinuxRepo = if ($env:FITNESS_LINUX_REPO) { $env:FITNESS_LINUX_REPO } else { "~/projects/fitness-ai-platform" }
$script:FitnessLinuxSsh = if ($env:FITNESS_LINUX_SSH) { $env:FITNESS_LINUX_SSH } else { "fitness-linux" }
$script:FitnessSnapshotDir = if ($env:FITNESS_SNAPSHOT_DIR) { $env:FITNESS_SNAPSHOT_DIR } else { "C:\projects\fitness_ai_external\snapshots" }
$script:FitnessApiPort = 8000
$script:FitnessFrontendPort = if ($env:FITNESS_FRONTEND_PORT) { [int]$env:FITNESS_FRONTEND_PORT } else { 3100 }
$script:FitnessNextDevPort = if ($env:FITNESS_NEXT_DEV_PORT) { [int]$env:FITNESS_NEXT_DEV_PORT } else { 3000 }

function Assert-FitnessRepo {
    if (-not (Test-Path -LiteralPath (Join-Path $script:FitnessWindowsRepo ".git"))) {
        throw "Health & Fitness Platform repository not found at $script:FitnessWindowsRepo"
    }
}

function Get-FitnessWindowsPython {
    $venvPython = Join-Path $script:FitnessWindowsRepo ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $venvPython) { return $venvPython }
    throw "Repository Python was not found at $venvPython"
}

function Get-FitnessBranch {
    Push-Location $script:FitnessWindowsRepo
    try { return (git branch --show-current).Trim() } finally { Pop-Location }
}

function Assert-FitnessCleanTree {
    Push-Location $script:FitnessWindowsRepo
    try {
        if (git status --porcelain) { throw "Working tree must be clean for this operation." }
    } finally { Pop-Location }
}

function Invoke-FitnessGitChecked {
    param(
        [Parameter(Mandatory = $true)][string]$Operation,
        [Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments
    )
    & git @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Operation failed." }
}

function Assert-FitnessMainMatchesOrigin {
    $localMain = (git rev-parse main).Trim()
    if ($LASTEXITCODE -ne 0) { throw "Could not resolve local main." }
    $originMain = (git rev-parse origin/main).Trim()
    if ($LASTEXITCODE -ne 0) { throw "Could not resolve origin/main." }
    if ($localMain -ne $originMain) { throw "STOP: local main does not match origin/main." }
}

function Assert-FitnessPortAvailable {
    param(
        [Parameter(Mandatory = $true)][int]$Port,
        [Parameter(Mandatory = $true)][string]$Label
    )
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($listener) { throw "$Label cannot start because port $Port is already listening." }
}

function Get-FitnessProcessChain {
    param(
        [Parameter(Mandatory = $true)][int]$ProcessId,
        [Parameter(Mandatory = $true)][object[]]$Processes
    )
    $byId = @{}
    foreach ($process in $Processes) { $byId[[int]$process.ProcessId] = $process }
    $chain = @()
    $seen = @{}
    $currentId = $ProcessId
    while ($currentId -gt 0 -and -not $seen.ContainsKey($currentId) -and $byId.ContainsKey($currentId)) {
        $seen[$currentId] = $true
        $current = $byId[$currentId]
        $chain += $current
        $currentId = [int]$current.ParentProcessId
    }
    return $chain
}

function Stop-FitnessOwnedListener {
    param(
        [Parameter(Mandatory = $true)][int]$Port,
        [Parameter(Mandatory = $true)][string]$ExpectedCommandPattern,
        [Parameter(Mandatory = $true)][string]$Label
    )
    $listeners = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
    if ($listeners.Count -eq 0) {
        Write-Host "$Label is not listening on port $Port."
        return
    }

    $processes = @(Get-CimInstance Win32_Process)
    $repoPattern = [regex]::Escape($script:FitnessWindowsRepo)
    foreach ($listener in $listeners) {
        $chain = @(Get-FitnessProcessChain -ProcessId $listener.OwningProcess -Processes $processes)
        $chainText = ($chain | ForEach-Object { $_.CommandLine }) -join "`n"
        if ($chain.Count -eq 0 -or $chainText -notmatch $repoPattern -or $chainText -notmatch $ExpectedCommandPattern) {
            Write-Warning "Refusing to stop PID $($listener.OwningProcess) on port $Port; project ownership was not verified."
            continue
        }

        $ownedChain = @($chain | Where-Object {
            $_.CommandLine -and ($_.CommandLine -match $repoPattern -or $_.CommandLine -match $ExpectedCommandPattern)
        })
        foreach ($process in $ownedChain) {
            Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Milliseconds 250
        $remaining = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        if ($remaining) {
            throw "Verified $Label process tree did not release port $Port."
        }
        Write-Host "Stopped verified $Label process tree for port $Port."
    }
}

function fitness {
    @"
Health & Fitness Platform command menu

Primary Windows runtime
  cdf              Repository root + venv activation
  cdff             Next.js frontend directory
  fapi             Start FastAPI on http://127.0.0.1:8000
  ffront           Start the existing production Next.js build on http://127.0.0.1:3100
  ffrontbuild      Rebuild, then start the production Next.js frontend
  fvalidatefront   Run frontend lint and production build without starting it
  fcleannext       Clear the Next.js .next cache after frontend processes are stopped
  fstart / app     Start FastAPI and the existing production frontend build
  frestart         Stop scoped product processes, then start them again
  fnext / fnextfg  Optional Next.js development server on port 3000
  fopen            Open the canonical product URL
  fports           Inspect product and Ollama ports
  wstatus / wstop  Inspect or stop repo-scoped Windows product processes

Git and delivery safety
  fpull, gsync, gstate, gcheck, gacp
  fbranch, fmerge, fsweep, fmem, fdoctor, fsnap

Secondary Linux / legacy tooling
  lpull, lstatus, lsetup, lvalidate, lollama, lsh
  Linux is optional validation/runtime/demo infrastructure, not the daily canonical runtime.
  Streamlit is legacy/developer-only and is not started by the primary commands.
"@
}

function fhelp { fitness }

function cdf {
    Assert-FitnessRepo
    Set-Location $script:FitnessWindowsRepo
    $env:PYTHONPATH = $script:FitnessWindowsRepo
    $activate = Join-Path $script:FitnessWindowsRepo ".venv\Scripts\Activate.ps1"
    if (Test-Path -LiteralPath $activate) { . $activate }
}

function cdff {
    Assert-FitnessRepo
    Set-Location $script:FitnessFrontendDir
}

function fapi {
    Assert-FitnessRepo
    Assert-FitnessPortAvailable -Port $script:FitnessApiPort -Label "FastAPI"
    $python = Get-FitnessWindowsPython
    Start-Process -FilePath $python -ArgumentList @("-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "$script:FitnessApiPort") -WorkingDirectory $script:FitnessWindowsRepo -WindowStyle Hidden
    Write-Host "FastAPI starting on http://127.0.0.1:$script:FitnessApiPort"
}

function fkillapi {
    Stop-FitnessOwnedListener -Port $script:FitnessApiPort -ExpectedCommandPattern "uvicorn.+api\.main:app" -Label "FastAPI"
}

function ffront {
    Assert-FitnessRepo
    Assert-FitnessPortAvailable -Port $script:FitnessFrontendPort -Label "Production Next.js"
    if (-not (Test-Path -LiteralPath (Join-Path $script:FitnessFrontendDir ".next"))) {
        throw "No production frontend build found. Run ffrontbuild first."
    }
    $command = "Set-Location -LiteralPath '$($script:FitnessFrontendDir.Replace("'", "''"))'; `$env:FITNESS_API_BASE_URL='http://127.0.0.1:$script:FitnessApiPort'; npm run start -- --hostname 0.0.0.0 --port $script:FitnessFrontendPort"
    Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile", "-Command", $command) -WindowStyle Hidden
    Write-Host "Production Next.js frontend starting on http://127.0.0.1:$script:FitnessFrontendPort"
}

function ffrontbuild {
    Assert-FitnessRepo
    fkillfront
    Push-Location $script:FitnessFrontendDir
    try {
        $env:FITNESS_API_BASE_URL = "http://127.0.0.1:$script:FitnessApiPort"
        npm run build
        if ($LASTEXITCODE -ne 0) { throw "Frontend production build failed." }
    } finally { Pop-Location }
    ffront
}

function fvalidatefront {
    Assert-FitnessRepo
    Push-Location $script:FitnessFrontendDir
    try {
        npm run lint
        if ($LASTEXITCODE -ne 0) { throw "Frontend lint failed." }
        $env:FITNESS_API_BASE_URL = "http://127.0.0.1:$script:FitnessApiPort"
        npm run build
        if ($LASTEXITCODE -ne 0) { throw "Frontend production build failed." }
    } finally { Pop-Location }
}

function fcleannext {
    Assert-FitnessRepo
    $productionListener = Get-NetTCPConnection -LocalPort $script:FitnessFrontendPort -State Listen -ErrorAction SilentlyContinue
    $developmentListener = Get-NetTCPConnection -LocalPort $script:FitnessNextDevPort -State Listen -ErrorAction SilentlyContinue
    if ($productionListener -or $developmentListener) {
        throw "Refusing to clear frontend/.next while Next.js is listening on port $script:FitnessFrontendPort or $script:FitnessNextDevPort. Stop the relevant frontend process first with fkillfront or fkillnext."
    }

    $nextCache = Join-Path $script:FitnessFrontendDir ".next"
    if (-not (Test-Path -LiteralPath $nextCache)) {
        Write-Host "Next.js .next cache is already absent."
        return
    }

    Remove-Item -LiteralPath $nextCache -Recurse -Force
    Write-Host "Cleared Next.js .next cache."
}

function fkillfront {
    Stop-FitnessOwnedListener -Port $script:FitnessFrontendPort -ExpectedCommandPattern "next(?:\.exe)?\s+start|npm(?:\.cmd)?\s+run\s+start|next-server" -Label "production Next.js"
}

function fnext {
    Assert-FitnessRepo
    Assert-FitnessPortAvailable -Port $script:FitnessNextDevPort -Label "Development Next.js"
    $command = "Set-Location -LiteralPath '$($script:FitnessFrontendDir.Replace("'", "''"))'; `$env:FITNESS_API_BASE_URL='http://127.0.0.1:$script:FitnessApiPort'; npm run dev -- --hostname 0.0.0.0 --port $script:FitnessNextDevPort"
    Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile", "-Command", $command) -WindowStyle Hidden
    Write-Host "Optional Next.js development server starting on http://127.0.0.1:$script:FitnessNextDevPort"
}

function fnextfg {
    Assert-FitnessRepo
    Assert-FitnessPortAvailable -Port $script:FitnessNextDevPort -Label "Development Next.js"
    Push-Location $script:FitnessFrontendDir
    try {
        $env:FITNESS_API_BASE_URL = "http://127.0.0.1:$script:FitnessApiPort"
        npm run dev -- --hostname 0.0.0.0 --port $script:FitnessNextDevPort
    } finally { Pop-Location }
}

function fkillnext {
    Stop-FitnessOwnedListener -Port $script:FitnessNextDevPort -ExpectedCommandPattern "next(?:\.exe)?\s+dev|npm(?:\.cmd)?\s+run\s+dev" -Label "development Next.js"
}

function fstart { fapi; ffront }
function app { fstart }
function wapp { Write-Warning "wapp is retained for compatibility; use fstart or app."; fstart }

function frestart {
    wstop
    fstart
}

function fopen { Start-Process "http://127.0.0.1:$script:FitnessFrontendPort" }

function fports {
    $ports = @($script:FitnessApiPort, $script:FitnessFrontendPort, $script:FitnessNextDevPort, 11434)
    foreach ($port in $ports) {
        $label = switch ($port) {
            8000 { "FastAPI (primary)" }
            3100 { "Next.js production (primary)" }
            3000 { "Next.js development (optional)" }
            11434 { "Ollama (optional)" }
            default { "Configured service" }
        }
        $listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if ($listeners) { Write-Host ("{0}: LISTENING - {1}" -f $port, $label) }
        else { Write-Host ("{0}: stopped - {1}" -f $port, $label) }
    }
}

function wstatus {
    Write-Host "Repo-scoped Windows process status"
    $repoNeedle = $script:FitnessWindowsRepo.ToLowerInvariant()
    Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and $_.CommandLine.ToLowerInvariant().Contains($repoNeedle) -and
        ($_.CommandLine -match "uvicorn|next (start|dev)|npm(.cmd)? run (start|dev)")
    } | Select-Object ProcessId, Name, CommandLine
    fports
}

function wstop { fkillapi; fkillfront; fkillnext }

function fpull {
    Assert-FitnessRepo
    Assert-FitnessCleanTree
    Push-Location $script:FitnessWindowsRepo
    try {
        Invoke-FitnessGitChecked "Fetch origin" fetch origin --prune
        Invoke-FitnessGitChecked "Switch to main" switch main
        Invoke-FitnessGitChecked "Fast-forward main" pull --ff-only origin main
        Assert-FitnessMainMatchesOrigin
        Assert-FitnessCleanTree
        git status --short --branch
        git log -5 --oneline --decorate
    } finally { Pop-Location }
}

function gsync { fpull }

function gstate {
    Assert-FitnessRepo
    Push-Location $script:FitnessWindowsRepo
    try {
        git branch --show-current
        git status --short --branch
        git log -1 --oneline
    } finally { Pop-Location }
}

function gcheck {
    param(
        [ValidateSet("docs-only", "code", "full")]
        [string]$Mode = "docs-only"
    )
    Assert-FitnessRepo
    Push-Location $script:FitnessWindowsRepo
    try {
        git diff --check
        if ($LASTEXITCODE -ne 0) { throw "Git diff check failed." }
        & (Join-Path $script:FitnessWindowsRepo "scripts\dev_commit_check.ps1") -Mode $Mode
        $python = Get-FitnessWindowsPython
        & $python (Join-Path $script:FitnessWindowsRepo "tools\project_memory_check.py") --project-root $script:FitnessWindowsRepo
        if ($LASTEXITCODE -ne 0) { throw "Project-memory checker failed." }
        & $python -m pytest (Join-Path $script:FitnessWindowsRepo "tests\test_project_memory_check.py") -q
        if ($LASTEXITCODE -ne 0) { throw "Project-memory tests failed." }
        & $python (Join-Path $script:FitnessWindowsRepo "tools\dev_assistant.py") memory-check
        if ($LASTEXITCODE -ne 0) { throw "Developer-assistant memory check failed." }
        & $python (Join-Path $script:FitnessWindowsRepo "tools\dev_assistant.py") stale-doc-check
        if ($LASTEXITCODE -ne 0) { throw "Developer-assistant stale-doc check failed." }
        git status --short --untracked-files=all
        git diff --cached --name-only
    } finally { Pop-Location }
}

function gacp {
    param(
        [Parameter(Mandatory = $true)][string]$Message,
        [switch]$AllowMain
    )
    Assert-FitnessRepo
    Push-Location $script:FitnessWindowsRepo
    try {
        $branch = (git branch --show-current).Trim()
        if ($branch -eq "main" -and -not $AllowMain) { throw "Refusing to commit on main. Use -AllowMain only with explicit reviewed authorization." }
        Write-Host "No files are staged automatically. Review and stage explicitly before continuing."
        git diff --cached --stat
        if (-not (git diff --cached --name-only)) { throw "Nothing is staged." }
        git commit -m $Message
        if ($LASTEXITCODE -ne 0) { throw "Commit failed." }
        git push -u origin $branch
        if ($LASTEXITCODE -ne 0) { throw "Push failed." }
    } finally { Pop-Location }
}

function fbranch {
    param([Parameter(Mandatory = $true)][string]$Name)
    Assert-FitnessRepo
    Assert-FitnessCleanTree
    Push-Location $script:FitnessWindowsRepo
    try {
        Invoke-FitnessGitChecked "Fetch origin" fetch origin --prune
        Invoke-FitnessGitChecked "Switch to main" switch main
        Invoke-FitnessGitChecked "Fast-forward main" pull --ff-only origin main
        Assert-FitnessMainMatchesOrigin
        Assert-FitnessCleanTree
        Invoke-FitnessGitChecked "Create feature branch" switch -c $Name
        git status --short --branch
    } finally { Pop-Location }
}

function fmerge {
    param(
        [Parameter(Mandatory = $true)][string]$FeatureBranch,
        [Parameter(Mandatory = $true)][string]$AcceptedFinalCommit
    )
    Assert-FitnessRepo
    Assert-FitnessCleanTree
    Push-Location $script:FitnessWindowsRepo
    try {
        Invoke-FitnessGitChecked "Fetch origin" fetch origin --prune
        Invoke-FitnessGitChecked "Switch to main" switch main
        Invoke-FitnessGitChecked "Fast-forward main" pull --ff-only origin main
        Assert-FitnessMainMatchesOrigin
        Assert-FitnessCleanTree
        git cat-file -e "$AcceptedFinalCommit`^{commit}"
        if ($LASTEXITCODE -ne 0) { throw "Accepted final commit does not resolve to a commit object." }
        git merge-base --is-ancestor $AcceptedFinalCommit $FeatureBranch
        if ($LASTEXITCODE -ne 0) { throw "STOP: accepted final commit is not contained in the requested feature branch." }
        Invoke-FitnessGitChecked "Merge feature branch" merge --no-ff $FeatureBranch
        git merge-base --is-ancestor $AcceptedFinalCommit main
        if ($LASTEXITCODE -ne 0) { throw "STOP: accepted final feature commit is not an ancestor of main; do not push or snapshot." }
        Write-Host "Accepted-final-commit ancestry verified. Validate merged main before pushing."
    } finally { Pop-Location }
}

function fsweep {
    Assert-FitnessRepo
    Push-Location $script:FitnessWindowsRepo
    try {
        $markers = @(
            "content" + "Reference",
            "oai" + "cite",
            "file" + "cite",
            "tool" + "cite",
            "tool" + "Citation",
            "turn[0-9]+(search|fetch|view|open)[0-9]+",
            "utm_source=" + "chat" + "gpt",
            "chat" + "gpt\.com",
            "<paste latest commit>",
            "<paste snapshot filename>"
        )
        $pattern = $markers -join "|"
        git grep -n -E $pattern -- .
        if ($LASTEXITCODE -eq 1) {
            $global:LASTEXITCODE = 0
            Write-Host "Artifact contamination sweep clean."
        } elseif ($LASTEXITCODE -ne 0) {
            throw "Artifact contamination sweep failed."
        } else {
            throw "Artifact contamination sweep found matches."
        }
    } finally { Pop-Location }
}

function fbranches {
    Assert-FitnessRepo
    Push-Location $script:FitnessWindowsRepo
    try { git branch --merged main } finally { Pop-Location }
}

function fmem {
    Assert-FitnessRepo
    Push-Location $script:FitnessWindowsRepo
    try {
        $python = Get-FitnessWindowsPython
        & $python (Join-Path $script:FitnessWindowsRepo "tools\project_memory_check.py") --project-root $script:FitnessWindowsRepo
        if ($LASTEXITCODE -ne 0) { throw "Project-memory checker failed." }
        & $python (Join-Path $script:FitnessWindowsRepo "tools\dev_assistant.py") memory-check
        if ($LASTEXITCODE -ne 0) { throw "Developer-assistant memory check failed." }
        & $python (Join-Path $script:FitnessWindowsRepo "tools\dev_assistant.py") stale-doc-check
        if ($LASTEXITCODE -ne 0) { throw "Developer-assistant stale-doc check failed." }
        & $python (Join-Path $script:FitnessWindowsRepo "tools\dev_assistant.py") continuity-brief
        if ($LASTEXITCODE -ne 0) { throw "Developer-assistant continuity brief failed." }
        & $python -m pytest (Join-Path $script:FitnessWindowsRepo "tests\test_project_memory_check.py") -q
        if ($LASTEXITCODE -ne 0) { throw "Project-memory tests failed." }
    } finally { Pop-Location }
}

function fdoctor {
    Assert-FitnessRepo
    Write-Host "Repository: $script:FitnessWindowsRepo"
    Write-Host "Frontend:   $script:FitnessFrontendDir"
    Write-Host "Snapshots:  $script:FitnessSnapshotDir"
    Write-Host "Product:    http://127.0.0.1:$script:FitnessFrontendPort"
    Write-Host "Python:     $(Get-FitnessWindowsPython)"
    gstate
    fports
}

function fsnap {
    param([Parameter(Mandatory = $true)][string]$Slug)
    Assert-FitnessRepo
    Assert-FitnessCleanTree
    if ((Get-FitnessBranch) -ne "main") { throw "Snapshots are created only from clean main." }
    if ($Slug -notmatch "^[a-z0-9]+(?:-[a-z0-9]+)*$") { throw "Slug must use lowercase kebab-case." }
    New-Item -ItemType Directory -Path $script:FitnessSnapshotDir -Force | Out-Null
    Push-Location $script:FitnessWindowsRepo
    try {
        $commit = (git rev-parse --short HEAD).Trim()
        $date = Get-Date -Format "yyyy-MM-dd"
        $zipName = "fitness_ai_snapshot_${date}_${commit}_main_${Slug}.zip"
        $snapshotPath = Join-Path $script:FitnessSnapshotDir $zipName
        git archive --format=zip --output=$snapshotPath HEAD
        if ($LASTEXITCODE -ne 0) { throw "Snapshot creation failed." }
        Write-Host "Snapshot created: $snapshotPath"
    } finally { Pop-Location }
}

# Secondary Linux helpers. These do not define the canonical daily runtime.
function lpull { ssh $script:FitnessLinuxSsh "cd $script:FitnessLinuxRepo && git pull --ff-only" }
function lstatus { ssh $script:FitnessLinuxSsh "cd $script:FitnessLinuxRepo && git status --short --branch && git log -1 --oneline" }
function lsetup { ssh $script:FitnessLinuxSsh "cd $script:FitnessLinuxRepo && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" }
function lvalidate { ssh $script:FitnessLinuxSsh "cd $script:FitnessLinuxRepo && .venv/bin/python -m pytest -q" }
function lollama { ssh $script:FitnessLinuxSsh "curl -fsS http://127.0.0.1:11434/api/tags" }
function lsh { ssh $script:FitnessLinuxSsh }
