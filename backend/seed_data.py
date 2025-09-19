#!/usr/bin/env python3
"""
Sample data seeding script for EduMentor platform
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).parent))

from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from dotenv import load_dotenv
import uuid
from datetime import datetime, timezone, timedelta

# Load environment variables
load_dotenv()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

async def clear_existing_data():
    """Clear existing data for fresh start"""
    print("🧹 Clearing existing data...")
    await db.users.delete_many({})
    await db.courses.delete_many({})
    await db.mentorship_sessions.delete_many({})
    await db.chat_messages.delete_many({})
    await db.progress.delete_many({})
    print("✅ Data cleared successfully")

async def seed_users():
    """Create sample users with different roles"""
    print("👥 Creating sample users...")
    
    users_data = [
        # Students
        {
            "id": str(uuid.uuid4()),
            "email": "alice.student@example.com",
            "full_name": "Alice Johnson",
            "role": "student",
            "skills": ["JavaScript", "HTML", "CSS"],
            "interests": ["Web Development", "UI/UX Design", "Mobile Apps"],
            "bio": "Passionate frontend developer looking to expand my skills in modern web technologies",
            "profile_image": "https://images.unsplash.com/photo-1494790108755-2616b812c2d3?w=150&h=150&fit=crop&crop=face",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "hashed_password": get_password_hash("password123")
        },
        {
            "id": str(uuid.uuid4()),
            "email": "bob.learner@example.com", 
            "full_name": "Bob Chen",
            "role": "student",
            "skills": ["Python", "SQL"],
            "interests": ["Data Science", "Machine Learning", "Analytics"],
            "bio": "Data enthusiast transitioning from business analysis to data science",
            "profile_image": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "hashed_password": get_password_hash("password123")
        },
        {
            "id": str(uuid.uuid4()),
            "email": "carol.student@example.com",
            "full_name": "Carol Martinez",
            "role": "student", 
            "skills": ["Java", "Spring Boot"],
            "interests": ["Backend Development", "Microservices", "Cloud Computing"],
            "bio": "Backend developer interested in scalable system architecture",
            "profile_image": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "hashed_password": get_password_hash("password123")
        },
        
        # Mentors
        {
            "id": str(uuid.uuid4()),
            "email": "david.mentor@example.com",
            "full_name": "Dr. David Rodriguez",
            "role": "mentor",
            "skills": ["React", "Node.js", "TypeScript", "GraphQL", "AWS"],
            "interests": ["Full-Stack Development", "System Architecture", "Teaching"],
            "bio": "Senior Software Engineer with 8+ years at Google. Passionate about mentoring next-gen developers.",
            "profile_image": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "hashed_password": get_password_hash("password123")
        },
        {
            "id": str(uuid.uuid4()),
            "email": "emma.expert@example.com",
            "full_name": "Emma Thompson",
            "role": "mentor",
            "skills": ["Python", "Machine Learning", "TensorFlow", "Data Analysis", "Statistics"],
            "interests": ["AI/ML", "Data Science", "Research", "Mentoring"],
            "bio": "ML Research Scientist at Meta. PhD in Computer Science, specialized in deep learning applications.",
            "profile_image": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&h=150&fit=crop&crop=face",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "hashed_password": get_password_hash("password123")
        },
        {
            "id": str(uuid.uuid4()),
            "email": "frank.fullstack@example.com",
            "full_name": "Frank Wilson",
            "role": "mentor",
            "skills": ["Vue.js", "Django", "PostgreSQL", "Docker", "Kubernetes"],
            "interests": ["Full-Stack Development", "DevOps", "Startups"],
            "bio": "CTO at a fintech startup. Expert in building scalable web applications from scratch.",
            "profile_image": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&h=150&fit=crop&crop=face",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "hashed_password": get_password_hash("password123")
        },
        
        # Admin
        {
            "id": str(uuid.uuid4()),
            "email": "admin@edumentor.com",
            "full_name": "Sarah Admin",
            "role": "admin",
            "skills": ["Platform Management", "User Experience", "Analytics"],
            "interests": ["Education Technology", "User Experience", "Platform Growth"],
            "bio": "Platform administrator ensuring the best learning experience for all users.",
            "profile_image": "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=150&h=150&fit=crop&crop=face",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "hashed_password": get_password_hash("admin123")
        }
    ]
    
    result = await db.users.insert_many(users_data)
    print(f"✅ Created {len(result.inserted_ids)} users")
    return users_data

async def seed_courses(users_data):
    """Create sample courses"""
    print("📚 Creating sample courses...")
    
    mentors = [user for user in users_data if user['role'] == 'mentor']
    
    courses_data = [
        {
            "id": str(uuid.uuid4()),
            "title": "Complete React Development Bootcamp",
            "description": "Master React from fundamentals to advanced concepts. Build 5 real-world projects including a full-stack e-commerce app. Learn React Hooks, Context API, Redux, and modern development practices.",
            "instructor_id": mentors[0]['id'],
            "category": "programming",
            "level": "intermediate",
            "duration_hours": 45,
            "price": 149.99,
            "thumbnail": "https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=400&h=240&fit=crop",
            "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            "tags": ["react", "javascript", "frontend", "hooks", "redux"],
            "is_published": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Machine Learning with Python",
            "description": "Comprehensive course covering supervised and unsupervised learning algorithms. Hands-on projects with scikit-learn, pandas, and numpy. Build predictive models for real business problems.",
            "instructor_id": mentors[1]['id'],
            "category": "data-science", 
            "level": "intermediate",
            "duration_hours": 60,
            "price": 199.99,
            "thumbnail": "https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=400&h=240&fit=crop",
            "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
            "tags": ["python", "machine-learning", "data-science", "ai", "statistics"],
            "is_published": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Full-Stack Web Development with Django & Vue.js",
            "description": "Build modern web applications using Django REST Framework and Vue.js. Learn authentication, database design, API development, and deployment strategies.",
            "instructor_id": mentors[2]['id'],
            "category": "programming",
            "level": "advanced",
            "duration_hours": 55,
            "price": 179.99,
            "thumbnail": "https://images.unsplash.com/photo-1627398242454-45a1465c2479?w=400&h=240&fit=crop",
            "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
            "tags": ["django", "vue", "fullstack", "api", "python"],
            "is_published": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "title": "JavaScript Fundamentals for Beginners",
            "description": "Start your programming journey with JavaScript. Learn variables, functions, objects, DOM manipulation, and asynchronous programming. Perfect for complete beginners.",
            "instructor_id": mentors[0]['id'],
            "category": "programming",
            "level": "beginner", 
            "duration_hours": 25,
            "price": 79.99,
            "thumbnail": "https://images.unsplash.com/photo-1579468118864-1b9ea3c0db4a?w=400&h=240&fit=crop",
            "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
            "tags": ["javascript", "programming", "beginner", "web-development"],
            "is_published": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Data Analysis with Python & Pandas",
            "description": "Learn to analyze and visualize data using Python libraries. Master pandas, matplotlib, and seaborn. Work with real datasets and create insightful reports.",
            "instructor_id": mentors[1]['id'],
            "category": "data-science",
            "level": "beginner",
            "duration_hours": 35,
            "price": 119.99,
            "thumbnail": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=240&fit=crop",
            "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4",
            "tags": ["python", "pandas", "data-analysis", "visualization", "statistics"],
            "is_published": True,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "title": "UI/UX Design Principles",
            "description": "Master the fundamentals of user interface and user experience design. Learn design thinking, prototyping, and user research methodologies.",
            "instructor_id": mentors[0]['id'],
            "category": "design",
            "level": "beginner",
            "duration_hours": 30,
            "price": 99.99,
            "thumbnail": "https://images.unsplash.com/photo-1561070791-2526d30994b5?w=400&h=240&fit=crop",
            "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4",
            "tags": ["ui", "ux", "design", "prototyping", "figma"],
            "is_published": True,
            "created_at": datetime.now(timezone.utc)
        }
    ]
    
    result = await db.courses.insert_many(courses_data)
    print(f"✅ Created {len(result.inserted_ids)} courses")
    return courses_data

async def seed_sessions(users_data, courses_data):
    """Create sample mentorship sessions"""
    print("📅 Creating sample mentorship sessions...")
    
    students = [user for user in users_data if user['role'] == 'student']
    mentors = [user for user in users_data if user['role'] == 'mentor']
    
    sessions_data = [
        {
            "id": str(uuid.uuid4()),
            "mentor_id": mentors[0]['id'],
            "student_id": students[0]['id'],
            "title": "React Hooks Deep Dive",
            "description": "One-on-one session to understand React Hooks and best practices",
            "scheduled_at": datetime.now(timezone.utc) + timedelta(days=2),
            "duration_minutes": 60,
            "status": "scheduled",
            "meeting_link": "https://meet.google.com/sample-link-1",
            "notes": "",
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "mentor_id": mentors[1]['id'],
            "student_id": students[1]['id'],
            "title": "Machine Learning Project Review",
            "description": "Review current ML project and discuss improvement strategies",
            "scheduled_at": datetime.now(timezone.utc) + timedelta(days=5),
            "duration_minutes": 90,
            "status": "scheduled",
            "meeting_link": "https://meet.google.com/sample-link-2",
            "notes": "",
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "mentor_id": mentors[2]['id'],
            "student_id": students[2]['id'],
            "title": "System Architecture Discussion",
            "description": "Completed session on microservices and system design patterns",
            "scheduled_at": datetime.now(timezone.utc) - timedelta(days=3),
            "duration_minutes": 60,
            "status": "completed",
            "meeting_link": "https://meet.google.com/sample-link-3",
            "notes": "Great discussion on microservices patterns. Student should focus on database design next.",
            "created_at": datetime.now(timezone.utc) - timedelta(days=5)
        }
    ]
    
    result = await db.mentorship_sessions.insert_many(sessions_data)
    print(f"✅ Created {len(result.inserted_ids)} mentorship sessions")

async def seed_progress(users_data, courses_data):
    """Create sample progress data"""
    print("📈 Creating sample progress data...")
    
    students = [user for user in users_data if user['role'] == 'student']
    
    progress_data = [
        {
            "id": str(uuid.uuid4()),
            "user_id": students[0]['id'],
            "course_id": courses_data[0]['id'],  # React course
            "completion_percentage": 65.0,
            "last_accessed": datetime.now(timezone.utc) - timedelta(hours=2),
            "completed_lessons": ["intro", "jsx-basics", "components", "props"]
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": students[0]['id'],
            "course_id": courses_data[3]['id'],  # JavaScript course
            "completion_percentage": 100.0,
            "last_accessed": datetime.now(timezone.utc) - timedelta(days=1),
            "completed_lessons": ["variables", "functions", "objects", "dom", "async"]
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": students[1]['id'],
            "course_id": courses_data[1]['id'],  # ML course
            "completion_percentage": 35.0,
            "last_accessed": datetime.now(timezone.utc) - timedelta(hours=5),
            "completed_lessons": ["intro-ml", "data-preprocessing"]
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": students[1]['id'],
            "course_id": courses_data[4]['id'],  # Data Analysis course
            "completion_percentage": 80.0,
            "last_accessed": datetime.now(timezone.utc) - timedelta(hours=1),
            "completed_lessons": ["pandas-basics", "data-cleaning", "visualization"]
        }
    ]
    
    result = await db.progress.insert_many(progress_data)
    print(f"✅ Created {len(result.inserted_ids)} progress records")

async def seed_chat_messages(users_data):
    """Create sample chat messages"""
    print("💬 Creating sample chat messages...")
    
    students = [user for user in users_data if user['role'] == 'student']
    mentors = [user for user in users_data if user['role'] == 'mentor']
    
    messages_data = [
        {
            "id": str(uuid.uuid4()),
            "sender_id": students[0]['id'],
            "receiver_id": mentors[0]['id'],
            "message": "Hi Dr. Rodriguez! I'm really excited about our upcoming React session. I've been working through the hooks section and have a few questions.",
            "timestamp": datetime.now(timezone.utc) - timedelta(hours=3),
            "is_read": True
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": mentors[0]['id'],
            "receiver_id": students[0]['id'],
            "message": "Great to hear from you, Alice! I'm looking forward to our session too. Feel free to prepare a list of your questions beforehand so we can make the most of our time together.",
            "timestamp": datetime.now(timezone.utc) - timedelta(hours=2, minutes=45),
            "is_read": True
        },
        {
            "id": str(uuid.uuid4()),
            "sender_id": students[1]['id'],
            "receiver_id": mentors[1]['id'],
            "message": "Emma, I've been struggling with the feature engineering part of my ML project. Could we discuss some techniques in our next session?",
            "timestamp": datetime.now(timezone.utc) - timedelta(hours=1),
            "is_read": False
        }
    ]
    
    result = await db.chat_messages.insert_many(messages_data)
    print(f"✅ Created {len(result.inserted_ids)} chat messages")

async def main():
    """Main seeding function"""
    print("🌱 Starting EduMentor platform data seeding...\n")
    
    try:
        # Clear existing data
        await clear_existing_data()
        
        # Seed data in order
        users_data = await seed_users()
        courses_data = await seed_courses(users_data)
        await seed_sessions(users_data, courses_data)
        await seed_progress(users_data, courses_data)
        await seed_chat_messages(users_data)
        
        print("\n" + "="*60)
        print("🎉 SEEDING COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\n📋 TEST ACCOUNTS:")
        print("👨‍🎓 Students:")
        print("   • alice.student@example.com (password: password123)")
        print("   • bob.learner@example.com (password: password123)")
        print("   • carol.student@example.com (password: password123)")
        print("\n👨‍🏫 Mentors:")
        print("   • david.mentor@example.com (password: password123)")
        print("   • emma.expert@example.com (password: password123)")
        print("   • frank.fullstack@example.com (password: password123)")
        print("\n👨‍💼 Admin:")
        print("   • admin@edumentor.com (password: admin123)")
        print("\n🚀 Platform ready for testing with sample data!")
        
    except Exception as e:
        print(f"❌ Error during seeding: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())