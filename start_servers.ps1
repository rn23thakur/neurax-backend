# start-servers.ps1
# Spins up neurax + resume_parser_api in separate terminal windows

$neuraxDir    = "C:\Users\aryan\Documents\Code Stuff\neurax"
$resumeApiDir = "C:\Users\aryan\Documents\Code Stuff\neurax\resume_parser_api"
$tesseractPath = "C:\Users\aryan\Documents\Code Stuff\neurax\resume_parser_api\Tesseract-OCR"
$popplerPath   = "C:\Users\aryan\Documents\Code Stuff\neurax\resume_parser_api\poppler-23.11.0\Library\bin"

# --- neurax (uv + uvicorn) ---
# Note: reload-exclude uses single quotes inside the here-string to avoid
# conflicts with the outer double-quoted -ArgumentList string.
$neuraxCmd = @"
    Set-Location '$neuraxDir'
    Write-Host '==> Starting neurax server...' -ForegroundColor Cyan
    uv run uvicorn main:app --host 0.0.0.0 --port 8000
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $neuraxCmd

# --- resume_parser_api ---
$resumeCmd = @"
    Set-Location '$resumeApiDir'
    `$env:PATH = '$tesseractPath;$popplerPath;' + `$env:PATH
    Write-Host '==> PATH updated with Tesseract + Poppler' -ForegroundColor DarkYellow
    Write-Host '==> Starting resume_parser_api server...' -ForegroundColor Yellow
    uv run python main.py
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $resumeCmd

# --- frontend static server ---
$frontendDir = "C:\Users\aryan\Documents\Code Stuff\neurax-frontend"
$frontendCmd = @"
    Set-Location '$frontendDir'
    Write-Host '==> Starting frontend server...' -ForegroundColor Green
    python -m http.server 3000
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host ""
Write-Host "All servers launched in separate windows." -ForegroundColor Green
Write-Host "  neurax            -> http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "  resume_parser_api -> http://127.0.0.1:8001" -ForegroundColor Yellow
Write-Host "  frontend          -> http://127.0.0.1:3000" -ForegroundColor Green