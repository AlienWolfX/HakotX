@echo off
setlocal

for %%F in (mini_xml\*.xml) do (
    call :processFile "%%F"
)

exit /b

:processFile
set "filepath=%~1"
set "tempfile=%filepath%.tmp"

for /F "usebackq delims=" %%A in ("%filepath%") do (
    set "line=%%A"
    setlocal enabledelayedexpansion
    set "line=!line:00=!"
    echo !line!>>"%tempfile%"
    endlocal
)

del "%filepath%"
ren "%tempfile%" "%~nx1"
