# Calendar Assistant - AI-Powered Diary & Calendar

A mobile-app-ready diary and calendar assistant built with LangGraph and FastAPI. The AI agent intelligently classifies user input into diary entries, calendar events, or query responses through a simple chat interface.

## 🚀 Features

- **Intelligent Classification**: AI automatically determines if your message is a diary entry, calendar event, or query
- **Natural Language Processing**: Chat naturally - "Had lunch with Sarah today" or "Meeting tomorrow at 3pm"
- **Dual Functionality**: Combines personal diary and calendar management in one interface
- **Mobile-Ready Architecture**: Built for future mobile app development
- **Real-time Chat Interface**: GPT-style conversation experience
- **User Authentication**: JWT-based authentication system ready for multi-user support
- **Offline-Ready**: Database design supports future offline/online synchronization

## 🏗️ Architecture

### Backend Stack
- **FastAPI**: Modern, fast web framework
- **LangGraph**: Workflow orchestration for AI agent
- **PostgreSQL**: Production-ready database (SQLite for development)
- **OpenAI GPT-4**: Natural language understanding
- **JWT Authentication**: Secure user management
- **SQLAlchemy**: Database ORM

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

### Calendar Events
- "Meeting with client tomorrow at 3pm"
- "Dentist appointment next Friday 2pm"
- "Team standup every Monday 9am"

### Queries
- "What did I do last Tuesday?"
- "Do I have any meetings tomorrow?"
- "Show me my diary entries from this week"

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

### Synchronization (Future)
- `POST /api/v1/sync/push` - Push local changes
- `GET /api/v1/sync/pull` - Pull remote changes
- `GET /api/v1/sync/status` - Sync status

## 🧠 AI Agent Workflow

The LangGraph workflow processes messages through these stages:

1. **Classification**: Determine if input is diary, calendar, or query
2. **Context Enrichment**: Add user history for better understanding
3. **Processing**: Extract relevant information and format appropriately
4. **Storage**: Save diary entries or calendar events to database
5. **Response Generation**: Create user-friendly confirmation messages

### Confidence Scoring
The agent calculates confidence scores based on temporal indicators:
- High confidence (>0.7): Direct processing
- Low confidence (<0.7): Request user confirmation

## 🔒 Security Considerations

- JWT tokens with configurable expiration
- Password hashing with bcrypt
- User-scoped data isolation
- Input validation and sanitization
- Rate limiting ready for production
- CORS configuration for mobile apps

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
DATABASE_URL=postgresql://user:pass@db-host/calendar_assistant
SECRET_KEY=secure-random-key-256-bits
OPENAI_API_KEY=your-production-openai-key
ENVIRONMENT=production
```

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

- **Multi-language Support**: Internationalization for global users
- **Voice Commands**: "Hey Assistant, what's my schedule today?"
- **Smart Suggestions**: AI-powered event and diary prompts
- **Integration APIs**: Connect with Google Calendar, Apple Calendar
- **Team Features**: Shared calendars with personal diary privacy
- **Export Options**: PDF reports, CSV exports, data portability
- **Biometric Security**: Fingerprint/Face ID for mobile apps
- **Widgets**: Home screen widgets for quick diary entries

---

Built with ❤️ using LangGraph, FastAPI, and OpenAI GPT-4 