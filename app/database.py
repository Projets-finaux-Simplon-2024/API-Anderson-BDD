from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Charger les variables d'environnement
import os
from dotenv import load_dotenv
load_dotenv()

# URL de la base de données
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin@localhost/anderson")

# Créer le moteur de base de données
engine = create_engine(DATABASE_URL)

# Créer une classe de base pour les modèles de base de données
Base = declarative_base()

# Créer une usine de sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dépendance pour obtenir une session de base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
