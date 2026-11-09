param([switch]$OpenBrowser)
$ErrorActionPreference = 'Stop'
$projectDirectory = $PSScriptRoot
$frontendDirectory = Join-Path $projectDirectory 'frontend'
$pythonExecutable = Join-Path $projectDirectory '.venv\Scripts\python.exe'
$nodeExecutable = (Get-Command node -ErrorAction Stop).Source
if (!(Test-Path -LiteralPath (Join-Path $frontendDirectory 'node_modules'))) { throw 'Run "npm install" in the frontend folder first.' }
if (!(Test-Path -LiteralPath $pythonExecutable)) { throw 'Create .venv and install backend/requirements.txt first. See NLP_GUIDE.md.' }

function Test-PreviewEndpoint([string]$Url) {
    try { return (Invoke-WebRequest -Uri $Url -TimeoutSec 3 -UseBasicParsing).StatusCode -eq 200 }
    catch { return $false }
}

if (!(Test-PreviewEndpoint 'http://127.0.0.1:8000/api/health')) {
    Start-Process -FilePath $pythonExecutable -ArgumentList '-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory $projectDirectory -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectDirectory 'backend\preview.log') -RedirectStandardError (Join-Path $projectDirectory 'backend\preview-error.log') | Out-Null
}
if (!(Test-PreviewEndpoint 'http://127.0.0.1:5173/')) {
    Start-Process -FilePath $nodeExecutable -ArgumentList 'node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','5173','--strictPort' -WorkingDirectory $frontendDirectory -WindowStyle Hidden -RedirectStandardOutput (Join-Path $frontendDirectory 'preview.log') -RedirectStandardError (Join-Path $frontendDirectory 'preview-error.log') | Out-Null
}
foreach ($url in @('http://127.0.0.1:8000/api/health', 'http://127.0.0.1:5173/')) {
    $ready = $false
    for ($attempt = 0; $attempt -lt 12; $attempt++) {
        if (Test-PreviewEndpoint $url) { $ready = $true; break }
        Start-Sleep -Milliseconds 500
    }
    if (!$ready) { throw "Server did not become ready at $url. Inspect backend/preview-error.log and frontend/preview-error.log. A port may already be occupied." }
    Write-Output "Ready: $url"
}
if ($OpenBrowser) { Start-Process 'http://127.0.0.1:5173/' }
