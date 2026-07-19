Option Explicit

Dim shell, fso, desktop, repo, iconPath, targetPath
Dim localOnly, localShortcut, desktopShortcut

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

repo = fso.GetParentFolderName(WScript.ScriptFullName)
desktop = shell.SpecialFolders("Desktop")
iconPath = repo & "\assets\career_accelerator.ico"
targetPath = repo & "\Data Career Accelerator.bat"
localOnly = WScript.Arguments.Named.Exists("LocalOnly")

Sub ConfigureShortcut(shortcutPath)
    Dim shortcut
    Set shortcut = shell.CreateShortcut(shortcutPath)
    shortcut.TargetPath = targetPath
    shortcut.WorkingDirectory = repo
    shortcut.Description = "Open Data Career Accelerator"
    shortcut.IconLocation = iconPath & ",0"
    shortcut.WindowStyle = 7
    shortcut.Save
End Sub

localShortcut = repo & "\Data Career Accelerator.lnk"
ConfigureShortcut localShortcut

If Not localOnly Then
    desktopShortcut = desktop & "\Data Career Accelerator.lnk"
    ConfigureShortcut desktopShortcut
    MsgBox "Data Career Accelerator shortcuts created with the custom icon.", 64, "Data Career Accelerator"
End If
