# The shared browser runtime connects to Chrome or starts its dedicated profile.
$localVoice = Join-Path (Split-Path -Parent $PSScriptRoot) ".venv\Scripts\chexsa-voice.exe"
if (Test-Path -LiteralPath $localVoice) {
    & $localVoice
}
else {
    chexsa-voice
}
