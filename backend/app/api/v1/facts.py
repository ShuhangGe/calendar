import uuid
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...models.database import get_db, User
from ...models.schemas import (
    UserFactCreate, UserFactUpdate, UserFactResponse,
    FactSearchRequest, FactSearchResponse,
    FactExtractionRequest, FactExtractionResponse,
    PaginatedResponse
)
from ...services.fact_service import FactService
from ...services.encryption_service import EncryptionService
from ...services.vector_service import VectorService
from ...services.fact_extraction_agent import FactExtractionAgent
from ...middleware.auth import get_current_user
from ...config import settings

router = APIRouter(prefix="/facts", tags=["facts"])

# Dependency injection for services
def get_fact_service(db: Session = Depends(get_db)) -> FactService:
    """Get FactService instance with dependencies"""
    encryption_service = EncryptionService(settings.fact_encryption_key)
    vector_service = VectorService(
        chroma_persist_directory=settings.chroma_persist_directory,
        openai_api_key=settings.openai_api_key,
        embedding_model=settings.embedding_model,
        similarity_threshold=settings.vector_similarity_threshold
    )
    return FactService(encryption_service, vector_service)

def get_fact_extraction_agent(fact_service: FactService = Depends(get_fact_service)) -> FactExtractionAgent:
    """Get FactExtractionAgent instance"""
    return FactExtractionAgent(fact_service, settings.openai_api_key)

@router.get("/", response_model=PaginatedResponse)
async def get_user_facts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    fact_service: FactService = Depends(get_fact_service),
    fact_types: Optional[List[str]] = Query(None, description="Filter by fact types"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence score")
):
    """
    Get paginated list of user facts with filtering
    """
    try:
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get user password hash for decryption
        user_password_hash = current_user.hashed_password
        
        # Retrieve facts
        facts = fact_service.get_user_facts(
            db=db,
            user_id=str(current_user.id),
            user_password_hash=user_password_hash,
            fact_types=fact_types,
            limit=per_page,
            offset=offset
        )
        
        # Filter by confidence if specified
        if min_confidence > 0.0:
            facts = [fact for fact in facts if fact.confidence_score >= min_confidence]
        
        # Get total count (simplified for now)
        total_count = len(facts)  # In production, would use separate count query
        total_pages = (total_count + per_page - 1) // per_page
        
        return PaginatedResponse(
            items=facts,
            total=total_count,
            page=page,
            per_page=per_page,
            pages=total_pages
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving facts: {str(e)}"
        )

@router.post("/", response_model=UserFactResponse, status_code=status.HTTP_201_CREATED)
async def create_fact(
    fact_data: UserFactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    fact_service: FactService = Depends(get_fact_service)
):
    """
    Create a new user fact
    """
    try:
        user_password_hash = current_user.hashed_password
        
        created_fact = fact_service.create_fact(
            db=db,
            user_id=str(current_user.id),
            user_password_hash=user_password_hash,
            fact_data=fact_data
        )
        
        if not created_fact:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create fact"
            )
        
        return created_fact
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating fact: {str(e)}"
        )

@router.put("/{fact_id}", response_model=UserFactResponse)
async def update_fact(
    fact_id: str,
    update_data: UserFactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    fact_service: FactService = Depends(get_fact_service)
):
    """
    Update an existing user fact
    """
    try:
        # Validate fact_id format
        try:
            uuid.UUID(fact_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid fact ID format"
            )
        
        user_password_hash = current_user.hashed_password
        
        updated_fact = fact_service.update_fact(
            db=db,
            fact_id=fact_id,
            user_id=str(current_user.id),
            user_password_hash=user_password_hash,
            update_data=update_data
        )
        
        if not updated_fact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fact not found"
            )
        
        return updated_fact
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating fact: {str(e)}"
        )

@router.delete("/{fact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fact(
    fact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    fact_service: FactService = Depends(get_fact_service)
):
    """
    Delete a user fact
    """
    try:
        # Validate fact_id format
        try:
            uuid.UUID(fact_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid fact ID format"
            )
        
        success = fact_service.delete_fact(
            db=db,
            fact_id=fact_id,
            user_id=str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fact not found"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting fact: {str(e)}"
        )

@router.post("/search", response_model=FactSearchResponse)
async def search_facts(
    search_request: FactSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    fact_service: FactService = Depends(get_fact_service)
):
    """
    Search facts using semantic similarity
    """
    try:
        start_time = time.time()
        user_password_hash = current_user.hashed_password
        
        # Perform context-based search
        search_results = fact_service.search_facts_by_context(
            user_id=str(current_user.id),
            user_password_hash=user_password_hash,
            context_query=search_request.query,
            fact_types=search_request.fact_types,
            limit=search_request.limit
        )
        
        # Extract facts and relevance scores
        facts = []
        relevance_scores = []
        
        for result in search_results:
            if result['fact'].confidence_score >= search_request.min_confidence:
                facts.append(result['fact'])
                relevance_scores.append(result['similarity_score'])
        
        search_time = time.time() - start_time
        
        return FactSearchResponse(
            facts=facts,
            relevance_scores=relevance_scores,
            search_time=search_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching facts: {str(e)}"
        )

@router.post("/extract", response_model=FactExtractionResponse)
async def extract_facts_from_conversation(
    extraction_request: FactExtractionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    fact_extraction_agent: FactExtractionAgent = Depends(get_fact_extraction_agent)
):
    """
    Manually trigger fact extraction from a conversation
    """
    try:
        start_time = time.time()
        
        # Get conversation
        from ...models.database import Conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == extraction_request.conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        user_password_hash = current_user.hashed_password
        
        # Extract facts
        extracted_facts = await fact_extraction_agent.extract_facts_from_conversation(
            db=db,
            conversation=conversation,
            user_password_hash=user_password_hash,
            force_extraction=extraction_request.force_extraction
        )
        
        processing_time = time.time() - start_time
        
        # Calculate average confidence
        if extracted_facts:
            avg_confidence = sum(fact.confidence_score for fact in extracted_facts) / len(extracted_facts)
        else:
            avg_confidence = 0.0
        
        return FactExtractionResponse(
            extracted_facts=extracted_facts,
            extraction_confidence=avg_confidence,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting facts: {str(e)}"
        )

@router.get("/stats")
async def get_fact_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    fact_service: FactService = Depends(get_fact_service)
):
    """
    Get user fact statistics
    """
    try:
        user_password_hash = current_user.hashed_password
        
        # Get all user facts
        all_facts = fact_service.get_user_facts(
            db=db,
            user_id=str(current_user.id),
            user_password_hash=user_password_hash,
            limit=1000  # Get all facts for stats
        )
        
        # Calculate statistics
        total_facts = len(all_facts)
        
        # Group by fact type
        fact_type_counts = {}
        confidence_scores = []
        sensitive_count = 0
        
        for fact in all_facts:
            fact_type_counts[fact.fact_type] = fact_type_counts.get(fact.fact_type, 0) + 1
            confidence_scores.append(fact.confidence_score)
            if fact.is_sensitive:
                sensitive_count += 1
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return {
            "total_facts": total_facts,
            "fact_types": fact_type_counts,
            "average_confidence": round(avg_confidence, 2),
            "sensitive_facts": sensitive_count,
            "confidence_distribution": {
                "high": len([s for s in confidence_scores if s >= 0.8]),
                "medium": len([s for s in confidence_scores if 0.5 <= s < 0.8]),
                "low": len([s for s in confidence_scores if s < 0.5])
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting fact statistics: {str(e)}"
        ) 