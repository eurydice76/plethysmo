@echo off

set current_dir=%cd%

rem the path to the python installer executable
set python_installer=%1

rem the path to the git directory for plethysmo
set git_dir=%2

rem the version to install
set version=%3

rem the directory that will contain the python + deps + plethysmo
set target_dir=%4

rem uninstall python
%python_installer% /quiet /uninstall

rem remove(if existing) target directory
rmdir /S /Q %target_dir%

rem create the target directory that will contains the python installation
mkdir %target_dir%

rem install python to the select target directory
%python_installer% /quiet TargetDir=%target_dir%

rem the path to pip executable
set pip_exe=%target_dir%\Scripts\pip.exe

rem install dependencies
%pip_exe% install matplotlib
%pip_exe% install pyEDFlib
%pip_exe% install pandas
%pip_exe% install PyQt5
%pip_exe% install openpyxl
%pip_exe% install scipy
%pip_exe% install xlwt

rem remove unused file for the bundle to reduce its size
rmdir /S /Q %target_dir%\Lib\site-packages\matplotlib\tests
rmdir /S /Q %target_dir%\Lib\site-packages\numpy\tests
rmdir /S /Q %target_dir%\Lib\site-packages\pandas\tests

rem the path to python executable
set python_exe=%target_dir%\python.exe

rem cleanup previous installations
cd %target_dir%\Lib\site-packages
for /f %%i in ('dir /a:d /S /B plethysmo*') do rmdir /S /Q %%i
del /Q %target_dir%\Scripts\plethysmo

rem checkout selected version of the plethysmo project
set git_exe="C:\Program Files\Git\bin\git.exe"
cd %git_dir%
%git_exe% fetch --all
%git_exe% checkout %version%

rem build and install plethysmo using the python installed in the target directory
rmdir /S /Q %git_dir%\build
%python_exe% setup.py build install

rem copy the LICENSE and CHANGELOG files
copy %git_dir%\LICENSE %git_dir%\deploy\windows
copy %git_dir%\CHANGELOG.md %git_dir%\deploy\windows\CHANGELOG.txt

rem the path to nsis executable
set makensis="C:\Program Files (x86)\NSIS\Bin\makensis.exe"
set nsis_installer=%git_dir%\deploy\windows\installer.nsi

del /Q %target_dir%\plethysmo-%version%-win-amd64.exe

%makensis% /V4 /Onsis_log.txt /DVERSION=%version% /DARCH=win-amd64 /DTARGET_DIR=%target_dir% %nsis_installer%

cd %current_dir%
