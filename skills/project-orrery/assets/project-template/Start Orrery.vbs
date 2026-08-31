Option Explicit

Dim shell, files, root, pythonw, candidate, command
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
root = files.GetParentFolderName(WScript.ScriptFullName)

candidate = shell.ExpandEnvironmentStrings("%USERPROFILE%") & "\anaconda3\pythonw.exe"
If files.FileExists(candidate) Then
  pythonw = candidate
Else
  pythonw = "pythonw.exe"
End If

command = Chr(34) & pythonw & Chr(34) & " -X utf8 " & _
  Chr(34) & root & "\scripts\docsite\serve_orrery.py" & Chr(34)
shell.CurrentDirectory = root
shell.Run command, 0, False

