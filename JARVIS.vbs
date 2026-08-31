' Double-click / desktop shortcut — no console window.
' Starts Hermes gateway if needed, then jarvis serve (MCP + alert poller + tray).
' Serve log → %APPDATA%\Jarvis\serve.log
' ⚠️ 用 python.exe（唔係 pythonw）：pythonw + WScript.Shell.Run 下 alerts MCP
' (uvicorn) 靜默死，8765 唔 listening（2026-08-27 實測）；python.exe + redirect
' 隱藏啟動一切正常。pythonw + bash 啟動反而 OK——只係 WScript 組合出事。
Option Explicit
Dim fso, sh, dir, py, hermes, env, q
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = dir

Set env = sh.Environment("PROCESS")
env("HERMES_HOME") = sh.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\hermes"
env("PYTHONPATH") = dir & "\src"
' Do NOT set PYTHONUTF8=1 — tasklist/OEM CLI on zh-TW Windows is mbcs/cp950.

py = "C:\Users\skps9\AppData\Local\Python\pythoncore-3.14-64\python.exe"
If Not fso.FileExists(py) Then
  ' pythonw fallback：serve 照行，但 MCP 可能唔起
  py = "C:\Users\skps9\AppData\Local\Python\pythoncore-3.14-64\pythonw.exe"
End If
If Not fso.FileExists(py) Then
  MsgBox "Python not found. Install Python 3.14 or fix JARVIS.vbs path.", vbCritical, "JARVIS"
  WScript.Quit 1
End If

hermes = env("HERMES_HOME") & "\hermes-agent\venv\Scripts\hermes.exe"
If fso.FileExists(hermes) Then
  ' Hidden; ignore errors if already running
  sh.Run """" & hermes & """ gateway start", 0, False
End If

' jarvis serve: tray + alerts MCP + ~2s poller (alert_tts=hermes)
' cmd /c + redirect：stderr 落 serve.log（診斷用）；window style 0 = 隱藏冇窗口
q = Chr(34)
sh.Run "cmd /c " & q & py & q & " -m jarvis serve > %APPDATA%\Jarvis\serve.log 2>&1", 0, False
