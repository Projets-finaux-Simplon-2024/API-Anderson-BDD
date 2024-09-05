@echo off
:: Vérifier si Docker est installé
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker n'est pas installé. Veuillez installer Docker et réessayer.
    pause
    exit /b
)

:: Vérifier si l'image Redis existe déjà
docker image inspect redis >nul 2>&1
if %errorlevel% neq 0 (
    echo Téléchargement de l'image Redis...
    docker pull redis:latest
)

:: Vérifier si un conteneur Redis est déjà en cours d'exécution
docker ps -a --filter "name=redis_container" | findstr "redis_container" >nul
if %errorlevel% neq 0 (
    echo Démarrage d'un nouveau conteneur Redis...
    docker run --name redis_container -p 6379:6379 -d redis:latest
) else (
    echo Le conteneur Redis existe déjà. Le démarrage...
    docker start redis_container
)

echo Redis est en cours d'exécution sur le port 6379.
pause