@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

rem Install org.idempiere.myappx.extension.repository into an iDempiere / appxserver
rem home with the Equinox p2 director. Same flags as update-prd.bat.
rem
rem Usage:
rem   p2-install.bat <idempiere-home>
rem
rem <idempiere-home> is the server directory that contains
rem plugins\org.eclipse.equinox.launcher_1.*.jar
rem Stop the server before running this.

set "IU=org.idempiere.myappx.extension.repository"
set "REPO=%~dp0org.idempiere.myappx.extension.repository.p2\target\repository"

if "%~1"=="" goto :usage
if /I "%~1"=="-h" goto :usage
if /I "%~1"=="--help" goto :usage
if /I "%~1"=="/?" goto :usage

set "DESTINATION=%~f1"
if not exist "%DESTINATION%\plugins\" (
	echo Server plugins directory not found: "%DESTINATION%\plugins"
	exit /b 1
)

if not exist "%REPO%\content.jar" if not exist "%REPO%\content.xml" (
	echo P2 repository not built: "%REPO%"
	echo Build it from myappx-extension-repository first:
	echo   mvn -Drevision=14.0.0-SNAPSHOT package
	exit /b 1
)

set "JARFILE="
for %%c in ("%DESTINATION%\plugins\org.eclipse.equinox.launcher_1.*.jar") do set "JARFILE=%%~fc"
if not defined JARFILE (
	echo Equinox launcher not found under "%DESTINATION%\plugins"
	exit /b 1
)

set "REPO_URL=%REPO:\=/%"
set "REPO_URL=file:/%REPO_URL%"

echo DESTINATION = %DESTINATION%
echo REPOSITORY  = %REPO_URL%
echo IU          = %IU%
echo JARFILE     = %JARFILE%

if not exist "%DESTINATION%\director\configuration\config.ini" (
	echo Seeding %DESTINATION%\director\configuration\config.ini
	if not exist "%DESTINATION%\director\configuration" mkdir "%DESTINATION%\director\configuration"
	copy /Y "%~dp0director\configuration\config.ini" "%DESTINATION%\director\configuration\config.ini" >nul
	if errorlevel 1 exit /b 1
	set "OSGI_JAR="
	for %%c in ("%DESTINATION%\plugins\org.eclipse.osgi_*.jar") do set "OSGI_JAR=%%~nxc"
	if not defined OSGI_JAR (
		echo org.eclipse.osgi not found under "%DESTINATION%\plugins"
		exit /b 1
	)
	powershell -NoProfile -Command "(Get-Content -Raw '!DESTINATION!\director\configuration\config.ini') -replace 'org\.eclipse\.osgi_[^\r\n]*\.jar','!OSGI_JAR!' | Set-Content -NoNewline '!DESTINATION!\director\configuration\config.ini'"
	if errorlevel 1 exit /b 1
)

pushd "%DESTINATION%"
if errorlevel 1 exit /b 1

echo.
echo Uninstalling %IU% when it is already installed...
java -Dorg.eclipse.ecf.provider.filetransfer.excludeContributors=org.eclipse.ecf.provider.filetransfer.httpclient4 -Djava.net.preferIPv4Stack=true -jar "%JARFILE%" -install director -profile DefaultProfile -configuration director/configuration -application org.eclipse.equinox.p2.director -consoleLog -profileProperties org.eclipse.update.install.features=true -destination "%DESTINATION%" -repository "%REPO_URL%" -uninstallIU %IU%

echo.
echo Installing %IU%...
java -Dorg.eclipse.ecf.provider.filetransfer.excludeContributors=org.eclipse.ecf.provider.filetransfer.httpclient4 -Djava.net.preferIPv4Stack=true -jar "%JARFILE%" -install director -profile DefaultProfile -configuration director/configuration -application org.eclipse.equinox.p2.director -consoleLog -profileProperties org.eclipse.update.install.features=true -destination "%DESTINATION%" -repository "%REPO_URL%" -installIU %IU%
set "INSTALL_RC=%ERRORLEVEL%"
popd
if not "%INSTALL_RC%"=="0" (
	echo Install failed with exit code %INSTALL_RC%
	exit /b %INSTALL_RC%
)

echo Installed %IU% into "%DESTINATION%"
echo Set -DIDEMPIERE_EXTENSION_REPOSITORY=http://127.0.0.1:18080/myappx-extension-repository and start the server.
exit /b 0

:usage
echo Usage: p2-install.bat ^<idempiere-home^>
echo.
echo idempiere-home contains plugins\org.eclipse.equinox.launcher_1.*.jar
echo P2 site: org.idempiere.myappx.extension.repository.p2\target\repository
echo IU:      org.idempiere.myappx.extension.repository
exit /b 1
