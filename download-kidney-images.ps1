# Kidney Histology Book - Image Acquisition Script
# Pure ASCII to avoid PowerShell encoding issues on Windows.

# Step 1: Create target directory
$targetDir = "assets\images\kidney-h-and-e"
New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
Write-Host "Created: $targetDir" -ForegroundColor Green

# Step 2: Image manifest
$images = @(
    @{
        WikimediaFile = "Kidney-Cortex.JPG"
        LocalFile = "01-normal-cortex.jpg"
        Description = "Normal human kidney cortex"
        Author = "Jpogi"
        License = "Public Domain"
    },
    @{
        WikimediaFile = "Arteriolosclerosis,_kidney,_HE_2.JPG"
        LocalFile = "07-arteriolosclerosis.jpg"
        Description = "Arteriolosclerosis in kidney"
        Author = "Wikimedia contributor"
        License = "CC-BY-SA 3.0"
    },
    @{
        WikimediaFile = "Histopathology_of_tubular_atrophy.png"
        LocalFile = "10-tubular-atrophy.png"
        Description = "Tubular atrophy"
        Author = "Mikael Haggstrom MD"
        License = "CC0 1.0"
    },
    @{
        WikimediaFile = "Histopathology_of_renal_autolysis.jpg"
        LocalFile = "12-renal-autolysis.jpg"
        Description = "Renal autolysis postmortem artifact"
        Author = "Mikael Haggstrom MD"
        License = "CC0 1.0"
    }
)

# Step 3: Download
$baseUrl = "https://commons.wikimedia.org/wiki/Special:FilePath/"
$failures = @()
$successes = 0

foreach ($img in $images) {
    $url = $baseUrl + $img.WikimediaFile
    $dest = Join-Path $targetDir $img.LocalFile
    Write-Host ""
    Write-Host "Downloading: $($img.LocalFile)" -ForegroundColor Cyan
    Write-Host "  Source: $($img.WikimediaFile)"
    Write-Host "  Author: $($img.Author)"
    Write-Host "  License: $($img.License)"
    try {
        Invoke-WebRequest -Uri $url -OutFile $dest -UserAgent "Mozilla/5.0" -ErrorAction Stop
        $sizeKB = [math]::Round((Get-Item $dest).Length / 1KB, 1)
        Write-Host "  [OK] Downloaded ($sizeKB KB)" -ForegroundColor Green
        $successes++
    } catch {
        Write-Host "  [FAIL] $_" -ForegroundColor Red
        $failures += $img.LocalFile
    }
}

# Step 4: Summary
Write-Host ""
Write-Host ("-" * 60)
Write-Host "SUMMARY: $successes succeeded, $($failures.Count) failed" -ForegroundColor Cyan

if ($failures.Count -gt 0) {
    Write-Host "Failed downloads:" -ForegroundColor Yellow
    $failures | ForEach-Object { Write-Host "  - $_" }
}

# Step 5: Write attribution file
$attribLines = @("# Image Attributions", "", "Sources from Wikimedia Commons.", "")
foreach ($img in $images) {
    $attribLines += "## $($img.LocalFile)"
    $attribLines += "- Source: https://commons.wikimedia.org/wiki/File:$($img.WikimediaFile)"
    $attribLines += "- Description: $($img.Description)"
    $attribLines += "- Author: $($img.Author)"
    $attribLines += "- License: $($img.License)"
    $attribLines += ""
}
$attribLines -join "`n" | Out-File -FilePath (Join-Path $targetDir "ATTRIBUTIONS.md") -Encoding utf8
Write-Host ""
Write-Host "Attribution file written: $targetDir\ATTRIBUTIONS.md" -ForegroundColor Green

Write-Host ""
Write-Host "Next step: launch Cowork with the kidney book prompt."
Write-Host "After Cowork writes chapters, run produce-book.py."
