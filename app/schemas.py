# schemas.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# ---- Gestion des utilisateurs ----------------------|
class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    role_id: int

class User(BaseModel):
    user_id: int
    username: str
    email: str
    role_id: int
    date_de_creation: Optional[datetime]
    created_at: Optional[datetime]  

    class Config:
        from_attributes = True

class Role(BaseModel):
    role_id: int
    role_name: str
    author_get_doc: bool
    author_post_doc: bool
    author_put_doc: bool
    author_patch_doc: bool
    author_delete_doc: bool
    author_get_collection: bool
    author_post_collection: bool
    author_put_collection: bool
    author_patch_collection: bool
    author_delete_collection: bool
    author_get_user: bool
    author_post_user: bool
    author_put_user: bool
    author_patch_user: bool
    author_delete_user: bool

    class Config:
        from_attributes = True
# ----------------------------------------------------|


# ---- Gestions des collections ----------------------|
class CollectionBase(BaseModel):
    name: str
    description: Optional[str] = None

class CollectionCreate(CollectionBase):
    pass

class CollectionUpdate(CollectionBase):
    pass

class Collection(CollectionBase):
    collection_id: int
    user_id: int
    date_de_creation: Optional[datetime]
    derniere_modification: Optional[datetime]
    etat_bucket: str

    class Config:
        from_attributes = True
# ----------------------------------------------------|



# ---- Gestion des token -----------------------------|
class Token(BaseModel):
    user_id: int
    username: str
    access_token: str
    token_type: str
    expires_in: int
    algorithm: str
    role_id: int
    role: Role
# ----------------------------------------------------|




# ---- Gestion de l'upload ---------------------------|
class DocumentCreate(BaseModel):
    collection_id: int
    collection_name: str
    title: str

class Document(BaseModel):
    document_id: int
    collection_id: int
    collection_name: str
    title: str
    title_document: str
    minio_link: str
    date_de_creation: Optional[datetime]
    created_at: Optional[datetime]
    posted_by: str
    number_of_chunks: Optional[int] = None
    execution_time: Optional[str] = None

    class Config:
        from_attributes = True
# ----------------------------------------------------|


# ---- Reponse top n chunk ---------------------------|
class ChunkResult(BaseModel):
    chunk_id: int
    document_id: int
    chunk_text: str
    distance: float

    class Config:
        from_attributes = True

class SearchResponse(BaseModel):
    results: List[ChunkResult]
# ----------------------------------------------------|