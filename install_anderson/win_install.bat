@echo off

REM Logout from any active Docker sessions to avoid potential pull issues
docker logout ghcr.io

REM Check if the monitoring network exists
docker network inspect monitoring_network >nul 2>&1

REM If the network does not exist, create it
IF %ERRORLEVEL% NEQ 0 (
    echo Monitoring network not found. Creating the network...
    FOR /F "tokens=*" %%i IN ('docker network create monitoring_network') DO SET NET_RESULT=%%i
    IF NOT DEFINED NET_RESULT (
        echo Failed to create the monitoring network.
        echo Press any key to exit...
        pause > nul
        exit /b 1
    )
    echo Monitoring network created successfully with ID: %NET_RESULT%
) ELSE (
    echo Monitoring network already exists.
)

REM Start Docker containers with Docker Compose
docker-compose -p container_anderson_back_office up --build -d

REM Check if Docker Compose was successful
IF %ERRORLEVEL% EQU 0 (
    echo Docker containers started successfully.
) ELSE (
    echo There was an error starting the Docker containers.
)

REM Wait for user input to close the terminal
echo Press any key to exit...
pause > nul