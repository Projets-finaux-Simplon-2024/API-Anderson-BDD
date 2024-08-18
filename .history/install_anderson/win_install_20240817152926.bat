@echo off
REM Change to the directory where the docker-compose.yml file is located

REM Start Docker containers with Docker Compose
docker-compose -p container_anderson_back_office up --build -d

REM End of script
