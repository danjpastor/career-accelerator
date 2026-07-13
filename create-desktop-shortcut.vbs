Set shell = CreateObject("WScript.Shell")
desktop = shell.SpecialFolders("Desktop")
repo = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

Set shortcut = shell.CreateShortcut(desktop & "\Career Accelerator.lnk")
shortcut.TargetPath = repo & "\Career Accelerator.bat"
shortcut.WorkingDirectory = repo
shortcut.Description = "Open the Career Accelerator desktop application"
shortcut.Save

MsgBox "Desktop shortcut created.", 64, "Career Accelerator"
