Option Explicit

Dim shell, fso, desktop, repo, iconPath, targetPath
Dim localOnly, localShortcut, desktopShortcut

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

repo = fso.GetParentFolderName(WScript.ScriptFullName)
desktop = shell.SpecialFolders("Desktop")
iconPath = repo & "\assets\career_accelerator.ico"
targetPath = repo & "\Career Accelerator.bat"
localOnly = WScript.Arguments.Named.Exists("LocalOnly")

Sub ConfigureShortcut(shortcutPath)
    Dim shortcut
    Set shortcut = shell.CreateShortcut(shortcutPath)
    shortcut.TargetPath = targetPath
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
    MsgBox "Career Accelerator shortcuts created with the custom icon.", 64, "Career Accelerator"
End If
