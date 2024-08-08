from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from . import models, schemas, database
from .auth import get_current_user, auth_router, check_permission, get_password_hash
from typing import List, Optional
from fastapi.templating import Jinja2Templates

# Créer l'application FastAPI avec des métadonnées personnalisées
app = FastAPI(
    docs_url="/",
    redoc_url="/docs",
    title="API de Gestion de documents pour Anderson",
    description="Cette API permet de d'agréger des documents, de créer des collections pour la circonscription des questions d'un LLM",
    version="1.0.0",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}
)

# Monter le routeur d'authentification
app.include_router(auth_router, prefix="/auth", tags=["Author"])

# Configurer le répertoire des templates
templates = Jinja2Templates(directory="templates")


# ------------------------------------------------------ Endpoint pour créer un utilisateur ----------------------------------------------------|
@app.post(
    "/create_user",
    response_model=schemas.User,
    summary="Création d'un utilisateur",
    description="Endpoint qui permet aux admins de créer un utilisateur",
    tags=["Gestion des utilisateurs"]
)
async def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user)
):
    check_permission(current_user, "author_post_user")

    # Vérifier si l'utilisateur existe déjà
    existing_user = db.query(models.User).filter(models.User.username == user.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Hacher le mot de passe avant de le stocker
    hashed_password = get_password_hash(user.password)

    # Créer le nouvel utilisateur
    new_user = models.User(
        username=user.username,
        passwords=hashed_password,
        email=user.email,
        role_id=user.role_id,
        date_de_creation=datetime.now().date(),
        created_at=datetime.now(timezone.utc)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

# ----------------------------------------------------------------------------------------------------------------------------------------------|


# ------------------------------------------------------ Endpoint pour consulter la liste des utilisateurs -------------------------------------|
@app.get(
    "/users",
    response_model=List[schemas.User],
    summary="Consulter la liste des utilisateurs",
    description="Endpoint qui permet de consulter la liste des utilisateurs",
    tags=["Gestion des utilisateurs"]
)
async def get_users(
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user)
):
    # Vérifier si l'utilisateur a les permissions nécessaires
    check_permission(current_user, "author_get_user")

    # Récupérer la liste des utilisateurs
    users = db.query(models.User).all()
    return users

# ----------------------------------------------------------------------------------------------------------------------------------------------|

# ------------------------------------------------------ Endpoint pour consulter un utilisateur par ID -----------------------------------------|
@app.get(
    "/users/{user_id}",
    response_model=schemas.User,
    summary="Consulter un utilisateur par ID",
    description="Endpoint qui permet de consulter un utilisateur spécifique par son ID",
    tags=["Gestion des utilisateurs"]
)
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user)
):
    # Vérifier si l'utilisateur a les permissions nécessaires
    check_permission(current_user, "author_get_user")

    # Récupérer l'utilisateur par ID
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

# ----------------------------------------------------------------------------------------------------------------------------------------------|

# ------------------------------------------------------ Endpoint pour mettre à jour un utilisateur --------------------------------------------|
@app.patch(
    "/users/{user_id}",
    response_model=schemas.User,
    summary="Mettre à jour un utilisateur",
    description="Endpoint qui permet de mettre à jour un utilisateur spécifique",
    tags=["Gestion des utilisateurs"]
)
async def update_user(
    user_id: int,
    user_update: schemas.UserCreate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user)
):
    # Vérifier si l'utilisateur a les permissions nécessaires
    check_permission(current_user, "author_patch_user")

    # Récupérer l'utilisateur par ID
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Mettre à jour les champs de l'utilisateur
    user.username = user_update.username or user.username
    user.email = user_update.email or user.email
    user.role_id = user_update.role_id or user.role_id

    if user_update.password:
        user.passwords = get_password_hash(user_update.password)

    db.commit()
    db.refresh(user)

    return user

# ----------------------------------------------------------------------------------------------------------------------------------------------|

# ------------------------------------------------------ Endpoint pour supprimer un utilisateur ------------------------------------------------|
@app.delete(
    "/users/{user_id}",
    response_model=dict,
    summary="Supprimer un utilisateur",
    description="Endpoint qui permet de supprimer un utilisateur spécifique",
    tags=["Gestion des utilisateurs"]
)
async def delete_user(
    user_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user)
):
    # Vérifier si l'utilisateur a les permissions nécessaires
    check_permission(current_user, "author_delete_user")

    # Récupérer l'utilisateur par ID
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Supprimer l'utilisateur
    db.delete(user)
    db.commit()

    return {"detail": "User deleted successfully"}

# ----------------------------------------------------------------------------------------------------------------------------------------------|

# ------------------------------------------------------ Endpoint pour créer une collection ---------------------------------------------------|
@app.post(
    "/create_collection",
    response_model=schemas.Collection,
    summary="Création d'une collection",
    description="Endpoint qui permet aux admins de créer une collection",
    tags=["Gestion des collections"]
)
async def create_collection(
    collection: schemas.CollectionCreate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user)
):
    check_permission(current_user, "author_post_collection")

    # Créer la nouvelle collection
    new_collection = models.Collection(
        name=collection.name,
        description=collection.description,
        user_id=current_user.user_id if isinstance(current_user, models.User) else current_user["user_id"],  # Associe la collection à l'utilisateur actuel
        date_de_creation=datetime.now().date(),
        created_at=datetime.now(timezone.utc)
    )
    db.add(new_collection)
    db.commit()
    db.refresh(new_collection)

    return new_collection
# ----------------------------------------------------------------------------------------------------------------------------------------------|

# ------------------------------------------------------ Endpoint pour consulter la liste des collections --------------------------------------|
@app.get(
    "/collections",
    response_model=List[schemas.Collection],
    summary="Consulter la liste des collections",
    description="Endpoint qui permet de consulter la liste des collections",
    tags=["Gestion des collections"]
)
async def get_collections(
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user)
):
    # Vérifier si l'utilisateur a les permissions nécessaires
    check_permission(current_user, "author_get_collection")

    # Récupérer la liste des collections
    collections = db.query(models.Collection).all()
    return collections

# ----------------------------------------------------------------------------------------------------------------------------------------------|

# ------------------------------------------------------ Endpoint pour consulter une collection par ID -----------------------------------------|
@app.get(
    "/collections/{collection_id}",
    response_model=schemas.Collection,
    summary="Consulter une collection par ID",
    description="Endpoint qui permet de consulter une collection spécifique par son ID",
    tags=["Gestion des collections"]
)
async def get_collection_by_id(
    collection_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user)
):
    # Vérifier si l'utilisateur a les permissions nécessaires
    check_permission(current_user, "author_get_collection")

    # Récupérer la collection par ID
    collection = db.query(models.Collection).filter(models.Collection.collection_id == collection_id).first()
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    return collection

# ----------------------------------------------------------------------------------------------------------------------------------------------|

# ------------------------------------------------------ Endpoint pour mettre à jour une collection --------------------------------------------|
@app.patch(
    "/collections/{collection_id}",
    response_model=schemas.Collection,
    summary="Mettre à jour une collection",
    description="Endpoint qui permet de mettre à jour une collection spécifique",
    tags=["Gestion des collections"]
)
async def update_collection(
    collection_id: int,
    collection_update: schemas.CollectionUpdate,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user)
):
    # Vérifier si l'utilisateur a les permissions nécessaires
    check_permission(current_user, "author_patch_collection")

    # Récupérer la collection par ID
    collection = db.query(models.Collection).filter(models.Collection.collection_id == collection_id).first()
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )

    # Mettre à jour les champs de la collection
    collection.name = collection_update.name or collection.name
    collection.description = collection_update.description or collection.description

    db.commit()
    db.refresh(collection)

    return collection

# ----------------------------------------------------------------------------------------------------------------------------------------------|

# ------------------------------------------------------ Endpoint pour supprimer une collection ------------------------------------------------|
@app.delete(
    "/collections/{collection_id}",
    response_model=dict,
    summary="Supprimer une collection",
    description="Endpoint qui permet de supprimer une collection spécifique",
    tags=["Gestion des collections"]
)
async def delete_collection(
    collection_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user)
):
    # Vérifier si l'utilisateur a les permissions nécessaires
    check_permission(current_user, "author_delete_collection")

    # Récupérer la collection par ID
    collection = db.query(models.Collection).filter(models.Collection.collection_id == collection_id).first()
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )

    # Supprimer la collection
    db.delete(collection)
    db.commit()

    return {"detail": "Collection deleted successfully"}

# ----------------------------------------------------------------------------------------------------------------------------------------------|

# Lancer le serveur avec Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

