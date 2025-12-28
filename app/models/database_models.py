from sqlalchemy import Column, Integer, String, Text, Float, JSON, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

Base = declarative_base()

class ROSDocumentChunk(Base):
    """ROS文档块表"""
    __tablename__ = "ros_document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(String(100), unique=True, index=True, nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)  # 存储JSON格式的向量
    embedding_vector = Column(String, nullable=True)  # 存储pgvector格式的向量
    # 重命名metadata为doc_metadata以避免冲突
    doc_metadata = Column(JSONB, nullable=False)
    category = Column(String(50), index=True, nullable=False)
    source_id = Column(String(100), index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_category_source', 'category', 'source_id'),
        Index('idx_doc_metadata', 'doc_metadata', postgresql_using='gin'),
        Index('idx_embedding_vector', 'embedding_vector'),
    )

class QueryHistory(Base):
    """查询历史表"""
    __tablename__ = "query_history"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(JSONB, nullable=True)
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_query_created', 'created_at'),
    )