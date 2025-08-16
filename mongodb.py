import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import random

# Try to import required packages, but don't fail if they're not installed
try:
    from pymongo import MongoClient, ReturnDocument
    from pymongo.collection import Collection
    from pymongo.database import Database
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    print("⚠️  WARNING: pymongo not installed. MongoDB functionality won't be available.")
    print("📝 To install: pip install pymongo")

try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("⚠️  WARNING: python-dotenv not installed. Environment variables from .env file won't be loaded.")
    print("📝 To install: pip install python-dotenv")

# MongoDB connection string from environment variable
# Default points to provided cluster if env not set
MONGO_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://anonymousbakaa:chillkro1@office-attendance-track.zfitwha.mongodb.net/?retryWrites=true&w=majority&appName=Office-attendance-track-v2"
)

if not MONGO_URI:
    print("⚠️  WARNING: MONGODB_URI environment variable is not set")
    print("📝 Please set it in your .env file or in your environment")
else:
    print(f"✅ MongoDB URI configured: {MONGO_URI[:20]}...")


class MongoDBManager:
    """MongoDB database manager for the Office Attendance Tracker application"""
    
    def __init__(self):
        """Initialize MongoDB connection and collections"""
        if not PYMONGO_AVAILABLE:
            print("❌ MongoDB functionality is not available. Please install pymongo.")
            return
            
        if not MONGO_URI:
            print("❌ MongoDB connection string is not set. Please set MONGODB_URI environment variable.")
            return
            
        try:
            print("🔄 Connecting to MongoDB Atlas...")
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            
            # Test connection with timeout
            self.client.admin.command('ping')
            print("✅ MongoDB connection test successful")
            
            self.db = self.client["office_attendance_db"]
            
            # Initialize collections
            self.users_collection = self.db["users"]
            self.attendance_collection = self.db["attendance"]
            self.todos_collection = self.db["todos"]
            self.deleted_users_collection = self.db["deleted_users"]
            self.messages_collection = self.db["messages"]
            self.notifications_collection = self.db["notifications"]
            
            # Create indexes for better query performance
            try:
                self.users_collection.create_index("email", unique=True)
                self.users_collection.create_index("employee_code", unique=True, sparse=True)
                self.attendance_collection.create_index([("user_id", 1), ("date", 1)], unique=True)
                self.todos_collection.create_index("user_id")
                self.messages_collection.create_index([("sender_id", 1), ("receiver_id", 1), ("timestamp", 1)])
                self.notifications_collection.create_index([("user_id", 1), ("timestamp", 1)])
                print("✅ MongoDB indexes created successfully")
            except Exception as index_error:
                print(f"⚠️ Warning: Could not create indexes: {index_error}")
                
            print("✅ Connected to MongoDB Atlas successfully")
        except Exception as e:
            print(f"❌ Error connecting to MongoDB: {e}")
            print("⚠️ The application may not function correctly without database connection")
            # Don't raise the exception, allow the app to start even with DB issues
            # This helps with debugging
    
    def initialize_default_data(self):
        """Initialize database with default data if collections are empty"""
        # Only add default data if collections are empty
        if self.users_collection.count_documents({}) == 0:
            default_users = self._get_default_users()
            self.users_collection.insert_many(default_users)
            print(f"✅ Initialized {len(default_users)} default users")
            
            # Generate attendance data for default users
            attendance_records = self._generate_default_attendance()
            if attendance_records:
                self.attendance_collection.insert_many(attendance_records)
                print(f"✅ Initialized {len(attendance_records)} default attendance records")

        # Ensure employee codes exist for all users
        try:
            # Ensure proper employee codes exist (admin=1000, users start at 1001)
            self.normalize_employee_codes()
        except Exception as e:
            print(f"⚠️ Could not normalize employee codes: {e}")
    
    def _get_default_users(self) -> List[Dict]:
        """Get default user data"""
        current_time = datetime.now().isoformat()
        users = [
            {
                "id": 1,
                "email": "admin@company.com",
                "password": "admin123",
                "full_name": "Admin User",
                "role": "admin",
                "created_at": current_time,
                "employee_code": 1000,
                "department": "Management"
            },
            {
                "id": 2,
                "email": "user1@company.com",
                "password": "user123",
                "full_name": "User One",
                "role": "user",
                "created_at": current_time,
                "employee_code": 1001,
                "department": "Engineering"
            },
            {
                "id": 3,
                "email": "user2@company.com",
                "password": "user123",
                "full_name": "User Two",
                "role": "user",
                "created_at": current_time,
                "employee_code": 1002,
                "department": "Marketing"
            },
            {
                "id": 4,
                "email": "user3@company.com",
                "password": "user123",
                "full_name": "User Three",
                "role": "user",
                "created_at": current_time,
                "employee_code": 1003,
                "department": "Engineering"
            },
            {
                "id": 5,
                "email": "user4@company.com",
                "password": "user123",
                "full_name": "User Four",
                "role": "user",
                "created_at": current_time,
                "employee_code": 1004,
                "department": "Finance"
            },
            {
                "id": 6,
                "email": "user5@company.com",
                "password": "user123",
                "full_name": "User Five",
                "role": "user",
                "created_at": current_time,
                "employee_code": 1005,
                "department": "Marketing"
            }
        ]
        return users

    def normalize_employee_codes(self) -> None:
        """Ensure admin has 1000 and users have sequential codes starting at 1001 for any missing."""
        # Ensure admin code
        admins = list(self.users_collection.find({"role": "admin"}))
        for admin in admins:
            if admin.get("employee_code") != 1000:
                try:
                    self.users_collection.update_one({"_id": admin["_id"]}, {"$set": {"employee_code": 1000}})
                except Exception as e:
                    print(f"⚠️ Failed setting admin employee_code: {e}")
        # Assign codes to users missing one
        users_missing = list(self.users_collection.find({
            "role": "user",
            "$or": [{"employee_code": {"$exists": False}}, {"employee_code": None}]
        }))
        if users_missing:
            # Determine next code >= 1001
            max_user_code_doc = self.users_collection.find_one(
                {"role": "user", "employee_code": {"$type": "int"}}, sort=[("employee_code", -1)]
            )
            next_code = max(1001, (max_user_code_doc["employee_code"] + 1) if max_user_code_doc else 1001)
            for user in sorted(users_missing, key=lambda u: u.get("id", 0)):
                try:
                    self.users_collection.update_one({"_id": user["_id"]}, {"$set": {"employee_code": next_code}})
                    next_code += 1
                except Exception as e:
                    print(f"⚠️ Failed to set employee_code for user {user.get('id')}: {e}")
    
    def _generate_default_attendance(self) -> List[Dict]:
        """Generate default attendance data"""
        from datetime import timedelta
        
        attendance_records = []
        record_id = 1
        
        # Start from April 1, 2025
        start_date = datetime(2025, 4, 1)
        # End at July 2, 2025
        end_date = datetime(2025, 7, 2)
        
        # Get all users except admin
        users = list(self.users_collection.find({"role": "user"}))
        
        for user in users:
            current_date = start_date
            while current_date <= end_date:
                # Skip weekends (Saturday=5, Sunday=6)
                if current_date.weekday() < 5:
                    # Random attendance pattern (85% present, 15% absent)
                    status = "present" if random.random() < 0.85 else "absent"
                    
                    # Generate random in and out times for present status
                    in_time = None
                    out_time = None
                    if status == "present":
                        # Random in time between 8:00 AM and 9:30 AM
                        in_hour = random.randint(8, 9)
                        in_minute = random.randint(0, 59) if in_hour < 9 else random.randint(0, 30)
                        in_time = f"{in_hour:02d}:{in_minute:02d}"
                        
                        # Random out time between 5:00 PM and 6:30 PM
                        out_hour = random.randint(17, 18)
                        out_minute = random.randint(0, 59) if out_hour < 18 else random.randint(0, 30)
                        out_time = f"{out_hour:02d}:{out_minute:02d}"
                    
                    attendance_records.append({
                        "id": record_id,
                        "user_id": user["id"],
                        "status": status,
                        "date": current_date.strftime("%Y-%m-%d"),
                        "notes": None,
                        "in_time": in_time,
                        "out_time": out_time
                    })
                    record_id += 1
                
                current_date += timedelta(days=1)
        
        return attendance_records
    
    # User operations
    def get_users(self) -> List[Dict]:
        """Get all users"""
        return list(self.users_collection.find({}, {"_id": 0}))
    
    def add_user(self, user_data: Dict) -> Dict:
        """Add a new user with auto-generated ID"""
        try:
            # Auto-generate user ID
            max_id = 0
            last_user = self.users_collection.find_one({}, sort=[("id", -1)])
            if last_user:
                max_id = last_user["id"]
            
            user_data['id'] = max_id + 1
            user_data['created_at'] = datetime.now().isoformat()

            # Auto-generate employee_code
            last_with_code = self.users_collection.find_one({"employee_code": {"$exists": True}}, sort=[("employee_code", -1)])
            next_employee_code = (last_with_code["employee_code"] + 1) if last_with_code and isinstance(last_with_code.get("employee_code"), int) else 1001
            user_data['employee_code'] = user_data.get('employee_code') or next_employee_code
            
            # Insert into MongoDB
            result = self.users_collection.insert_one(user_data)
            
            if not result.acknowledged:
                raise Exception("Failed to insert user into database")
            
            # Verify the user was created
            created_user = self.users_collection.find_one({"_id": result.inserted_id})
            if not created_user:
                raise Exception("User was not found after creation")
            
            # Return the user without MongoDB _id
            return {k: v for k, v in created_user.items() if k != '_id'}
        except Exception as e:
            print(f"❌ Error adding user: {e}")
            raise
    
    def delete_user(self, user_id: int) -> Optional[Dict]:
        """Delete a user and store for undo"""
        # Find the user
        user_to_delete = self.users_collection.find_one({"id": user_id})
        if not user_to_delete:
            return None
        
        # Store user data for undo functionality
        user_attendance = list(self.attendance_collection.find({"user_id": user_id}, {"_id": 0}))
        user_todos = list(self.todos_collection.find({"user_id": user_id}, {"_id": 0}))
        user_messages = list(self.messages_collection.find({"$or": [{"sender_id": user_id}, {"receiver_id": user_id}]}, {"_id": 0}))
        user_notifications = list(self.notifications_collection.find({"user_id": user_id}, {"_id": 0}))
        
        deleted_user_data = {
            "user": {k: v for k, v in user_to_delete.items() if k != '_id'},
            "attendance": user_attendance,
            "todos": user_todos,
            "messages": user_messages,
            "notifications": user_notifications,
            "deleted_at": datetime.now().isoformat()
        }
        
        # Store deleted user data
        self.deleted_users_collection.insert_one(deleted_user_data)
        
        # Delete user's messages, notifications, attendance and todos
        self.messages_collection.delete_many({"$or": [{"sender_id": user_id}, {"receiver_id": user_id}]})
        self.notifications_collection.delete_many({"user_id": user_id})
        self.attendance_collection.delete_many({"user_id": user_id})
        self.todos_collection.delete_many({"user_id": user_id})
        
        # Delete the user
        self.users_collection.delete_one({"id": user_id})
        
        return {k: v for k, v in user_to_delete.items() if k != '_id'}
        
        return {k: v for k, v in user_to_delete.items() if k != '_id'}
    
    # Message operations
    def get_messages(self, user_id: int = None, sender_id: int = None, receiver_id: int = None) -> List[Dict]:
        """Get messages with optional filtering"""
        query = {}
        if user_id:
            query = {"$or": [{"sender_id": user_id}, {"receiver_id": user_id}]}
        elif sender_id and receiver_id:
            query = {"$or": [
                {"sender_id": sender_id, "receiver_id": receiver_id},
                {"sender_id": receiver_id, "receiver_id": sender_id}
            ]}
        elif sender_id:
            query = {"sender_id": sender_id}
        elif receiver_id:
            query = {"receiver_id": receiver_id}
            
        return list(self.messages_collection.find(query, {"_id": 0}).sort("timestamp", 1))
    
    def add_message(self, message_data: Dict) -> Dict:
        """Add a new message"""
        try:
            # Auto-generate message ID
            max_id = 0
            last_message = self.messages_collection.find_one({}, sort=[("id", -1)])
            if last_message:
                max_id = last_message["id"]
            
            message_data['id'] = max_id + 1
            message_data['timestamp'] = message_data.get('timestamp') or datetime.now().isoformat()
            
            # Insert into MongoDB
            result = self.messages_collection.insert_one(message_data)
            
            if not result.acknowledged:
                raise Exception("Failed to insert message into database")
            
            # Verify the message was created
            created_message = self.messages_collection.find_one({"_id": result.inserted_id})
            if not created_message:
                raise Exception("Message was not found after creation")
            
            # Create notification for the receiver
            sender = self.users_collection.find_one({"id": message_data["sender_id"]}, {"_id": 0})
            if sender:
                notification_data = {
                    "user_id": message_data["receiver_id"],
                    "type": "message",
                    "content": f"New message from {sender.get('full_name', 'Unknown')}",
                    "reference_id": message_data['id'],
                    "is_read": False,
                    "timestamp": datetime.now().isoformat()
                }
                self.add_notification(notification_data)
            
            # Return the message without MongoDB _id
            return {k: v for k, v in created_message.items() if k != '_id'}
        except Exception as e:
            print(f"❌ Error adding message: {e}")
            raise
    
    # Notification operations
    def get_notifications(self, user_id: int, unread_only: bool = False) -> List[Dict]:
        """Get notifications for a user"""
        query = {"user_id": user_id}
        if unread_only:
            query["is_read"] = False
            
        return list(self.notifications_collection.find(query, {"_id": 0}).sort("timestamp", -1))
    
    def add_notification(self, notification_data: Dict) -> Dict:
        """Add a new notification"""
        try:
            # Auto-generate notification ID
            max_id = 0
            last_notification = self.notifications_collection.find_one({}, sort=[("id", -1)])
            if last_notification:
                max_id = last_notification["id"]
            
            notification_data['id'] = max_id + 1
            notification_data['timestamp'] = notification_data.get('timestamp') or datetime.now().isoformat()
            notification_data['is_read'] = notification_data.get('is_read', False)
            
            # Insert into MongoDB
            result = self.notifications_collection.insert_one(notification_data)
            
            if not result.acknowledged:
                raise Exception("Failed to insert notification into database")
            
            # Verify the notification was created
            created_notification = self.notifications_collection.find_one({"_id": result.inserted_id})
            if not created_notification:
                raise Exception("Notification was not found after creation")
            
            # Return the notification without MongoDB _id
            return {k: v for k, v in created_notification.items() if k != '_id'}
        except Exception as e:
            print(f"❌ Error adding notification: {e}")
            raise
    
    def mark_notification_read(self, notification_id: int) -> Optional[Dict]:
        """Mark a notification as read"""
        result = self.notifications_collection.find_one_and_update(
            {"id": notification_id},
            {"$set": {"is_read": True}},
            return_document=ReturnDocument.AFTER
        )
        
        if not result:
            return None
            
        return {k: v for k, v in result.items() if k != '_id'}
    
    def mark_all_notifications_read(self, user_id: int) -> int:
        """Mark all notifications for a user as read"""
        result = self.notifications_collection.update_many(
            {"user_id": user_id, "is_read": False},
            {"$set": {"is_read": True}}
        )
        
        return result.modified_count
    
    def undo_user_deletion(self, user_id: int) -> Optional[Dict]:
        """Restore a deleted user"""
        # Find deleted user data
        deleted_user_data = self.deleted_users_collection.find_one({"user.id": user_id})
        if not deleted_user_data:
            return None
        
        # Restore user
        self.users_collection.insert_one(deleted_user_data["user"])
        
        # Restore attendance records if any
        if deleted_user_data["attendance"]:
            self.attendance_collection.insert_many(deleted_user_data["attendance"])
        
        # Restore todos if any
        if deleted_user_data["todos"]:
            self.todos_collection.insert_many(deleted_user_data["todos"])
        
        # Restore messages if any
        if "messages" in deleted_user_data and deleted_user_data["messages"]:
            self.messages_collection.insert_many(deleted_user_data["messages"])
        
        # Restore notifications if any
        if "notifications" in deleted_user_data and deleted_user_data["notifications"]:
            self.notifications_collection.insert_many(deleted_user_data["notifications"])
        
        # Remove from deleted users collection
        self.deleted_users_collection.delete_one({"user.id": user_id})
        
        # Return the restored data without MongoDB _id
        return {k: v for k, v in deleted_user_data.items() if k != '_id'}
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get a user by ID from active users"""
        user = self.users_collection.find_one({"id": user_id})
        if user:
            return {k: v for k, v in user.items() if k != '_id'}
        return None
    
    def get_deleted_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get a deleted user by ID from deleted_users collection"""
        deleted_user = self.deleted_users_collection.find_one({"user.id": user_id})
        if deleted_user:
            return {k: v for k, v in deleted_user.items() if k != '_id'}
        return None
    
    def permanently_remove_deleted_user(self, user_id: int) -> bool:
        """Permanently remove a user from deleted_users collection"""
        result = self.deleted_users_collection.delete_one({"user.id": user_id})
        return result.deleted_count > 0
    
    # Attendance operations
    def get_attendance(self, user_id: Optional[int] = None, month: Optional[int] = None, year: Optional[int] = None) -> List[Dict]:
        """Get attendance records with optional filters"""
        query = {}
        
        if user_id is not None:
            query["user_id"] = user_id
            
        if month is not None or year is not None:
            date_query = {}
            if year is not None:
                date_query["$regex"] = f"^{year}-"
            if month is not None:
                month_str = f"{month:02d}"
                if year is not None:
                    date_query["$regex"] = f"^{year}-{month_str}"
                else:
                    date_query["$regex"] = f"\\d{{4}}-{month_str}"
            query["date"] = date_query
            
        return list(self.attendance_collection.find(query, {"_id": 0}))
    
    def add_attendance(self, attendance_data: Dict) -> Dict:
        """Add or update attendance record for the given user and date"""
        try:
            # Check if record exists for this user and date
            existing_record = self.attendance_collection.find_one({
                "user_id": attendance_data["user_id"],
                "date": attendance_data["date"]
            })
            
            if existing_record:
                # Update existing record
                self.attendance_collection.update_one(
                    {"id": existing_record["id"]},
                    {"$set": {
                        "status": attendance_data["status"],
                        "notes": attendance_data.get("notes"),
                        "in_time": attendance_data.get("in_time", existing_record.get("in_time")),
                        "out_time": attendance_data.get("out_time", existing_record.get("out_time"))
                    }}
                )
                updated_record = self.attendance_collection.find_one({"id": existing_record["id"]})
                return {k: v for k, v in updated_record.items() if k != '_id'}
            else:
                # Create new record
                max_id = 0
                last_attendance = self.attendance_collection.find_one({}, sort=[("id", -1)])
                if last_attendance:
                    max_id = last_attendance["id"]
                
                attendance_data['id'] = max_id + 1
                
                # Insert into MongoDB
                result = self.attendance_collection.insert_one(attendance_data)
                
                if not result.acknowledged:
                    raise Exception("Failed to insert attendance record into database")
                
                # Verify the attendance record was created
                created_record = self.attendance_collection.find_one({"_id": result.inserted_id})
                if not created_record:
                    raise Exception("Attendance record was not found after creation")
                
                # Return the record without MongoDB _id
                return {k: v for k, v in created_record.items() if k != '_id'}
        except Exception as e:
            print(f"❌ Error adding/updating attendance record: {e}")
            raise
    
    def delete_attendance(self, attendance_id: int) -> Optional[Dict]:
        """Delete attendance record"""
        record = self.attendance_collection.find_one({"id": attendance_id})
        if not record:
            return None
            
        self.attendance_collection.delete_one({"id": attendance_id})
        return {k: v for k, v in record.items() if k != '_id'}
    
    # Todo operations
    def get_todos(self, user_id: Optional[int] = None) -> List[Dict]:
        """Get todos with optional user filter"""
        query = {}
        if user_id is not None:
            query["user_id"] = user_id
            
        return list(self.todos_collection.find(query, {"_id": 0}))
    
    def add_todo(self, todo_data: Dict) -> Dict:
        """Add a new todo with auto-generated ID"""
        try:
            # Auto-generate todo ID
            max_id = 0
            last_todo = self.todos_collection.find_one({}, sort=[("id", -1)])
            if last_todo:
                max_id = last_todo["id"]
            
            todo_data['id'] = max_id + 1
            if not todo_data.get('date_created'):
                todo_data['date_created'] = datetime.now().isoformat()
            
            # Insert into MongoDB
            result = self.todos_collection.insert_one(todo_data)
            
            if not result.acknowledged:
                raise Exception("Failed to insert todo into database")
            
            # Verify the todo was created
            created_todo = self.todos_collection.find_one({"_id": result.inserted_id})
            if not created_todo:
                raise Exception("Todo was not found after creation")
            
            # Return the todo without MongoDB _id
            return {k: v for k, v in created_todo.items() if k != '_id'}
        except Exception as e:
            print(f"❌ Error adding todo: {e}")
            raise
    
    def update_todo(self, todo_id: int, notes: str) -> Optional[Dict]:
        """Update todo notes"""
        todo = self.todos_collection.find_one({"id": todo_id})
        if not todo:
            return None
            
        self.todos_collection.update_one(
            {"id": todo_id},
            {"$set": {"notes": notes}}
        )
        
        updated_todo = self.todos_collection.find_one({"id": todo_id})
        return {k: v for k, v in updated_todo.items() if k != '_id'}
    
    def delete_todo(self, todo_id: int) -> Optional[Dict]:
        """Delete todo"""
        todo = self.todos_collection.find_one({"id": todo_id})
        if not todo:
            return None
            
        self.todos_collection.delete_one({"id": todo_id})
        return {k: v for k, v in todo.items() if k != '_id'}

# Create a singleton instance
mongodb = MongoDBManager()