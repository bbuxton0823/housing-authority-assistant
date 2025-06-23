# Videos Directory

This directory contains demonstration videos for the Housing Authority Assistant.

## Video Support in GitHub

GitHub supports these video formats in repositories:
- **MP4** (recommended)
- **MOV** 
- **WEBM**

**File size limit**: 10MB per file

## Available Videos

### 1. Inspection Reschedule Demo (`inspection-reschedule-demo.mov`) ✅ **AVAILABLE**
**Duration**: ~2 minutes  
**File Size**: 11MB (stored locally - exceeds GitHub 10MB limit)
**Content**:
- Demonstrates the enhanced inspection reschedule system
- Shows intelligent parsing of user input (T-code + date + reason)
- Displays improved user experience with 9AM-4PM time blocks
- Shows proper handling of reschedule reasons like "I'm sick"
- Demonstrates HPS worker notification process

**Key Features Shown**:
- Complex input parsing: "T1234567 7/30/2025"
- Reason collection: "I'm sick"
- Professional confirmation messaging
- Contact information forwarding to HPS

**Note**: Video is currently stored in `docs/videos/` but not committed to git due to file size. Consider compressing or using Git LFS for repository inclusion.

### 2. Complete System Demo (`housing-authority-demo.mp4`)
**Duration**: 3-5 minutes
**Content**:
- Quick overview of the interface
- Demonstration of all 5 agents
- Show agent handoffs in action
- Multilingual capabilities
- Guardrail protection

**Script Outline**:
```
0:00-0:30 - Introduction and interface overview
0:30-1:30 - Inspection scheduling demo
1:30-2:30 - Landlord services and HPS agent
2:30-3:30 - Multilingual support (Spanish example)
3:30-4:00 - Guardrails demonstration
4:00-4:30 - Summary and key features
```

### 3. Agent Handoffs Demo (`agent-handoffs.mp4`)
**Duration**: 2-3 minutes
**Content**:
- Focus on the agent panel
- Show triage routing
- Demonstrate each agent's specialization
- Context passing between agents

### 4. Multilingual Features (`multilingual-demo.mp4`)
**Duration**: 1-2 minutes
**Content**:
- English to Spanish conversation
- Auto-detection demonstration
- Context persistence
- Cultural appropriateness

### 5. Setup Walkthrough (`setup-guide.mp4`)
**Duration**: 5-10 minutes
**Content**:
- Step-by-step installation
- Environment setup
- First run
- Common issues and solutions

## Recording Guidelines

### Technical Requirements
- **Resolution**: 1920x1080 (1080p) minimum
- **Frame Rate**: 30 FPS recommended
- **Audio**: Clear narration with good microphone
- **Format**: MP4 with H.264 encoding for best compatibility

### Content Guidelines
- **Clear narration**: Explain what you're doing
- **Steady pace**: Not too fast, allow viewers to follow
- **Show results**: Demonstrate actual functionality
- **No sensitive data**: Use example data only
- **Professional**: Clean background, good lighting

## Recording Tools

### Screen Recording Software

**Free Options**:
- **OBS Studio** (Windows/macOS/Linux) - Professional, open source
- **QuickTime Player** (macOS) - Built-in, simple
- **Windows Game Bar** (Windows) - Built-in
- **SimpleScreenRecorder** (Linux) - Lightweight

**Paid Options**:
- **Camtasia** - Professional editing features
- **ScreenFlow** (macOS) - Professional with editing
- **Loom** - Easy web-based recording

### Audio Recording
- **Built-in microphone**: Usually adequate for demos
- **External microphone**: Better quality for professional videos
- **Noise cancellation**: Use quiet environment or software filtering

## Video Creation Process

### 1. Preparation
```bash
# Ensure system is ready
npm run build          # Build frontend
uvicorn api:app --reload  # Start backend

# Clean up desktop
# Close unnecessary applications
# Prepare demo script/outline
```

### 2. Recording Setup
- **Browser**: Use incognito/private mode for clean interface
- **Zoom level**: 100% for consistent viewing
- **Window size**: Full screen or large window
- **Demo data**: Prepare realistic but safe examples

### 3. Recording Checklist
- [ ] Audio levels tested
- [ ] Screen resolution correct
- [ ] Demo script ready
- [ ] Browser bookmarks hidden
- [ ] Notifications disabled
- [ ] Demo data prepared

### 4. Post-Production
- **Editing**: Trim start/end, remove mistakes
- **Audio**: Normalize levels, remove background noise
- **Compression**: Optimize for 10MB GitHub limit
- **Quality check**: Test playback on different devices

## Video Compression

To fit GitHub's 10MB limit:

### Using FFmpeg
```bash
# Install FFmpeg first
# Then compress video:

ffmpeg -i input.mp4 -vcodec libx264 -crf 28 -preset fast \
  -vf "scale=1920:1080" -acodec aac -b:a 128k output.mp4

# For smaller files:
ffmpeg -i input.mp4 -vcodec libx264 -crf 32 -preset fast \
  -vf "scale=1280:720" -acodec aac -b:a 96k output.mp4
```

### Using Online Tools
- **HandBrake** (free, cross-platform)
- **CloudConvert** (online)
- **Video Compressor** (various online tools)

### Compression Settings
```
Resolution: 1920x1080 (or 1280x720 for smaller files)
Frame Rate: 30 FPS
Video Codec: H.264
Audio Codec: AAC
Bitrate: Variable (target final size < 10MB)
```

## Adding Videos to Repository

### 1. File Naming
Use exact names referenced in documentation:
- `housing-authority-demo.mp4`
- `agent-handoffs.mp4`
- `multilingual-demo.mp4`
- `setup-guide.mp4`

### 2. Upload Process
```bash
# Add videos to git
git add docs/videos/your-video.mp4
git commit -m "Add demonstration video"

# Note: Large files may take time to upload
git push origin main
```

### 3. Git LFS (for larger files)
If videos exceed 10MB, consider Git LFS:

```bash
# Install Git LFS
git lfs install

# Track video files
git lfs track "*.mp4"
git add .gitattributes

# Add and commit as normal
git add docs/videos/large-video.mp4
git commit -m "Add large demo video via LFS"
```

## Alternative Video Hosting

For videos larger than 10MB:

### YouTube
1. Upload to YouTube
2. Create thumbnail
3. Link in documentation:
```markdown
[![Video Title](thumbnail.png)](https://youtube.com/watch?v=VIDEO_ID)
```

### Vimeo
Similar to YouTube, often preferred for professional content.

### GitHub Releases
1. Create a release
2. Attach video files as assets
3. Link to release assets in documentation

## Video Accessibility

### Captions/Subtitles
- **Auto-generated**: Use YouTube's auto-captioning
- **Manual**: Create SRT files for accuracy
- **Multiple languages**: Provide Spanish captions for multilingual content

### Descriptions
Provide text descriptions of video content for accessibility:

```markdown
## Video Description
This 5-minute video demonstrates the Housing Authority Assistant:
1. Interface overview showing agent panel and chat interface
2. Inspection scheduling workflow with agent handoff
3. Multilingual support with Spanish conversation
4. Guardrail protection against off-topic requests
```

## Testing Videos

Before committing:

1. **Playback test**: Ensure video plays correctly
2. **Audio check**: Verify audio is clear and synchronized
3. **Size check**: Confirm file is under 10MB
4. **Content review**: Ensure no sensitive information
5. **Link test**: Verify markdown links work correctly

## Updating Documentation

After adding videos, update relevant documentation:

1. **README.md**: Links are already configured
2. **DETAILED_SETUP.md**: Reference setup video
3. **API_REFERENCE.md**: Link to API demonstration videos

---

**Quick Start for Video Creation:**

1. **Set up recording environment**
2. **Use OBS Studio or similar tool**
3. **Record 1080p at 30 FPS**
4. **Keep under 10MB** (compress if needed)
5. **Add to this directory**
6. **Commit to git**

The documentation will automatically reference your videos once they're added with the correct filenames.