@echo off
REM Change to the directory where the docker-compose.yml file is located
cd /d %~dp0

REM Stop and remove Docker containers, networks, images, and volumes
docker-compose -p bdd_anderson down --rmi all -v

REM End of script
