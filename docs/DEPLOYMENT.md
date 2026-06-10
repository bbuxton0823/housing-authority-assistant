# Deploying to Cloudflare

The app has two parts with different hosting needs:

- **Frontend (Next.js)** → runs great on **Cloudflare Pages**
- **Backend (Python/FastAPI)** → cannot run on Cloudflare Workers (Python agents SDK needs a real Python runtime). Two good options below, both keep everything on your Cloudflare account/domain.

## Option A — Demo today: Pages + Cloudflare Tunnel (15 minutes)

Run the backend on your Mac (or any machine) and expose it through your Cloudflare account with a tunnel. Nothing leaves your control; great for live demos.

```bash
# 1. Backend running locally
cd python-backend
python -m uvicorn api:app --port 8000

# 2. Tunnel it through your Cloudflare account
brew install cloudflared
cloudflared tunnel login                       # one-time, picks your CF account/zone
cloudflared tunnel create haa-backend
cloudflared tunnel route dns haa-backend api.yourdomain.com
cloudflared tunnel run --url http://localhost:8000 haa-backend
# -> backend is now live at https://api.yourdomain.com

# 3. Frontend on Cloudflare Pages
cd ui
npm install
npx @cloudflare/next-on-pages                  # builds for Pages
npx wrangler pages project create housing-authority-assistant
npx wrangler pages deploy .vercel/output/static --project-name housing-authority-assistant
```

Then in the Cloudflare dashboard → Pages → your project → Settings → Environment variables, set:

| Variable | Value |
| --- | --- |
| `BACKEND_URL` | `https://api.yourdomain.com` |

(The Next.js rewrites proxy `/chat`, `/voice/*`, `/admin/*`, `/health` to `BACKEND_URL` server-side on the edge, so there are no CORS issues and the browser only ever talks to your Pages domain.)

Quick variant without a custom domain: `cloudflared tunnel --url http://localhost:8000` gives a temporary `*.trycloudflare.com` URL — fine for a one-off demo.

## Option B — Always-on: hosted backend behind Cloudflare

Host the backend on a small Python host (Render, Fly.io, Railway, or a $5 VPS) and put Cloudflare DNS/proxy in front:

```bash
# Render example: create a Web Service from the repo with
#   Root directory: python-backend
#   Build: pip install -r requirements.txt
#   Start: uvicorn api:app --host 0.0.0.0 --port $PORT
# Environment: copy the contents of python-backend/.env into Render's env settings
```

Point `api.yourdomain.com` (proxied/orange-cloud) at the host, deploy the frontend to Pages exactly as in Option A, and set `BACKEND_URL` the same way.

## Taking live phone calls (Twilio number +1 571 626 7576)

The backend already speaks TwiML; the number just needs to point at it.

1. Expose the backend publicly (either tunnel works):
   ```bash
   ngrok http 8000                      # or: cloudflared tunnel --url http://localhost:8000
   ```
2. In `python-backend/.env`, set `WEBHOOK_BASE_URL=https://<your-tunnel-url>` and restart the backend.
3. In the Twilio console -> Phone Numbers -> Active numbers -> your number -> Configure:

   | Setting | Value |
   | --- | --- |
   | Voice: "A call comes in" | **POST** `https://<your-tunnel-url>/webhooks/voice/incoming` |
   | Voice: "Call status changes" | **POST** `https://<your-tunnel-url>/webhooks/voice/status` |

   (The current config points to an old ngrok URL with path `/webhook/voice` - note the path here is different: `/webhooks/voice/incoming`.)
4. Call +1 571 626 7576. The triage flow answers, routes through the live agents, and says "transfer ... representative" requests get `<Dial>`ed to `HOUSING_OFFICE_PHONE`.

Notes: the free ngrok URL changes on every restart - re-update both places. SMS is not implemented (the number's current `/webhook/sms` setting can be cleared).

**ElevenLabs voices on phone calls:** the backend renders every reply to MP3 with your ElevenLabs key (per-agent voices) and serves it to Twilio via `<Play>` - so the same voices callers hear on the web work on the phone. No ElevenLabs key goes into Twilio, and no ConversationRelay/AI-ML addendum is required. Requirements: `WEBHOOK_BASE_URL` must be set (Twilio fetches the audio from it) and `ELEVENLABS_API_KEY` valid; if synthesis ever fails the call automatically falls back to Twilio Polly. Set `PHONE_TTS=polly` to force the fallback. Generated audio is cached in `python-backend/voice_cache/` (gitignored). ConversationRelay (`ttsProvider="ElevenLabs"`) remains an optional future upgrade for lower latency, but it requires accepting Twilio's Predictive/Generative AI-ML Features Addendum - that's an agreement for you to accept (or not) in Voice -> Settings -> General; nothing in this app needs it.

## Pre-launch checklist (either option)

- [ ] `ALLOWED_ORIGINS` env on the backend set to your Pages URL (only needed if you skip the rewrites and call the API cross-origin)
- [ ] **Protect `/admin/routing`** — put Cloudflare Access (Zero Trust) in front of `api.yourdomain.com/admin/*`, or add an auth token. It edits where caller PII gets emailed.
- [ ] Conversation state is in-memory — one backend instance only (fine for a pilot; move `InMemoryConversationStore` to KV/Redis for scale)
- [ ] SMTP settings in the backend env if you want referral emails to actually send
- [ ] Rotate the OpenAI/ElevenLabs keys before public launch (they were shared in chat during development)
- [ ] Cloudflare rate limiting rule on `/chat` (e.g., 20 req/min per IP) — every request costs OpenAI tokens

## Demo assets

`docs/demo/` contains ready-to-share material produced from a real end-to-end run:
`demo_call.mp3` (2:05 call), `demo_call_waveform.mp4` (video), `demo_call_waveform.gif`
(short loop), `demo_call_waveform.png` (voice-wave still), and `demo_call_transcript.md`.
