-- Drop authentication system tables for DB-GPT v0.8.0

-- Drop indexes
DROP INDEX IF EXISTS idx_sessions_expires_at;
DROP INDEX IF EXISTS idx_sessions_user_id;
DROP INDEX IF EXISTS idx_sessions_session_id;
DROP INDEX IF EXISTS idx_user_db_access_db_name;
DROP INDEX IF EXISTS idx_user_db_access_user_id;
DROP INDEX IF EXISTS idx_users_role_id;
DROP INDEX IF EXISTS idx_users_email;
DROP INDEX IF EXISTS idx_users_username;

-- Drop tables in reverse order due to foreign key dependencies
DROP TABLE IF EXISTS dbgpt_serve_auth_sessions;
DROP TABLE IF EXISTS dbgpt_serve_auth_user_db_access;
DROP TABLE IF EXISTS dbgpt_serve_auth_users;
DROP TABLE IF EXISTS dbgpt_serve_auth_roles; 