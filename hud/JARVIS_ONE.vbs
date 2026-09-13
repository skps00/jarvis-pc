' JARVIS ONE launcher — hidden startup for jarvis-hud (Electron)
' Usage: double-click, or place a shortcut in shell:startup for autostart.
Set sh = CreateObject("WScript.Shell")
' npm start runs electron . — hidden console
sh.Run "cmd /c cd /d C:\Users\skps9\Documents\Code_Project\jarvis-hud && npm start", 0, False
