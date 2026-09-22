$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function Start-ProjectTerminal {
    param(
        [Parameter(Mandatory = $true)][string]$Title,
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)][string]$Command
    )

    $escapedDirectory = $Directory.Replace("'", "''")
    $terminalCommand = "`$Host.UI.RawUI.WindowTitle='$Title'; Set-Location -LiteralPath '$escapedDirectory'; $Command"
    Start-Process powershell.exe -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $terminalCommand)
}

Start-ProjectTerminal -Title "OFFIT FastAPI :8001" `
    -Directory (Join-Path $projectRoot "shopdb2_backend_uv_fastapi1") `
    -Command "uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001"

Start-ProjectTerminal -Title "OFFIT 고객 :5173" `
    -Directory (Join-Path $projectRoot "shopdb2_customer_frontend") `
    -Command "npm run dev"

Start-ProjectTerminal -Title "OFFIT 지사 :5174" `
    -Directory (Join-Path $projectRoot "SHOPDB2_지사관리_프로젝트") `
    -Command "npm run dev"

Start-ProjectTerminal -Title "OFFIT 본사 :3000" `
    -Directory (Join-Path $projectRoot "shopdb2_frontend_hq") `
    -Command "`$env:PORT='3000'; `$env:BROWSER='none'; npm start"

Start-ProjectTerminal -Title "OFFIT 통합 로그인 :4173" `
    -Directory (Join-Path $projectRoot "SHOPDB2_통합로그인_포털") `
    -Command "npm run dev"

Write-Host ""
Write-Host "OFFIT 전체 서버를 실행했습니다." -ForegroundColor Green
Write-Host "통합 로그인: http://127.0.0.1:4173"
Write-Host "각 터미널의 서버 준비가 끝난 뒤 위 주소를 여세요."
