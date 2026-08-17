[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OutputRoot,

    [Parameter(Mandatory = $true)]
    [string]$Model,

    [Parameter(Mandatory = $true)]
    [string]$ReasoningEffort,

    [string]$PermissionProfile = "workspace-write; approval=automatic-review",

    [ValidateSet("disabled", "enabled-but-task-prohibited")]
    [string]$NetworkPolicy = "disabled",

    [ValidateRange(1, 240)]
    [int]$TimeBudgetMinutes = 30,

    [ValidateRange(1, 3)]
    [int]$MaxParallel = 3,

    [string]$AgentCommand = "codex",
    [string[]]$AgentPrefixArg = @(),
    [string[]]$TaskId = @(),
    [ValidateSet("A", "B", "C")]
    [string[]]$Variant = @(),
    [switch]$Resume,
    [switch]$DryRun,
    [switch]$StopOnFailure
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runner = Join-Path $scriptRoot "run_pilot.py"
$arguments = @(
    $runner,
    "--output-root", $OutputRoot,
    "--model", $Model,
    "--reasoning-effort", $ReasoningEffort,
    "--permission-profile", $PermissionProfile,
    "--network-policy", $NetworkPolicy,
    "--time-budget-minutes", [string]$TimeBudgetMinutes,
    "--max-parallel", [string]$MaxParallel,
    "--agent-command", $AgentCommand
)
foreach ($prefixArgument in $AgentPrefixArg) {
    $arguments += @("--agent-prefix-arg", $prefixArgument)
}
foreach ($selectedTaskId in $TaskId) {
    $arguments += @("--task-id", $selectedTaskId)
}
foreach ($selectedVariant in $Variant) {
    $arguments += @("--variant", $selectedVariant)
}
if ($Resume) { $arguments += "--resume" }
if ($DryRun) { $arguments += "--dry-run" }
if ($StopOnFailure) { $arguments += "--stop-on-failure" }

& python @arguments
exit $LASTEXITCODE
