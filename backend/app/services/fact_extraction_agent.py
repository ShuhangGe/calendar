import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import openai
from sqlalchemy.orm import Session

from ..models.database import Conversation, UserFact
from ..models.schemas import UserFactCreate, UserFactResponse
from .fact_service import FactService

logger = logging.getLogger(__name__)

class FactExtractionAgent:
    def __init__(self, fact_service: FactService, openai_api_key: str):
        """Initialize fact extraction agent with fact service and OpenAI"""
        self.fact_service = fact_service
        openai.api_key = openai_api_key
        
        # Fact extraction prompt templates
        self.extraction_prompts = {
            "personal": """
            Analyze this conversation and extract personal facts about the user. Look for:
            - Name, age, birthday, family members
            - Hobbies, interests, skills
            - Personal preferences, habits
            - Location, living situation
            
            Return facts as JSON array with format:
            [{"fact_key": "name", "fact_value": "John", "confidence": 0.9, "is_sensitive": false}]
            """,
            
            "preference": """
            Analyze this conversation and extract user preferences. Look for:
            - Food preferences, dietary restrictions
            - Activity preferences, dislikes
            - Communication style preferences
            - Time preferences, scheduling habits
            
            Return facts as JSON array with format:
            [{"fact_key": "dietary_preference", "fact_value": "vegetarian", "confidence": 0.8, "is_sensitive": false}]
            """,
            
            "work": """
            Analyze this conversation and extract work-related facts. Look for:
            - Job title, company, industry
            - Work schedule, meeting patterns
            - Professional skills, certifications
            - Career goals, projects
            
            Return facts as JSON array with format:
            [{"fact_key": "job_title", "fact_value": "Software Engineer", "confidence": 0.9, "is_sensitive": false}]
            """,
            
            "health": """
            Analyze this conversation and extract health-related facts. Look for:
            - Medical conditions, allergies
            - Medications, treatments
            - Exercise habits, fitness goals
            - Mental health preferences
            
            Mark health facts as sensitive. Return facts as JSON array with format:
            [{"fact_key": "allergy", "fact_value": "peanuts", "confidence": 0.9, "is_sensitive": true}]
            """
        }
    
    async def extract_facts_from_conversation(self, 
                                            db: Session,
                                            conversation: Conversation,
                                            user_password_hash: str,
                                            force_extraction: bool = False) -> List[UserFactResponse]:
        """Extract facts from a conversation using GPT-4"""
        try:
            extracted_facts = []
            conversation_text = f"User: {conversation.user_input}\nAssistant: {conversation.agent_response}"
            
            # Extract facts by category
            for fact_type, prompt_template in self.extraction_prompts.items():
                try:
                    facts = await self._extract_facts_by_type(
                        conversation_text, fact_type, prompt_template
                    )
                    
                    for fact_data in facts:
                        # Validate confidence threshold
                        if fact_data['confidence'] >= 0.7 or force_extraction:
                            # Check for duplicates
                            if not self._is_duplicate_fact(db, str(conversation.user_id), fact_data):
                                # Create fact
                                fact_create = UserFactCreate(
                                    fact_type=fact_type,
                                    fact_key=fact_data['fact_key'],
                                    fact_value=fact_data['fact_value'],
                                    confidence_score=fact_data['confidence'],
                                    is_sensitive=fact_data.get('is_sensitive', False),
                                    source_conversation_id=conversation.id
                                )
                                
                                created_fact = self.fact_service.create_fact(
                                    db=db,
                                    user_id=str(conversation.user_id),
                                    user_password_hash=user_password_hash,
                                    fact_data=fact_create
                                )
                                
                                if created_fact:
                                    extracted_facts.append(created_fact)
                                    logger.info(f"Extracted {fact_type} fact: {fact_data['fact_key']}")
                
                except Exception as e:
                    logger.error(f"Error extracting {fact_type} facts: {e}")
                    continue
            
            logger.info(f"Extracted {len(extracted_facts)} facts from conversation {conversation.id}")
            return extracted_facts
            
        except Exception as e:
            logger.error(f"Error in fact extraction: {e}")
            return []
    
    async def _extract_facts_by_type(self, conversation_text: str, fact_type: str, prompt_template: str) -> List[Dict]:
        """Extract facts of specific type using GPT-4"""
        try:
            full_prompt = f"{prompt_template}\n\nConversation:\n{conversation_text}\n\nExtracted facts (JSON only):"
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a fact extraction expert. Extract only clear, factual information. Return valid JSON only."},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                facts = json.loads(response_text)
                if isinstance(facts, list):
                    # Validate each fact
                    validated_facts = []
                    for fact in facts:
                        if self._validate_fact_structure(fact):
                            validated_facts.append(fact)
                    return validated_facts
                else:
                    logger.warning(f"Invalid JSON structure for {fact_type}: expected list")
                    return []
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing error for {fact_type}: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Error in GPT-4 fact extraction for {fact_type}: {e}")
            return []
    
    def validate_fact_confidence(self, fact_data: Dict) -> float:
        """Validate and adjust fact confidence based on context"""
        base_confidence = fact_data.get('confidence', 0.0)
        
        # Confidence adjustments based on fact characteristics
        fact_key = fact_data.get('fact_key', '').lower()
        fact_value = fact_data.get('fact_value', '').lower()
        
        # Boost confidence for specific patterns
        if any(keyword in fact_key for keyword in ['name', 'age', 'job', 'company']):
            base_confidence = min(1.0, base_confidence + 0.1)
        
        # Reduce confidence for vague or uncertain language
        uncertain_words = ['maybe', 'perhaps', 'might', 'possibly', 'sometimes']
        if any(word in fact_value for word in uncertain_words):
            base_confidence = max(0.0, base_confidence - 0.2)
        
        # Boost confidence for specific values
        if any(pattern in fact_value for pattern in ['years old', '@', '.com', 'monday', 'tuesday']):
            base_confidence = min(1.0, base_confidence + 0.1)
        
        return round(base_confidence, 2)
    
    def merge_duplicate_facts(self, db: Session, user_id: str, new_fact: Dict) -> bool:
        """Check and merge duplicate facts to prevent redundancy"""
        try:
            # Look for existing facts with same key
            existing_facts = db.query(UserFact).filter(
                UserFact.user_id == user_id,
                UserFact.fact_type == new_fact.get('fact_type', '')
            ).all()
            
            for existing_fact in existing_facts:
                # Decrypt existing fact for comparison
                try:
                    decrypted_existing = self.fact_service._decrypt_fact(
                        existing_fact, user_id, "placeholder_password_hash"  # This needs proper session handling
                    )
                    
                    # Check for similar fact keys (fuzzy matching)
                    if self._are_facts_similar(decrypted_existing.fact_key, new_fact['fact_key']):
                        # Update with higher confidence value
                        if new_fact['confidence'] > decrypted_existing.confidence_score:
                            logger.info(f"Updating fact with higher confidence: {new_fact['fact_key']}")
                            return True  # Indicates should update existing fact
                        else:
                            logger.info(f"Skipping duplicate fact: {new_fact['fact_key']}")
                            return False  # Skip this fact
                            
                except Exception as e:
                    logger.error(f"Error comparing facts: {e}")
                    continue
            
            return True  # No duplicates found, proceed with creation
            
        except Exception as e:
            logger.error(f"Error in duplicate fact checking: {e}")
            return True  # Default to allowing fact creation
    
    async def batch_process_conversations(self, 
                                        db: Session,
                                        user_id: str,
                                        user_password_hash: str,
                                        conversation_ids: List[str],
                                        max_parallel: int = 3) -> List[UserFactResponse]:
        """Process multiple conversations for fact extraction"""
        try:
            all_extracted_facts = []
            
            # Process conversations in batches to avoid rate limits
            for i in range(0, len(conversation_ids), max_parallel):
                batch_ids = conversation_ids[i:i + max_parallel]
                batch_tasks = []
                
                for conv_id in batch_ids:
                    conversation = db.query(Conversation).filter(
                        Conversation.id == conv_id,
                        Conversation.user_id == user_id
                    ).first()
                    
                    if conversation:
                        task = self.extract_facts_from_conversation(
                            db, conversation, user_password_hash
                        )
                        batch_tasks.append(task)
                
                # Execute batch
                if batch_tasks:
                    import asyncio
                    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                    
                    for result in batch_results:
                        if isinstance(result, list):
                            all_extracted_facts.extend(result)
                        elif isinstance(result, Exception):
                            logger.error(f"Batch processing error: {result}")
            
            logger.info(f"Batch processed {len(conversation_ids)} conversations, extracted {len(all_extracted_facts)} facts")
            return all_extracted_facts
            
        except Exception as e:
            logger.error(f"Error in batch fact processing: {e}")
            return []
    
    def _validate_fact_structure(self, fact: Dict) -> bool:
        """Validate that fact has required structure"""
        required_fields = ['fact_key', 'fact_value', 'confidence']
        return all(field in fact for field in required_fields)
    
    def _is_duplicate_fact(self, db: Session, user_id: str, new_fact: Dict) -> bool:
        """Check if fact already exists for user"""
        try:
            # Simple duplicate check based on fact_key similarity
            # In production, this would use proper decryption and fuzzy matching
            return False  # Simplified for now
        except Exception as e:
            logger.error(f"Error checking duplicates: {e}")
            return False
    
    def _are_facts_similar(self, fact1: str, fact2: str, threshold: float = 0.8) -> bool:
        """Check if two fact keys are semantically similar"""
        # Simple similarity check - in production would use more sophisticated matching
        fact1_lower = fact1.lower().strip()
        fact2_lower = fact2.lower().strip()
        
        # Exact match
        if fact1_lower == fact2_lower:
            return True
        
        # Substring match
        if fact1_lower in fact2_lower or fact2_lower in fact1_lower:
            return True
        
        # Could add Levenshtein distance or semantic similarity here
        return False

# Celery task wrapper for background processing
def create_celery_fact_extraction_task(app):
    """Create Celery task for background fact extraction"""
    try:
        from celery import Celery
        
        @app.task(bind=True, max_retries=3)
        def extract_facts_background(self, conversation_id: str, user_id: str, user_password_hash: str):
            """Background task for fact extraction"""
            try:
                # This would need proper dependency injection in real implementation
                logger.info(f"Starting background fact extraction for conversation {conversation_id}")
                
                # Placeholder for actual implementation
                # Would need to:
                # 1. Get database session
                # 2. Initialize services
                # 3. Run extraction
                # 4. Handle errors and retries
                
                return {"status": "completed", "conversation_id": conversation_id}
                
            except Exception as e:
                logger.error(f"Background fact extraction failed: {e}")
                # Retry logic
                if self.request.retries < self.max_retries:
                    raise self.retry(countdown=60, exc=e)
                else:
                    return {"status": "failed", "error": str(e)}
        
        return extract_facts_background
    
    except ImportError:
        logger.warning("Celery not available, background processing disabled")
        return None 