[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OutputRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-Sha256Hex {
    param(
        [Parameter(Mandatory = $true)]
        [string]$LiteralPath
    )

    $stream = [System.IO.File]::OpenRead($LiteralPath)
    try {
        $sha256 = [System.Security.Cryptography.SHA256]::Create()
        try {
            $hashBytes = $sha256.ComputeHash($stream)
            return -join ($hashBytes | ForEach-Object { $_.ToString("x2") })
        }
        finally {
            $sha256.Dispose()
        }
    }
    finally {
        $stream.Dispose()
    }
}

function ConvertTo-TomlQuotedPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    return $Path.Replace("\", "/").Replace('"', '\"')
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $scriptRoot "..\..\..\..")).Path
$configPath = Join-Path $scriptRoot "pilot-config.json"
$config = [System.IO.File]::ReadAllText($configPath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json

$outputFullPath = [System.IO.Path]::GetFullPath($OutputRoot)
$repoFullPath = [System.IO.Path]::GetFullPath($repoRoot)
$repoPrefix = $repoFullPath.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar

if ($outputFullPath.Equals($repoFullPath, [System.StringComparison]::OrdinalIgnoreCase) -or
    $outputFullPath.StartsWith($repoPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "OutputRoot must be outside the Project Orrery source repository."
}

if (Test-Path -LiteralPath $outputFullPath) {
    throw "OutputRoot already exists. Choose a new path: $outputFullPath"
}

if ($config.task_id -ne "PO-CR-004" -or $config.external_context_policy -ne "repository_only") {
    throw "Unexpected or unsafe pilot configuration."
}

if ($config.harness_overlay_path -ne ".codex/config.toml") {
    throw "Unexpected harness overlay path."
}

& git -C $repoRoot cat-file -e "$($config.base_commit)^{commit}"
if ($LASTEXITCODE -ne 0) {
    throw "The benchmark base commit is unavailable in the source repository."
}

$commonTaskPath = Join-Path $scriptRoot $config.common_task_file
$commonTask = [System.IO.File]::ReadAllText($commonTaskPath, [System.Text.Encoding]::UTF8)
if (-not $commonTask.Contains($config.canonical_skill_url)) {
    throw "The common task packet does not contain the canonical Skill URL."
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$utf8WithBom = New-Object System.Text.UTF8Encoding($true)
$userProfilePath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::UserProfile)
$codexConfigRoot = if ([string]::IsNullOrWhiteSpace($env:CODEX_HOME)) {
    Join-Path $userProfilePath ".codex"
}
else {
    [System.IO.Path]::GetFullPath($env:CODEX_HOME)
}
$disabledSkillPaths = @(
    (Join-Path $codexConfigRoot "skills\project-orrery"),
    (Join-Path $userProfilePath ".agents\skills\project-orrery"),
    (Join-Path $codexConfigRoot "skills\.system\openai-docs"),
    (Join-Path $codexConfigRoot "skills\.system\skill-installer")
) | Select-Object -Unique
$overlayLines = @(
    "# Generated benchmark harness overlay. Do not edit or use as task evidence.",
    "# It keeps external Skill context out of the A/B/C comparison.",
    ""
)
foreach ($skillPath in $disabledSkillPaths) {
    $overlayLines += "[[skills.config]]"
    $overlayLines += "path = `"$(ConvertTo-TomlQuotedPath -Path $skillPath)`""
    $overlayLines += "enabled = false"
    $overlayLines += ""
}
$overlayContent = $overlayLines -join [System.Environment]::NewLine

New-Item -ItemType Directory -Path $outputFullPath | Out-Null
$operatorPath = Join-Path $outputFullPath "_operator"
New-Item -ItemType Directory -Path $operatorPath | Out-Null
$archivePath = Join-Path $outputFullPath "_baseline.zip"

& git -C $repoRoot archive --format=zip --output=$archivePath $config.base_commit
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $archivePath)) {
    throw "Failed to create the benchmark baseline archive."
}

$variantRecords = @()
$overlaySha256 = $null
foreach ($variant in @("A", "B", "C")) {
    $variantRelativePath = $config.variants.$variant
    $variantSourcePath = Join-Path $scriptRoot $variantRelativePath
    $variantInstructions = [System.IO.File]::ReadAllText($variantSourcePath, [System.Text.Encoding]::UTF8)
    $prompt = @"
<!-- prompt_revision: $($config.prompt_revision) -->
<!-- variant: $variant -->

$($commonTask.TrimEnd())

---

$($variantInstructions.TrimEnd())
"@

    $promptPath = Join-Path $operatorPath "PROMPT-$variant.zh-CN.md"
    [System.IO.File]::WriteAllText($promptPath, $prompt, $utf8WithBom)

    $targetPath = Join-Path $outputFullPath "$($config.task_id)-$variant"
    New-Item -ItemType Directory -Path $targetPath | Out-Null
    Expand-Archive -LiteralPath $archivePath -DestinationPath $targetPath

    $overlayPath = Join-Path $targetPath $config.harness_overlay_path
    New-Item -ItemType Directory -Path (Split-Path -Parent $overlayPath) -Force | Out-Null
    [System.IO.File]::WriteAllText($overlayPath, $overlayContent, $utf8NoBom)
    $currentOverlaySha256 = Get-Sha256Hex -LiteralPath $overlayPath
    if ($null -eq $overlaySha256) {
        $overlaySha256 = $currentOverlaySha256
    }
    elseif ($overlaySha256 -ne $currentOverlaySha256) {
        throw "Harness overlays differ between variants."
    }

    & git -C $targetPath init -b benchmark | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "git init failed for $targetPath" }
    & git -C $targetPath add --all
    if ($LASTEXITCODE -ne 0) { throw "git add failed for $targetPath" }
    & git -C $targetPath -c user.name="Project Orrery Benchmark" -c user.email="benchmark@local.invalid" commit -m "benchmark baseline $($config.task_id) $($config.pilot_id) variant $variant" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "baseline commit failed for $targetPath" }

    $head = (& git -C $targetPath rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0) { throw "failed to resolve benchmark HEAD for $targetPath" }

    $variantRecords += [ordered]@{
        variant = $variant
        repository_path = $targetPath
        repository_commit = $head
        prompt_path = $promptPath
        prompt_sha256 = Get-Sha256Hex -LiteralPath $promptPath
        variant_instruction_sha256 = Get-Sha256Hex -LiteralPath $variantSourcePath
    }
}

$archiveParent = [System.IO.Path]::GetFullPath([System.IO.Path]::GetDirectoryName($archivePath))
if (-not $archiveParent.Equals($outputFullPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to remove an archive outside OutputRoot."
}
Remove-Item -LiteralPath $archivePath -Force

$manifest = [ordered]@{
    schema_version = 1
    pilot_id = $config.pilot_id
    task_id = $config.task_id
    prompt_revision = $config.prompt_revision
    generated_at = (Get-Date).ToString("o")
    source_base_commit = $config.base_commit
    canonical_skill_url = $config.canonical_skill_url
    external_context_policy = $config.external_context_policy
    harness_overlay = [ordered]@{
        path = $config.harness_overlay_path
        sha256 = $overlaySha256
        disabled_skill_ids = @($config.disabled_skill_ids)
        purpose = "Disable current external Skill context equally across all variants."
    }
    common_task_sha256 = Get-Sha256Hex -LiteralPath $commonTaskPath
    allowed_post_edit_commands = @($config.allowed_post_edit_commands)
    variants = $variantRecords
}

$manifestPath = Join-Path $operatorPath "pilot-manifest.json"
[System.IO.File]::WriteAllText(
    $manifestPath,
    ($manifest | ConvertTo-Json -Depth 8),
    $utf8WithBom
)

Write-Output "Prepared $($config.pilot_id) repositories and checksummed prompts:"
$variantRecords | ForEach-Object {
    Write-Output "  $($_.variant): $($_.repository_path)"
    Write-Output "     prompt: $($_.prompt_path)"
    Write-Output "     sha256: $($_.prompt_sha256)"
}
Write-Output "Operator manifest: $manifestPath"
Write-Output "Send the entire matching PROMPT file as the first message in each fresh task."
