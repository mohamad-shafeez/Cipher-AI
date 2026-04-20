Set WinScriptHost = CreateObject("WScript.Shell")
' This runs the sentinel.py invisibly (0 = hidden window)
WinScriptHost.Run Chr(34) & "pythonw.exe" & Chr(34) & " " & Chr(34) & "D:\cipher_sentinel\sentinel.py" & Chr(34), 0
Set WinScriptHost = Nothing