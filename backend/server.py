from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
import json


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="EduMentor API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# WebSocket manager for real-time chat
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.user_connections[user_id] = websocket

    def disconnect(self, websocket: WebSocket, user_id: str):
        self.active_connections.remove(websocket)
        if user_id in self.user_connections:
            del self.user_connections[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.user_connections:
            await self.user_connections[user_id].send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Models
class UserRole(str):
    STUDENT = "student"
    MENTOR = "mentor"
    ADMIN = "admin"

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    role: str = UserRole.STUDENT
    skills: List[str] = []
    interests: List[str] = []
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = UserRole.STUDENT
    skills: List[str] = []
    interests: List[str] = []
    bio: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Course(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    instructor_id: str
    category: str
    level: str  # beginner, intermediate, advanced
    duration_hours: int
    price: float
    thumbnail: Optional[str] = None
    video_url: Optional[str] = None
    tags: List[str] = []
    is_published: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CourseCreate(BaseModel):
    title: str
    description: str
    category: str
    level: str
    duration_hours: int
    price: float
    thumbnail: Optional[str] = None
    video_url: Optional[str] = None
    tags: List[str] = []

class MentorshipSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mentor_id: str
    student_id: str
    title: str
    description: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: int = 60
    status: str = "scheduled"  # scheduled, completed, cancelled
    meeting_link: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SessionCreate(BaseModel):
    mentor_id: str
    title: str
    description: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: int = 60

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    receiver_id: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_read: bool = False

class MessageCreate(BaseModel):
    receiver_id: str
    message: str

class Progress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    course_id: str
    completion_percentage: float = 0.0
    last_accessed: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_lessons: List[str] = []

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = await db.users.find_one({"email": email})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

def require_role(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

# Authentication endpoints
@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create user
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.dict()
    user_dict.pop('password')
    
    user = User(**user_dict)
    user_doc = user.dict()
    user_doc['hashed_password'] = hashed_password
    
    await db.users.insert_one(user_doc)
    return user

@api_router.post("/auth/login")
async def login(user_credentials: UserLogin):
    user = await db.users.find_one({"email": user_credentials.email})
    if not user or not verify_password(user_credentials.password, user['hashed_password']):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['email']}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": User(**user)
    }

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# Course endpoints
@api_router.post("/courses", response_model=Course)
async def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(require_role([UserRole.MENTOR, UserRole.ADMIN]))
):
    course_dict = course_data.dict()
    course_dict['instructor_id'] = current_user.id
    course = Course(**course_dict)
    await db.courses.insert_one(course.dict())
    return course

@api_router.get("/courses", response_model=List[Course])
async def get_courses(
    category: Optional[str] = None,
    level: Optional[str] = None,
    search: Optional[str] = None
):
    query = {"is_published": True}
    if category:
        query["category"] = category
    if level:
        query["level"] = level
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    courses = await db.courses.find(query).to_list(length=None)
    return [Course(**course) for course in courses]

@api_router.get("/courses/{course_id}", response_model=Course)
async def get_course(course_id: str):
    course = await db.courses.find_one({"id": course_id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return Course(**course)

# Mentorship endpoints
@api_router.get("/mentors", response_model=List[User])
async def get_mentors(skills: Optional[str] = None):
    query = {"role": UserRole.MENTOR, "is_active": True}
    if skills:
        skill_list = [s.strip() for s in skills.split(',')]
        query["skills"] = {"$in": skill_list}
    
    mentors = await db.users.find(query).to_list(length=None)
    return [User(**mentor) for mentor in mentors]

@api_router.post("/mentorship/sessions", response_model=MentorshipSession)
async def book_session(
    session_data: SessionCreate,
    current_user: User = Depends(require_role([UserRole.STUDENT]))
):
    # Check if mentor exists
    mentor = await db.users.find_one({"id": session_data.mentor_id, "role": UserRole.MENTOR})
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")
    
    session_dict = session_data.dict()
    session_dict['student_id'] = current_user.id
    session = MentorshipSession(**session_dict)
    await db.mentorship_sessions.insert_one(session.dict())
    return session

@api_router.get("/mentorship/sessions", response_model=List[MentorshipSession])
async def get_sessions(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.STUDENT:
        query = {"student_id": current_user.id}
    elif current_user.role == UserRole.MENTOR:
        query = {"mentor_id": current_user.id}
    else:  # Admin
        query = {}
    
    sessions = await db.mentorship_sessions.find(query).to_list(length=None)
    return [MentorshipSession(**session) for session in sessions]

# Chat endpoints
@api_router.post("/chat/messages", response_model=ChatMessage)
async def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user)
):
    message_dict = message_data.dict()
    message_dict['sender_id'] = current_user.id
    message = ChatMessage(**message_dict)
    
    await db.chat_messages.insert_one(message.dict())
    
    # Send real-time message
    await manager.send_personal_message(
        json.dumps({
            "type": "new_message",
            "data": message.dict(),
            "sender_name": current_user.full_name
        }),
        message_data.receiver_id
    )
    
    return message

@api_router.get("/chat/conversations/{user_id}", response_model=List[ChatMessage])
async def get_conversation(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    messages = await db.chat_messages.find({
        "$or": [
            {"sender_id": current_user.id, "receiver_id": user_id},
            {"sender_id": user_id, "receiver_id": current_user.id}
        ]
    }).sort("timestamp", 1).to_list(length=None)
    
    return [ChatMessage(**message) for message in messages]

# Progress tracking
@api_router.post("/progress/{course_id}")
async def update_progress(
    course_id: str,
    completion_percentage: float,
    current_user: User = Depends(get_current_user)
):
    progress_data = {
        "user_id": current_user.id,
        "course_id": course_id,
        "completion_percentage": completion_percentage,
        "last_accessed": datetime.now(timezone.utc)
    }
    
    await db.progress.update_one(
        {"user_id": current_user.id, "course_id": course_id},
        {"$set": progress_data},
        upsert=True
    )
    
    return {"message": "Progress updated successfully"}

@api_router.get("/progress", response_model=List[Progress])
async def get_user_progress(current_user: User = Depends(get_current_user)):
    progress_list = await db.progress.find({"user_id": current_user.id}).to_list(length=None)
    return [Progress(**progress) for progress in progress_list]

# WebSocket endpoint for real-time chat
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
            pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

# Include the router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)