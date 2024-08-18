@echo off

REM Start Docker containers with Docker Compose
docker-compose -p container_anderson_back_office up --build -d

REM End of script
