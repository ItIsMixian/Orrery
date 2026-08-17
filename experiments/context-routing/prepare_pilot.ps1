[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OutputRoot,

    [ValidateSet("PO-CR-004")]
    [string]$TaskId = "PO-CR-004"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $scriptRoot "..\..")).Path
$outputFullPath = [System.IO.Path]::GetFullPath($OutputRoot)
$repoFullPath = [System.IO.Path]::GetFullPath($repoRoot)
$repoPrefix = $repoFullPath.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar

if ($outputFullPath.Equals($repoFullPath, [System.StringComparison]::OrdinalIgnoreCase) -or
    $outputFullPath.StartsWith($repoPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "OutputRoot must be outside the Project Orrery source repository."
}

if (Test-Path -LiteralPath $outputFullPath) {
    throw "OutputRoot already exists. Choose a new empty path: $outputFullPath"
}

$task = @{
    Id = "PO-CR-004"
    BaseCommit = "e0680523e4cacde2e8413188e04e801e9c2c1c81"
}

& git -C $repoRoot cat-file -e "$($task.BaseCommit)^{commit}"
if ($LASTEXITCODE -ne 0) {
    throw "The benchmark base commit is unavailable in the source repository."
}

New-Item -ItemType Directory -Path $outputFullPath | Out-Null
$archivePath = Join-Path $outputFullPath "_baseline.zip"

& git -C $repoRoot archive --format=zip --output=$archivePath $task.BaseCommit
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $archivePath)) {
    throw "Failed to create the benchmark baseline archive."
}

$created = @()
foreach ($variant in @("A", "B", "C")) {
    $targetPath = Join-Path $outputFullPath "$($task.Id)-$variant"
    New-Item -ItemType Directory -Path $targetPath | Out-Null
    Expand-Archive -LiteralPath $archivePath -DestinationPath $targetPath

    & git -C $targetPath init -b benchmark | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "git init failed for $targetPath" }

    & git -C $targetPath add --all
    if ($LASTEXITCODE -ne 0) { throw "git add failed for $targetPath" }

    & git -C $targetPath -c user.name="Project Orrery Benchmark" -c user.email="benchmark@local.invalid" commit -m "benchmark baseline $($task.Id) variant $variant" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "baseline commit failed for $targetPath" }

    $created += $targetPath
}

if ([System.IO.Path]::GetDirectoryName($archivePath) -ne $outputFullPath) {
    throw "Refusing to remove an archive outside OutputRoot."
}
Remove-Item -LiteralPath $archivePath -Force

Write-Output "Prepared isolated benchmark repositories with no remotes or future Project Orrery history:"
$created | ForEach-Object { Write-Output "  $_" }
Write-Output "Open each directory in a separate new Codex task and use the matching prompt under experiments/context-routing/prompts/."
