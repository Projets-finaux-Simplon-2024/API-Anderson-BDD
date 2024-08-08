from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from .schemas import Token, Role as RoleSchema
from .database import get_db
from .models import User, Role
from passlib.context import CryptContext

# Charger les variables d'environnement à partir du fichier .env
load_dotenv()

SUPER_USER = os.getenv("SUPER_USER")
SUPER_PASSWORD = os.getenv("SUPER_PASSWORD")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

auth_router = APIRouter()

# ---- Personnalisation du formulaire de connexion
class OAuth2PasswordRequestFormCustom:
    def __init__(
        self,
        username: str = Form(...),
        password: str = Form(...),
    ):
        self.username = username
        self.password = password

# ---- Vérification du mot de passe
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# ---- Hacher le mot de passe
def get_password_hash(password):
    return pwd_context.hash(password)

# ---- Authentification de l'utilisateur
def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if user and verify_password(password, user.passwords):
        return user
    return None

# ---- Création du token d'accès
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ---- Crédential
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    if username == SUPER_USER:
        super_user_role = RoleSchema(
            role_id=0,
            role_name="superuser",
            author_get_doc=True,
            author_post_doc=True,
            author_put_doc=True,
            author_patch_doc=True,
            author_delete_doc=True,
            author_get_collection=True,
            author_post_collection=True,
            author_put_collection=True,
            author_patch_collection=True,
            author_delete_collection=True,
            author_get_user=True,
            author_post_user=True,
            author_put_user=True,
            author_patch_user=True,
            author_delete_user=True
        )
        return {"username": SUPER_USER, "role": super_user_role}

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# ------------------------------------------------------ Vérification des permissions ----------------------------------------------------------|
def check_permission(current_user, permission: str):
    if isinstance(current_user, dict) and current_user["username"] == SUPER_USER:
        return
    if not getattr(current_user.role, permission, False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have permission to {permission.replace('_', ' ')}."
        )
# ----------------------------------------------------------------------------------------------------------------------------------------------|



# ------------------------------------------------------ Endpoint pour récupérer un token ------------------------------------------------------|
@auth_router.post(
        "/token",
        response_model=Token,
        summary="Récupération d'un token d'authentification",
        description="Récupération d'un token d'authentification crypté par défaut avec un algorithme HS256 pour une durée de 30 minutes"
)
async def login_for_access_token(form_data: OAuth2PasswordRequestFormCustom = Depends(), db: Session = Depends(get_db)):
    if form_data.username == SUPER_USER and verify_password(form_data.password, SUPER_PASSWORD):
        # Créer une réponse pour le super utilisateur
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": form_data.username}, expires_delta=access_token_expires
        )
        super_role = RoleSchema(
            role_id=0,
            role_name="superuser",
            author_get_doc=True,
            author_post_doc=True,
            author_put_doc=True,
            author_patch_doc=True,
            author_delete_doc=True,
            author_get_collection=True,
            author_post_collection=True,
            author_put_collection=True,
            author_patch_collection=True,
            author_delete_collection=True,
            author_get_user=True,
            author_post_user=True,
            author_put_user=True,
            author_patch_user=True,
            author_delete_user=True
        )
        return {
            "user_id": 0,
            "username": SUPER_USER,
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES,
            "algorithm": ALGORITHM,
            "role_id": 0,
            "role": super_role
        }

    # Authentification pour les utilisateurs de la base de données
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    user_role = db.query(Role).filter(Role.role_id == user.role_id).first()
    role_data = RoleSchema(
        role_id=user_role.role_id,
        role_name=user_role.role_name,
        author_get_doc=user_role.author_get_doc,
        author_post_doc=user_role.author_post_doc,
        author_put_doc=user_role.author_put_doc,
        author_patch_doc=user_role.author_patch_doc,
        author_delete_doc=user_role.author_delete_doc,
        author_get_collection=user_role.author_get_collection,
        author_post_collection=user_role.author_post_collection,
        author_put_collection=user_role.author_put_collection,
        author_patch_collection=user_role.author_patch_collection,
        author_delete_collection=user_role.author_delete_collection,
        author_get_user=user_role.author_get_user,
        author_post_user=user_role.author_post_user,
        author_put_user=user_role.author_put_user,
        author_patch_user=user_role.author_patch_user,
        author_delete_user=user_role.author_delete_user
    )
    return {
        "user_id": user.user_id,
        "username": user.username,
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES,
        "algorithm": ALGORITHM,
        "role_id": user.role_id,
        "role": role_data
    }
# ----------------------------------------------------------------------------------------------------------------------------------------------|
