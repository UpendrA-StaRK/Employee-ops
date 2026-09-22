@echo off
setlocal enabledelayedexpansion

set ARGS=
for %%x in (%*) do (
    set "ARG=%%~x"
    if /i not "!ARG!"=="jdk.incubator.vector" (
        if /i not "!ARG!"=="--add-modules" (
            set "ARGS=!ARGS! %%x"
        )
    )
)

"C:\Program Files\Java\jdk-27\bin\java.exe" !ARGS!
