-- DocuSearch_AI Database Initialization
-- Creates required databases for Dify, n8n, and Plugin Daemon

-- Create n8n database
CREATE DATABASE n8n;

-- Create dify_plugin database for Plugin Daemon
CREATE DATABASE dify_plugin;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE n8n TO postgres;
GRANT ALL PRIVILEGES ON DATABASE dify_plugin TO postgres;
