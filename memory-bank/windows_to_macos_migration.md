# Windows to macOS Migration Guide

This document outlines the process and considerations for migrating the Freya AI Companion project from Windows with WSL to macOS.

## Environment Differences

### File System
- **Windows + WSL**: Used path mapping with `/mnt/c/Users/...` for Windows paths
- **macOS**: Uses standard Unix paths `/Users/blackcanopy/...`

### Python Environment
- **Windows**: Used Windows Python from WSL (`venv/Scripts/python.exe`)
- **macOS**: Uses native macOS Python with standard Unix paths (`venv/bin/python`)

### Command Differences
- **Windows + WSL**: Required quoted paths for spaces and Windows executables
- **macOS**: Uses standard Unix path conventions without special handling

## Migration Steps

1. **Repository Transfer**
   - Cloned repository to macOS system
   - Updated local configuration files

2. **Python Virtual Environment**
   - Created new virtual environment on macOS
   - Installed dependencies using `pip install -r requirements.txt`

3. **Database Setup**
   - Configured PostgreSQL on macOS
   - Updated connection string in environment variables
   - Ran migrations to ensure schema parity

4. **Testing After Migration**
   - Ran all tests to verify functionality
   - Verified API endpoints work correctly
   - Confirmed database access and operations

## Updated Development Commands

### Backend Commands (macOS)
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the backend
python -m uvicorn app.main:app --reload
# Or use the helper script:
python scripts/run_server.py

# Database setup
python scripts/setup_test_db.py  # Create test database
python -m alembic upgrade head   # Run migrations

# Testing
python -m pytest tests/ -v       # Run all tests
python -m pytest tests/test_api.py -k test_health  # Specific test

# Quick test scripts
python scripts/test_all.py       # Comprehensive integration tests
python scripts/create_test_user.py  # Create test user
python scripts/test_chat_simple.py  # Test chat endpoint
```

### Quick Testing Workflow
```bash
# Terminal 1: Start the server
cd /Users/blackcanopy/Documents/Projects/new-freya-who-this
source venv/bin/activate
python scripts/run_server.py

# Terminal 2: Run tests
cd /Users/blackcanopy/Documents/Projects/new-freya-who-this
source venv/bin/activate
python scripts/test_all.py  # Quick integration tests
```

### Testing Server-Sent Events (SSE)
```bash
# Terminal 1: Start the server
cd /Users/blackcanopy/Documents/Projects/new-freya-who-this
source venv/bin/activate
python scripts/run_server.py

# Terminal 2: Create test user (if not already created)
cd /Users/blackcanopy/Documents/Projects/new-freya-who-this
source venv/bin/activate
python scripts/create_test_user_direct.py

# Terminal 3: Test SSE endpoint
cd /Users/blackcanopy/Documents/Projects/new-freya-who-this
source venv/bin/activate
python scripts/test_sse_endpoint.py  # Basic SSE test
python scripts/test_sse_raw.py  # Detailed event inspection
```

## Troubleshooting

1. **Virtual Environment Issues**
   - If encountering issues with the existing virtual environment, create a new one:
     ```bash
     python -m venv venv
     source venv/bin/activate
     pip install -r requirements.txt
     ```

2. **PostgreSQL Configuration**
   - macOS PostgreSQL may use different default settings
   - Update `.env` file with correct connection string
   - Verify PostgreSQL service is running: `brew services list`

3. **Path-Related Issues**
   - Update any hardcoded Windows paths in configuration files
   - Check for Windows-specific path separators (`\`) in code

4. **Permissions Issues**
   - Ensure proper file permissions for executables and scripts
   - Use `chmod +x` for any scripts that need to be executable

## Additional Considerations

1. **Development Tools**
   - macOS offers native terminal with better Unix compatibility
   - Consider using macOS-native PostgreSQL tools and clients
   - VS Code and other development tools work similarly across platforms

2. **Performance Improvements**
   - Native Unix environment may offer better performance than WSL
   - Direct filesystem access without WSL translation layer
   - Native Python performance may be improved

This migration guide will be updated as additional platform-specific considerations arise during development.
