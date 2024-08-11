from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, ForeignKey, Date
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
from pgvector.sqlalchemy import Vector


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(30), nullable=False)
    passwords = Column(String(60), nullable=False)
    email = Column(String(100), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False)
    date_de_creation = Column(Date)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    role = relationship("Role", back_populates="users")
    collections = relationship("Collection", back_populates="user")

class Role(Base):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50))
    description = Column(Text)
    author_get_doc = Column(Boolean, default=False)
    author_post_doc = Column(Boolean, default=False)
    author_put_doc = Column(Boolean, default=False)
    author_patch_doc = Column(Boolean, default=False)
    author_delete_doc = Column(Boolean, default=False)
    author_get_collection = Column(Boolean, default=False)
    author_post_collection = Column(Boolean, default=False)
    author_put_collection = Column(Boolean, default=False)
    author_patch_collection = Column(Boolean, default=False)
    author_delete_collection = Column(Boolean, default=False)
    author_get_user = Column(Boolean, default=False)
    author_post_user = Column(Boolean, default=False)
    author_put_user = Column(Boolean, default=False)
    author_patch_user = Column(Boolean, default=False)
    author_delete_user = Column(Boolean, default=False)

    users = relationship("User", back_populates="role")

class Collection(Base):
    __tablename__ = "collections"

    collection_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    date_de_creation = Column(Date)
    derniere_modification = Column(TIMESTAMP, default=datetime.utcnow)
    etat_bucket = Column(String(300))

    user = relationship("User", back_populates="collections")
    documents = relationship("Document", back_populates="collection", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"

    document_id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(Integer, ForeignKey("collections.collection_id"), nullable=False)
    title = Column(String(100), nullable=False)
    title_document = Column(String(255), nullable=False)
    minio_link = Column(String(255), nullable=False)
    date_de_creation = Column(Date)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    posted_by = Column(String(30), nullable=False)
    num_of_chunks = Column(Integer, nullable=False, default=0)  # Nouvelle colonne ajoutée

    collection = relationship("Collection", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    chunk_id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.document_id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    taille_chunk = Column(Integer, nullable=False)
    embedding_cohere = Column(Vector(dim=1024), nullable=True)
    embedding_solon = Column(Vector(dim=1024), nullable=True)
    embedding_bge = Column(Vector(dim=1024), nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    document = relationship("Document", back_populates="chunks")
