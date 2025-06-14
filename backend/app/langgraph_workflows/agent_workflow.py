from langgraph.graph import StateGraph, END
from .nodes import (
    classify_input_node,
    confirmation_node,
    context_enrichment_node,
    process_diary_node,
    process_calendar_node,
    process_query_node,
    store_diary_node,
    store_calendar_node,
    notification_scheduling_node,
    fact_extraction_trigger_node,
    generate_response_node
)
from . import AgentState

def create_agent_workflow():
    """
    Create the main LangGraph workflow for the calendar assistant agent
    """
    workflow = StateGraph(AgentState)
    
    # Add all nodes to the workflow
    workflow.add_node("classify_input", classify_input_node)
    workflow.add_node("confirmation", confirmation_node)
    workflow.add_node("context_enrichment", context_enrichment_node)
    workflow.add_node("process_diary", process_diary_node)
    workflow.add_node("process_calendar", process_calendar_node)
    workflow.add_node("process_query", process_query_node)
    workflow.add_node("store_diary", store_diary_node)
    workflow.add_node("store_calendar", store_calendar_node)
    workflow.add_node("fact_extraction_trigger", fact_extraction_trigger_node)
    workflow.add_node("notification_scheduling", notification_scheduling_node)
    workflow.add_node("generate_response", generate_response_node)
    
    # Set entry point
    workflow.set_entry_point("classify_input")
    
    # Define routing logic
    def route_after_classification(state: AgentState):
        """Route based on classification and confidence"""
        if state.get("requires_confirmation", False):
            return "confirmation"
        else:
            return "context_enrichment"
    
    def route_after_context(state: AgentState):
        """Route to appropriate processing node based on classification"""
        classification = state["classification"]
        
        if classification == "diary":
            return "process_diary"
        elif classification == "calendar":
            return "process_calendar"
        elif classification == "query":
            return "process_query"
        else:
            return "generate_response"  # Fallback
    
    def route_after_processing(state: AgentState):
        """Route to storage or response generation"""
        classification = state["classification"]
        
        if classification == "diary":
            return "store_diary"
        elif classification == "calendar":
            return "store_calendar"
        else:
            return "generate_response"  # Queries don't need storage
    
    def route_after_storage(state: AgentState):
        """Route to fact extraction after storage"""
        return "fact_extraction_trigger"
    
    def route_after_fact_extraction(state: AgentState):
        """Route to notification or response generation after fact extraction"""
        classification = state["classification"]
        
        if classification == "calendar":
            return "notification_scheduling"
        else:
            return "generate_response"
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "classify_input",
        route_after_classification,
        {
            "confirmation": "confirmation",
            "context_enrichment": "context_enrichment"
        }
    )
    
    # Confirmation leads to end (requires user interaction)
    workflow.add_edge("confirmation", END)
    
    # Context enrichment routes to processing
    workflow.add_conditional_edges(
        "context_enrichment",
        route_after_context,
        {
            "process_diary": "process_diary",
            "process_calendar": "process_calendar",
            "process_query": "process_query",
            "generate_response": "generate_response"
        }
    )
    
    # Processing routes to storage or response
    workflow.add_conditional_edges(
        "process_diary",
        route_after_processing,
        {
            "store_diary": "store_diary",
            "generate_response": "generate_response"
        }
    )
    
    workflow.add_conditional_edges(
        "process_calendar",
        route_after_processing,
        {
            "store_calendar": "store_calendar",
            "generate_response": "generate_response"
        }
    )
    
    workflow.add_edge("process_query", "generate_response")
    
    # Storage routes to fact extraction
    workflow.add_conditional_edges(
        "store_diary",
        route_after_storage,
        {
            "fact_extraction_trigger": "fact_extraction_trigger"
        }
    )
    
    workflow.add_conditional_edges(
        "store_calendar",
        route_after_storage,
        {
            "fact_extraction_trigger": "fact_extraction_trigger"
        }
    )
    
    # Fact extraction routes to notification or response
    workflow.add_conditional_edges(
        "fact_extraction_trigger",
        route_after_fact_extraction,
        {
            "notification_scheduling": "notification_scheduling",
            "generate_response": "generate_response"
        }
    )
    
    # Notification scheduling leads to response
    workflow.add_edge("notification_scheduling", "generate_response")
    
    # Response generation leads to end
    workflow.add_edge("generate_response", END)
    
    return workflow.compile()

# Create the compiled workflow instance
agent_workflow = create_agent_workflow() 