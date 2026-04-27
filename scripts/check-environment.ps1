# =============================================================================
# check-environment.ps1
# =============================================================================
# Verifies all dependencies are installed correctly for the book production
# pipeline on a Windows machine.
#
# USAGE:
#   1. Open PowerShell as Administrator (or regular if you prefer)
#   2. Navigate to the library folder
#   3. Run: powershell -ExecutionPolicy Bypass -File check-environment.ps1
#
# OR if execution policy isn't set:
#   Right-click and select "Run with PowerShell"
#
# =============================================================================

$ErrorActionPreference = "Continue"
$WarningPreference = "Continue"

# Track results
$script:passed = 0
$script:warned = 0
$script:failed = 0

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host "===============================================================================" -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host "===============================================================================" -ForegroundColor Cyan
}

function Write-Pass {
    param([string]$Message)
    Write-Host "  [OK]   " -NoNewline -ForegroundColor Green
    Write-Host $Message
    $script:passed++
}

function Write-Warn {
    param([string]$Message, [string]$Hint = "")
    Write-Host "  [WARN] " -NoNewline -ForegroundColor Yellow
    Write-Host $Message
    if ($Hint) {
        Write-Host "         Hint: $Hint" -ForegroundColor DarkYellow
    }
    $script:warned++
}

function Write-Fail {
    param([string]$Message, [string]$Fix = "")
    Write-Host "  [FAIL] " -NoNewline -ForegroundColor Red
    Write-Host $Message
    if ($Fix) {
        Write-Host "         Fix:  $Fix" -ForegroundColor DarkRed
    }
    $script:failed++
}

function Test-Command {
    param([string]$Cmd)
    return [bool](Get-Command $Cmd -ErrorAction SilentlyContinue)
}

function Get-CommandVersion {
    param([string]$Cmd, [string]$VersionFlag = "--version")
    try {
        $output = & $Cmd $VersionFlag 2>&1 | Select-Object -First 1
        return $output.ToString().Trim()
    } catch {
        return "(version not available)"
    }
}

# =============================================================================
# Main checks
# =============================================================================

Clear-Host
Write-Host ""
Write-Host "  Library Production Pipeline - Environment Check" -ForegroundColor White
Write-Host "  Target machine: $env:COMPUTERNAME ($env:USERNAME)" -ForegroundColor Gray
Write-Host "  Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray

$libraryPath = "C:\Users\FUJITSU-T902\Downloads\library"

# -----------------------------------------------------------------------------
Write-Header "1. Library folder structure"
# -----------------------------------------------------------------------------

if (Test-Path $libraryPath) {
    Write-Pass "Library folder exists at $libraryPath"

    $requiredFolders = @("scripts", "data", "assets", "assets\fonts", "assets\books", "assets\covers", "css", "js", "drafts")
    foreach ($folder in $requiredFolders) {
        $full = Join-Path $libraryPath $folder
        if (Test-Path $full) {
            Write-Pass "Folder exists: $folder"
        } else {
            if ($folder -eq "drafts") {
                Write-Warn "Folder missing: $folder" "Will be created automatically when you produce a book"
            } else {
                Write-Fail "Folder missing: $folder" "Copy this folder from your old machine"
            }
        }
    }

    $requiredFiles = @(
        "index.html",
        "css\style.css",
        "js\main.js",
        "data\books.json",
        "scripts\produce-book.py",
        "assets\fonts\Amiri-Regular.ttf",
        "assets\fonts\Amiri-Bold.ttf"
    )
    foreach ($file in $requiredFiles) {
        $full = Join-Path $libraryPath $file
        if (Test-Path $full) {
            $sizeBytes = (Get-Item $full).Length
            $sizeKB = [math]::Round($sizeBytes / 1024, 1)
            Write-Pass "File exists: $file ($sizeKB KB)"
        } else {
            Write-Fail "File missing: $file" "Copy from your old machine"
        }
    }
} else {
    Write-Fail "Library folder not found at $libraryPath" "Copy the entire library folder from your old machine to this path"
    Write-Host ""
    Write-Host "Cannot continue checks without the library folder. Exiting." -ForegroundColor Red
    exit 1
}

# -----------------------------------------------------------------------------
Write-Header "2. Critical script integrity"
# -----------------------------------------------------------------------------

$scriptPath = Join-Path $libraryPath "scripts\produce-book.py"
if (Test-Path $scriptPath) {
    $size = (Get-Item $scriptPath).Length
    $lineCount = (Get-Content $scriptPath).Count

    if ($size -gt 40000) {
        Write-Pass "produce-book.py size: $size bytes (expected ~45000)"
    } else {
        Write-Fail "produce-book.py size: $size bytes (expected ~45000)" "Re-copy the file - it appears truncated"
    }

    if ($lineCount -gt 1100) {
        Write-Pass "produce-book.py lines: $lineCount (expected ~1189)"
    } else {
        Write-Fail "produce-book.py lines: $lineCount (expected ~1189)" "Re-copy the file - content is incomplete"
    }
}

# -----------------------------------------------------------------------------
Write-Header "3. Python installation"
# -----------------------------------------------------------------------------

if (Test-Command "python") {
    $pyVersion = Get-CommandVersion "python"
    Write-Pass "Python found: $pyVersion"

    # Check version is 3.10+
    if ($pyVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -eq 3 -and $minor -ge 10 -and $minor -le 13) {
            Write-Pass "Python version is in the recommended range (3.10-3.13)"
        } elseif ($major -eq 3 -and $minor -ge 14) {
            Write-Warn "Python $major.$minor is very new - some libraries may have compatibility issues" "If you hit issues, install Python 3.12 from python.org"
        } else {
            Write-Fail "Python version too old: $major.$minor" "Install Python 3.12 from https://python.org/downloads/"
        }
    }
} else {
    Write-Fail "Python not found in PATH" "Install Python 3.12 from https://python.org/downloads/ - check 'Add to PATH' during install"
}

if (Test-Command "pip") {
    $pipVersion = Get-CommandVersion "pip"
    Write-Pass "pip found: $pipVersion"
} else {
    Write-Fail "pip not found in PATH" "Run: python -m ensurepip --upgrade"
}

# -----------------------------------------------------------------------------
Write-Header "4. Python packages"
# -----------------------------------------------------------------------------

$pythonPackages = @{
    "weasyprint" = "PDF generation (CRITICAL)"
    "ebooklib"   = "ePub generation (CRITICAL)"
    "PIL"        = "Cover image generation (CRITICAL)"
    "markdown"   = "Markdown to HTML (CRITICAL)"
    "pypdf"      = "PDF page counting (optional)"
}

foreach ($pkg in $pythonPackages.Keys) {
    $description = $pythonPackages[$pkg]
    try {
        $result = & python -c "import $pkg; print('OK')" 2>&1
        if ($result -match "OK") {
            Write-Pass "Python package: $pkg ($description)"
        } else {
            $pipName = if ($pkg -eq "PIL") { "pillow" } else { $pkg }
            Write-Fail "Python package missing: $pkg ($description)" "Run: pip install $pipName"
        }
    } catch {
        Write-Fail "Could not check package: $pkg" "Verify Python is working"
    }
}

# -----------------------------------------------------------------------------
Write-Header "5. WeasyPrint runtime libraries (GTK)"
# -----------------------------------------------------------------------------

# WeasyPrint needs libgobject and pango at runtime
$gtkPaths = @(
    "C:\Program Files\GTK3-Runtime Win64\bin",
    "C:\msys64\mingw64\bin",
    "C:\GTK\bin"
)

$gtkFound = $false
foreach ($p in $gtkPaths) {
    if (Test-Path $p) {
        $libgobject = Get-ChildItem $p -Filter "libgobject*.dll" -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($libgobject) {
            Write-Pass "GTK runtime found: $p"
            $gtkFound = $true

            # Check it's in PATH
            if ($env:Path -split ";" | Where-Object { $_ -eq $p }) {
                Write-Pass "GTK is in PATH"
            } else {
                Write-Warn "GTK is installed but not in PATH" "Add $p to PATH environment variable"
            }
            break
        }
    }
}

if (-not $gtkFound) {
    # Try to actually run weasyprint to see if it can find libs
    try {
        $wpTest = & python -c "from weasyprint import HTML; HTML(string='<p>test</p>').write_pdf('$env:TEMP\wp_test.pdf'); print('OK')" 2>&1
        if ($wpTest -match "OK") {
            Write-Pass "WeasyPrint can render PDFs (GTK libs found via some path)"
            Remove-Item "$env:TEMP\wp_test.pdf" -ErrorAction SilentlyContinue
        } else {
            Write-Fail "WeasyPrint cannot find GTK libraries" "Install GTK3 runtime from https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases"
            Write-Host "         Detail: $wpTest" -ForegroundColor DarkRed
        }
    } catch {
        Write-Fail "WeasyPrint test failed" "Install GTK3 runtime, see fix above"
    }
}

# -----------------------------------------------------------------------------
Write-Header "6. Node.js and npm"
# -----------------------------------------------------------------------------

if (Test-Command "node") {
    $nodeVersion = Get-CommandVersion "node"
    Write-Pass "Node.js found: $nodeVersion"
} else {
    Write-Fail "Node.js not found in PATH" "Install from https://nodejs.org/ (LTS version)"
}

if (Test-Command "npm") {
    $npmVersion = Get-CommandVersion "npm"
    Write-Pass "npm found: v$npmVersion"
} else {
    Write-Fail "npm not found in PATH" "Reinstall Node.js - npm should come with it"
}

# -----------------------------------------------------------------------------
Write-Header "7. Node.js packages (docx)"
# -----------------------------------------------------------------------------

$nodeModules = Join-Path $libraryPath "node_modules"
if (Test-Path $nodeModules) {
    $docxModule = Join-Path $nodeModules "docx"
    if (Test-Path $docxModule) {
        Write-Pass "docx package installed in node_modules/"

        # Test it actually loads
        Push-Location $libraryPath
        try {
            $docxTest = & node -e "console.log(require('docx').Document ? 'OK' : 'FAIL')" 2>&1
            if ($docxTest -match "OK") {
                Write-Pass "docx package can be imported"
            } else {
                Write-Fail "docx package found but won't import" "Run: cd $libraryPath && npm install docx"
            }
        } finally {
            Pop-Location
        }
    } else {
        Write-Fail "docx package not found" "Run: cd $libraryPath && npm install docx"
    }
} else {
    Write-Fail "node_modules folder missing" "Run: cd $libraryPath && npm install docx"
}

# -----------------------------------------------------------------------------
Write-Header "8. Git installation"
# -----------------------------------------------------------------------------

if (Test-Command "git") {
    $gitVersion = Get-CommandVersion "git"
    Write-Pass "Git found: $gitVersion"

    # Check user config
    Push-Location $libraryPath -ErrorAction SilentlyContinue
    try {
        $gitName = git config user.name 2>$null
        $gitEmail = git config user.email 2>$null

        if ($gitName) {
            Write-Pass "Git user.name configured: $gitName"
        } else {
            Write-Warn "Git user.name not set" "Run: git config --global user.name 'Your Name'"
        }

        if ($gitEmail) {
            Write-Pass "Git user.email configured: $gitEmail"
        } else {
            Write-Warn "Git user.email not set" "Run: git config --global user.email 'you@example.com'"
        }

        # Check if this is a git repo
        if (Test-Path (Join-Path $libraryPath ".git")) {
            Write-Pass "Library folder is a Git repository"

            # Check remote
            $remote = git remote -v 2>$null | Select-Object -First 1
            if ($remote -match "fadhlyemen/library") {
                Write-Pass "Git remote points to fadhlyemen/library"
            } else {
                Write-Warn "Git remote not pointing to fadhlyemen/library" "Check: git remote -v"
            }
        } else {
            Write-Fail "Library folder is not a Git repository" "Either copy the .git folder from old machine, or clone fresh: git clone https://github.com/fadhlyemen/library.git"
        }
    } finally {
        Pop-Location
    }
} else {
    Write-Fail "Git not found in PATH" "Install from https://git-scm.com/downloads"
}

# -----------------------------------------------------------------------------
Write-Header "9. Claude Desktop / Cowork (optional)"
# -----------------------------------------------------------------------------

$claudeDesktopPath = "$env:LOCALAPPDATA\AnthropicClaude"
$claudeProgramPath = "$env:LOCALAPPDATA\Programs\Claude"

if (Test-Path $claudeDesktopPath) {
    Write-Pass "Claude Desktop installed at $claudeDesktopPath"
} elseif (Test-Path $claudeProgramPath) {
    Write-Pass "Claude Desktop installed at $claudeProgramPath"
} else {
    Write-Warn "Claude Desktop not detected" "Optional - install from https://claude.ai/download if you want to use Cowork"
}

# -----------------------------------------------------------------------------
Write-Header "10. End-to-end smoke test"
# -----------------------------------------------------------------------------

# This actually runs the script with --no-git on a tiny test book
Write-Host "  Attempting a tiny test book to verify the pipeline works..." -ForegroundColor White

$testDir = Join-Path $libraryPath "drafts\_env_test"
$testArDir = Join-Path $testDir "ar"
$testEnDir = Join-Path $testDir "en"

# Create test content
try {
    New-Item -ItemType Directory -Force -Path $testArDir | Out-Null
    New-Item -ItemType Directory -Force -Path $testEnDir | Out-Null

    # Write Arabic test content using explicit UTF-8 byte writing to avoid
    # encoding issues when this script file itself has been edited or saved
    # through tools that mangle Arabic characters.
    # Bytes encode Arabic text equivalent to: hash space [test-word] newline newline [text-word]
    $arBytes = [byte[]](0x23, 0x20, 0xD8, 0xA7, 0xD8, 0xAE, 0xD8, 0xAA, 0xD8, 0xA8, 0xD8, 0xA7, 0xD8, 0xB1, 0x0A, 0x0A, 0xD9, 0x86, 0xD8, 0xB5, 0x20, 0xD9, 0x82, 0xD8, 0xB5, 0xD9, 0x8A, 0xD8, 0xB1, 0x20, 0xD9, 0x84, 0xD9, 0x84, 0xD8, 0xA7, 0xD8, 0xAE, 0xD8, 0xAA, 0xD8, 0xA8, 0xD8, 0xA7, 0xD8, 0xB1, 0x2E)
    [System.IO.File]::WriteAllBytes("$testArDir\01.md", $arBytes)

    # English content can be written safely
    [System.IO.File]::WriteAllText("$testEnDir\01.md", "# Test`n`nShort test text.", [System.Text.Encoding]::UTF8)

    # Title arguments - pass as arrays to avoid quoting issues
    # Title argument bytes - encodes Arabic text equivalent to "[test-word] [environment-word]"
    $titleArBytes = [byte[]](0xD8, 0xA7, 0xD8, 0xAE, 0xD8, 0xAA, 0xD8, 0xA8, 0xD8, 0xA7, 0xD8, 0xB1, 0x20, 0xD8, 0xA7, 0xD9, 0x84, 0xD8, 0xA8, 0xD9, 0x8A, 0xD8, 0xA6, 0xD8, 0xA9)
    $titleAr = [System.Text.Encoding]::UTF8.GetString($titleArBytes)

    Push-Location $libraryPath
    try {
        # Set console code page to UTF-8 so subprocess encoding works
        $oldOutputEncoding = [Console]::OutputEncoding
        [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
        $env:PYTHONIOENCODING = "utf-8"

        $output = & python scripts\produce-book.py `
            --slug "_env_test" `
            --title-ar $titleAr `
            --title-en "Environment Test" `
            --category tech `
            --content-dir "drafts/_env_test" `
            --no-git 2>&1 | Out-String

        [Console]::OutputEncoding = $oldOutputEncoding

        if ($output -match "Done") {
            Write-Pass "End-to-end smoke test PASSED - pipeline is working"

            # Cleanup test artifacts
            Remove-Item "$libraryPath\assets\books\_env_test.*" -Force -ErrorAction SilentlyContinue
            Remove-Item "$libraryPath\assets\covers\_env_test.jpg" -Force -ErrorAction SilentlyContinue
            Remove-Item $testDir -Recurse -Force -ErrorAction SilentlyContinue

            # Remove the test entry from books.json
            try {
                $booksJsonText = Get-Content "$libraryPath\data\books.json" -Raw -Encoding UTF8
                $booksJson = $booksJsonText | ConvertFrom-Json
                $booksJson.books = @($booksJson.books | Where-Object { $_.id -ne "_env_test" })
                $cleanJson = $booksJson | ConvertTo-Json -Depth 10
                [System.IO.File]::WriteAllText("$libraryPath\data\books.json", $cleanJson, [System.Text.Encoding]::UTF8)
                Write-Pass "Test artifacts cleaned up"
            } catch {
                Write-Warn "Could not clean books.json automatically" "Manually remove the '_env_test' entry from data\books.json"
            }
        } else {
            Write-Fail "End-to-end smoke test FAILED" "See output below"
            Write-Host ""
            Write-Host "Script output:" -ForegroundColor Yellow
            Write-Host $output -ForegroundColor DarkYellow
        }
    } finally {
        Pop-Location
    }
} catch {
    Write-Fail "End-to-end smoke test crashed" $_.Exception.Message
    # Cleanup anyway
    Remove-Item $testDir -Recurse -Force -ErrorAction SilentlyContinue
}

# =============================================================================
# Summary
# =============================================================================
Write-Header "Summary"

Write-Host ""
Write-Host "  Passed:    $script:passed" -ForegroundColor Green
Write-Host "  Warnings:  $script:warned" -ForegroundColor Yellow
Write-Host "  Failed:    $script:failed" -ForegroundColor Red
Write-Host ""

if ($script:failed -eq 0) {
    Write-Host "  Environment is ready to produce books." -ForegroundColor Green
    Write-Host ""
    Write-Host "  Next: try producing a small book to validate the full workflow:" -ForegroundColor White
    Write-Host "    cd $libraryPath" -ForegroundColor Gray
    Write-Host "    python scripts\produce-book.py --slug `"test-book`" --title-ar `"Test`" --title-en `"Test`" --category tech --content-dir drafts/test-book --no-git" -ForegroundColor Gray
} elseif ($script:failed -le 2) {
    Write-Host "  Environment is mostly working but has some issues. Address the FAIL items above." -ForegroundColor Yellow
} else {
    Write-Host "  Environment has significant issues. Address all FAIL items before producing books." -ForegroundColor Red
}

Write-Host ""
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""
