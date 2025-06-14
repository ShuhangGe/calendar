import uuid
from datetime import datetime
from typing import Optional, TypedDict, List, Dict, Any

class AgentState(TypedDict):
    """
    Enhanced state schema for the LangGraph agent workflow with long-term memory
    """
    user_id: str
    session_id: str
    user_input: str
    classification: str
    extracted_datetime: Optional[datetime]
    timezone: str
    processed_content: str
    storage_result: str
    agent_response: str
    confidence_score: float
    requires_confirmation: bool
    # Long-term memory fields
    user_facts: List[Dict[str, Any]]
    fact_context: str
    personalization_enabled: bool
