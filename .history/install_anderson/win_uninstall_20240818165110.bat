@echo off

REM Stop and remove Docker containers, networks, images, and volumes
docker-compose -p container_anderson_back_office down --rmi all -v

REM End of script
