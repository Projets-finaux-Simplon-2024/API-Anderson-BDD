@echo off

:: Définir la version de Python à utiliser
set PYTHON_VERSION=py -3.12

:: Vérifier si l'environnement virtuel existe
if not exist "env_api_anderson" (
    echo Création de l'environnement virtuel...
    %PYTHON_VERSION% -m venv env_api_anderson
)

:: Activer l'environnement virtuel
call env_api_anderson\Scripts\activate

:: Upgrade de pip
python -m pip install --upgrade pip

:: Installer les dépendances
python -m pip install -r requirements.txt

:: Appliquer les migrations Alembic
alembic upgrade head

:: Lancer l'application
uvicorn app.main:app --reload

:: Désactiver l'environnement virtuel
deactivate

echo Fin de l'exécution du script.
pause