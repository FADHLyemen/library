# LLM4Yemen -- Add Dr. Yousif Alyousifi to teaching team
# Run from repo root: C:\Users\FUJITSU-T902\Downloads\llm4yemen-site\site
# If blocked: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = "C:\Users\FUJITSU-T902\Downloads\llm4yemen-site\site"

Write-Host "=== LLM4Yemen Team Update: Adding Dr. Yousif Alyousifi ===" -ForegroundColor Cyan

# Copy updated files
$files = @("team.html", "curriculum.html", "index.html")
foreach ($f in $files) {
    $src = Join-Path $scriptDir $f
    $dst = Join-Path $repoRoot $f
    Copy-Item -Path $src -Destination $dst -Force
    Write-Host "  Copied: $f" -ForegroundColor Green
}

# Git commit and push
Set-Location $repoRoot
git add team.html curriculum.html index.html
git commit -m "Add Dr. Yousif Alyousifi to teaching team + assign instructors to all weeks/books"
git push

Write-Host ""
Write-Host "=== Done! Live at: https://fadhlyemen.github.io/llm4yemen/team.html ===" -ForegroundColor Cyan
