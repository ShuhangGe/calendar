import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from ..langgraph_workflows.agent_workflow import agent_workflow
from ..langgraph_workflows import AgentState
from ..models.database import Conversation
from .storage_service import StorageService

class AgentService:
    """
    Service class for orchestrating the LangGraph agent workflow with user authentication
    """
    
    def __init__(self):
        self.storage_service = StorageService()
        self.workflow = agent_workflow
    
    async def process_message(
        self, 
        user_id: uuid.UUID, 
        message: str, 
        session_id: Optional[uuid.UUID] = None,
        timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """
        Process a user message through the LangGraph workflow
        
        Args:
            user_id: The user's unique identifier
            message: The user's input message
            session_id: Optional session identifier for conversation grouping
            timezone: User's timezone for datetime processing
            
        Returns:
            Dictionary containing agent response and metadata
        """
        
        # Generate session ID if not provided
        if not session_id:
            session_id = uuid.uuid4()
        
        # Initialize agent state
        initial_state: AgentState = {
            "user_id": str(user_id),
            "session_id": str(session_id),
            "user_input": message,
            "classification": "",
            "extracted_datetime": None,
            "timezone": timezone,
            "processed_content": "",
            "storage_result": "",
            "agent_response": "",
            "confidence_score": 0.0,
            "requires_confirmation": False
        }
        
        try:
            # Run the workflow
            result = await self.workflow.ainvoke(initial_state)
            
            # Store conversation record
            await self._store_conversation(
                user_id=user_id,
                session_id=session_id,
                user_input=message,
                agent_response=result["agent_response"],
                classification=result["classification"]
            )
            
            return {
                "response": result["agent_response"],
                "classification": result["classification"],
                "session_id": session_id,
                "timestamp": datetime.now(),
                "confidence_score": result.get("confidence_score", 0.0),
                "requires_confirmation": result.get("requires_confirmation", False),
                "extracted_datetime": result.get("extracted_datetime"),
                "storage_result": result.get("storage_result", "")
            }
            
        except Exception as e:
            # Handle errors gracefully
            error_response = f"I'm sorry, I encountered an error processing your message: {str(e)}"
            
            # Still store the conversation for debugging
            await self._store_conversation(
                user_id=user_id,
                session_id=session_id,
                user_input=message,
                agent_response=error_response,
                classification="error"
            )
            
            return {
                "response": error_response,
                "classification": "error",
                "session_id": session_id,
                "timestamp": datetime.now(),
                "confidence_score": 0.0,
                "requires_confirmation": False,
                "error": str(e)
            }
    
    async def _store_conversation(
        self,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        user_input: str,
        agent_response: str,
        classification: str
    ):
        """
        Store conversation record in database
        """
        try:
            conversation = Conversation(
                user_id=user_id,
                user_input=user_input,
                agent_response=agent_response,
                classification=classification,
                session_id=session_id
            )
            
            self.storage_service.create_conversation(conversation)
            
        except Exception as e:
            # Log error but don't fail the main operation
            print(f"Failed to store conversation: {e}")
    
    def get_conversation_history(
        self, 
        user_id: uuid.UUID, 
        session_id: Optional[uuid.UUID] = None,
        limit: int = 50
    ) -> list:
        """
        Get conversation history for a user
        
        Args:
            user_id: The user's unique identifier
            session_id: Optional session identifier to filter by
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversation records
        """
        try:
            conversations = self.storage_service.get_conversation_history(
                user_id=user_id,
                session_id=session_id,
                limit=limit
            )
            
            return [
                {
                    "id": str(conv.id),
                    "user_input": conv.user_input,
                    "agent_response": conv.agent_response,
                    "classification": conv.classification,
                    "created_at": conv.created_at,
                    "session_id": str(conv.session_id)
                }
                for conv in conversations
            ]
            
        except Exception as e:
            print(f"Failed to get conversation history: {e}")
            return []
    
    def clear_conversation_history(
        self, 
        user_id: uuid.UUID, 
        session_id: Optional[uuid.UUID] = None
    ) -> bool:
        """
        Clear conversation history for a user
        
        Args:
            user_id: The user's unique identifier
            session_id: Optional session identifier to filter by
            
        Returns:
            Boolean indicating success
        """
        try:
            return self.storage_service.clear_conversation_history(
                user_id=user_id,
                session_id=session_id
            )
        except Exception as e:
            print(f"Failed to clear conversation history: {e}")
            return False
    
    def get_user_stats(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get user statistics for dashboard/insights
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            Dictionary containing user statistics
        """
        try:
            diary_entries = self.storage_service.get_diary_entries(user_id, limit=1000)
            upcoming_events = self.storage_service.get_upcoming_events(user_id, limit=100)
            conversations = self.storage_service.get_conversation_history(user_id, limit=1000)
            
            return {
                "total_diary_entries": len(diary_entries),
                "total_upcoming_events": len(upcoming_events),
                "total_conversations": len(conversations),
                "most_recent_diary": diary_entries[0].created_at if diary_entries else None,
                "next_event": upcoming_events[0].event_datetime if upcoming_events else None,
                "last_conversation": conversations[0].created_at if conversations else None
            }
            
        except Exception as e:
            print(f"Failed to get user stats: {e}")
            return {}
    
    def classify_message_preview(self, message: str, timezone: str = "UTC") -> Dict[str, Any]:
        """
        Preview message classification without storing (for UI feedback)
        
        Args:
            message: The user's input message
            timezone: User's timezone
            
        Returns:
            Dictionary containing classification preview
        """
        try:
            # Simple classification preview without full workflow
            message_lower = message.lower()
            
            diary_indicators = ["today", "yesterday", "had", "went", "did", "was", "felt", "experienced"]
            calendar_indicators = ["tomorrow", "next", "schedule", "meeting", "appointment", "remind", "will"]
            query_indicators = ["what", "when", "where", "how", "did i", "do i have", "show me"]
            
            diary_score = sum(1 for indicator in diary_indicators if indicator in message_lower)
            calendar_score = sum(1 for indicator in calendar_indicators if indicator in message_lower)
            query_score = sum(1 for indicator in query_indicators if indicator in message_lower)
            
            if diary_score >= calendar_score and diary_score >= query_score:
                classification = "diary"
                confidence = min(diary_score / len(diary_indicators) + 0.5, 1.0)
            elif calendar_score >= query_score:
                classification = "calendar"
                confidence = min(calendar_score / len(calendar_indicators) + 0.5, 1.0)
            else:
                classification = "query"
                confidence = min(query_score / len(query_indicators) + 0.5, 1.0)
            
            return {
                "classification": classification,
                "confidence": confidence,
                "requires_confirmation": confidence < 0.7
            }
            
        except Exception as e:
            return {
                "classification": "unknown",
                "confidence": 0.0,
                "requires_confirmation": True,
                "error": str(e)
            } 