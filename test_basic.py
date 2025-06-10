#!/usr/bin/env python3
"""
Basic test script to verify Calendar Assistant setup and functionality
"""

import sys
import os
sys.path.append('backend')

try:
    from backend.app.config import settings
    from backend.app.services.storage_service import StorageService
    from backend.app.models.database import User, DiaryEntry, CalendarEvent
    
    print("✅ All imports successful!")
    
    # Test 1: Configuration
    print(f"\n📋 Configuration Test:")
    print(f"  Database URL: {settings.database_url}")
    print(f"  Environment: {settings.environment}")
    print(f"  App Name: {settings.app_name}")
    
    # Test 2: Database initialization
    print(f"\n🗄️  Database Test:")
    storage_service = StorageService()
    
    try:
        storage_service.init_db()
        print("  ✅ Database initialized successfully")
    except Exception as e:
        print(f"  ❌ Database initialization failed: {e}")
        sys.exit(1)
    
    # Test 3: Basic database operations
    print(f"\n👤 User Operations Test:")
    
    # Create a test user
    test_user_data = {
        "email": "test@example.com",
        "hashed_password": "hashed_password_123",
        "timezone": "UTC"
    }
    
    try:
        # Check if user already exists
        existing_user = storage_service.get_user_by_email("test@example.com")
        if existing_user:
            print("  ℹ️  Test user already exists, using existing user")
            test_user = existing_user
        else:
            test_user = storage_service.create_user(test_user_data)
            print("  ✅ Test user created successfully")
        
        print(f"    User ID: {test_user.id}")
        print(f"    Email: {test_user.email}")
        
    except Exception as e:
        print(f"  ❌ User creation failed: {e}")
        sys.exit(1)
    
    # Test 4: Diary entry operations
    print(f"\n📔 Diary Operations Test:")
    
    try:
        diary_entry = DiaryEntry(
            user_id=test_user.id,
            content="Test diary entry for setup verification",
        )
        
        created_entry = storage_service.create_diary_entry(diary_entry)
        print("  ✅ Diary entry created successfully")
        print(f"    Entry ID: {created_entry.id}")
        print(f"    Content: {created_entry.content}")
        
        # Retrieve entries
        entries = storage_service.get_diary_entries(test_user.id, limit=5)
        print(f"  ✅ Retrieved {len(entries)} diary entries")
        
    except Exception as e:
        print(f"  ❌ Diary operations failed: {e}")
    
    # Test 5: Calendar event operations
    print(f"\n📅 Calendar Operations Test:")
    
    try:
        from datetime import datetime, timedelta
        
        calendar_event = CalendarEvent(
            user_id=test_user.id,
            title="Test Meeting",
            description="Setup verification meeting",
            event_datetime=datetime.now() + timedelta(days=1),
            duration_minutes=60
        )
        
        created_event = storage_service.create_calendar_event(calendar_event)
        print("  ✅ Calendar event created successfully")
        print(f"    Event ID: {created_event.id}")
        print(f"    Title: {created_event.title}")
        print(f"    Date: {created_event.event_datetime}")
        
        # Retrieve events
        events = storage_service.get_upcoming_events(test_user.id, limit=5)
        print(f"  ✅ Retrieved {len(events)} upcoming events")
        
    except Exception as e:
        print(f"  ❌ Calendar operations failed: {e}")
    
    # Test 6: LangGraph workflow import
    print(f"\n🤖 AI Workflow Test:")
    
    try:
        from backend.app.langgraph_workflows.agent_workflow import agent_workflow
        from backend.app.services.agent_service import AgentService
        
        print("  ✅ LangGraph workflow imported successfully")
        
        agent_service = AgentService()
        print("  ✅ Agent service initialized successfully")
        
        # Test classification preview (doesn't require OpenAI)
        preview = agent_service.classify_message_preview("Had lunch today")
        print(f"  ✅ Classification preview works: {preview['classification']}")
        
    except Exception as e:
        print(f"  ⚠️  AI workflow test failed (this is expected without OpenAI key): {e}")
    
    print(f"\n🎉 Basic setup verification completed!")
    print(f"\n🚀 Ready to run the application:")
    print(f"   cd calendar_assistant/backend")
    print(f"   python -m app.main")
    print(f"\n   Then visit: http://localhost:8000")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the calendar_assistant directory and have installed requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1) 