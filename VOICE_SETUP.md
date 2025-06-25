# Voice Integration Setup for Mac

## Step 1: Get Your ElevenLabs API Key

1. Visit https://elevenlabs.io
2. Sign up or create an account (free tier available)
3. Go to your Profile/Settings page
4. Find and copy your API key (starts with letters/numbers)

## Step 2: Set Up API Key (Mac-Safe Method)

**Option A: Direct File Edit**
1. Open the `.env` file in a text editor:
   ```bash
   nano .env
   ```

2. Replace `your-elevenlabs-api-key-here` with your actual API key:
   ```
   ELEVENLABS_API_KEY=your-actual-api-key-here
   ```

3. Save and exit (Ctrl+X, then Y, then Enter)

**Option B: Command Line (if you have the key ready)**
```bash
# Replace YOUR_ACTUAL_KEY with your real API key
echo "ELEVENLABS_API_KEY=YOUR_ACTUAL_KEY" >> .env
```

## Step 3: Test the Setup

Run this command to test your API key:

```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('ELEVENLABS_API_KEY')
print(f'✅ API key found: {key[:10]}...' if key and len(key) > 10 else '❌ No valid API key found')
"
```

## Step 4: Start the Voice-Enabled Assistant

1. **Start the backend with voice support:**
   ```bash
   cd python-backend
   python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

2. **In a new terminal, start the frontend:**
   ```bash
   cd ui
   npm run dev
   ```

3. **Visit the app:**
   Open http://localhost:3000

## Voice Features Available

- **Agent-specific voice characteristics**
- **Natural speech optimization** 
- **Voice-guided web navigation**
- **Multilingual support** (English, Spanish, Mandarin)
- **Read-only page guidance** (no form filling)

## Troubleshooting

**If you get Unicode errors:**
- This is common with Mac Terminal copy/paste
- Use the setup script: `python setup_voice_keys.py`
- Or manually type the API key instead of pasting

**If voice doesn't work:**
- Check your ElevenLabs account has credits
- Verify the API key is correct
- Check the logs for specific error messages

**If navigation doesn't work:**
- Make sure Playwright browsers are installed: `python -m playwright install`
- Check that the Housing Authority website is accessible

## Available Voice Commands

Once running, you can test these phrases:

- "I need to schedule an inspection" → Navigates to scheduling page
- "How do I apply for housing assistance?" → Goes to application page  
- "What are your office hours?" → Shows contact information
- "Tell me about payment options" → Landlord payment information

The assistant will speak responses and automatically guide you to relevant web pages!