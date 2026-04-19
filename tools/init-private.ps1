$privateRoot = ".private"
$directories = @(
    $privateRoot,
    (Join-Path $privateRoot "tasks"),
    (Join-Path $privateRoot "notes"),
    (Join-Path $privateRoot "ai")
)

foreach ($directory in $directories) {
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
}

$readmePath = Join-Path $privateRoot "README.md"
$templatePath = Join-Path "tools" "templates\private-readme.md"

if ((-not (Test-Path $readmePath)) -and (Test-Path $templatePath)) {
    [System.IO.File]::Copy($templatePath, $readmePath, $false)
}
