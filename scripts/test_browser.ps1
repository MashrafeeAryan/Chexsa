param([string]$Python = "")

$ErrorActionPreference = "Stop"
$repoPath = Split-Path -Parent $PSScriptRoot
if (-not $Python) {
    $Python = Join-Path $repoPath ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $Python)) { $Python = "python" }
}
$startedChrome = $null
$testExitCode = 1
try {
    try {
        Invoke-RestMethod "http://127.0.0.1:9222/json/version" -TimeoutSec 1 | Out-Null
    }
    catch {
        $chromePath = Join-Path $env:ProgramFiles "Google\Chrome\Application\chrome.exe"
        if (-not (Test-Path -LiteralPath $chromePath)) {
            $chromePath = Join-Path ${env:ProgramFiles(x86)} "Google\Chrome\Application\chrome.exe"
        }
        if (-not (Test-Path -LiteralPath $chromePath)) { throw "Chrome is required for browser integration tests." }
        $profilePath = Join-Path $repoPath ".chexsa\test-chrome"
        $startedChrome = Start-Process -FilePath $chromePath -ArgumentList @("--headless=new", "--remote-debugging-port=9222", "--user-data-dir=`"$profilePath`"", "--no-first-run", "about:blank") -WindowStyle Hidden -PassThru
        $ready = $false
        for ($attempt = 0; $attempt -lt 40; $attempt++) {
            try {
                Invoke-RestMethod "http://127.0.0.1:9222/json/version" -TimeoutSec 1 | Out-Null
                $ready = $true
                break
            }
            catch { Start-Sleep -Milliseconds 250 }
        }
        if (-not $ready) { throw "Test Chrome did not become ready." }
    }
    & $Python (Join-Path $repoPath "tests\browser_engine_integration.py")
    $testExitCode = $LASTEXITCODE
}
finally {
    if ($startedChrome -and -not $startedChrome.HasExited) {
        Stop-Process -Id $startedChrome.Id -ErrorAction SilentlyContinue
    }
}
exit $testExitCode
