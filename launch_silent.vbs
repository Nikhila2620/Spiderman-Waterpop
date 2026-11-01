' Silent Zero-Terminal Bootstrapper for Spider-Man Waterpop
' Launches run_app.bat with window style 0 (completely hidden, no terminal flash)
Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
strDir = FSO.GetParentFolderName(WScript.ScriptFullName)
batPath = """" & strDir & "\run_app.bat"""
WshShell.Run batPath, 0, False
Set WshShell = Nothing
Set FSO = Nothing
