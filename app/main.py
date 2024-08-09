from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from . import models, schemas, database
from .auth import get_current_user, auth_router, check_permission, get_password_hash
from typing import List, Optional
from fastapi.templating import Jinja2Templates
from minio import Minio
from minio.commonconfig import REPLACE, CopySource
from dotenv import load_dotenv

import os
import io
import re


# Charger les variables d'environnement
load_dotenv()

MINIO_URL = os.getenv("MINIO_URL")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")

# Initialiser le client Minio
minio_client = Minio(
    MINIO_URL,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)


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

    # Normaliser le nom de la collection pour les noms de buckets
    normalized_name = collection.name.replace(" ", "-").replace("_", "-").lower()

    # Vérifier si une collection avec le même nom existe déjà
    existing_collection = db.query(models.Collection).filter(
        models.Collection.name == normalized_name,
        models.Collection.user_id == (current_user.user_id if isinstance(current_user, models.User) else current_user["user_id"])
    ).first()
    if existing_collection:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A collection with this name already exists."
        )

    # Créer la nouvelle collection dans la BDD
    new_collection = models.Collection(
        name=normalized_name,
        description=collection.description,
        user_id=current_user.user_id if isinstance(current_user, models.User) else current_user["user_id"],  # Associe la collection à l'utilisateur actuel
        date_de_creation=datetime.now().date(),
        derniere_modification=datetime.now(timezone.utc)
    )
    db.add(new_collection)
    db.commit()
    db.refresh(new_collection)

    # Créer le bucket MinIO associé à la collection
    bucket_name = f"collection-{new_collection.collection_id}-{normalized_name}" 
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            new_collection.etat_bucket = "créé"
        else:
            new_collection.etat_bucket = "existant"
    except Exception as e:
        new_collection.etat_bucket = f"non-créé: {str(e)}"

    # Mettre à jour la collection dans la base de données avec l'état du bucket
    db.commit()

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

    # Conserver le nom original du bucket pour une éventuelle mise à jour
    original_bucket_name = f"collection-{collection.collection_id}-{re.sub(r'[^a-zA-Z0-9\-]', '-', collection.name)}"

    # Mettre à jour les champs de la collection
    old_name = collection.name
    collection.name = collection_update.name or collection.name
    collection.description = collection_update.description or collection.description

    # Normaliser le nom du nouveau bucket
    new_bucket_name = f"collection-{collection.collection_id}-{re.sub(r'[^a-zA-Z0-9\-]', '-', collection.name)}"

    # Si le nom de la collection a changé, renommer le bucket dans MinIO
    if collection_update.name and collection_update.name != old_name:
        try:
            # Créer le nouveau bucket s'il n'existe pas
            if not minio_client.bucket_exists(new_bucket_name):
                minio_client.make_bucket(new_bucket_name)

            # Copier chaque objet du bucket original vers le nouveau
            objects = minio_client.list_objects(original_bucket_name, recursive=True)
            for obj in objects:
                minio_client.copy_object(
                    bucket_name=new_bucket_name,
                    object_name=obj.object_name,
                    source=CopySource(original_bucket_name, obj.object_name)
                )

            # Supprimer l'ancien bucket
            objects = minio_client.list_objects(original_bucket_name, recursive=True)
            for obj in objects:
                minio_client.remove_object(original_bucket_name, obj.object_name)

            minio_client.remove_bucket(original_bucket_name)

            collection.etat_bucket = "mis à jour"
        except Exception as e:
            collection.etat_bucket = f"non-mis à jour: {str(e)}"

    # Mettre à jour les dates de création pour refléter la dernière mise à jour
    collection.derniere_modification = datetime.now(timezone.utc)

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

    # Nom du bucket MinIO associé à la collection
    bucket_name = f"collection-{collection.collection_id}-{collection.name.replace(' ', '-').replace('_', '-')}"

    # Vider le bucket dans MinIO
    try:
        objects = minio_client.list_objects(bucket_name, recursive=True)
        for obj in objects:
            minio_client.remove_object(bucket_name, obj.object_name)
        minio_client.remove_bucket(bucket_name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete bucket from MinIO: {str(e)}"
        )

    # Supprimer les documents associés et les chunks de la base de données
    db.query(models.Document).filter(models.Document.collection_id == collection_id).delete(synchronize_session=False)
    db.delete(collection)
    db.commit()

    return {"detail": "Collection, associated documents, and MinIO bucket deleted successfully"}

# ----------------------------------------------------------------------------------------------------------------------------------------------|

# ------------------------------------------------------ Endpoint pour upload un document ------------------------------------------------------|
@app.post(
    "/upload_document",
    response_model=schemas.Document,
    summary="Uploader un document dans une collection",
    description="Endpoint qui permet d'uploader un document dans une collection spécifique",
    tags=["Gestion des documents"]
)
async def upload_document(
    collection_id: int = Form(...),
    collection_name: str = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(get_current_user)
):
    check_permission(current_user, "author_post_collection")

    # Normalisation du nom du document pour le stockage dans MinIO
    title_document = file.filename.replace(" ", "-")

    # Nom du bucket MinIO associé à la collection
    bucket_name = f"collection-{collection_id}-{collection_name.replace(' ', '-').replace('_', '-')}"

    # Stocker le fichier dans le bucket MinIO
    try:
        minio_client.put_object(
            bucket_name=bucket_name,
            object_name=title_document,
            data=file.file,
            length=-1,  # minio will automatically calculate the length
            part_size=10*1024*1024  # 10 MB part size
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to MinIO: {str(e)}"
        )

    # Créer l'entrée du document dans la base de données
    new_document = models.Document(
        collection_id=collection_id,
        title=title,
        title_document=title_document,
        minio_link=f"http://{MINIO_URL}/browser/{bucket_name}/{title_document}",
        date_de_creation=datetime.now().date(),
        created_at=datetime.now(timezone.utc),
        posted_by=current_user.username if isinstance(current_user, models.User) else current_user["username"]
    )
    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return {
        "document_id": new_document.document_id,
        "collection_id": new_document.collection_id,
        "collection_name": collection_name,  # Ajout du nom de la collection à la réponse
        "title": new_document.title,
        "title_document": new_document.title_document,
        "minio_link": new_document.minio_link,
        "date_de_creation": new_document.date_de_creation,
        "created_at": new_document.created_at,
        "posted_by": new_document.posted_by
    }
# ----------------------------------------------------------------------------------------------------------------------------------------------|


# Lancer le serveur avec Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

