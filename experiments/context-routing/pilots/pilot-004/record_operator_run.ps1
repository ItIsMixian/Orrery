[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OutputRoot,

    [Parameter(Mandatory = $true)]
    [ValidateSet("Start", "Finish", "Contaminate", "Intervention", "Seal")]
    [string]$Action,

    [string]$RunKey,
    [string]$TaskId,
    [string]$Message,
    [string]$ThreadId,
    [switch]$CopyPrompt,
    [switch]$ConfirmSameExecutionSettings
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

function Write-Utf8BomJson {
    param(
        [Parameter(Mandatory = $true)]
        [string]$LiteralPath,

        [Parameter(Mandatory = $true)]
        [object]$Value
    )

    $encoding = New-Object System.Text.UTF8Encoding($true)
    [System.IO.File]::WriteAllText(
        $LiteralPath,
        ($Value | ConvertTo-Json -Depth 12),
        $encoding
    )
}

$outputFullPath = [System.IO.Path]::GetFullPath($OutputRoot)
$operatorPath = Join-Path $outputFullPath "_operator"
$manifestPath = Join-Path $operatorPath "pilot-manifest.json"
$profilePath = Join-Path $operatorPath "execution-profile.json"
$logPath = Join-Path $operatorPath "operator-run-log.json"

foreach ($requiredPath in @($manifestPath, $profilePath, $logPath)) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        throw "Missing pilot operator artifact: $requiredPath"
    }
}

$manifest = [System.IO.File]::ReadAllText($manifestPath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
$log = [System.IO.File]::ReadAllText($logPath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
if ($manifest.pilot_id -ne "pilot-004" -or $log.pilot_id -ne $manifest.pilot_id) {
    throw "This helper only accepts a pilot-004 output root."
}
if ($null -ne $log.sealed_at) {
    throw "Operator log is already sealed and cannot be changed."
}

$currentProfileSha256 = Get-Sha256Hex -LiteralPath $profilePath
if ($currentProfileSha256 -ne $manifest.execution_profile.sha256 -or
    $currentProfileSha256 -ne $log.execution_profile_sha256) {
    throw "Execution profile checksum mismatch. Do not continue this pilot."
}

$now = (Get-Date).ToString("o")

if ($Action -in @("Start", "Finish", "Contaminate")) {
    if ([string]::IsNullOrWhiteSpace($RunKey)) {
        throw "-$Action requires -RunKey."
    }
    $matches = @($log.runs | Where-Object { $_.run_key -eq $RunKey })
    if ($matches.Count -ne 1) {
        throw "RunKey must resolve exactly once: $RunKey"
    }
    $run = $matches[0]

    if ($Action -eq "Start") {
        if ($run.status -ne "pending") {
            throw "Run is not pending: $RunKey ($($run.status))"
        }
        $run.status = "running"
        $run.operator_started_at = $now
        if (-not [string]::IsNullOrWhiteSpace($ThreadId)) {
            $run.thread_id = $ThreadId
        }
        if ($CopyPrompt) {
            $promptText = [System.IO.File]::ReadAllText([string]$run.prompt_path, [System.Text.Encoding]::UTF8)
            Set-Clipboard -Value $promptText
        }
    }
    elseif ($Action -eq "Finish") {
        if ($run.status -ne "running") {
            throw "Run is not running: $RunKey ($($run.status))"
        }
        $manifestRun = @($manifest.runs | Where-Object { $_.run_key -eq $RunKey })[0]
        $receiptPath = Join-Path ([string]$manifestRun.repository_path) ([string]$manifest.agent_receipt.path)
        if (-not (Test-Path -LiteralPath $receiptPath -PathType Leaf)) {
            throw "Agent receipt is missing; do not mark the run finished: $receiptPath"
        }
        $run.status = "completed"
        $run.operator_ended_at = $now
        if (-not [string]::IsNullOrWhiteSpace($ThreadId)) {
            $run.thread_id = $ThreadId
        }
    }
    else {
        if ($run.status -notin @("pending", "running")) {
            throw "Run cannot be marked contaminated from status $($run.status): $RunKey"
        }
        if ([string]::IsNullOrWhiteSpace($Message)) {
            throw "Contaminate requires -Message with a redacted reason."
        }
        $run.status = "contaminated"
        if ($null -eq $run.operator_started_at) {
            $run.operator_started_at = $now
        }
        $run.operator_ended_at = $now
        if (-not [string]::IsNullOrWhiteSpace($ThreadId)) {
            $run.thread_id = $ThreadId
        }
        $run.notes = @($run.notes) + @("CONTAMINATED: $Message")
    }
}
elseif ($Action -eq "Intervention") {
    if ([string]::IsNullOrWhiteSpace($TaskId) -or [string]::IsNullOrWhiteSpace($Message)) {
        throw "Intervention requires -TaskId and -Message."
    }
    $taskRuns = @($log.runs | Where-Object { $_.task_id -eq $TaskId })
    if ($taskRuns.Count -ne 3) {
        throw "A synchronized intervention requires exactly three variants for $TaskId."
    }
    $entry = [ordered]@{
        recorded_at = $now
        message = $Message
        applies_to = @($taskRuns | ForEach-Object { $_.run_key })
    }
    foreach ($run in $taskRuns) {
        $run.interventions = @($run.interventions) + @($entry)
    }
}
else {
    if (-not $ConfirmSameExecutionSettings) {
        throw "Seal requires -ConfirmSameExecutionSettings."
    }
    $unfinished = @($log.runs | Where-Object { $_.status -notin @("completed", "contaminated") })
    if ($unfinished.Count -gt 0) {
        throw "Cannot seal; unfinished runs: $((@($unfinished | ForEach-Object { $_.run_key })) -join ', ')"
    }
    $log.sealed_at = $now
    $log.operator_attestation = [ordered]@{
        confirmed_at = $now
        same_execution_profile_used = $true
        unrecorded_interventions = $false
        statement = "All runs used the checksummed execution profile; all operator interventions are recorded in this log."
    }
}

Write-Utf8BomJson -LiteralPath $logPath -Value $log

if ($Action -eq "Start" -and $CopyPrompt) {
    Write-Output "Started $RunKey and copied its full Prompt to the clipboard."
}
elseif ($Action -eq "Intervention") {
    Write-Output "Recorded one synchronized intervention for all variants of $TaskId."
}
elseif ($Action -eq "Seal") {
    Write-Output "Sealed operator log: $logPath"
}
else {
    Write-Output "$Action recorded for $RunKey."
}
