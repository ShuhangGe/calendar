import os
import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from .config import settings
from .services.storage_service import StorageService
from .services.auth_service import AuthService
from .services.agent_service import AgentService

# Initialize services
storage_service = StorageService()
auth_service = AuthService()
agent_service = AgentService()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="AI-powered diary and calendar assistant"
)

# Configure CORS for mobile app access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        storage_service.init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for deployment monitoring"""
    return {
        "status": "healthy",
        "version": settings.version,
        "environment": settings.environment
    }

# Root endpoint - serve web frontend
@app.get("/")
async def root():
    """Serve the web frontend HTML"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Calendar Assistant</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .chat-container {
                height: 400px;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
                overflow-y: auto;
                margin-bottom: 20px;
                background-color: #fafafa;
            }
            .message {
                margin-bottom: 15px;
                padding: 10px;
                border-radius: 8px;
            }
            .user-message {
                background-color: #007bff;
                color: white;
                margin-left: 20%;
                text-align: right;
            }
            .agent-message {
                background-color: #e9ecef;
                color: #333;
                margin-right: 20%;
            }
            .input-container {
                display: flex;
                gap: 10px;
            }
            input[type="text"] {
                flex: 1;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 16px;
            }
            button {
                padding: 10px 20px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover {
                background-color: #0056b3;
            }
            .status {
                text-align: center;
                margin-bottom: 20px;
                padding: 10px;
                border-radius: 5px;
                background-color: #d4edda;
                color: #155724;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Calendar Assistant</h1>
            <div class="status">
                <p>AI-powered diary and calendar assistant - MVP Version</p>
                <p>Type messages like: "Had lunch with Sarah today" or "Meeting tomorrow at 3pm" or "What did I do yesterday?"</p>
            </div>
            
            <div class="chat-container" id="chatContainer">
                <div class="message agent-message">
                    Hello! I'm your calendar assistant. I can help you record diary entries,
                    schedule calendar events, and answer questions about your data.
                    
                    Try saying something like:
                    • "Had a great meeting with the team today"
                    • "Dentist appointment tomorrow at 2pm"
                    • "What meetings do I have this week?"
                </div>
            </div>
            
            <div class="input-container">
                <input type="text" id="messageInput" placeholder="Type your message here..." />
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>

        <script>
            // For MVP - using direct API calls without authentication
            // In production, implement proper authentication
            
            function addMessage(content, isUser = false) {
                const chatContainer = document.getElementById('chatContainer');
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message ' + (isUser ? 'user-message' : 'agent-message');
                messageDiv.textContent = content;
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
            
            async function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                
                if (!message) return;
                
                // Add user message to chat
                addMessage(message, true);
                input.value = '';
                
                try {
                    // For MVP, we'll use a simplified API call
                    addMessage('Processing your message...', false);
                    
                    // Simulate processing (in real implementation, call the API)
                    setTimeout(() => {
                        const lastMessage = document.querySelector('.chat-container .message:last-child');
                        if (message.toLowerCase().includes('today') || message.toLowerCase().includes('yesterday')) {
                            lastMessage.textContent = '✓ Saved to your diary for ' + new Date().toLocaleDateString();
                        } else if (message.toLowerCase().includes('tomorrow') || message.toLowerCase().includes('meeting')) {
                            lastMessage.textContent = '✓ Added to your calendar';
                        } else if (message.toLowerCase().includes('what') || message.toLowerCase().includes('show')) {
                            lastMessage.textContent = 'I can help you search your diary and calendar data. This is the MVP version - full search functionality coming soon!';
                        } else {
                            lastMessage.textContent = 'I processed your message. This is the MVP version - full AI processing coming soon!';
                        }
                    }, 1000);
                    
                } catch (error) {
                    addMessage('Sorry, there was an error processing your message.', false);
                }
            }
            
            // Allow Enter key to send message
            document.getElementById('messageInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Import API routes (these will be created next)
# from .api.v1 import auth, chat, diary, calendar, sync
# from .api import websocket

# Include API routers
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
# app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
# app.include_router(diary.router, prefix="/api/v1/diary", tags=["diary"])
# app.include_router(calendar.router, prefix="/api/v1/calendar", tags=["calendar"])
# app.include_router(sync.router, prefix="/api/v1/sync", tags=["sync"])
# app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

# For development
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.environment == "development" else False
    ) 