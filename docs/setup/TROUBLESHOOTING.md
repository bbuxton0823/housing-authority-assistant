# Troubleshooting Guide - Housing Authority Assistant

Common issues and solutions for the Housing Authority Assistant.

## 📋 Quick Diagnostics

Run this checklist first:

```bash
# 1. Check versions
node --version    # Should be 18.x.x+
python --version  # Should be 3.10.x+
git --version     # Any recent version

# 2. Check processes
curl http://localhost:8000/health  # Backend health
curl http://localhost:3000         # Frontend health

# 3. Check environment
cd python-backend && source .venv/bin/activate
python -c "import os; print('✅ API Key loaded' if os.getenv('OPENAI_API_KEY') else '❌ No API key')"
```

## 🚨 Common Issues

### Backend Issues

#### Issue: Backend Won't Start
```
Error: ModuleNotFoundError: No module named 'openai-agents'
```

**Solutions:**
```bash
# 1. Activate virtual environment
cd python-backend
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Upgrade pip and reinstall
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall

# 3. If still failing, recreate virtual environment
deactivate
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Issue: OpenAI API Key Error
```
Error: 'ascii' codec can't encode character '\u2011'
```

**Solutions:**
```bash
# 1. Check for Unicode characters in API key
cat .env | grep OPENAI_API_KEY
# Look for non-standard hyphens or spaces

# 2. Re-copy API key from OpenAI dashboard
# Ensure no hidden characters

# 3. Test API key format
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('OPENAI_API_KEY')
try:
    key.encode('ascii')
    print('✅ API key encoding valid')
except UnicodeEncodeError as e:
    print(f'❌ API key encoding error: {e}')
"
```

#### Issue: Import Errors
```
Error: ImportError: cannot import name 'Agent' from 'agents'
```

**Solutions:**
```bash
# 1. Check agents SDK version
pip show openai-agents

# 2. Update to latest version
pip install --upgrade openai-agents

# 3. Clear Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -delete

# 4. Restart terminal and reactivate venv
```

#### Issue: Port Already in Use
```
Error: [Errno 48] Address already in use
```

**Solutions:**
```bash
# 1. Find process using port 8000
lsof -i :8000
# OR on Windows:
netstat -ano | findstr :8000

# 2. Kill the process
kill -9 <PID>
# OR on Windows:
taskkill /PID <PID> /F

# 3. Use different port
python -m uvicorn api:app --port 8001
```

### Frontend Issues

#### Issue: Frontend Build Errors
```
Error: Module not found: Can't resolve '@/components/Chat'
```

**Solutions:**
```bash
# 1. Check file case sensitivity
ls ui/components/
# Ensure Chat.tsx exists (capital C)

# 2. Clear Next.js cache
cd ui
rm -rf .next node_modules/.cache
npm install

# 3. Rebuild
npm run build
```

#### Issue: TypeScript Errors
```
Error: Type 'string' is not assignable to type 'Date'
```

**Solutions:**
```bash
# 1. Check TypeScript configuration
cat ui/tsconfig.json

# 2. Fix type issues in components
# Update timestamp fields to use new Date() instead of Date.now()

# 3. Run type checking
npm run type-check
```

#### Issue: Proxy Connection Failed
```
Error: ECONNREFUSED 127.0.0.1:8000
```

**Solutions:**
```bash
# 1. Verify backend is running
curl http://localhost:8000/health

# 2. Check proxy configuration
cat ui/next.config.mjs
# Ensure destination points to correct backend URL

# 3. Test direct API call
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

### Installation Issues

#### Issue: Python Virtual Environment Creation Fails
```
Error: No module named venv
```

**Solutions:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-venv

# CentOS/RHEL
sudo yum install python3-venv

# macOS with Homebrew
brew install python@3.10

# Windows - reinstall Python with venv option checked
```

#### Issue: Node.js Permission Errors (Linux/macOS)
```
Error: EACCES: permission denied, mkdir '/usr/local/lib/node_modules'
```

**Solutions:**
```bash
# 1. Use Node Version Manager (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18

# 2. OR fix npm permissions
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

#### Issue: Git Clone Permission Denied
```
Error: Permission denied (publickey)
```

**Solutions:**
```bash
# 1. Use HTTPS instead of SSH
git clone https://github.com/username/housing-authority-assistant.git

# 2. OR set up SSH keys
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
# Add public key to GitHub account
```

## 🔧 Advanced Troubleshooting

### Memory Issues

#### High Memory Usage
```bash
# Monitor memory usage
htop  # Linux/macOS
# OR Task Manager on Windows

# Solutions:
# 1. Restart backend periodically
# 2. Reduce uvicorn workers
python -m uvicorn api:app --workers 1

# 3. Monitor for memory leaks
pip install memory-profiler
python -m memory_profiler main.py
```

#### Out of Memory Errors
```bash
# Increase system swap (Linux)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Reduce resource usage
# 1. Close unused applications
# 2. Use production build for frontend
npm run build && npm start
```

### Performance Issues

#### Slow API Responses
```bash
# 1. Check OpenAI API status
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# 2. Monitor network latency
ping api.openai.com

# 3. Add request logging
# In python-backend/api.py, add timing logs

# 4. Consider implementing caching
pip install redis
# Add Redis caching layer
```

#### Frontend Performance Issues
```bash
# 1. Use production build
npm run build
npm start

# 2. Enable compression
# Add compression middleware

# 3. Optimize bundle size
npm run build -- --analyze
```

### Database/Storage Issues

#### Context Not Persisting
```bash
# Check in-memory storage (development only)
# For production, implement persistent storage:

# 1. Add Redis
pip install redis
docker run -d -p 6379:6379 redis:alpine

# 2. OR use database
pip install sqlalchemy psycopg2-binary
# Implement proper session storage
```

### Security Issues

#### CORS Errors
```javascript
// Error: Access to fetch at 'http://localhost:8000/chat' 
// from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Solutions:**
```python
# In python-backend/api.py, update CORS settings:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### API Key Exposure
```bash
# 1. Check for committed keys
git log --grep="api.*key" -i
git log -p | grep -i "openai"

# 2. If found, rotate immediately
# Generate new key on OpenAI platform

# 3. Add to .gitignore
echo ".env" >> .gitignore
git add .gitignore
git commit -m "Add .env to gitignore"
```

## 🧪 Debugging Tools

### Backend Debugging

#### Enable Debug Logging
```python
# In python-backend/api.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Test Individual Components
```python
# Test agents directly
python -c "
import asyncio
from main import triage_agent, create_initial_context
from agents import Runner

async def test():
    ctx = create_initial_context()
    result = await Runner.run(
        triage_agent, 
        [{'content': 'I need help', 'role': 'user'}], 
        context=ctx
    )
    print(result)

asyncio.run(test())
"
```

#### Database Connection Test
```python
# If using external database
python -c "
import psycopg2  # or your database connector
try:
    conn = psycopg2.connect('your_connection_string')
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

### Frontend Debugging

#### Browser Console
```javascript
// Open browser dev tools (F12)
// Check for JavaScript errors
console.log('Frontend debugging enabled');

// Test API connection
fetch('/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({message: 'test'})
})
.then(r => r.json())
.then(console.log)
.catch(console.error);
```

#### Next.js Debug Mode
```bash
# Run with debug output
DEBUG=* npm run dev

# OR specific debug categories
DEBUG=next:* npm run dev
```

### Network Debugging

#### Capture HTTP Traffic
```bash
# Using curl with verbose output
curl -v -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# Using tcpdump (Linux/macOS)
sudo tcpdump -i lo0 -A port 8000

# Using Wireshark (GUI option)
# Filter: tcp.port == 8000
```

## 📊 Monitoring & Logs

### Log Locations

**Backend Logs:**
- Console output where uvicorn is running
- Add file logging if needed:
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('housing-authority.log'),
        logging.StreamHandler()
    ]
)
```

**Frontend Logs:**
- Browser console (F12)
- Terminal where `npm run dev` is running
- Add custom logging:
```javascript
// In your components
console.log('Debug info:', data);
```

### Health Monitoring

#### Create Health Check Script
```bash
#!/bin/bash
# health_check.sh

echo "Checking backend..."
BACKEND=$(curl -s http://localhost:8000/health | grep -o '"ok"' || echo "FAIL")

echo "Checking frontend..."
FRONTEND=$(curl -s http://localhost:3000 | grep -o 'Housing Authority' || echo "FAIL")

echo "Backend: $BACKEND"
echo "Frontend: $FRONTEND"

if [[ "$BACKEND" == "FAIL" || "$FRONTEND" == "FAIL" ]]; then
    echo "❌ Health check failed"
    exit 1
else
    echo "✅ All services healthy"
fi
```

#### Automated Monitoring
```bash
# Add to crontab for regular checks
crontab -e
# Add line:
# */5 * * * * /path/to/health_check.sh
```

## 🆘 Getting Help

### Before Asking for Help

1. **Check this guide** - search for your error message
2. **Check logs** - both backend and frontend
3. **Test basic functionality** - health endpoints
4. **Try basic solutions** - restart services, clear cache

### Information to Include

When reporting issues:

```bash
# System information
uname -a
python --version
node --version
npm --version

# Error details
# Copy exact error message
# Include relevant log snippets
# Describe steps to reproduce
```

### Getting Support

1. **GitHub Issues**: Most comprehensive help
   - Include system info and error logs
   - Tag with appropriate labels

2. **Email Support**: customerservice@smchousing.org
   - For urgent production issues

3. **Community Resources**:
   - OpenAI Agents SDK documentation
   - Next.js community forums
   - FastAPI documentation

### Creating Good Bug Reports

```markdown
## Bug Description
Brief description of the issue

## Environment
- OS: macOS 12.6
- Python: 3.10.8
- Node.js: 18.12.1
- Browser: Chrome 108.0.5359.124

## Steps to Reproduce
1. Start backend with `uvicorn api:app`
2. Send POST request to /chat
3. Observe error

## Expected Behavior
Should return valid JSON response

## Actual Behavior
Returns 500 error with stack trace

## Logs
```
[Include relevant log output]
```

## Additional Context
Any other relevant information
```

---

This troubleshooting guide covers the most common issues. If you encounter something not listed here, please contribute by adding it to help other users!