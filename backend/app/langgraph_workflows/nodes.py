import re
import uuid
from datetime import datetime, timedelta
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from ..models.database import DiaryEntry, CalendarEvent, Conversation
from ..services.storage_service import StorageService
from . import AgentState

# Initialize OpenAI client
llm = ChatOpenAI(model="gpt-4", temperature=0.1)

def classify_input_node(state: AgentState) -> AgentState:
    """
    Timezone-aware classification node that determines if input is diary, calendar, or query
    """
    user_input = state["user_input"]
    timezone = state.get("timezone", "UTC")
    
    classification_prompt = f"""
    Analyze the following user input and classify it into one of three categories:
    1. "diary" - Personal reflections, experiences, things that happened, emotions, daily events
    2. "calendar" - Future events, appointments, reminders, scheduling, meetings
    3. "query" - Questions about past events or future plans, requests for information
    
    User timezone: {timezone}
    User input: "{user_input}"
    
    Consider temporal indicators:
    - Past tense or completed actions → diary
    - Future tense or scheduling language → calendar  
    - Question words or information requests → query
    
    Respond with ONLY the classification: diary, calendar, or query
    """
    
    messages = [SystemMessage(content=classification_prompt)]
    response = llm.invoke(messages)
    classification = response.content.strip().lower()
    
    # Confidence scoring based on temporal indicators
    confidence_score = calculate_classification_confidence(user_input, classification)
    
    state["classification"] = classification
    state["confidence_score"] = confidence_score
    state["requires_confirmation"] = confidence_score < 0.7
    
    return state

def calculate_classification_confidence(user_input: str, classification: str) -> float:
    """Calculate confidence score for classification"""
    diary_indicators = ["today", "yesterday", "had", "went", "did", "was", "felt", "experienced"]
    calendar_indicators = ["tomorrow", "next", "schedule", "meeting", "appointment", "remind", "will"]
    query_indicators = ["what", "when", "where", "how", "did i", "do i have", "show me"]
    
    user_lower = user_input.lower()
    
    if classification == "diary":
        score = sum(1 for indicator in diary_indicators if indicator in user_lower) / len(diary_indicators)
    elif classification == "calendar":
        score = sum(1 for indicator in calendar_indicators if indicator in user_lower) / len(calendar_indicators)
    else:  # query
        score = sum(1 for indicator in query_indicators if indicator in user_lower) / len(query_indicators)
    
    return min(score + 0.5, 1.0)  # Base confidence + indicator bonus

def confirmation_node(state: AgentState) -> AgentState:
    """
    Handle uncertain classifications by asking for confirmation
    """
    if not state["requires_confirmation"]:
        return state
    
    classification = state["classification"]
    user_input = state["user_input"]
    
    confirmation_prompt = f"""
    I'm not entirely sure how to classify this input: "{user_input}"
    
    I think it's a {classification} entry. Should I:
    - Save it as a diary entry (personal memory/reflection)
    - Add it to your calendar (future event/reminder) 
    - Answer it as a question about your data
    
    Please let me know if my classification is correct or how you'd like me to handle this.
    """
    
    state["agent_response"] = confirmation_prompt
    return state

def context_enrichment_node(state: AgentState) -> AgentState:
    """
    Add user history context to improve processing
    """
    storage_service = StorageService()
    user_id = uuid.UUID(state["user_id"])
    
    # Get recent context for better understanding
    recent_entries = storage_service.get_recent_diary_entries(user_id, limit=5)
    upcoming_events = storage_service.get_upcoming_events(user_id, limit=5)
    
    context_info = {
        "recent_diary_count": len(recent_entries),
        "upcoming_events_count": len(upcoming_events),
        "user_timezone": state["timezone"]
    }
    
    # Store context for use in processing nodes
    state["context_info"] = str(context_info)
    return state

def extract_datetime_info(text: str, timezone: str = "UTC") -> Optional[datetime]:
    """
    Extract datetime information from text using regex patterns
    """
    now = datetime.now()
    
    # Common patterns
    if "tomorrow" in text.lower():
        return now + timedelta(days=1)
    elif "next week" in text.lower():
        return now + timedelta(days=7)
    elif "today" in text.lower():
        return now
    elif "yesterday" in text.lower():
        return now - timedelta(days=1)
    
    # Time patterns (simple extraction)
    time_patterns = [
        r'(\d{1,2}):(\d{2})\s*(am|pm)',
        r'(\d{1,2})\s*(am|pm)',
        r'at\s+(\d{1,2})'
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, text.lower())
        if match:
            # Basic time extraction - could be enhanced
            try:
                hour = int(match.group(1))
                if len(match.groups()) > 2 and match.group(3) == 'pm' and hour != 12:
                    hour += 12
                return now.replace(hour=hour, minute=0, second=0, microsecond=0)
            except:
                continue
    
    return None

def process_diary_node(state: AgentState) -> AgentState:
    """
    Enhanced diary processing node with user context
    """
    user_input = state["user_input"]
    timezone = state["timezone"]
    
    # Extract date mentioned in the content
    extracted_date = extract_datetime_info(user_input, timezone)
    
    # Process and clean content
    processed_content = user_input.strip()
    
    # Prepare for storage
    state["processed_content"] = processed_content
    state["extracted_datetime"] = extracted_date
    
    return state

def process_calendar_node(state: AgentState) -> AgentState:
    """
    Enhanced calendar processing node with timezone handling
    """
    user_input = state["user_input"]
    timezone = state["timezone"]
    
    # Extract event details using LLM
    extraction_prompt = f"""
    Extract event details from this text: "{user_input}"
    
    Provide the following information:
    - Title: (brief event title)
    - Description: (any additional details)
    - DateTime: (when should this event occur, considering timezone: {timezone})
    - Duration: (estimated duration in minutes, default 60)
    
    Format as: Title|Description|DateTime|Duration
    """
    
    messages = [SystemMessage(content=extraction_prompt)]
    response = llm.invoke(messages)
    
    try:
        parts = response.content.strip().split('|')
        title = parts[0].replace('Title: ', '').strip()
        description = parts[1].replace('Description: ', '').strip() if len(parts) > 1 else ""
        
        # Extract datetime
        extracted_datetime = extract_datetime_info(user_input, timezone) or datetime.now() + timedelta(hours=1)
        
        state["processed_content"] = f"{title}|{description}|{extracted_datetime.isoformat()}|60"
        state["extracted_datetime"] = extracted_datetime
        
    except Exception as e:
        # Fallback processing
        state["processed_content"] = f"{user_input}||{datetime.now().isoformat()}|60"
        state["extracted_datetime"] = datetime.now() + timedelta(hours=1)
    
    return state

def process_query_node(state: AgentState) -> AgentState:
    """
    Query processing node with user-specific data filtering
    """
    storage_service = StorageService()
    user_id = uuid.UUID(state["user_id"])
    user_input = state["user_input"]
    
    # Search through user's data
    diary_entries = storage_service.search_diary_entries(user_id, user_input)
    calendar_events = storage_service.search_calendar_events(user_id, user_input)
    
    # Generate response using found data
    response_prompt = f"""
    User question: "{user_input}"
    
    Found diary entries: {len(diary_entries)} entries
    Found calendar events: {len(calendar_events)} events
    
    Provide a helpful response based on the available data. If no relevant data found, 
    let the user know what information is available or suggest how they might rephrase their question.
    """
    
    messages = [SystemMessage(content=response_prompt)]
    response = llm.invoke(messages)
    
    state["processed_content"] = response.content.strip()
    return state

def store_diary_node(state: AgentState) -> AgentState:
    """
    Store diary entry in database
    """
    storage_service = StorageService()
    user_id = uuid.UUID(state["user_id"])
    
    try:
        diary_entry = DiaryEntry(
            user_id=user_id,
            content=state["processed_content"],
            date_mentioned=state["extracted_datetime"].date() if state["extracted_datetime"] else None
        )
        
        created_entry = storage_service.create_diary_entry(diary_entry)
        state["storage_result"] = f"Diary entry saved with ID: {created_entry.id}"
        
    except Exception as e:
        state["storage_result"] = f"Error saving diary entry: {str(e)}"
    
    return state

def store_calendar_node(state: AgentState) -> AgentState:
    """
    Store calendar event in database
    """
    storage_service = StorageService()
    user_id = uuid.UUID(state["user_id"])
    
    try:
        # Parse processed content
        parts = state["processed_content"].split('|')
        title = parts[0] if parts else state["user_input"]
        description = parts[1] if len(parts) > 1 else ""
        event_datetime = state["extracted_datetime"] or datetime.now() + timedelta(hours=1)
        duration = int(parts[3]) if len(parts) > 3 else 60
        
        calendar_event = CalendarEvent(
            user_id=user_id,
            title=title,
            description=description,
            event_datetime=event_datetime,
            duration_minutes=duration
        )
        
        created_event = storage_service.create_calendar_event(calendar_event)
        state["storage_result"] = f"Calendar event saved: {created_event.title} at {created_event.event_datetime}"
        
    except Exception as e:
        state["storage_result"] = f"Error saving calendar event: {str(e)}"
    
    return state

def notification_scheduling_node(state: AgentState) -> AgentState:
    """
    Schedule push notifications for future calendar events
    (Framework for future push notification implementation)
    """
    if state["classification"] == "calendar" and state["extracted_datetime"]:
        event_time = state["extracted_datetime"]
        notification_time = event_time - timedelta(minutes=15)  # 15 min reminder
        
        # TODO: Implement actual push notification scheduling
        # For now, just log the intent
        state["notification_scheduled"] = f"Notification scheduled for {notification_time}"
    
    return state

def generate_response_node(state: AgentState) -> AgentState:
    """
    Generate final response to user based on classification and storage result
    """
    classification = state["classification"]
    storage_result = state.get("storage_result", "")
    
    if state.get("requires_confirmation", False):
        # Response already set in confirmation_node
        return state
    
    if classification == "diary":
        state["agent_response"] = f"✓ Saved to your diary for {datetime.now().strftime('%B %d, %Y')}"
    elif classification == "calendar":
        if state["extracted_datetime"]:
            date_str = state["extracted_datetime"].strftime('%B %d, %Y at %I:%M %p')
            state["agent_response"] = f"✓ Added to calendar: {date_str}"
        else:
            state["agent_response"] = "✓ Added to your calendar"
    elif classification == "query":
        state["agent_response"] = state["processed_content"]
    else:
        state["agent_response"] = "I processed your message, but I'm not sure how to categorize it."
    
    return state 