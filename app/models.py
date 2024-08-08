from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, ForeignKey, Date, Index
from sqlalchemy.orm import relationship
from sqlalchemy_utils import TSVectorType
from .database import Base
from datetime import datetime

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
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    user = relationship("User", back_populates="collections")
    documents = relationship("Document", back_populates="collection")

class Document(Base):
    __tablename__ = "documents"

    document_id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(Integer, ForeignKey("collections.collection_id"), nullable=False)
    title = Column(String(100), nullable=False)
    minio_link = Column(String(100), nullable=False)
    date_de_creation = Column(Date)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    posted_by = Column(String(30), nullable=False)

    collection = relationship("Collection", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document")

class Chunk(Base):
    __tablename__ = "chunks"

    chunk_id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.document_id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    taille_chunk = Column(Integer, nullable=False)
    embedding_cohere = Column(TSVectorType)
    embedding_solon = Column(TSVectorType)
    embedding_bge = Column(TSVectorType)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index("embedding_cohere_index", "document_id", "embedding_cohere"),
        Index("embedding_solon_index", "document_id", "embedding_solon"),
        Index("embedding_bge_index", "document_id", "embedding_bge"),
    )
