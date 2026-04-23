' create_shortcut.vbs — Tworzy skrot ZelaznaCRM na pulpicie uzytkownika
' Uzycie: cscript create_shortcut.vbs

Dim oShell, oLink, sDesktop, sProjectDir, sBatFile, sIconFile

Set oShell = CreateObject("WScript.Shell")

sDesktop    = oShell.SpecialFolders("Desktop")
sProjectDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
sBatFile    = sProjectDir & "start_zelaznaCRM.bat"
sIconFile   = sProjectDir & "static\img\zelaznaCRM.ico"

Set oLink = oShell.CreateShortcut(sDesktop & "\ZelaznaCRM.lnk")
oLink.TargetPath       = sBatFile
oLink.WorkingDirectory = sProjectDir
oLink.IconLocation     = sIconFile & ", 0"
oLink.Description      = "ZelaznaCRM — System CRM dla zespolow sprzedazowych"
oLink.WindowStyle      = 1
oLink.Save

WScript.Echo "Skrot ZelaznaCRM zostal utworzony na pulpicie."
WScript.Echo "Lokalizacja: " & sDesktop & "\ZelaznaCRM.lnk"
