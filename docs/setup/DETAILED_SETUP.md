# Detailed Setup Guide - Housing Authority Assistant

This comprehensive guide will walk you through setting up the Housing Authority Assistant from scratch, including all prerequisites, configuration options, and troubleshooting steps.

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Prerequisites Installation](#prerequisites-installation)
3. [Repository Setup](#repository-setup)
4. [Backend Configuration](#backend-configuration)
5. [Frontend Configuration](#frontend-configuration)
6. [Environment Variables](#environment-variables)
7. [Running the Application](#running-the-application)
8. [Verification & Testing](#verification--testing)
9. [Production Deployment](#production-deployment)
10. [Common Issues](#common-issues)

## 🖥️ System Requirements

### Minimum Requirements
- **OS**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Network**: Internet connection for API calls

### Software Requirements
- **Node.js**: Version 18.0.0 or higher
- **npm**: Version 8.0.0 or higher (comes with Node.js)
- **Python**: Version 3.10.0 or higher
- **Git**: Latest version
- **Code Editor**: VS Code, WebStorm, or similar (recommended)

## 🔧 Prerequisites Installation

### 1. Install Node.js

**Windows/macOS:**
1. Visit [nodejs.org](https://nodejs.org/)
2. Download the LTS version (18.x or higher)
3. Run the installer with default settings
4. Verify installation:
   ```bash
   node --version  # Should show v18.x.x or higher
   npm --version   # Should show 8.x.x or higher
   ```

**Linux (Ubuntu/Debian):**
```bash
# Install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installation
node --version
npm --version
```

### 2. Install Python

**Windows:**
1. Visit [python.org](https://python.org/downloads/)
2. Download Python 3.10+ installer
3. **Important**: Check "Add Python to PATH" during installation
4. Verify installation:
   ```cmd
   python --version  # Should show 3.10.x or higher
   pip --version     # Should be available
   ```

**macOS:**
```bash
# Using Homebrew (recommended)
brew install python@3.10

# Or download from python.org
# Verify installation
python3 --version
pip3 --version
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip
python3.10 --version
pip3 --version
```

### 3. Install Git

**Windows:** Download from [git-scm.com](https://git-scm.com/download/win)
**macOS:** `brew install git` or download from git-scm.com
**Linux:** `sudo apt install git`

Verify: `git --version`

## 📁 Repository Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/housing-authority-assistant.git
cd housing-authority-assistant

# Verify structure
ls -la
# Should see: python-backend/, ui/, docs/, README.md, etc.
```

### 2. Understand the Project Structure

```
housing-authority-assistant/
├── python-backend/           # FastAPI backend
│   ├── main.py              # Core agents and business logic
│   ├── api.py               # API endpoints and routing
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # Environment variables
├── ui/                      # Next.js frontend
│   ├── app/                 # App router pages
│   ├── components/          # React components
│   ├── lib/                 # Utilities and API calls
│   ├── public/              # Static assets
│   ├── package.json         # Node.js dependencies
│   └── next.config.mjs      # Next.js configuration
├── docs/                    # Documentation and assets
│   ├── screenshots/         # UI screenshots
│   ├── videos/              # Demo videos
│   └── setup/               # Setup guides
└── README.md                # Main documentation
```

## ⚙️ Backend Configuration

### 1. Navigate to Backend Directory

```bash
cd python-backend
```

### 2. Create Virtual Environment

**Windows:**
```cmd
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt.

### 3. Install Python Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify installation
pip list
# Should show: openai-agents, pydantic, fastapi, uvicorn, python-dotenv
```

### 4. Set Up Environment Variables

```bash
# Create environment file
cp .env.example .env

# Edit the .env file
nano .env  # or use your preferred editor
```

Add your OpenAI API key:
```env
# OpenAI API Configuration
OPENAI_API_KEY=sk-your-actual-openai-api-key-here

# Optional: Set log level for debugging
LOG_LEVEL=INFO
```

**Getting an OpenAI API Key:**
1. Visit [platform.openai.com](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. **Important**: Ensure you have access to the Agents SDK (may require special access)

### 5. Verify Backend Setup

```bash
# Test Python imports
python -c "
import main
import api
print('✅ All imports successful')
"

# Test environment loading
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('OPENAI_API_KEY')
print('✅ API key loaded') if key else print('❌ API key not found')
"
```

## 🎨 Frontend Configuration

### 1. Navigate to Frontend Directory

```bash
cd ../ui  # From python-backend directory
# OR
cd ui     # From project root
```

### 2. Install Node.js Dependencies

```bash
# Install all dependencies
npm install

# This will install:
# - Next.js framework
# - React and TypeScript
# - Tailwind CSS for styling
# - UI components and utilities
```

### 3. Verify Frontend Setup

```bash
# Check installed packages
npm list --depth=0

# Test TypeScript compilation
npx tsc --noEmit

# Test Next.js configuration
npm run build
```

## 🔐 Environment Variables

### Backend Variables (.env)

```env
# Required
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
API_HOST=0.0.0.0                 # Default: 0.0.0.0
API_PORT=8000                    # Default: 8000
```

### Frontend Variables (if needed)

Create `ui/.env.local` for frontend-specific variables:
```env
# API URL (only if different from default)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Analytics or other services
NEXT_PUBLIC_ANALYTICS_ID=your-analytics-id
```

## 🚀 Running the Application

### Method 1: Manual Start (Recommended for Development)

**Terminal 1 - Backend:**
```bash
cd python-backend
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd ui
npm run dev  # Development with hot reload
# OR
npm start    # Production build
```

### Method 2: Using Package Scripts

The project includes convenient scripts:

**Backend scripts:**
```bash
cd python-backend
# Development with auto-reload
python -m uvicorn api:app --reload

# Production
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

**Frontend scripts:**
```bash
cd ui
npm run dev          # Development server
npm run build        # Production build
npm run start        # Start production server
npm run lint         # Code linting
```

### Method 3: Docker (Advanced)

If you prefer containerization, create these files:

**Dockerfile.backend:**
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY python-backend/requirements.txt .
RUN pip install -r requirements.txt
COPY python-backend/ .
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Dockerfile.frontend:**
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY ui/package*.json ./
RUN npm ci
COPY ui/ .
RUN npm run build
CMD ["npm", "start"]
```

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

## ✅ Verification & Testing

### 1. Health Check

```bash
# Test backend health
curl http://localhost:8000/health
# Expected: {"status":"ok"}

# Test frontend
curl http://localhost:3000
# Expected: HTML response
```

### 2. API Testing

```bash
# Test chat endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I need to schedule an inspection"}'

# Expected: JSON response with agent routing
```

### 3. Frontend Testing

1. Visit http://localhost:3000
2. Verify the interface loads
3. Test chat functionality:
   - Type: "I need to schedule an inspection"
   - Should route to Inspection Agent
   - Agent panel should show active agent

### 4. End-to-End Testing

Test all major workflows:

**Inspection Scheduling:**
```
Input: "I need to schedule an HQS inspection for 123 Main St"
Expected: Routes to Inspection Agent, asks for date/time
```

**Multilingual Support:**
```
Input: "Necesito programar una inspección"
Expected: Responds in Spanish
```

**Guardrails:**
```
Input: "What's the weather today?"
Expected: Blocked with contact information
```

**Agent Handoffs:**
```
Input: "I need Section 8 landlord forms"
Expected: Routes to Landlord Services Agent
```

## 🌐 Production Deployment

### Environment Setup

**Production Backend:**
```bash
# Use production WSGI server
pip install gunicorn

# Run with multiple workers
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

**Production Frontend:**
```bash
# Build optimized version
npm run build

# Start production server
npm start
```

### Security Considerations

1. **API Key Security:**
   - Use environment variables, never commit keys
   - Consider using a secrets management service
   - Rotate keys regularly

2. **CORS Configuration:**
   - Update `python-backend/api.py` CORS settings
   - Restrict to your domain in production

3. **Rate Limiting:**
   - Implement rate limiting for API endpoints
   - Consider using Redis for session storage

4. **HTTPS:**
   - Use SSL certificates in production
   - Update all URLs to HTTPS

### Deployment Options

1. **Traditional Servers:**
   - Linux VPS with nginx reverse proxy
   - AWS EC2, Google Cloud VM, etc.

2. **Platform as a Service:**
   - **Backend**: Railway, Render, Fly.io
   - **Frontend**: Vercel, Netlify

3. **Container Platforms:**
   - Docker Swarm, Kubernetes
   - AWS ECS, Google Cloud Run

4. **Serverless:**
   - AWS Lambda (with serverless framework)
   - Vercel Functions

## 🔧 Advanced Configuration

### Custom Agent Development

To add new agents:

1. **Define Agent in main.py:**
```python
custom_agent = Agent[HousingAuthorityContext](
    name="Custom Agent",
    model="gpt-4o",
    handoff_description="Description here",
    instructions="Agent instructions",
    tools=[your_tools],
    input_guardrails=[guardrails],
)
```

2. **Add to API routing:**
```python
# In api.py _get_agent_by_name()
custom_agent.name: custom_agent,

# In _build_agents_list()
make_agent_dict(custom_agent),
```

3. **Add handoff relationships:**
```python
# In main.py
triage_agent.handoffs.append(custom_agent)
custom_agent.handoffs.append(triage_agent)
```

### Custom Tools

Create specialized tools:

```python
@function_tool(
    name_override="custom_tool",
    description_override="Your tool description"
)
async def custom_tool(
    context: RunContextWrapper[HousingAuthorityContext],
    parameter: str
) -> str:
    """Tool implementation."""
    # Your logic here
    return "Tool result"
```

### Guardrail Customization

Create custom guardrails:

```python
@guardrail_function(
    name="Custom Guardrail",
    instructions="Your guardrail logic"
)
async def custom_guardrail(
    agent: Agent,
    input: List[Dict[str, str]],
    context: RunContextWrapper[HousingAuthorityContext]
) -> str:
    # Guardrail logic
    return "approved"  # or "rejected"
```

## 🐛 Common Issues

### Installation Issues

**Python Virtual Environment:**
```bash
# If venv creation fails
python -m pip install --upgrade pip
python -m pip install virtualenv
python -m virtualenv .venv
```

**Node.js Permission Issues (Linux/macOS):**
```bash
# Fix npm permissions
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### Runtime Issues

**Backend Import Errors:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Frontend Build Errors:**
```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
npm run build
```

**API Connection Issues:**
- Check firewall settings
- Verify port 8000 is not blocked
- Confirm backend is running: `curl http://localhost:8000/health`

### Performance Issues

**Slow API Responses:**
- Check OpenAI API quota and limits
- Monitor network connectivity
- Consider implementing caching

**High Memory Usage:**
- Restart backend periodically
- Monitor for memory leaks
- Consider using gunicorn with multiple workers

## 📞 Support

For additional help:

1. **Check the logs:**
   - Backend: Terminal output where uvicorn is running
   - Frontend: Browser console (F12)

2. **Common solutions:**
   - Restart both backend and frontend
   - Clear browser cache
   - Check environment variables

3. **Get help:**
   - Open GitHub issue with error details
   - Include logs and system information
   - Contact: customerservice@smchousing.org

---

This completes the detailed setup guide. Follow these steps carefully, and you should have a fully functional Housing Authority Assistant system!