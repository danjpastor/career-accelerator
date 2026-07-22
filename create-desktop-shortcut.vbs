Option Explicit

Dim shell, fso, desktop, repo, iconPath, targetPath
Dim localOnly, localShortcut, desktopShortcut

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

repo = fso.GetParentFolderName(WScript.ScriptFullName)
desktop = shell.SpecialFolders("Desktop")
iconPath = repo & "\application\assets\pathways\career_accelerator.ico"
If Not fso.FileExists(iconPath) Then
    iconPath = repo & "\application\assets\career_accelerator.ico"
End If
targetPath = repo & "\Launch-Career-Accelerator-Hidden.vbs"
localOnly = WScript.Arguments.Named.Exists("LocalOnly")

Sub ConfigureShortcut(shortcutPath)
    Dim shortcut
    Set shortcut = shell.CreateShortcut(shortcutPath)
    shortcut.TargetPath = "wscript.exe"
    shortcut.Arguments = Chr(34) & targetPath & Chr(34)
    shortcut.WorkingDirectory = repo
    shortcut.Description = "Open Career Accelerator"
    shortcut.IconLocation = iconPath & ",0"
    shortcut.WindowStyle = 7
    shortcut.Save
End Sub

localShortcut = repo & "\Career Accelerator.lnk"
ConfigureShortcut localShortcut

If Not localOnly Then
    desktopShortcut = desktop & "\Career Accelerator.lnk"
    ConfigureShortcut desktopShortcut
    MsgBox "Career Accelerator shortcuts created.", 64, "Career Accelerator"
End If
