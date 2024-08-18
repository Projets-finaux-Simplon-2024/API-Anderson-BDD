@echo off

REM Logout from any active Docker sessions to avoid potential pull issues
docker logout ghcr.io

REM Start Docker containers with Docker Compose
docker-compose -p container_anderson_back_office up --build -d

REM End of script
