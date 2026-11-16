Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
currentDir = FSO.GetParentFolderName(WScript.ScriptFullName)
batPath = currentDir & "\launch_ada.bat"
WshShell.Run "cmd.exe /c """ & batPath & """", 0, False
Set WshShell = Nothing
Set FSO = Nothing
