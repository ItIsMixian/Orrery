[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OutputRoot,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Model,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ReasoningEffort,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$PermissionProfile,

    [ValidateNotNullOrEmpty()]
    [string]$Harness = "Codex desktop",

    [ValidateSet("disabled", "enabled-but-task-prohibited")]
    [string]$NetworkPolicy = "disabled",

    [ValidateRange(1, 240)]
    [int]$TimeBudgetMinutes = 30,

    [string]$TaskIds = "",

    [string]$Variants = ""
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

function Write-Utf8BomJson {
    param(
        [Parameter(Mandatory = $true)]
        [string]$LiteralPath,

        [Parameter(Mandatory = $true)]
        [object]$Value,

        [Parameter(Mandatory = $true)]
        [System.Text.Encoding]$Encoding
    )

    [System.IO.File]::WriteAllText(
        $LiteralPath,
        ($Value | ConvertTo-Json -Depth 12),
        $Encoding
    )
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $scriptRoot "..\..\..\..")).Path
$configPath = Join-Path $scriptRoot "pilot-config.json"
$config = [System.IO.File]::ReadAllText($configPath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json

$availableTaskIds = @($config.tasks | ForEach-Object { [string]$_.task_id })
$availableVariants = @($config.variants.PSObject.Properties.Name | ForEach-Object { [string]$_ })
$selectedTaskIds = if ([string]::IsNullOrWhiteSpace($TaskIds)) {
    @($availableTaskIds)
}
else {
    @($TaskIds.Split(",", [System.StringSplitOptions]::RemoveEmptyEntries) | ForEach-Object { $_.Trim() })
}
$selectedVariants = if ([string]::IsNullOrWhiteSpace($Variants)) {
    @($availableVariants)
}
else {
    @($Variants.Split(",", [System.StringSplitOptions]::RemoveEmptyEntries) | ForEach-Object { $_.Trim() })
}
if ($selectedTaskIds.Count -eq 0 -or $selectedVariants.Count -eq 0) {
    throw "At least one task and one variant must be selected."
}
if (@($selectedTaskIds | Select-Object -Unique).Count -ne $selectedTaskIds.Count) {
    throw "TaskIds must not contain duplicates."
}
if (@($selectedVariants | Select-Object -Unique).Count -ne $selectedVariants.Count) {
    throw "Variants must not contain duplicates."
}
foreach ($taskId in $selectedTaskIds) {
    if ($availableTaskIds -notcontains $taskId) { throw "Unknown selected task: $taskId" }
}
foreach ($variant in $selectedVariants) {
    if ($availableVariants -notcontains $variant) { throw "Unknown selected variant: $variant" }
}

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
if ($config.pilot_id -ne "pilot-004" -or $config.external_context_policy -ne "repository_only") {
    throw "Unexpected or unsafe pilot configuration."
}
if ($config.harness_overlay_path -ne ".codex/config.toml") {
    throw "Unexpected harness overlay path."
}
if ($config.agent_receipt_path -ne ".benchmark/agent-receipt.json") {
    throw "Unexpected Agent receipt path."
}

$commonProtocolPath = Join-Path $scriptRoot $config.common_protocol_file
$commonProtocol = [System.IO.File]::ReadAllText($commonProtocolPath, [System.Text.Encoding]::UTF8)
$receiptSchemaSource = Join-Path $scriptRoot $config.agent_receipt_schema
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
    "# It keeps external Skill context out of the B/H comparison.",
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

$executionProfile = [ordered]@{
    schema_version = 1
    pilot_id = $config.pilot_id
    recorded_at = (Get-Date).ToString("o")
    recorded_by = "operator"
    model = $Model
    reasoning_effort = $ReasoningEffort
    permission_profile = $PermissionProfile
    harness = $Harness
    network_policy = $NetworkPolicy
    time_budget_minutes = $TimeBudgetMinutes
    selected_task_ids = @($selectedTaskIds)
    selected_variants = @($selectedVariants)
}
$profilePath = Join-Path $operatorPath "execution-profile.json"
Write-Utf8BomJson -LiteralPath $profilePath -Value $executionProfile -Encoding $utf8WithBom
$profileSha256 = Get-Sha256Hex -LiteralPath $profilePath

$receiptSchemaPath = Join-Path $operatorPath "agent-receipt.schema.json"
[System.IO.File]::WriteAllText(
    $receiptSchemaPath,
    [System.IO.File]::ReadAllText($receiptSchemaSource, [System.Text.Encoding]::UTF8),
    $utf8WithBom
)
$receiptSchemaSha256 = Get-Sha256Hex -LiteralPath $receiptSchemaPath

$securityAcceptanceSource = Join-Path $scriptRoot $config.holdout_acceptance.path
$securityAcceptancePath = Join-Path $operatorPath "holdout-acceptance.py"
[System.IO.File]::WriteAllText(
    $securityAcceptancePath,
    [System.IO.File]::ReadAllText($securityAcceptanceSource, [System.Text.Encoding]::UTF8),
    $utf8WithBom
)
$securityAcceptanceSha256 = Get-Sha256Hex -LiteralPath $securityAcceptancePath

$runRecords = @()
$overlaySha256 = $null
$seenTaskIds = @{}

foreach ($selectedTaskId in $selectedTaskIds) {
    $taskConfig = @($config.tasks | Where-Object { $_.task_id -eq $selectedTaskId })[0]
    $taskId = [string]$taskConfig.task_id
    if ($seenTaskIds.ContainsKey($taskId)) {
        throw "Duplicate task in pilot configuration: $taskId"
    }
    $seenTaskIds[$taskId] = $true

    $baseCommit = [string]$config.baseline_commit
    & git -C $repoRoot cat-file -e "$baseCommit`^{commit}"
    if ($LASTEXITCODE -ne 0) {
        throw "Benchmark base commit is unavailable for $taskId."
    }

    $taskSourcePath = Join-Path $scriptRoot $taskConfig.task_file
    $taskInstructions = [System.IO.File]::ReadAllText($taskSourcePath, [System.Text.Encoding]::UTF8)
    if (-not $taskInstructions.Contains($taskId)) {
        throw "Task packet does not identify $taskId."
    }
    if ($taskInstructions.Contains($baseCommit)) {
        throw "Task packet leaks a historical commit identifier: $taskId"
    }

    $expectedWrites = @($taskConfig.expected_product_write_paths)
    if ($expectedWrites.Count -lt 1) { throw "Task has no allowed product path: $taskId" }
    $expectedWriteLines = @($expectedWrites | ForEach-Object { "- ``$_``" })
    $validationCommands = @($taskConfig.validation_commands)
    $validationLines = @()
    foreach ($command in $validationCommands) {
        $validationLines += "- ``$((@($command) -join ' '))``"
    }

    $archivePath = Join-Path $outputFullPath "_baseline-$taskId.zip"
    & git -C $repoRoot archive --format=zip --output=$archivePath $baseCommit
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $archivePath)) {
        throw "Failed to create benchmark baseline archive for $taskId."
    }

    foreach ($variant in $selectedVariants) {
        $variantSourcePath = Join-Path $scriptRoot $config.variants.$variant
        $variantInstructions = [System.IO.File]::ReadAllText($variantSourcePath, [System.Text.Encoding]::UTF8)
        $runKey = "$taskId-$variant"
        $contractHeader = @"
<!-- pilot_id: $($config.pilot_id) -->
<!-- prompt_revision: $($config.prompt_revision) -->
<!-- task_id: $taskId -->
<!-- variant: $variant -->

# RUN CONTRACT

- `pilot_id`: `$($config.pilot_id)`
- `prompt_revision`: `$($config.prompt_revision)`
- `task_id`: `$taskId`
- `variant`: `$variant`
- `agent_receipt_path`: `$($config.agent_receipt_path)`
- `agent_receipt_schema_sha256`: `$receiptSchemaSha256`

## expected_product_writes

$($expectedWriteLines -join [System.Environment]::NewLine)

## validation_commands

$($validationLines -join [System.Environment]::NewLine)
"@
        $prompt = @"
$($contractHeader.TrimEnd())

---

$($commonProtocol.TrimEnd())

---

$($taskInstructions.TrimEnd())

---

$($variantInstructions.TrimEnd())
"@

        $promptPath = Join-Path $operatorPath "PROMPT-$runKey.zh-CN.md"
        [System.IO.File]::WriteAllText($promptPath, $prompt, $utf8WithBom)

        $targetPath = Join-Path $outputFullPath $runKey
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
            throw "Harness overlays differ between prepared repositories."
        }

        & git -C $targetPath init -b benchmark | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "git init failed for $targetPath" }
        & git -C $targetPath add --all
        if ($LASTEXITCODE -ne 0) { throw "git add failed for $targetPath" }
        & git -C $targetPath -c user.name="Project Orrery Benchmark" -c user.email="benchmark@local.invalid" commit -m "benchmark baseline $runKey $($config.pilot_id)" | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "baseline commit failed for $targetPath" }

        $excludePath = Join-Path $targetPath ".git\info\exclude"
        $excludeText = [System.IO.File]::ReadAllText($excludePath, [System.Text.Encoding]::UTF8)
        if (-not $excludeText.Contains($config.agent_receipt_path)) {
            if ($excludeText.Length -gt 0 -and -not $excludeText.EndsWith("`n")) {
                $excludeText += [System.Environment]::NewLine
            }
            $excludeText += $config.agent_receipt_path + [System.Environment]::NewLine
            [System.IO.File]::WriteAllText($excludePath, $excludeText, $utf8NoBom)
        }

        $head = (& git -C $targetPath rev-parse HEAD).Trim()
        if ($LASTEXITCODE -ne 0) { throw "failed to resolve benchmark HEAD for $targetPath" }

        $runRecords += [ordered]@{
            run_key = $runKey
            task_id = $taskId
            task_category = [string]$taskConfig.category
            task_risk = [string]$taskConfig.risk
            variant = $variant
            source_base_commit = $baseCommit
            repository_path = $targetPath
            repository_commit = $head
            prompt_path = $promptPath
            prompt_sha256 = Get-Sha256Hex -LiteralPath $promptPath
            task_packet_sha256 = Get-Sha256Hex -LiteralPath $taskSourcePath
            variant_instruction_sha256 = Get-Sha256Hex -LiteralPath $variantSourcePath
            expected_product_write_paths = $expectedWrites
            validation_commands = $validationCommands
        }
    }

    $archiveParent = [System.IO.Path]::GetFullPath([System.IO.Path]::GetDirectoryName($archivePath))
    if (-not $archiveParent.Equals($outputFullPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove an archive outside OutputRoot."
    }
    Remove-Item -LiteralPath $archivePath -Force
}

$manifest = [ordered]@{
    schema_version = 1
    pilot_id = $config.pilot_id
    prompt_revision = $config.prompt_revision
    generated_at = (Get-Date).ToString("o")
    external_context_policy = $config.external_context_policy
    selection = [ordered]@{
        task_ids = @($selectedTaskIds)
        variants = @($selectedVariants)
        run_count = $runRecords.Count
        purpose = "Explicit Harness selection; omitted configured runs are outside this experiment, not missing evidence."
    }
    execution_profile = [ordered]@{
        path = "execution-profile.json"
        sha256 = $profileSha256
        evidence_origin = "operator"
    }
    harness_overlay = [ordered]@{
        path = $config.harness_overlay_path
        sha256 = $overlaySha256
        disabled_skill_ids = @($config.disabled_skill_ids)
        purpose = "Disable current external Skill context equally across all variants."
    }
    agent_receipt = [ordered]@{
        path = $config.agent_receipt_path
        schema_path = "agent-receipt.schema.json"
        schema_sha256 = $receiptSchemaSha256
        evidence_origin = "agent"
    }
    holdout_acceptance = [ordered]@{
        path = "holdout-acceptance.py"
        sha256 = $securityAcceptanceSha256
        task_ids = @($config.holdout_acceptance.task_ids)
        evidence_origin = "operator"
    }
    baseline_commit = [string]$config.baseline_commit
    task_order_seed = [int]$config.task_order_seed
    frozen_h_sha256 = Get-Sha256Hex -LiteralPath (Join-Path $scriptRoot $config.variants.H)
    common_protocol_sha256 = Get-Sha256Hex -LiteralPath $commonProtocolPath
    runs = $runRecords
}
$manifestPath = Join-Path $operatorPath "pilot-manifest.json"
Write-Utf8BomJson -LiteralPath $manifestPath -Value $manifest -Encoding $utf8WithBom

$operatorRuns = @($runRecords | ForEach-Object {
    [ordered]@{
        run_key = $_.run_key
        task_id = $_.task_id
        variant = $_.variant
        prompt_path = $_.prompt_path
        prompt_sha256 = $_.prompt_sha256
        status = "pending"
        operator_started_at = $null
        operator_ended_at = $null
        thread_id = $null
        interventions = @()
        notes = @()
    }
})
$operatorLog = [ordered]@{
    schema_version = 1
    pilot_id = $config.pilot_id
    execution_profile_sha256 = $profileSha256
    created_at = (Get-Date).ToString("o")
    sealed_at = $null
    operator_attestation = $null
    runs = $operatorRuns
}
$operatorLogPath = Join-Path $operatorPath "operator-run-log.json"
Write-Utf8BomJson -LiteralPath $operatorLogPath -Value $operatorLog -Encoding $utf8WithBom

Write-Output "Prepared $($runRecords.Count) isolated repositories for $($config.pilot_id)."
Write-Output "Execution profile: $profilePath"
Write-Output "Operator run log: $operatorLogPath"
Write-Output "Pilot manifest: $manifestPath"
Write-Output "Use record_operator_run.ps1 -Action Start -CopyPrompt before opening each fresh task."
