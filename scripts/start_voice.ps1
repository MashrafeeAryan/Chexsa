# Start Chrome for Chexsa, then start voice mode.

$chrome = "$env:ProgramFiles\Google\Chrome\Application\chrome.exe"

if (-not (Test-Path $chrome)) {
    $chrome = "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe"
}

if (-not (Test-Path $chrome)) {
    throw "Google Chrome was not found."
}

try {
    Invoke-RestMethod "http://127.0.0.1:9222/json/version" `
        -TimeoutSec 1 | Out-Null
}
catch {
    Start-Process $chrome -ArgumentList @(
        "--remote-debugging-port=9222",
        "--user-data-dir=$env:TEMP\chexsa-chrome"
    )

    Start-Sleep -Seconds 2
}

chexsa-voice
