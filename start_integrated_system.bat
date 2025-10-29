@echo off
echo Starting Integrated Face Recognition Clocking System...
echo.

echo Starting Face Recognition Service...
start "Face Recognition API" cmd /k "cd /d %~dp0 && python main.py"

echo Waiting for Face Recognition Service to start...
timeout /t 5 /nobreak > nul

echo Starting Backend Service...
start "Backend API" cmd /k "cd /d %~dp0\..\Clocking-System-Backend && python manage.py runserver 127.0.0.1:8001"

echo Waiting for Backend Service to start...
timeout /t 5 /nobreak > nul

echo Starting Web Application...
start "Web Application" cmd /k "cd /d %~dp0\..\Clocking-Web-Application && ng serve --port 4200"

echo.
echo All services are starting...
echo.
echo Face Recognition API: http://127.0.0.1:8000
echo Backend API: http://127.0.0.1:8001/api
echo Web Application: http://localhost:4200
echo.
echo Press any key to close this window...
pause > nul