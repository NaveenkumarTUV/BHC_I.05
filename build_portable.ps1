<#
.SYNOPSIS
    Build the BHC Quotation Generator portable executable.
.DESCRIPTION
    Activates the project venv, runs PyInstaller, and prepares
    the distribution folder with required external files.
#>

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$Venv        = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"
$SpecFile    = Join-Path $ProjectRoot "bhc_quotation.spec"
$DistDir     = Join-Path $ProjectRoot "dist\BHC_Quotation_Generator"

Write-Host "`n=== BHC Quotation Generator — Build ===" -ForegroundColor Cyan

# 1. Activate venv
if (Test-Path $Venv) {
    & $Venv
    Write-Host "[OK] Virtual environment activated." -ForegroundColor Green
} else {
    Write-Host "[ERROR] Virtual environment not found at $Venv" -ForegroundColor Red
    exit 1
}

# 2. Run PyInstaller
Write-Host "`n[BUILD] Running PyInstaller..." -ForegroundColor Yellow
Push-Location $ProjectRoot
pyinstaller --clean --noconfirm $SpecFile
Pop-Location

if (-not (Test-Path (Join-Path $DistDir "BHC_Quotation_Generator.exe"))) {
    Write-Host "`n[ERROR] Build failed — exe not found." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Build succeeded." -ForegroundColor Green

# 3. Create .env template in dist folder
Write-Host "`n[SETUP] Preparing distribution folder..." -ForegroundColor Yellow

# Copy the project .env (with actual network paths) to the dist folder
$EnvSrc  = Join-Path $ProjectRoot ".env"
$EnvDest = Join-Path $DistDir ".env"
if (Test-Path $EnvSrc) {
    Copy-Item -Path $EnvSrc -Destination $EnvDest -Force
    Write-Host "  - Copied .env (with network paths) to dist"
} else {
    Write-Host "  [WARN] No .env found at project root; dist folder has no .env"
}

Write-Host "`n=== Build Complete ===" -ForegroundColor Cyan
Write-Host "Distribution folder: $DistDir"
Write-Host "To run: .\dist\BHC_Quotation_Generator\BHC_Quotation_Generator.exe`n"
