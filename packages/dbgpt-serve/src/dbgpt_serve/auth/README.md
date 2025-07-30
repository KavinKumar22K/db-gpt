# DB-GPT Authentication System

This package provides a comprehensive authentication and authorization system for DB-GPT, enabling user-based access control, role-based permissions, and secure session management.

## Features

- **User Authentication**: Login/logout with JWT tokens and session management
- **User Registration**: Self-service user registration with email validation
- **Role-Based Access Control**: User and admin roles with different permissions
- **Database Access Control**: Admin-managed database access permissions per user
- **File Isolation**: User-specific file uploads and storage
- **Chat History Isolation**: User-specific chat sessions and history
- **Session Management**: Secure session handling with expiration

## Architecture

### Database Models

- **UserEntity**: User accounts with authentication credentials
- **RoleEntity**: Roles with permission definitions (user, admin)
- **UserDatabaseAccessEntity**: Per-user database access permissions
- **SessionEntity**: Active user sessions with JWT tokens

### API Endpoints

- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/me` - Get current user info
- `GET /api/v1/auth/users` - Get all users (admin only)
- `POST /api/v1/auth/database-access/grant` - Grant database access (admin only)
- `POST /api/v1/auth/database-access/revoke` - Revoke database access (admin only)
- `GET /api/v1/auth/database-access` - Get user's accessible databases

## Role-Based Permissions

### User Role
- **chat**: Access to chat functionality
- **explore**: Access to explore/query functionality
- **construct**: No access (false)
- **admin**: No access (false)

### Admin Role
- **chat**: Access to chat functionality
- **explore**: Access to explore/query functionality
- **construct**: Access to construct/build functionality
- **admin**: Access to admin functionality

## Default Credentials

- **Username**: admin
- **Password**: dbgpt2024
- **Email**: admin@dbgpt.com

> **Security Note**: Change the default admin password immediately in production!

## User Isolation

### Chat History
- Each user only sees their own chat conversations
- Chat history is filtered by `user_name`
- Users cannot access other users' conversations

### File Uploads
- Files are stored in user-specific buckets (`bucket_username`)
- Users can only access their own uploaded files
- File metadata includes user ownership information

### Database Access
- Users only have access to databases explicitly granted by admins
- Superusers have access to all databases
- Database connections check user permissions before allowing access

## Frontend Integration

### Login Page
- Located at `/login`
- Supports both login and registration
- Handles session cookies and local storage

### Role-Based Routing
- Construct functionality is hidden from non-admin users
- Admin interface is available at `/admin/users`
- Navigation adapts based on user permissions

### Authentication Flow
1. User logs in via `/login`
2. Backend validates credentials and creates session
3. Frontend stores user info and session cookie
4. Subsequent requests include session cookie for authentication
5. Backend validates session and user permissions for each request

## Configuration

### JWT Settings
- **Secret Key**: Configurable via `jwt_secret_key`
- **Algorithm**: HS256 (configurable)
- **Expiration**: 24 hours (configurable)

### Session Settings
- **Expiration**: 30 days (configurable)
- **Cookie Name**: `dbgpt_auth_session`

### Password Requirements
- **Minimum Length**: 8 characters (configurable)
- **Hashing**: PBKDF2-HMAC-SHA256 with 100,000 iterations

## Installation

1. **Database Migration**: Run the SQL migration scripts in `assets/schema/upgrade/v0_8_0/`
2. **Service Registration**: The auth service is automatically registered in the component initialization
3. **Frontend Routes**: The login page and admin interface are included in the web package

## API Usage Examples

### User Registration
```python
import requests

response = requests.post('/api/v1/auth/register', json={
    'username': 'newuser',
    'email': 'user@example.com',
    'password': 'securepassword',
    'full_name': 'New User'
})
```

### User Login
```python
response = requests.post('/api/v1/auth/login', json={
    'username': 'newuser',
    'password': 'securepassword'
})

if response.json()['success']:
    session_id = response.json()['data']['session_id']
    # Use session_id for subsequent requests
```

### Grant Database Access (Admin)
```python
response = requests.post('/api/v1/auth/database-access/grant', 
    json={
        'user_id': 2,
        'db_name': 'production_db'
    },
    cookies={'dbgpt_auth_session': admin_session_id}
)
```

## Security Considerations

1. **Password Security**: Passwords are hashed with PBKDF2-HMAC-SHA256
2. **Session Security**: Sessions expire automatically and can be invalidated
3. **Database Isolation**: Users cannot access unauthorized databases
4. **File Isolation**: User files are stored in separate buckets
5. **Role Validation**: All admin operations validate user permissions

## Migration from Mock Auth

The system is designed to be backward compatible with the existing mock authentication:

1. If auth service is not available, falls back to mock authentication
2. Existing API endpoints continue to work with the new auth middleware
3. Gradual migration path allows testing and rollback if needed

## Troubleshooting

### Common Issues

1. **Session Expired**: Users need to log in again
2. **Permission Denied**: Check user role and permissions
3. **Database Connection Failed**: Verify user has database access
4. **File Upload Failed**: Check user authentication and file permissions

### Logs

Authentication events are logged with appropriate levels:
- INFO: Successful logins, permission grants
- WARNING: Failed authentication attempts, permission denials
- ERROR: System errors, database connection issues 