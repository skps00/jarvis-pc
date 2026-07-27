Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = dir
sh.Run """C:\Users\skps9\AppData\Local\Python\pythoncore-3.14-64\pythonw.exe"" -m jarvis serve", 0, False