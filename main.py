from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import random
from datetime import datetime, timedelta
import json
import os

# Try to import dotenv, but don't fail if it's not installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  WARNING: python-dotenv not installed. Environment variables from .env file won't be loaded.")
    print("📝 To install: pip install python-dotenv")

# Import MongoDB connection
from mongodb import mongodb

app = FastAPI(title="Office Attendance Management API", version="1.0.0")

# Configure CORS to allow frontend access
origins = [
    "https://office-attendance-track-frontend.onrender.com",
    "https://office-attendance-track-backend.onrender.com", 
    "http://localhost:3000",
    "http://localhost:3001",
    "*"  # Allow all origins for now to fix connectivity issues
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporarily allow all origins to fix 502 issues
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Pydantic models for request/response
class LoginRequest(BaseModel):
    employee_code: int
    password: str
    role: str  # 'user' or 'admin'

class User(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    employee_code: int
    department: Optional[str] = None

class LoginResponse(BaseModel):
    success: bool
    user: Optional[User] = None
    message: Optional[str] = None

class AttendanceRequest(BaseModel):
    user_id: int
    status: str
    date: str
    notes: Optional[str] = None
    in_time: Optional[str] = None  # 24-hour format HH:MM
    out_time: Optional[str] = None # 24-hour format HH:MM

class AttendanceRecord(BaseModel):
    id: int
    user_id: int
    status: str
    date: str
    notes: Optional[str] = None
    in_time: Optional[str] = None  # 24-hour format HH:MM
    out_time: Optional[str] = None # 24-hour format HH:MM

class TodoRequest(BaseModel):
    user_id: int
    notes: str
    date_created: Optional[str] = None

class Todo(BaseModel):
    id: int
    user_id: int
    notes: str
    date_created: str

class CreateUserRequest(BaseModel):
    email: str
    password: str
    full_name: str
    role: Optional[str] = "user"
    employee_code: Optional[int] = None
    department: Optional[str] = None

class MessageRequest(BaseModel):
    sender_id: int
    receiver_id: int
    content: str
    message_type: Optional[str] = "text"
    type: Optional[str] = "personal"  # personal, group, admin

class Message(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    timestamp: str
    type: str

class NotificationRequest(BaseModel):
    user_id: int
    type: str
    content: str
    reference_id: Optional[int] = None

class Notification(BaseModel):
    id: int
    user_id: int
    type: str
    content: str
    timestamp: str
    status: str
    reference_id: Optional[int] = None

# Load environment variables
# The dotenv import is now handled by the try-except block above

# Initialize MongoDB with default data on startup
@app.on_event("startup")
async def startup_event():
    try:
        # Initialize default data if collections are empty
        mongodb.initialize_default_data()
        print("✅ MongoDB initialized with default data")
    except Exception as e:
        print(f"❌ Error initializing MongoDB: {e}")
        # Don't let MongoDB errors crash the app startup
        print("⚠️ App will continue running without database initialization")

@app.get("/")
def read_root():
    """Root endpoint for health check"""
    return {
        "status": "online",
        "message": "Office Attendance API is running",
        "version": "1.0.0", 
        "documentation": "/docs",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.now().isoformat()
    }

# Message endpoints
@app.get("/api/messages")
def get_messages(user_id: Optional[int] = None, sender_id: Optional[int] = None, receiver_id: Optional[int] = None):
    """Get messages with optional filtering"""
    try:
        messages = mongodb.get_messages(user_id, sender_id, receiver_id)
        return {"success": True, "messages": messages}
    except Exception as e:
        print(f"❌ Error getting messages: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/messages")
def add_message(message_data: MessageRequest):
    """Add a new message"""
    try:
        message = mongodb.add_message(message_data.dict())
        return {"success": True, "message": message}
    except Exception as e:
        print(f"❌ Error adding message: {e}")
        return {"success": False, "message": str(e)}

# Notification endpoints
@app.get("/api/notifications")
def get_notifications(user_id: int, unread_only: Optional[bool] = False):
    """Get notifications for a user"""
    try:
        notifications = mongodb.get_notifications(user_id, unread_only)
        return {"success": True, "notifications": notifications}
    except Exception as e:
        print(f"❌ Error getting notifications: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/notifications")
def add_notification(notification_data: NotificationRequest):
    """Add a new notification"""
    try:
        notification = mongodb.add_notification(notification_data.dict())
        return {"success": True, "notification": notification}
    except Exception as e:
        print(f"❌ Error adding notification: {e}")
        return {"success": False, "message": str(e)}

@app.put("/api/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int):
    """Mark a notification as read"""
    try:
        notification = mongodb.mark_notification_read(notification_id)
        if not notification:
            return {"success": False, "message": "Notification not found"}
        return {"success": True, "notification": notification}
    except Exception as e:
        print(f"❌ Error marking notification as read: {e}")
        return {"success": False, "message": str(e)}

@app.put("/api/notifications/read-all")
def mark_all_notifications_read(user_id: int):
    """Mark all notifications for a user as read"""
    try:
        count = mongodb.mark_all_notifications_read(user_id)
        return {"success": True, "count": count}
    except Exception as e:
        print(f"❌ Error marking all notifications as read: {e}")
        return {"success": False, "message": str(e)}



@app.get("/api/test")
def test_endpoint():
    """Test endpoint for debugging"""
    return {"status": "ok", "message": "Test endpoint working", "timestamp": datetime.now().isoformat()}

@app.get("/api/health")
def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "attendance-api", "timestamp": datetime.now().isoformat()}

@app.options("/api/login")
def login_options():
    """Handle CORS preflight request for login"""
    return {}

@app.get("/api/login")
def login_get(employee_code: int, password: str):
    """Login endpoint (GET method)"""
    print("Received request for /api/login (GET)")
    try:
        # Get all users from MongoDB
        users = mongodb.get_users()
        
        if not users:
            print("⚠️ Warning: No users found in database")
            return {"success": False, "message": "Authentication service unavailable. Please try again later."}
        
        # Find user by employee_code and password
        user = next((u for u in users if int(u.get("employee_code", 0)) == int(employee_code) and u["password"] == password), None)
        
        if user:
            # Return user info without password
            user_info = {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"],
                "employee_code": user.get("employee_code"),
                "department": user.get("department")
            }
            print(f"✅ User {user.get('employee_code')} logged in successfully (GET method)")
            return {"success": True, "user": user_info}
        else:
            print(f"❌ Failed login attempt for employee_code: {employee_code} (GET method)")
            return {"success": False, "message": "Invalid employee code or password"}
    except Exception as e:
        print(f"❌ Error during login (GET method): {e}")
        return {"success": False, "message": "An error occurred during login. Please try again later."}

@app.post("/api/login")
def login_post(login_data: LoginRequest):
    """Login endpoint (POST method)"""
    print("Received request for /api/login (POST)")
    try:
        # Get all users from MongoDB
        users = mongodb.get_users()
        
        if not users:
            print("⚠️ Warning: No users found in database")
            return {"success": False, "message": "Authentication service unavailable. Please try again later."}
        
        # Find user by employee_code and password
        user = next((u for u in users if int(u.get("employee_code", 0)) == int(login_data.employee_code) and u["password"] == login_data.password), None)
        
        if user:
            # Check if the role matches
            if user["role"] != login_data.role:
                if login_data.role == "admin":
                    return {"success": False, "message": "You are not an admin. Please use user login section."}
                else:
                    return {"success": False, "message": "You are an admin. Please use admin login section."}
            # Return user info without password
            user_info = {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"],
                "employee_code": user.get("employee_code"),
                "department": user.get("department")
            }
            print(f"✅ User {user.get('employee_code')} logged in successfully")
            return {"success": True, "user": user_info}
        else:
            print(f"❌ Failed login attempt for employee_code: {login_data.employee_code}")
            return {"success": False, "message": "Invalid employee code or password"}
    except Exception as e:
        print(f"❌ Error during login: {e}")
        return {"success": False, "message": "An error occurred during login. Please try again later."}

@app.options("/api/users")
def users_options():
    """Handle CORS preflight request for users"""
    return {}

@app.get("/api/users")
def get_users():
    """Get all users"""
    print("Received request for /api/users")
    try:
        # Get users from MongoDB
        users = mongodb.get_users()
        
        # Remove passwords from response
        sanitized_users = []
        for user in users:
            sanitized_user = {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"],
                "employee_code": user.get("employee_code"),
                "department": user.get("department"),  # Add department field
                "created_at": user.get("created_at")
            }
            sanitized_users.append(sanitized_user)
            
        return {"success": True, "users": sanitized_users}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/users")
def create_user(user_data: CreateUserRequest):
    """Create a new user"""
    try:
        # Get all users from MongoDB
        users = mongodb.get_users()
    
        # Check if email already exists
        if any(u["email"] == user_data.email for u in users):
            return {"success": False, "message": "Email already exists"}
    
        # Create new user
        new_user = {
            "email": user_data.email,
            "password": user_data.password,
            "full_name": user_data.full_name,
            "role": user_data.role,
            "employee_code": user_data.employee_code,
            "department": user_data.department  # Add department field
        }
        
        # Add user to MongoDB
        created_user = mongodb.add_user(new_user)
        
        # Return sanitized user (without password)
        sanitized_user = {
            "id": created_user["id"],
            "email": created_user["email"],
            "full_name": created_user["full_name"],
            "role": created_user["role"],
            "employee_code": created_user.get("employee_code"),
            "department": created_user.get("department"),  # Add department field
            "created_at": created_user.get("created_at")
        }
        
        return {"success": True, "user": sanitized_user}
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return {"success": False, "message": str(e)}

@app.delete("/api/users/{user_id}")
def delete_user(user_id: int):
    """Delete a user (soft delete with undo capability)"""
    try:
        # Delete user from MongoDB
        deleted_data = mongodb.delete_user(user_id)
        
        if not deleted_data:
            return {"success": False, "message": "User not found"}
            
        # Return success response
        return {
            "success": True,
            "message": f"User {user_id} deleted successfully",
            "user": {
                "id": deleted_data["user"]["id"],
                "email": deleted_data["user"]["email"],
                "full_name": deleted_data["user"]["full_name"]
            }
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/users/{user_id}/permanent-delete")
def permanent_delete_user(user_id: int):
    """Permanently delete a user without undo capability"""
    try:
        # First check if user exists in active users
        user_data = mongodb.get_user_by_id(user_id)
        if user_data:
            # User is active, delete them normally
            deleted_data = mongodb.delete_user(user_id)
            if not deleted_data:
                return {"success": False, "message": "User not found"}
        else:
            # User might be in deleted_users collection, check there
            deleted_user_data = mongodb.get_deleted_user_by_id(user_id)
            if not deleted_user_data:
                return {"success": False, "message": "User not found"}
            
            # Remove from deleted_users collection permanently
            mongodb.permanently_remove_deleted_user(user_id)
            deleted_data = {"user": deleted_user_data["user"]}
            
        # Return success response
        return {
            "success": True,
            "message": f"User {user_id} permanently deleted",
            "user": {
                "id": deleted_data["user"]["id"],
                "email": deleted_data["user"]["email"],
                "full_name": deleted_data["user"]["full_name"]
            }
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/users/{user_id}/undo")
def undo_user_deletion(user_id: int):
    """Undo a user deletion"""
    try:
        # Restore user from MongoDB
        restored_data = mongodb.undo_user_deletion(user_id)
        
        if not restored_data:
            return {"success": False, "message": "Deleted user not found"}
            
        # Return success response
        return {
            "success": True,
            "message": f"User {user_id} restored successfully",
            "user": {
                "id": restored_data["user"]["id"],
                "email": restored_data["user"]["email"],
                "full_name": restored_data["user"]["full_name"]
            }
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.options("/api/attendance")
def attendance_options():
    """Handle CORS preflight request for attendance"""
    return {}

@app.get("/api/attendance")
def get_attendance(
    user_id: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None)
):
    """Get attendance records with optional filters"""
    try:
        records = mongodb.get_attendance(user_id, month, year)
        return {"success": True, "records": records}
    except Exception as e:
        print(f"❌ Error getting attendance records: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/attendance")
def create_attendance(record: AttendanceRequest):
    """Create a new attendance record"""
    try:
        # Prevent marking attendance on weekends (Saturday=5, Sunday=6)
        try:
            parsed_date = datetime.strptime(record.date, "%Y-%m-%d")
            if parsed_date.weekday() >= 5:
                return {"success": False, "message": "Attendance cannot be marked on weekends"}
        except Exception:
            # If date parsing fails, return error
            return {"success": False, "message": "Invalid date format. Expected YYYY-MM-DD"}

        # Add attendance record to MongoDB
        created_record = mongodb.add_attendance({
            "user_id": record.user_id,
            "status": record.status,
            "date": record.date,
            "notes": record.notes,
            "in_time": record.in_time,
            "out_time": record.out_time
        })
        
        return {"success": True, "record": created_record}
    except Exception as e:
        print(f"❌ Error creating attendance record: {e}")
        return {"success": False, "message": str(e)}

@app.delete("/api/attendance/{attendance_id}")
def delete_attendance(attendance_id: int):
    """Delete an attendance record"""
    try:
        deleted_record = mongodb.delete_attendance(attendance_id)
        if not deleted_record:
            return {"success": False, "message": "Attendance record not found"}
        return {"success": True, "record": deleted_record}
    except Exception as e:
        print(f"❌ Error deleting attendance record: {e}")
        return {"success": False, "message": str(e)}

@app.get("/api/attendance/stats")
def get_attendance_stats(
    user_id: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None)
):
    """Get attendance statistics"""
    try:
        # Get attendance records from MongoDB
        records = mongodb.get_attendance(user_id, month, year)
        
        # Calculate statistics
        total_records = len(records)
        present_records = len([r for r in records if r["status"] == "present"])
        absent_records = len([r for r in records if r["status"] == "absent"])
        
        present_percentage = (present_records / total_records * 100) if total_records > 0 else 0
        absent_percentage = (absent_records / total_records * 100) if total_records > 0 else 0

        return {
            "success": True,
            "present_days": present_records,
            "absent_days": absent_records,
            "total_days": total_records,
            "present_percentage": round(present_percentage, 2),
            "absent_percentage": round(absent_percentage, 2)
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.options("/api/todos")
def todos_options():
    """Handle CORS preflight request for todos"""
    return {}

@app.get("/api/todos")
def get_todos(user_id: Optional[int] = Query(None)):
    """Get todos for a specific user or all todos"""
    try:
        todos = mongodb.get_todos(user_id)
        return {"success": True, "todos": todos}
    except Exception as e:
        print(f"❌ Error getting todos: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/todos")
def create_todo(todo: TodoRequest):
    """Create a new todo"""
    try:
        # Add todo to MongoDB
        created_todo = mongodb.add_todo({
            "user_id": todo.user_id,
            "notes": todo.notes,
            "date_created": todo.date_created or datetime.now().isoformat()
        })
        
        return {"success": True, "todo": created_todo}
    except Exception as e:
        print(f"❌ Error creating todo: {e}")
        return {"success": False, "message": str(e)}

@app.put("/api/todos/{todo_id}")
def update_todo(todo_id: int, notes: Optional[str] = Query(None)):
    """Update a todo's notes"""
    try:
        if notes is None:
            return {"success": False, "message": "Notes cannot be empty"}
        updated_todo = mongodb.update_todo(todo_id, notes)
        if not updated_todo:
            return {"success": False, "message": "Todo not found"}
        return {"success": True, "todo": updated_todo}
    except Exception as e:
        print(f"❌ Error updating todo: {e}")
        return {"success": False, "message": str(e)}

@app.delete("/api/todos/{todo_id}")
def delete_todo(todo_id: int):
    """Delete a todo"""
    try:
        deleted_todo = mongodb.delete_todo(todo_id)
        if not deleted_todo:
            return {"success": False, "message": "Todo not found"}
        return {"success": True, "todo": deleted_todo}
    except Exception as e:
        print(f"❌ Error deleting todo: {e}")
        return {"success": False, "message": str(e)}

@app.get("/api/logout")
def logout():
    """Logout endpoint"""
    return {"success": True, "message": "Logged out successfully"}

# Teams endpoints
@app.get("/api/teams/department/{department}")
def get_department_members(department: str):
    """Get all members of a specific department"""
    try:
        members = mongodb.get_department_members(department)
        return {"success": True, "members": members}
    except Exception as e:
        print(f"❌ Error getting department members: {e}")
        return {"success": False, "message": str(e)}

@app.get("/api/teams/user/{user_id}/department")
def get_user_department(user_id: int):
    """Get department of a specific user"""
    try:
        department = mongodb.get_user_department(user_id)
        if department:
            return {"success": True, "department": department}
        else:
            return {"success": False, "message": "User not found"}
    except Exception as e:
        print(f"❌ Error getting user department: {e}")
        return {"success": False, "message": str(e)}

# Messages endpoints
@app.get("/api/messages/{user_id}")
def get_user_messages(user_id: int, chat_type: str = Query("all")):
    """Get messages for a specific user"""
    try:
        messages = mongodb.get_messages(user_id, chat_type)
        return {"success": True, "messages": messages}
    except Exception as e:
        print(f"❌ Error getting messages: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/messages")
def add_message(message_data: MessageRequest):
    """Add a new message"""
    try:
        created_message = mongodb.add_message({
            "sender_id": message_data.sender_id,
            "receiver_id": message_data.receiver_id,
            "content": message_data.content,
            "type": message_data.type,
            "timestamp": datetime.now().isoformat()
        })
        return {"success": True, "message": created_message}
    except Exception as e:
        print(f"❌ Error adding message: {e}")
        return {"success": False, "message": str(e)}

# Notifications endpoints
@app.get("/api/notifications/{user_id}")
def get_user_notifications(user_id: int):
    """Get notifications for a specific user"""
    try:
        notifications = mongodb.get_notifications(user_id)
        return {"success": True, "notifications": notifications}
    except Exception as e:
        print(f"❌ Error getting notifications: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/notifications")
def add_notification(notification_data: NotificationRequest):
    """Add a new notification"""
    try:
        created_notification = mongodb.add_notification({
            "user_id": notification_data.user_id,
            "type": notification_data.type,
            "content": notification_data.content,
            "reference_id": notification_data.reference_id,
            "timestamp": datetime.now().isoformat()
        })
        return {"success": True, "notification": created_notification}
    except Exception as e:
        print(f"❌ Error adding notification: {e}")
        return {"success": False, "message": str(e)}

@app.put("/api/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int):
    """Mark notification as read"""
    try:
        updated_notification = mongodb.mark_notification_read(notification_id)
        if not updated_notification:
            return {"success": False, "message": "Notification not found"}
        return {"success": True, "notification": updated_notification}
    except Exception as e:
        print(f"❌ Error marking notification read: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/attendance/force-sync")
def force_sync_attendance():
    """Force synchronization of attendance data"""
    try:
        # Get total record count for response
        all_records = mongodb.get_attendance()
        record_count = len(all_records)
        return {"success": True, "message": "Attendance data synchronized successfully", "record_count": record_count}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/ping")
def ping():
    print("/ping endpoint hit")
    return {"message": "pong"}

@app.post("/api/force-reinitialize")
def force_reinitialize():
    """Force re-initialization of database with all 21 users"""
    try:
        # Clear existing users and recreate them
        mongodb.users_collection.delete_many({})
        mongodb.attendance_collection.delete_many({})
        
        # Re-initialize
        mongodb.initialize_default_data()
        
        # Get final count
        user_count = mongodb.users_collection.count_documents({})
        
        return {
            "success": True, 
            "message": f"Database re-initialized successfully with {user_count} users",
            "user_count": user_count
        }
    except Exception as e:
        return {"success": False, "message": f"Error re-initializing: {str(e)}"}

# Add this for Render deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
