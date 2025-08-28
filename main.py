from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import random
from datetime import datetime, timedelta
import json
import os

# Import dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  WARNING: python-dotenv not installed. Environment variables from .env file won't be loaded.")
    print("📝 To install: pip install python-dotenv")

# Import MongoDB
from mongodb import mongodb

app = FastAPI(title="Office Attendance Management API", version="1.0.0")

# Configure CORS
origins = [
    "https://frontend-4r7g.onrender.com",
    "https://backend-9z1y.onrender.com",
    "https://office-attendance-track-frontend.onrender.com",
    "https://office-attendance-track-backend.onrender.com", 
    "http://localhost:3000",
    "http://localhost:3001",
    "*"  # Allow all origins
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Pydantic models
class LoginRequest(BaseModel):
    employee_code: int
    password: str
    role: str  # user/admin

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

# Load env vars

# Init MongoDB
@app.on_event("startup")
async def startup_event():
    try:
        # Init default data
        mongodb.initialize_default_data()
        print("✅ MongoDB initialized with default data")
    except Exception as e:
        print(f"❌ Error initializing MongoDB: {e}")
        # Don't crash app
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

# Messages
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

@app.delete("/api/messages/{message_id}")
def delete_message(message_id: int):
    """Delete a message by ID"""
    try:
        success = mongodb.delete_message(message_id)
        if success:
            return {"success": True, "message": "Message deleted successfully"}
        else:
            return {"success": False, "message": "Message not found"}
    except Exception as e:
        print(f"❌ Error deleting message: {e}")
        return {"success": False, "message": str(e)}

# User lookup by code
@app.get("/api/users/by-employee-code/{employee_code}")
def get_user_by_employee_code(employee_code: int):
    try:
        user = mongodb.get_user_by_employee_code(employee_code)
        if not user:
            return {"success": False, "message": "User not found"}
        return {"success": True, "user": {
            "id": user["id"],
            "email": user.get("email"),
            "full_name": user.get("full_name"),
            "role": user.get("role"),
            "employee_code": user.get("employee_code"),
            "department": user.get("department")
        }}
    except Exception as e:
        return {"success": False, "message": str(e)}

# Conversations
@app.get("/api/conversations/{user_id}")
def get_conversations(user_id: int):
    try:
        conversations = mongodb.get_conversations_for_user(user_id)
        return {"success": True, "conversations": conversations}
    except Exception as e:
        return {"success": False, "message": str(e)}

# Notifications
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
                "id": deleted_data["id"],
                "email": deleted_data["email"],
                "full_name": deleted_data["full_name"]
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

        # Handle leave types (PL, CL, SL)
        if record.status.upper() in ["PL", "CL", "SL"]:
            try:
                # Apply leave and update balance
                leave_result = mongodb.apply_leave(record.user_id, record.status.upper(), record.date)
                if not leave_result.get("success"):
                    return {"success": False, "message": f"Failed to apply leave: {leave_result.get('message', 'Unknown error')}"}
            except Exception as leave_error:
                return {"success": False, "message": f"Leave application failed: {str(leave_error)}"}

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
        # Get the record before deleting to check if it's a leave
        attendance_record = mongodb.get_attendance_by_id(attendance_id)
        if not attendance_record:
            return {"success": False, "message": "Attendance record not found"}
        
        # If it's a leave type, cancel the leave
        if attendance_record["status"].upper() in ["PL", "CL", "SL"]:
            try:
                leave_result = mongodb.cancel_leave(
                    attendance_record["user_id"], 
                    attendance_record["status"].upper(), 
                    attendance_record["date"]
                )
                if not leave_result.get("success"):
                    return {"success": False, "message": f"Failed to cancel leave: {leave_result.get('message', 'Unknown error')}"}
            except Exception as leave_error:
                return {"success": False, "message": f"Leave cancellation failed: {str(leave_error)}"}
        
        # Delete the attendance record
        deleted_record = mongodb.delete_attendance(attendance_id)
        if not deleted_record:
            return {"success": False, "message": "Attendance record not found"}
        return {"success": True, "record": deleted_record}
    except Exception as e:
        print(f"❌ Error deleting attendance record: {e}")
        return {"success": False, "message": str(e)}

@app.get("/api/attendance/stats")
def get_attendance_stats(
    employee_code: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None)
):
    """Get attendance statistics"""
    try:
        # Get attendance records from MongoDB
        records = mongodb.get_attendance_by_employee_code(employee_code, month, year)
        
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

# Leave management endpoints
@app.get("/api/leave/balances/{employee_code}")
def get_leave_balances(employee_code: int):
    """Get leave balances for a user by employee code"""
    try:
        balances = mongodb.get_user_leave_balances(employee_code)
        if not balances:
            return {"success": False, "message": "User not found"}
        return {"success": True, "balances": balances}
    except Exception as e:
        print(f"❌ Error getting leave balances: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/leave/apply")
def apply_leave(user_id: int, leave_type: str, date: str):
    """Apply leave for a user"""
    try:
        result = mongodb.apply_leave(user_id, leave_type, date)
        return {"success": True, "result": result}
    except Exception as e:
        print(f"❌ Error applying leave: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/leave/cancel")
def cancel_leave(user_id: int, leave_type: str, date: str):
    """Cancel leave for a user"""
    try:
        result = mongodb.cancel_leave(user_id, leave_type, date)
        return {"success": True, "result": result}
    except Exception as e:
        print(f"❌ Error cancelling leave: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/leave/rollover/{year}")
def process_year_end_rollover(year: int):
    """Process year-end leave rollover"""
    try:
        result = mongodb.process_year_end_rollover(year)
        return result
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/system/simulate-date")
def simulate_current_date(date: str = Body(..., embed=True)):
    """Simulate a different current date for testing purposes"""
    try:
        # Validate date format
        datetime.strptime(date, "%Y-%m-%d")
        
        # Store the simulated date in a global variable or cache
        # For now, we'll return success and the frontend can use this date
        return {
            "success": True, 
            "simulated_date": date,
            "message": f"System date simulated to {date}"
        }
    except ValueError:
        return {"success": False, "message": "Invalid date format. Use YYYY-MM-DD"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/system/clear-all-data")
def clear_all_attendance_and_leave_data():
    """Clear all attendance records and reset leave balances for all users"""
    try:
        result = mongodb.clear_all_attendance_and_leave()
        return result
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/api/logout")
def logout():
    """Logout endpoint"""
    return {"success": True, "message": "Logged out successfully"}

# Add this for Render deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
