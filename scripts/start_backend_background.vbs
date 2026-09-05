' MediaFlow Downloader - Silent Background Runner
' Starts the backend server with no console window so closing terminals does not kill it.

Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
strScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
strAppDir = FSO.GetParentFolderName(strScriptDir)
WshShell.CurrentDirectory = strAppDir

strCommand = "py -3.14 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"
' 0 = Hide window completely, False = Do not wait for completion
WshShell.Run strCommand, 0, False

Set WshShell = Nothing
