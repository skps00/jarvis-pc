' Double-click / desktop shortcut — no console window.
' Starts Hermes gateway if needed, then jarvis serve (MCP + alert poller + tray).
Option Explicit
Dim fso, sh, dir, pyw, hermes, env
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = dir

Set env = sh.Environment("PROCESS")
env("HERMES_HOME") = sh.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\hermes"
env("PYTHONPATH") = dir & "\src"
' Do NOT set PYTHONUTF8=1 — tasklist/OEM CLI on zh-TW Windows is mbcs/cp950.

pyw = "C:\Users\skps9\AppData\Local\Python\pythoncore-3.14-64\pythonw.exe"
If Not fso.FileExists(pyw) Then
  pyw = "C:\Users\skps9\AppData\Local\Python\bin\pythonw.exe"
End If
If Not fso.FileExists(pyw) Then
  MsgBox "pythonw.exe not found. Install Python 3.14 or fix JARVIS.vbs path.", vbCritical, "JARVIS"
  WScript.Quit 1
End If

hermes = env("HERMES_HOME") & "\hermes-agent\venv\Scripts\hermes.exe"
If fso.FileExists(hermes) Then
  ' Hidden; ignore errors if already running
  sh.Run """" & hermes & """ gateway start", 0, False
End If

' jarvis serve: tray + alerts MCP + ~2s poller (alert_tts=hermes)
sh.Run """" & pyw & """ -m jarvis serve", 0, False
