# Office Attendance Tracking System - Backend API

A robust FastAPI-based backend service for managing office attendance, user management, and task tracking. This system provides a comprehensive REST API for the Office Attendance Tracking application.

## 🚀 Live Deployment

**Hosted URL:** https://office-attendance-track-backend.onrender.com

## 🛠️ Technology Stack

- **Framework:** FastAPI (Python web framework)
- **Database:** MongoDB Atlas (Cloud database)
- **Authentication:** Role-based access control (Admin/User)
- **API Documentation:** Auto-generated with FastAPI
- **Deployment:** Render (Web Service)
- **CORS:** Cross-Origin Resource Sharing enabled

## 📦 Dependencies

- `fastapi==0.95.2` - Web framework
- `uvicorn==0.22.0` - ASGI server
- `python-multipart==0.0.6` - Form data handling
- `pydantic==1.10.16` - Data validation
- `pymongo==4.6.1` - MongoDB driver
- `python-dotenv==1.0.0` - Environment variables


## 🔐 Authentication & Authorization

### Default Credentials

#### Admin User
- **Email:** admin@company.com
- **Password:** admin123
- **Role:** admin

#### Regular Users
- **Email:** user1@company.com, user2@company.com, user3@company.com, user4@company.com, user5@company.com
- **Password:** user123
- **Role:** user

### Role-Based Access Control
- **Admin Role:** Full access to all features including user management
- **User Role:** Limited access to personal attendance and todos

## 📡 API Endpoints

### Authentication
- `POST /api/login` - User authentication with role validation
- `GET /api/logout` - User logout

### User Management (Admin Only)
- `GET /api/users` - Get all users
- `POST /api/users` - Create new user
- `DELETE /api/users/{user_id}` - Soft delete user
- `POST /api/users/{user_id}/permanent-delete` - Permanently delete user
- `POST /api/users/{user_id}/undo` - Restore deleted user

### Attendance Management
- `GET /api/attendance` - Get attendance records (filtered by user, month, year)
- `POST /api/attendance` - Mark attendance
- `DELETE /api/attendance/{attendance_id}` - Delete attendance record
- `GET /api/attendance/stats` - Get attendance statistics
- `POST /api/attendance/force-sync` - Force sync attendance data

### Todo Management
- `GET /api/todos` - Get todos (filtered by user)
- `POST /api/todos` - Create new todo
- `PUT /api/todos/{todo_id}` - Update todo
- `DELETE /api/todos/{todo_id}` - Delete todo

## 🔧 Key Features

### Admin Features
1. **User Management**
   - View all users in the system
   - Create new users with role assignment
   - Soft delete users (recoverable)
   - Permanently delete users
   - Restore deleted users

2. **Attendance Oversight**
   - View attendance records for all users
   - Filter attendance by user, month, and year
   - Access attendance statistics
   - Edit attendance records
   - Force sync attendance data

3. **Todo Management**
   - View all todos in the system
   - Create, edit, and delete todos for any user
   - Monitor task completion

### User Features
1. **Personal Attendance**
   - Mark daily attendance (present/absent)
   - View personal attendance history
   - Add notes to attendance records
   - View attendance statistics

2. **Personal Todo Management**
   - Create personal todos
   - Edit and delete own todos
   - Track task completion

## 🗄️ Database Schema

### Collections
1. **users** - User accounts and profiles
2. **attendance** - Daily attendance records
3. **todos** - Task management
4. **deleted_users** - Soft-deleted users (for recovery)

### Data Relationships
- Attendance records are linked to users via `user_id`
- Todos are linked to users via `user_id`
- All records maintain referential integrity

## 🚀 Deployment

### Render Configuration
- **Service Type:** Web Service
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

## 🔒 Security Features

- **CORS Protection:** Configured for cross-origin requests
- **Input Validation:** Pydantic models for request validation
- **Role Validation:** Server-side role checking
- **Error Handling:** Comprehensive error responses
- **Database Security:** MongoDB Atlas with connection string authentication


## 🐛 Error Handling

- **HTTP Status Codes:** Proper status code responses
- **Error Messages:** User-friendly error descriptions
- **Logging:** Comprehensive server-side logging
- **Graceful Degradation:** App continues running even if MongoDB fails

## 📝 API Documentation

Access interactive API documentation at:
- **Swagger UI:** `/docs`
- **ReDoc:** `/redoc`

 
**Status:** Production Ready
