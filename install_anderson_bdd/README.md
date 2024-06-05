docker-compose -p bdd_anderson up --build -d

docker-compose -p bdd_anderson up -d

docker-compose -p bdd_anderson down
Arrête les conteneurs.
-Supprime les conteneurs.
-Supprime les réseaux créés par Docker Compose.
-Supprime les volumes créés par Docker Compose (si l'option -v est utilisée).
-Supprime les images créées par Docker Compose (si l'option --rmi est utilisée).



docker-compose -p bdd_anderson start

docker-compose -p bdd_anderson stop


