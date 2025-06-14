# Calendar Assistant - AI-Powered Diary & Calendar with Long-Term Memory

A mobile-app-ready diary and calendar assistant built with LangGraph and FastAPI. The AI agent intelligently classifies user input into diary entries, calendar events, or query responses through a simple chat interface. **Now featuring advanced long-term memory capabilities** that learn and remember personal facts about each user for increasingly personalized interactions.

## 🚀 Features

### Core Functionality
- **Intelligent Classification**: AI automatically determines if your message is a diary entry, calendar event, or query
- **Natural Language Processing**: Chat naturally - "Had lunch with Sarah today" or "Meeting tomorrow at 3pm"
- **Dual Functionality**: Combines personal diary and calendar management in one interface
- **Mobile-Ready Architecture**: Built for future mobile app development
- **Real-time Chat Interface**: GPT-style conversation experience
- **User Authentication**: JWT-based authentication system ready for multi-user support
- **Offline-Ready**: Database design supports future offline/online synchronization

### 🧠 Long-Term Memory System (NEW)
- **Automatic Fact Extraction**: AI learns personal details from every conversation (preferences, habits, work info, health data)
- **Semantic Memory Search**: Vector-based similarity search finds contextually relevant personal facts
- **Personalized Responses**: Tailored interactions based on individual user history and preferences
- **Encrypted Personal Data**: All sensitive information encrypted per-user with optional double encryption
- **Intelligent Context**: Responses like *"I noticed you usually prefer morning meetings, this fits your pattern!"*
- **Privacy-First Design**: Facts stored securely with user-specific encryption keys
- **Fact Categories**: Organized into personal, preference, work, and health categories
- **Confidence Scoring**: AI assigns confidence scores to extracted facts for reliability
- **Memory Analytics**: Insights into your personal data patterns and fact distribution

## 🏗️ Architecture

### Backend Stack
- **FastAPI**: Modern, fast web framework
- **LangGraph**: Workflow orchestration for AI agent
- **PostgreSQL**: Production-ready database (SQLite for development)
- **OpenAI GPT-4**: Natural language understanding and fact extraction
- **JWT Authentication**: Secure user management
- **SQLAlchemy**: Database ORM with advanced session management

### Long-Term Memory Stack (NEW)
- **Chroma DB**: Vector database for semantic fact search
- **OpenAI Embeddings**: text-embedding-ada-002 for fact vectorization
- **Cryptography (Fernet)**: User-specific fact encryption with key rotation
- **Sentence Transformers**: Additional embedding capabilities
- **Background Processing**: Celery-ready fact extraction pipeline
- **Connection Pooling**: Optimized database performance for fact operations

### Mobile-Ready Design
- RESTful API with versioning (`/api/v1/`)
- WebSocket support for real-time features
- User-scoped data isolation
- Sync framework for offline/online capabilities
- CORS enabled for mobile app access

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.8+
- PostgreSQL (or SQLite for development)
- OpenAI API key

### 1. Clone and Setup
```bash
git clone <repository-url>
cd calendar_assistant/backend
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the backend directory:

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost/calendar_assistant
# For development, you can use SQLite:
# DATABASE_URL=sqlite:///./calendar_assistant.db

# Security
SECRET_KEY=your-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Services
OPENAI_API_KEY=your-openai-api-key

# Long-Term Memory Configuration (NEW)
FACT_ENCRYPTION_KEY=your-fact-encryption-key-change-this
CHROMA_PERSIST_DIRECTORY=./chroma_db
EMBEDDING_MODEL=text-embedding-ada-002
VECTOR_SIMILARITY_THRESHOLD=0.6
MAX_RELEVANT_FACTS=10

# Environment
ENVIRONMENT=development
```

### 4. Database Setup
```bash
# For development with SQLite (no additional setup needed)
# For PostgreSQL:
createdb calendar_assistant
```

### 5. Run the Application
```bash
# From the backend directory
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Access the Application
- Web Interface: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## 💬 Usage Examples

### Diary Entries
- "Had a great lunch with Sarah today"
- "Feeling excited about the new project"
- "Went for a run this morning, felt amazing"
- "I'm vegetarian and loved the new quinoa salad"

### Calendar Events
- "Meeting with client tomorrow at 3pm"
- "Dentist appointment next Friday 2pm"
- "Team standup every Monday 9am"
- "Yoga class every Wednesday 6pm"

### Queries
- "What did I do last Tuesday?"
- "Do I have any meetings tomorrow?"
- "Show me my diary entries from this week"

### 🧠 Personalized AI Responses (Powered by Long-Term Memory)

**After the AI learns about you:**

*User:* "Schedule a meeting for tomorrow morning"  
*AI:* "✓ Added to calendar: Tomorrow at 9:00 AM. I noticed you prefer morning meetings and usually have your best focus then!"

*User:* "What should I eat for lunch?"  
*AI:* "Based on your vegetarian preferences and your love for quinoa salads, how about trying that new Mediterranean place you mentioned wanting to visit?"

*User:* "I'm feeling stressed about work"  
*AI:* "I remember yoga classes on Wednesdays help you relax. There's one tonight at 6pm on your calendar, and you mentioned they always make you feel better."

**The AI automatically learns and remembers:**
- Your dietary preferences and restrictions
- Your work schedule patterns and meeting preferences  
- Your exercise habits and stress relief activities
- Your family members, friends, and important relationships
- Your allergies, health conditions, and medical information (encrypted)
- Your hobbies, interests, and personal goals

## 📱 Mobile App Development Roadmap

### Phase 1: React Native Foundation
```
mobile_app/
├── src/
│   ├── components/
│   │   ├── ChatInterface/
│   │   ├── DiaryView/
│   │   └── CalendarView/
│   ├── services/
│   │   ├── api.js
│   │   ├── auth.js
│   │   └── storage.js
│   ├── store/
│   │   └── redux/
│   └── screens/
│       ├── ChatScreen.js
│       ├── DiaryScreen.js
│       └── CalendarScreen.js
```

### Phase 2: Enhanced Features
- **Offline-First Architecture**
  - Local SQLite database
  - Background sync
  - Conflict resolution
  - Optimistic updates

- **Push Notifications**
  - Calendar reminders
  - Diary prompts
  - Weekly summaries

- **Voice Integration**
  - Voice-to-text input
  - Hands-free diary entries
  - Audio responses

### Phase 3: Advanced Features
- **Location Services**
  - Automatic location tagging
  - Location-based reminders
  - Travel diary integration

- **Photo Integration**
  - Photo attachments to diary entries
  - Visual calendar events
  - Memory triggers

- **Analytics & Insights**
  - Mood tracking patterns
  - Productivity insights
  - Personal statistics

## 🔧 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh
- `GET /api/v1/auth/me` - Current user info

### Chat Interface
- `POST /api/v1/chat/message` - Process message
- `GET /api/v1/chat/history` - Conversation history
- `DELETE /api/v1/chat/history` - Clear history

### Diary Management
- `GET /api/v1/diary/entries` - Get diary entries
- `PUT /api/v1/diary/entries/{id}` - Update entry
- `DELETE /api/v1/diary/entries/{id}` - Delete entry

### Calendar Management
- `GET /api/v1/calendar/events` - Get calendar events
- `PUT /api/v1/calendar/events/{id}` - Update event
- `DELETE /api/v1/calendar/events/{id}` - Delete event

### Long-Term Memory Management (NEW)
- `GET /api/v1/facts/` - Get user facts with pagination and filtering
- `POST /api/v1/facts/` - Create new user fact
- `PUT /api/v1/facts/{fact_id}` - Update existing fact
- `DELETE /api/v1/facts/{fact_id}` - Delete user fact
- `POST /api/v1/facts/search` - Semantic search through user facts
- `POST /api/v1/facts/extract` - Manual fact extraction from conversation
- `GET /api/v1/facts/stats` - User fact analytics and insights

### Synchronization (Future)
- `POST /api/v1/sync/push` - Push local changes
- `GET /api/v1/sync/pull` - Pull remote changes
- `GET /api/v1/sync/status` - Sync status

## 🧠 Enhanced AI Agent Workflow

The LangGraph workflow processes messages through these stages:

1. **Classification**: Determine if input is diary, calendar, or query
2. **Context Enrichment**: Add user history and retrieve relevant personal facts using vector similarity
3. **Processing**: Extract relevant information and format appropriately with personalized context
4. **Storage**: Save diary entries or calendar events to database
5. **Fact Extraction**: Background AI analysis to extract and store personal facts (preferences, habits, etc.)
6. **Response Generation**: Create personalized, context-aware confirmation messages

### Enhanced Features

#### Confidence Scoring
The agent calculates confidence scores based on temporal indicators:
- High confidence (>0.7): Direct processing
- Low confidence (<0.7): Request user confirmation

#### Fact Extraction Pipeline
- **Automatic Learning**: Every conversation is analyzed for personal facts
- **Category Classification**: Facts organized into personal, preference, work, health categories
- **Confidence Validation**: Only facts with >70% confidence are stored automatically
- **Duplicate Detection**: Smart merging prevents redundant fact storage
- **Background Processing**: Fact extraction runs asynchronously to maintain chat responsiveness

#### Personalization Engine
- **Vector Similarity**: Semantic search finds contextually relevant facts
- **Context Weighting**: Recent facts and high-confidence facts prioritized
- **Response Enhancement**: Base responses enriched with personal touches
- **Privacy Aware**: Sensitive facts double-encrypted and carefully handled

## 🔒 Security Considerations

### Core Security
- JWT tokens with configurable expiration
- Password hashing with bcrypt
- User-scoped data isolation
- Input validation and sanitization
- Rate limiting ready for production
- CORS configuration for mobile apps

### Long-Term Memory Security (NEW)
- **Per-User Encryption**: Each user's facts encrypted with unique keys derived from their password
- **Double Encryption**: Sensitive facts (health, financial) receive additional encryption layer
- **Key Rotation**: Encryption keys can be rotated without data loss
- **No Plain Text Storage**: Personal facts never stored unencrypted in database
- **Salt-Based Key Derivation**: PBKDF2 with 100,000 iterations for key generation
- **Secure Vector Storage**: Embeddings stored separately from encrypted fact data
- **Access Logging**: All fact access attempts logged for security auditing
- **Privacy Controls**: Users can mark facts as sensitive for enhanced protection

## 🚀 Deployment

### Docker Deployment (Recommended)
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables for Production
```env
# Core Configuration
DATABASE_URL=postgresql://user:pass@db-host/calendar_assistant
SECRET_KEY=secure-random-key-256-bits
OPENAI_API_KEY=your-production-openai-key
ENVIRONMENT=production

# Long-Term Memory Configuration
FACT_ENCRYPTION_KEY=secure-fact-encryption-key-256-bits
CHROMA_PERSIST_DIRECTORY=/app/chroma_data
EMBEDDING_MODEL=text-embedding-ada-002
VECTOR_SIMILARITY_THRESHOLD=0.6
MAX_RELEVANT_FACTS=10
```

### Production Deployment Notes
- **Chroma DB**: Ensure persistent volume mounted at `CHROMA_PERSIST_DIRECTORY`
- **Encryption Keys**: Use cryptographically secure random keys (256-bit minimum)
- **Vector Storage**: Chroma database requires approximately 1.5MB per 1000 facts
- **Memory Usage**: Plan for ~500MB additional RAM for vector operations
- **Background Tasks**: Consider Redis + Celery for production fact extraction

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For questions and support:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the example usage above

## 🔮 Future Enhancements

### Phase 1: Intelligence & Integration
- **Multi-language Support**: Internationalization for global users
- **Voice Commands**: "Hey Assistant, what's my schedule today?"
- **Smart Suggestions**: AI-powered event and diary prompts based on learned patterns
- **Integration APIs**: Connect with Google Calendar, Apple Calendar, Notion
- **Advanced Fact Analysis**: Mood pattern recognition, productivity insights
- **Proactive Notifications**: "You usually go to yoga on Wednesdays, reminder set for tonight"

### Phase 2: Collaboration & Export
- **Team Features**: Shared calendars with personal diary privacy
- **Export Options**: PDF reports, CSV exports, data portability
- **Fact Sharing**: Selectively share facts with family members or colleagues
- **Memory Backup**: Encrypted cloud backup of personal fact database
- **Cross-Device Sync**: Seamless fact synchronization across devices

### Phase 3: Advanced Features
- **Biometric Security**: Fingerprint/Face ID for mobile apps
- **Widgets**: Home screen widgets for quick diary entries
- **ML Insights**: Advanced analytics on personal patterns and trends
- **Graph Relationships**: Visualize connections between facts, events, and people
- **Habit Tracking**: Automatic detection and tracking of personal habits
- **Predictive Scheduling**: AI suggests optimal times for events based on your patterns

---

## 🎯 What Makes This Special

This isn't just another calendar app - it's a **learning AI companion** that becomes more helpful over time:

- **Remembers Your Preferences**: "I know you prefer morning meetings"
- **Contextual Awareness**: "Since you're vegetarian, here are lunch suggestions"
- **Pattern Recognition**: "You usually feel better after yoga"
- **Privacy-First**: All personal data encrypted and secure
- **Continuously Learning**: Gets smarter with every interaction

Built with ❤️ using LangGraph, FastAPI, OpenAI GPT-4, ChromaDB, and advanced encryption 