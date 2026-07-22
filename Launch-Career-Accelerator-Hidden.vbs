Option Explicit
Dim shell, fso, repo, command, rc
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
repo = fso.GetParentFolderName(WScript.ScriptFullName)
command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File " & _
          Chr(34) & repo & "\Launch-Career-Accelerator.ps1" & Chr(34)
rc = shell.Run(command, 0, False)
If rc <> 0 Then
    MsgBox "Career Accelerator could not launch. Check the logs folder.", 16, "Career Accelerator"
End If
