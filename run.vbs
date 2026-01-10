Set WshShell = CreateObject("WScript.Shell")
strPath = WshShell.CurrentDirectory & "\.env\Scripts\pythonw.exe"
strScript = WshShell.CurrentDirectory & "\detect.py"
WshShell.Run strPath & " " & strScript, 0, False
