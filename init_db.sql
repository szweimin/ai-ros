-- 启用pgvector扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 创建ROS文档块表
CREATE TABLE IF NOT EXISTS ros_document_chunks (
    id SERIAL PRIMARY KEY,
    chunk_id VARCHAR(100) UNIQUE NOT NULL,
    text TEXT NOT NULL,
    embedding JSONB,
    metadata JSONB NOT NULL,
    category VARCHAR(50) NOT NULL,
    source_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_source (source_id),
    INDEX idx_chunk_id (chunk_id)
);

-- 创建查询历史表
CREATE TABLE IF NOT EXISTS query_history (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    answer TEXT NOT NULL