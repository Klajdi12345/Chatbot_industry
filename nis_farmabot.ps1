# FarmaBot: nis gjithçka me një klikim (Ollama → Neo4j lokal → aplikacioni → shfletuesi)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$logs = Join-Path $root 'logs'
New-Item -ItemType Directory -Force $logs | Out-Null
$Host.UI.RawUI.WindowTitle = 'FarmaBot'

function Test-Porti([int]$porti) {
    $c = New-Object Net.Sockets.TcpClient
    try { $c.Connect('127.0.0.1', $porti); return $true } catch { return $false } finally { $c.Close() }
}

function Prit-Portin([int]$porti, [int]$sekonda, [string]$emri) {
    for ($i = 0; $i -lt $sekonda; $i++) {
        if (Test-Porti $porti) { return }
        Start-Sleep -Seconds 1
    }
    throw "$emri nuk u nis brenda $sekonda sekondave. Shiko dosjen logs\."
}

function Hap([string]$tekst) { Write-Host "  $tekst" -ForegroundColor Cyan }
function Ok([string]$tekst) { Write-Host "  [OK] $tekst" -ForegroundColor Green }

try {
    Write-Host ""
    Write-Host "  FarmaBot po niset..." -ForegroundColor White
    Write-Host ""

    # 1. Ollama (modelet gjuhësore)
    if (Test-Porti 11434) { Ok 'Ollama po punon' }
    else {
        Hap '[1/3] Po nis Ollama...'
        $ollama = (Get-Command ollama -ErrorAction SilentlyContinue).Source
        if (-not $ollama) { $ollama = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe' }
        Start-Process $ollama -ArgumentList 'serve' -WindowStyle Hidden `
            -RedirectStandardOutput "$logs\ollama.out.log" -RedirectStandardError "$logs\ollama.err.log"
        Prit-Portin 11434 60 'Ollama'
        Ok 'Ollama u nis'
    }

    # 2. Neo4j lokal (databaza)
    if (Test-Porti 7687) { Ok 'Neo4j po punon' }
    else {
        Hap '[2/3] Po nis databazën Neo4j (deri në 1 minutë)...'
        $env:JAVA_HOME = Join-Path $root 'neo4j_local\jre'
        Start-Process (Join-Path $root 'neo4j_local\server\bin\neo4j.bat') -ArgumentList 'console' `
            -WorkingDirectory (Join-Path $root 'neo4j_local\server') -WindowStyle Hidden `
            -RedirectStandardOutput "$logs\neo4j.out.log" -RedirectStandardError "$logs\neo4j.err.log"
        Prit-Portin 7687 180 'Neo4j'
        Ok 'Neo4j u nis'
    }

    # 3. Aplikacioni FarmaBot (web: python -m web)
    if (Test-Porti 8501) { Ok 'FarmaBot po punon' }
    else {
        Hap '[3/3] Po nis FarmaBot-in...'
        Start-Process (Join-Path $root 'venv_chatbot\Scripts\python.exe') `
            -ArgumentList '-m', 'web' -WorkingDirectory $root -WindowStyle Hidden `
            -RedirectStandardOutput "$logs\farmabot.out.log" -RedirectStandardError "$logs\farmabot.err.log"
        Prit-Portin 8501 90 'FarmaBot'
        Ok 'FarmaBot u nis'
    }

    Start-Process 'http://localhost:8501'
    Write-Host ""
    Write-Host "  Gati! FarmaBot u hap te http://localhost:8501" -ForegroundColor Green
    Start-Sleep -Seconds 3
}
catch {
    Write-Host ""
    Write-Host "  GABIM: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Shtyp Enter për ta mbyllur dritaren."
    [void][Console]::ReadLine()
}
