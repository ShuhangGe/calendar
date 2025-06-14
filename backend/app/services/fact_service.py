import uuid
import pickle
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
import logging

from ..models.database import UserFact, VectorEmbedding, User, Conversation
from ..models.schemas import UserFactCreate, UserFactUpdate, UserFactResponse
from .encryption_service import EncryptionService
from .vector_service import VectorService

logger = logging.getLogger(__name__)

class FactService:
    def __init__(self, 
                 encryption_service: EncryptionService,
                 vector_service: VectorService):
        """Initialize fact service with encryption and vector services"""
        self.encryption_service = encryption_service
        self.vector_service = vector_service
        
    def create_fact(self, 
                   db: Session,
                   user_id: str,
                   user_password_hash: str,
                   fact_data: UserFactCreate) -> Optional[UserFactResponse]:
        """Create new fact with encryption and embedding generation"""
        try:
            # Encrypt fact value and key
            if fact_data.is_sensitive:
                encrypted_value = self.encryption_service.encrypt_sensitive_fact(
                    fact_data.fact_value, user_id, user_password_hash
                )
                encrypted_key = self.encryption_service.encrypt_sensitive_fact(
                    fact_data.fact_key, user_id, user_password_hash
                )
            else:
                encrypted_value = self.encryption_service.encrypt_fact(
                    fact_data.fact_value, user_id, user_password_hash
                )
                encrypted_key = self.encryption_service.encrypt_fact(
                    fact_data.fact_key, user_id, user_password_hash
                )
            
            # Create fact record
            db_fact = UserFact(
                user_id=uuid.UUID(user_id),
                fact_type=fact_data.fact_type,
                fact_key=encrypted_key,
                fact_value=encrypted_value,
                confidence_score=fact_data.confidence_score,
                source_conversation_id=fact_data.source_conversation_id,
                is_sensitive=fact_data.is_sensitive
            )
            
            db.add(db_fact)
            db.flush()  # Get the fact ID
            
            # Generate and store embedding
            fact_text = f"{fact_data.fact_key}: {fact_data.fact_value}"
            embedding = self.vector_service.generate_embedding_sync(fact_text)
            
            # Store embedding in Chroma
            self.vector_service.store_embedding(
                fact_id=str(db_fact.id),
                user_id=user_id,
                fact_text=fact_text,
                embedding=embedding,
                metadata={
                    "fact_type": fact_data.fact_type,
                    "confidence_score": fact_data.confidence_score,
                    "is_sensitive": fact_data.is_sensitive
                }
            )
            
            # Store embedding record in database
            db_embedding = VectorEmbedding(
                fact_id=db_fact.id,
                embedding_vector=pickle.dumps(embedding),
                embedding_model=self.vector_service.embedding_model
            )
            
            db.add(db_embedding)
            db.commit()
            
            logger.info(f"Created fact {db_fact.id} for user {user_id}")
            
            # Return decrypted response
            return UserFactResponse(
                id=db_fact.id,
                user_id=db_fact.user_id,
                fact_type=fact_data.fact_type,
                fact_key=fact_data.fact_key,
                fact_value=fact_data.fact_value,
                confidence_score=fact_data.confidence_score,
                source_conversation_id=fact_data.source_conversation_id,
                created_at=db_fact.created_at,
                last_accessed=db_fact.last_accessed,
                is_sensitive=fact_data.is_sensitive,
                encryption_key_version=db_fact.encryption_key_version
            )
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating fact: {e}")
            raise
    
    def get_user_facts(self, 
                      db: Session,
                      user_id: str,
                      user_password_hash: str,
                      fact_types: Optional[List[str]] = None,
                      limit: int = 50,
                      offset: int = 0) -> List[UserFactResponse]:
        """Get user facts with simple confidence + recency scoring"""
        try:
            query = db.query(UserFact).filter(UserFact.user_id == uuid.UUID(user_id))
            
            if fact_types:
                query = query.filter(UserFact.fact_type.in_(fact_types))
            
            # Simple scoring: confidence * 0.7 + recency * 0.3
            facts = query.order_by(
                desc(UserFact.confidence_score * 0.7 + 
                     func.extract('epoch', func.now() - UserFact.created_at) / 86400 * 0.3)
            ).offset(offset).limit(limit).all()
            
            # Decrypt and return facts
            decrypted_facts = []
            for fact in facts:
                try:
                    decrypted_fact = self._decrypt_fact(fact, user_id, user_password_hash)
                    decrypted_facts.append(decrypted_fact)
                    
                    # Update last_accessed
                    fact.last_accessed = datetime.now()
                except Exception as e:
                    logger.error(f"Error decrypting fact {fact.id}: {e}")
                    continue
            
            db.commit()
            logger.info(f"Retrieved {len(decrypted_facts)} facts for user {user_id}")
            return decrypted_facts
            
        except Exception as e:
            logger.error(f"Error getting user facts: {e}")
            return []
    
    def search_facts_by_context(self, 
                               user_id: str,
                               user_password_hash: str,
                               context_query: str,
                               fact_types: Optional[List[str]] = None,
                               limit: int = 10) -> List[Dict]:
        """Search facts using vector similarity"""
        try:
            # Search using vector service
            similar_facts = self.vector_service.search_similar_facts(
                query_text=context_query,
                user_id=user_id,
                limit=limit,
                fact_types=fact_types
            )
            
            # Add decrypted fact data
            enriched_facts = []
            for fact_data in similar_facts:
                fact_id = fact_data['fact_id']
                similarity_score = fact_data['similarity_score']
                
                # Get full fact from database (this could be optimized)
                db_fact = self._get_fact_by_id(fact_id)
                if db_fact:
                    try:
                        decrypted_fact = self._decrypt_fact(db_fact, user_id, user_password_hash)
                        enriched_facts.append({
                            'fact': decrypted_fact,
                            'similarity_score': similarity_score,
                            'metadata': fact_data['metadata']
                        })
                    except Exception as e:
                        logger.error(f"Error decrypting fact {fact_id}: {e}")
                        continue
            
            logger.info(f"Found {len(enriched_facts)} relevant facts for context query")
            return enriched_facts
            
        except Exception as e:
            logger.error(f"Error searching facts by context: {e}")
            return []
    
    def get_relevant_facts(self, 
                          db: Session,
                          user_id: str,
                          user_password_hash: str,
                          context: str,
                          max_facts: int = 10) -> List[UserFactResponse]:
        """Get relevant facts combining multiple retrieval strategies"""
        try:
            # Strategy 1: Vector similarity search
            vector_facts = self.search_facts_by_context(
                user_id=user_id,
                user_password_hash=user_password_hash,
                context_query=context,
                limit=max_facts
            )
            
            # Strategy 2: Recent high-confidence facts
            recent_facts = self.get_user_facts(
                db=db,
                user_id=user_id,
                user_password_hash=user_password_hash,
                limit=max_facts // 2
            )
            
            # Combine and deduplicate
            combined_facts = {}
            
            # Add vector facts with similarity weighting
            for fact_data in vector_facts:
                fact = fact_data['fact']
                score = fact_data['similarity_score'] * 0.8 + fact.confidence_score * 0.2
                combined_facts[str(fact.id)] = (fact, score)
            
            # Add recent facts with recency weighting
            for fact in recent_facts[:max_facts // 2]:
                if str(fact.id) not in combined_facts:
                    # Calculate recency score (newer = higher score)
                    days_old = (datetime.now() - fact.created_at).days
                    recency_score = max(0, 1.0 - (days_old / 30))  # Decay over 30 days
                    score = fact.confidence_score * 0.6 + recency_score * 0.4
                    combined_facts[str(fact.id)] = (fact, score)
            
            # Sort by combined score and return top facts
            sorted_facts = sorted(combined_facts.values(), key=lambda x: x[1], reverse=True)
            top_facts = [fact for fact, score in sorted_facts[:max_facts]]
            
            logger.info(f"Retrieved {len(top_facts)} relevant facts for user context")
            return top_facts
            
        except Exception as e:
            logger.error(f"Error getting relevant facts: {e}")
            return []
    
    def update_fact(self, 
                   db: Session,
                   fact_id: str,
                   user_id: str,
                   user_password_hash: str,
                   update_data: UserFactUpdate) -> Optional[UserFactResponse]:
        """Update fact with re-encryption if needed"""
        try:
            fact = db.query(UserFact).filter(
                and_(UserFact.id == uuid.UUID(fact_id), 
                     UserFact.user_id == uuid.UUID(user_id))
            ).first()
            
            if not fact:
                return None
            
            # Update fields
            for field, value in update_data.dict(exclude_unset=True).items():
                if field in ['fact_key', 'fact_value'] and value is not None:
                    # Re-encrypt updated values
                    if fact.is_sensitive:
                        encrypted_value = self.encryption_service.encrypt_sensitive_fact(
                            value, user_id, user_password_hash
                        )
                    else:
                        encrypted_value = self.encryption_service.encrypt_fact(
                            value, user_id, user_password_hash
                        )
                    setattr(fact, field, encrypted_value)
                elif value is not None:
                    setattr(fact, field, value)
            
            # Update embedding if fact content changed
            if update_data.fact_key is not None or update_data.fact_value is not None:
                # Get current decrypted values
                decrypted_fact = self._decrypt_fact(fact, user_id, user_password_hash)
                fact_text = f"{decrypted_fact.fact_key}: {decrypted_fact.fact_value}"
                
                # Update vector embedding
                self.vector_service.update_embedding(
                    fact_id=fact_id,
                    new_text=fact_text,
                    metadata={
                        "fact_type": fact.fact_type,
                        "confidence_score": fact.confidence_score,
                        "is_sensitive": fact.is_sensitive
                    }
                )
            
            db.commit()
            logger.info(f"Updated fact {fact_id}")
            
            return self._decrypt_fact(fact, user_id, user_password_hash)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating fact: {e}")
            raise
    
    def delete_fact(self, 
                   db: Session,
                   fact_id: str,
                   user_id: str) -> bool:
        """Delete fact with cascade deletion of embeddings"""
        try:
            fact = db.query(UserFact).filter(
                and_(UserFact.id == uuid.UUID(fact_id), 
                     UserFact.user_id == uuid.UUID(user_id))
            ).first()
            
            if not fact:
                return False
            
            # Delete vector embedding
            self.vector_service.delete_embedding(fact_id)
            
            # Delete database records
            db.query(VectorEmbedding).filter(VectorEmbedding.fact_id == fact.id).delete()
            db.delete(fact)
            db.commit()
            
            logger.info(f"Deleted fact {fact_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting fact: {e}")
            return False
    
    def _decrypt_fact(self, fact: UserFact, user_id: str, user_password_hash: str) -> UserFactResponse:
        """Helper method to decrypt fact data"""
        if fact.is_sensitive:
            decrypted_key = self.encryption_service.decrypt_sensitive_fact(
                fact.fact_key, user_id, user_password_hash
            )
            decrypted_value = self.encryption_service.decrypt_sensitive_fact(
                fact.fact_value, user_id, user_password_hash
            )
        else:
            decrypted_key = self.encryption_service.decrypt_fact(
                fact.fact_key, user_id, user_password_hash
            )
            decrypted_value = self.encryption_service.decrypt_fact(
                fact.fact_value, user_id, user_password_hash
            )
        
        return UserFactResponse(
            id=fact.id,
            user_id=fact.user_id,
            fact_type=fact.fact_type,
            fact_key=decrypted_key,
            fact_value=decrypted_value,
            confidence_score=fact.confidence_score,
            source_conversation_id=fact.source_conversation_id,
            created_at=fact.created_at,
            last_accessed=fact.last_accessed,
            is_sensitive=fact.is_sensitive,
            encryption_key_version=fact.encryption_key_version
        )
    
    def _get_fact_by_id(self, fact_id: str) -> Optional[UserFact]:
        """Helper method to get fact by ID (placeholder for proper session handling)"""
        # This would need proper session management in real implementation
        # For now, returning None to avoid session issues
        return None 