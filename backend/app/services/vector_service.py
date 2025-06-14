import os
import json
import pickle
import numpy as np
from typing import List, Dict, Optional, Tuple
import chromadb
from chromadb.config import Settings
import openai
import logging
from datetime import datetime
import asyncio
import uuid

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self, 
                 chroma_persist_directory: str,
                 openai_api_key: str,
                 embedding_model: str = "text-embedding-ada-002",
                 similarity_threshold: float = 0.6):
        """Initialize vector service with Chroma client and OpenAI"""
        self.chroma_persist_directory = chroma_persist_directory
        self.embedding_model = embedding_model
        self.similarity_threshold = similarity_threshold
        openai.api_key = openai_api_key
        
        # Initialize Chroma client
        self.client = self.create_chroma_client()
        self.collection = self.client.get_or_create_collection(
            name="user_facts",
            metadata={"hnsw:space": "cosine"}
        )
        
    def create_chroma_client(self) -> chromadb.Client:
        """Create and configure Chroma client"""
        try:
            # Ensure persist directory exists
            os.makedirs(self.chroma_persist_directory, exist_ok=True)
            
            client = chromadb.PersistentClient(
                path=self.chroma_persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            logger.info(f"Chroma client initialized with persist directory: {self.chroma_persist_directory}")
            return client
        except Exception as e:
            logger.error(f"Error creating Chroma client: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API"""
        try:
            response = await openai.Embedding.acreate(
                model=self.embedding_model,
                input=text
            )
            embedding = response['data'][0]['embedding']
            
            logger.debug(f"Generated embedding for text length: {len(text)}, dimension: {len(embedding)}")
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def generate_embedding_sync(self, text: str) -> List[float]:
        """Synchronous version of embedding generation"""
        try:
            response = openai.Embedding.create(
                model=self.embedding_model,
                input=text
            )
            embedding = response['data'][0]['embedding']
            
            logger.debug(f"Generated embedding for text length: {len(text)}, dimension: {len(embedding)}")
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def store_embedding(self, 
                       fact_id: str, 
                       user_id: str, 
                       fact_text: str, 
                       embedding: List[float],
                       metadata: Dict = None) -> bool:
        """Store embedding in Chroma database"""
        try:
            # Prepare metadata
            stored_metadata = {
                "user_id": user_id,
                "fact_id": fact_id,
                "created_at": datetime.now().isoformat(),
                "text_length": len(fact_text)
            }
            
            if metadata:
                stored_metadata.update(metadata)
            
            # Store in Chroma
            self.collection.add(
                embeddings=[embedding],
                documents=[fact_text],
                metadatas=[stored_metadata],
                ids=[fact_id]
            )
            
            logger.info(f"Stored embedding for fact_id: {fact_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing embedding: {e}")
            return False
    
    def search_similar_facts(self, 
                           query_text: str, 
                           user_id: str,
                           limit: int = 10,
                           fact_types: Optional[List[str]] = None) -> List[Dict]:
        """Search for similar facts using vector similarity"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding_sync(query_text)
            
            # Prepare where clause for user filtering
            where_clause = {"user_id": user_id}
            if fact_types:
                where_clause["fact_type"] = {"$in": fact_types}
            
            # Search in Chroma
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results
            similar_facts = []
            if results['ids'] and results['ids'][0]:
                for i, fact_id in enumerate(results['ids'][0]):
                    similarity_score = 1 - results['distances'][0][i]  # Convert distance to similarity
                    
                    if similarity_score >= self.similarity_threshold:
                        similar_facts.append({
                            'fact_id': fact_id,
                            'document': results['documents'][0][i],
                            'metadata': results['metadatas'][0][i],
                            'similarity_score': similarity_score
                        })
            
            logger.info(f"Found {len(similar_facts)} similar facts for user {user_id}")
            return similar_facts
        except Exception as e:
            logger.error(f"Error searching similar facts: {e}")
            return []
    
    async def batch_embed_facts(self, fact_texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple facts in batch"""
        try:
            # OpenAI supports batch embedding
            response = await openai.Embedding.acreate(
                model=self.embedding_model,
                input=fact_texts
            )
            
            embeddings = [item['embedding'] for item in response['data']]
            
            logger.info(f"Generated {len(embeddings)} embeddings in batch")
            return embeddings
        except Exception as e:
            logger.error(f"Error in batch embedding: {e}")
            raise
    
    def update_embedding(self, fact_id: str, new_text: str, metadata: Dict = None) -> bool:
        """Update existing embedding with new text"""
        try:
            # Generate new embedding
            new_embedding = self.generate_embedding_sync(new_text)
            
            # Delete old embedding
            self.collection.delete(ids=[fact_id])
            
            # Store new embedding
            updated_metadata = metadata or {}
            updated_metadata.update({
                "updated_at": datetime.now().isoformat(),
                "text_length": len(new_text)
            })
            
            self.collection.add(
                embeddings=[new_embedding],
                documents=[new_text],
                metadatas=[updated_metadata],
                ids=[fact_id]
            )
            
            logger.info(f"Updated embedding for fact_id: {fact_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating embedding: {e}")
            return False
    
    def delete_embedding(self, fact_id: str) -> bool:
        """Delete embedding from Chroma database"""
        try:
            self.collection.delete(ids=[fact_id])
            logger.info(f"Deleted embedding for fact_id: {fact_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting embedding: {e}")
            return False
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the vector collection"""
        try:
            count = self.collection.count()
            return {
                "total_embeddings": count,
                "collection_name": self.collection.name,
                "persist_directory": self.chroma_persist_directory
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)} 