# Spike — Windows Hermes speak fixed English

**Date:** 2026-08-09  
**Host:** Windows native Hermes (`%LOCALAPPDATA%\hermes`, v0.20.0)  
**Gate for:** alerts MCP (Hermes TTS path)

## Install

```powershell
# Non-interactive (already used for this spike)
irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1 -OutFile $env:TEMP\hermes-install.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File $env:TEMP\hermes-install.ps1 -NonInteractive -SkipSetup

# TTS deps (not in baseline venv)
& "$env:LOCALAPPDATA\hermes\bin\uv.exe" pip install --python "$env:LOCALAPPDATA\hermes\hermes-agent\venv\Scripts\python.exe" edge-tts sounddevice
```

## Command used (FACT)

```powershell
$env:HERMES_HOME = "$env:LOCALAPPDATA\hermes"
$env:Path = [Environment]::GetEnvironmentVariable('Path','User') + ';' + [Environment]::GetEnvironmentVariable('Path','Machine')
$py = "$env:LOCALAPPDATA\hermes\hermes-agent\venv\Scripts\python.exe"
# Python one-shot: tools.tts_tool.text_to_speech_tool(text=..., provider="edge")
# then ffplay -nodisp -autoexit <mp3>
```

Phrase: `Sir, Discord needs attention.`

## Latency (FACT)

| Step | Seconds |
|------|---------|
| Edge TTS synth (warm) | **~0.54–0.60** |
| Edge TTS synth (cold first) | ~1.87 |
| ffplay wall (includes audio length) | ~3.2 |
| **Time-to-speech-ready** (synth done, ready to play) | **&lt; 1s** |

Target &lt;3s enqueue→speech: **synth path meets target**. Full wall clock includes spoken duration; do not compare that to &lt;3s.

## Notes

- `play_audio_file()` alone failed: `No audio player available` until `ffplay` on PATH (WinGet Gyan.FFmpeg).
- Alert path should call Hermes TTS tool / voice mode after peek; ensure ffmpeg/ffplay on Hermes PATH or use Hermes voice playback that uses sounddevice.
- WSL Hermes not used for this spike (eng plan: Windows native).
