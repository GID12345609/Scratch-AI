$ErrorActionPreference = "Stop"
Set-Location "D:\ScratchGrok"

$env:AI_MODEL = "gpt-6"

& ".\.venv\Scripts\python.exe" ".\app.py"
