@echo off
REM Development startup script for Windows

echo Starting ShortsGen services...

REM Create output directory
if not exist "output" mkdir output
if not exist "output\scenes" mkdir output\scenes
if not exist "output\video" mkdir output\video
if not exist "output\voice" mkdir output\voice
if not exist "output\text" mkdir output\text

REM Start API Gateway
echo Starting API Gateway on port 8000...
cd api_gateway
start "API Gateway" python app.py

REM Start Processing Service
echo Starting Processing Service on port 8001...
cd ..\processing_service
start "Processing Service" python app.py

REM Start Text Service
echo Starting Text Service on port 8002...
cd ..\text_service
start "Text Service" python app.py

echo Services started!
echo.
echo API Gateway: http://localhost:8000
echo Processing Service: http://localhost:8001
echo Text Service: http://localhost:8002
echo.
echo Check the opened terminal windows for service logs.
echo To stop services, close the terminal windows or press Ctrl+C in each.

cd ..
