-- Authentication system tables for DB-GPT v0.8.0

-- Create roles table
CREATE TABLE IF NOT EXISTS dbgpt_serve_auth_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(64) NOT NULL UNIQUE,
    description VARCHAR(255),
    permissions TEXT,
    gmt_created DATETIME DEFAULT CURRENT_TIMESTAMP,
    gmt_modified DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_role_name UNIQUE (name)
);

-- Create users table
CREATE TABLE IF NOT EXISTS dbgpt_serve_auth_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(128) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(64) NOT NULL,
    full_name VARCHAR(255),
    avatar_url VARCHAR(512),
    is_active BOOLEAN DEFAULT 1,
    is_superuser BOOLEAN DEFAULT 0,
    role_id INTEGER NOT NULL,
    last_login DATETIME,
    gmt_created DATETIME DEFAULT CURRENT_TIMESTAMP,
    gmt_modified DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_username UNIQUE (username),
    CONSTRAINT uk_email UNIQUE (email),
    FOREIGN KEY (role_id) REFERENCES dbgpt_serve_auth_roles(id)
);

-- Create user database access table
CREATE TABLE IF NOT EXISTS dbgpt_serve_auth_user_db_access (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    db_name VARCHAR(255) NOT NULL,
    granted_by INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    gmt_created DATETIME DEFAULT CURRENT_TIMESTAMP,
    gmt_modified DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_user_db_access UNIQUE (user_id, db_name),
    FOREIGN KEY (user_id) REFERENCES dbgpt_serve_auth_users(id),
    FOREIGN KEY (granted_by) REFERENCES dbgpt_serve_auth_users(id)
);

-- Create sessions table
CREATE TABLE IF NOT EXISTS dbgpt_serve_auth_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    jwt_token TEXT NOT NULL,
    expires_at DATETIME NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    user_agent VARCHAR(512),
    ip_address VARCHAR(45),
    gmt_created DATETIME DEFAULT CURRENT_TIMESTAMP,
    gmt_modified DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES dbgpt_serve_auth_users(id)
);

-- Insert default roles
INSERT OR IGNORE INTO dbgpt_serve_auth_roles (name, description, permissions) VALUES 
('user', 'Regular user with chat and explore access', '{"chat": true, "explore": true, "construct": false, "admin": false}'),
('admin', 'Administrator with full access', '{"chat": true, "explore": true, "construct": true, "admin": true}');

-- Insert default admin user (password: dbgpt2024)
-- Salt: 1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
-- Hash: pbkdf2_hmac('sha256', 'dbgpt2024', salt, 100000)
INSERT OR IGNORE INTO dbgpt_serve_auth_users (
    username, 
    email, 
    password_hash, 
    salt, 
    full_name, 
    is_superuser, 
    role_id
) VALUES (
    'admin',
    'admin@dbgpt.com',
    'f8c2e6b8c5a4d3e9f7b1a2c8d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6',
    '1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
    'Administrator',
    1,
    (SELECT id FROM dbgpt_serve_auth_roles WHERE name = 'admin')
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_username ON dbgpt_serve_auth_users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON dbgpt_serve_auth_users(email);
CREATE INDEX IF NOT EXISTS idx_users_role_id ON dbgpt_serve_auth_users(role_id);
CREATE INDEX IF NOT EXISTS idx_user_db_access_user_id ON dbgpt_serve_auth_user_db_access(user_id);
CREATE INDEX IF NOT EXISTS idx_user_db_access_db_name ON dbgpt_serve_auth_user_db_access(db_name);
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON dbgpt_serve_auth_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON dbgpt_serve_auth_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON dbgpt_serve_auth_sessions(expires_at); 