param(
  [switch]$Fast,
  [switch]$Clean
)

$ErrorActionPreference = 'Continue'
$Root   = Split-Path -Parent $MyInvocation.MyCommand.Path
$Out    = Join-Path $Root 'build'
$TexBin = 'C:\texlive\2025\bin\windows'
$env:Path = "$TexBin;$env:Path"

if ($Clean) {
  if (Test-Path $Out) { Remove-Item $Out -Recurse -Force }
  Write-Host '已清理 build/ 目录。' -ForegroundColor Green
  exit 0
}

New-Item -ItemType Directory -Force -Path $Out | Out-Null
Set-Location $Root
$Log = Join-Path $Out 'main.log'

function Show-Errors {
  if (-not (Test-Path $Log)) { Write-Host '  (无日志)'; return }
  $hits = Select-String -Path $Log -Pattern '^!|\.tex:\d+:' | Select-Object -First 25
  if ($hits) { $hits | ForEach-Object { '  ' + $_.Line } }
  else { Write-Host '  (日志中未发现 ! 开头的错误行)' }
}

function Invoke-Xelatex {
  param([string]$Tag)
  Write-Host "==> xelatex ($Tag)" -ForegroundColor Cyan
  if (Test-Path $Log) { Remove-Item $Log -Force -ErrorAction SilentlyContinue }
  & xelatex -interaction=nonstopmode -file-line-error -output-directory="$Out" main.tex > $null 2>&1
  $code = $LASTEXITCODE
  $fatal = $false
  if (Test-Path $Log) { $fatal = [bool](Select-String -Path $Log -Pattern '^!' -Quiet) }
  if ($fatal) {
    Write-Host "xelatex ($Tag) 出现 LaTeX 错误：" -ForegroundColor Red
    Show-Errors
    exit 1
  }
  Write-Host "    exit=$code (日志无致命错误)" -ForegroundColor DarkGray
}

if ($Fast) {
  Invoke-Xelatex 'single-pass'
} else {
  Invoke-Xelatex 'pass1'
  if (Test-Path (Join-Path $Root 'refs\references.bib')) {
    Write-Host '==> bibtex main' -ForegroundColor Cyan
    Push-Location $Out
    $env:BIBINPUTS = "$Root\refs;$Root;"
    & bibtex main > $null 2>&1
    Remove-Item Env:\BIBINPUTS -ErrorAction SilentlyContinue
    Pop-Location
  }
  Invoke-Xelatex 'pass2'
  Invoke-Xelatex 'pass3'
  if (Test-Path (Join-Path $Out 'main.idx')) {
    Write-Host '==> makeindex' -ForegroundColor Cyan
    Push-Location $Out
    & makeindex -q main.idx > $null 2>&1
    Pop-Location
    Invoke-Xelatex 'pass-index'
  }
}

$pdf = Join-Path $Out 'main.pdf'
if (Test-Path $pdf) {
  $pages = (& pdfinfo $pdf | Select-String 'Pages:').ToString().Trim()
  $size  = [math]::Round((Get-Item $pdf).Length / 1MB, 2)
  Write-Host ''
  Write-Host "编译成功：$pdf" -ForegroundColor Green
  Write-Host "  $pages"
  Write-Host "  大小：$size MB"
  Write-Host ''
  Write-Host '交叉引用/引用告警：' -ForegroundColor Yellow
  $warn = Select-String -Path $Log -Pattern 'Warning.*(undefined|multiply defined|Citation)' | Select-Object -First 20
  if ($warn) { $warn | ForEach-Object { '  ' + $_.Line.Trim() } } else { Write-Host '  (无)' }
  if (Test-Path (Join-Path $Out 'main.blg')) {
    $blg = Select-String -Path (Join-Path $Out 'main.blg') -Pattern 'Warning|error' | Select-Object -First 10
    if ($blg) { Write-Host 'bibtex 告警：' -ForegroundColor Yellow; $blg | ForEach-Object { '  ' + $_.Line.Trim() } }
  }
} else {
  Write-Host '编译失败：未生成 PDF' -ForegroundColor Red
  Show-Errors
  exit 1
}
