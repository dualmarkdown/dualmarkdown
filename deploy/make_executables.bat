@echo off
set bindir=..\bin
set base_tmpdir=tmp
set package_locdir=..\dualmarkdown
set option=%1

if "%option%" == "clean" (
echo "Cleaning up"
del /s /q %bindir% %base_tmpdir%
rmdir /s /q %bindir% %base_tmpdir%
exit /b 0
)



if exist %bindir% (
echo "Removing existing version of bin directory"
del /s /q %bindir%
rmdir %bindir%
)

mkdir %bindir%

if exist %base_tmpdir% (
echo "Removing existing version of tmp directory"
del /s /q %base_tmpdir%
rmdir %bindir%
)


mkdir %base_tmpdir%

set failed=0

:: Stage 1: build executable files 
for %%p in (dual_md teaching_md) do (	

if not exist "%package_locdir%\%%p.py" (
echo "Package file %package_locdir%\%%p.py does not exist"
		exit /b 1
) else (
	echo|set /p="Building executable file for %%p ..."

mkdir %base_tmpdir%\%%p
cd %base_tmpdir%/%%p
pyinstaller --onefile "..\..\%package_locdir%/%%p.py" 1> ..\%%p.log 2>&1

if errorlevel 1 (
	cd ..\..
	echo "Pyinstaller failed: errlevel %errorlevel%"
	exit /b 2
)

echo Done

cd ..\..\
)
)


:: Stage 1: build executable files 
for %%p in (dual_md teaching_md) do (	

	if not exist %base_tmpdir%\%%p\dist\%%p.exe (
		echo "Executable file %base_tmpdir%\%%p\dist\%%p.exe not found. Can't copy"
		exit /b 3
	)

	copy %base_tmpdir%\%%p\dist\%%p.exe %bindir%
)

PAUSE

 

