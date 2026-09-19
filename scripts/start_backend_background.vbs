' MediaFlow Downloader - Silent Background Runner
' Starts the backend server with no console window so closing terminals does not kill it.

Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
strScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
strAppDir = FSO.GetParentFolderName(strScriptDir)
WshShell.CurrentDirectory = strAppDir

strBackendLog = strScriptDir & "\backend.log"
strCommand = "cmd.exe /c ""cd /d """ & strAppDir & """ && py -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 >> """ & strBackendLog & """ 2>&1"""
' 0 = Hide window completely, False = Do not wait for completion
WshShell.Run strCommand, 0, False

Set WshShell = Nothing
Set FSO = Nothing
