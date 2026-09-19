' MediaFlow Downloader - 24/7 Always-On Background Runner
' Starts the backend server and Cloudflare remote tunnel completely invisibly with no terminal windows.

Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

strScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
strAppDir = FSO.GetParentFolderName(strScriptDir)

WshShell.CurrentDirectory = strAppDir

' Log file paths
strBackendLog = strScriptDir & "\backend.log"
strTunnelLog = strScriptDir & "\tunnel.log"

' 1. Start FastAPI Backend Server silently via cmd wrapper
strBackendCmd = "cmd.exe /c cd /d """ & strAppDir & """ && py -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 >> """ & strBackendLog & """ 2>&1"
WshShell.Run strBackendCmd, 0, False

' 2. Start Cloudflare 5G Tunnel silently (if cloudflared.exe exists)
strCloudflared = strScriptDir & "\cloudflared.exe"
If FSO.FileExists(strCloudflared) Then
    strTunnelCmd = "cmd.exe /c cd /d """ & strScriptDir & """ && """ & strCloudflared & """ tunnel --url http://localhost:8000 --logfile """ & strTunnelLog & """"
    WshShell.Run strTunnelCmd, 0, False
End If

Set WshShell = Nothing
Set FSO = Nothing
