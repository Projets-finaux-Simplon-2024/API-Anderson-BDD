from fastapi import FastAPI

# Créer l'application FastAPI avec des métadonnées personnalisées
app = FastAPI(
    docs_url="/",
    redoc_url="/docs",
    title="API de Gestion de documents pour Anderson",
    description="Cette API permet de d'agréger des documents, de créer des collections pour la circonscription des questions d'un LLM",
    version="1.0.0",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}
)

@app.get("/test")
def read_root():
    return {"Hello": "World"}
