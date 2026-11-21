# FarmaBot: ndal aplikacionin dhe databazën lokale Neo4j (Ollama lihet ndezur).
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# Aplikacioni Streamlit i këtij projekti
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
    Where-Object { $_.CommandLine -like '*streamlit*' -and $_.ExecutablePath -like "$root*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host "U ndal FarmaBot (PID $($_.ProcessId))" }

# Neo4j lokal i këtij projekti (java nga neo4j_local\jre)
Get-CimInstance Win32_Process -Filter "Name = 'java.exe'" |
    Where-Object { $_.ExecutablePath -like "$root\neo4j_local*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host "U ndal Neo4j (PID $($_.ProcessId))" }
