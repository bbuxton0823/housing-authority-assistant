# Screenshots Directory

This directory contains screenshots of the Housing Authority Assistant interface.

## Required Screenshots

To complete the documentation, please add the following screenshots:

### 1. Agent View (`agent-view.png`)
- Full interface showing the agent orchestration panel
- Include: Available agents, guardrails, conversation context, runner output
- Recommended size: 1920x1080 or higher
- Format: PNG for best quality

### 2. Customer View (`customer-view.png`)
- Clean chat interface from user perspective
- Show Housing Authority branding
- Include sample conversation
- Recommended size: 1920x1080 or higher
- Format: PNG for best quality

### 3. Inspection Flow (`inspection-flow.png`)
- Screenshot of inspection scheduling conversation
- Show agent handoff from Triage to Inspection Agent
- Include context updates
- Recommended size: 1920x1080 or higher
- Format: PNG for best quality

### 4. Spanish Response (`spanish-response.png`)
- Demonstration of multilingual support
- Show Spanish input and response
- Highlight language detection in context
- Recommended size: 1920x1080 or higher
- Format: PNG for best quality

### 5. Video Thumbnail (`video-thumbnail.png`)
- Attractive thumbnail for demo video
- Include Housing Authority branding
- Show key interface elements
- Recommended size: 1280x720 (16:9 aspect ratio)
- Format: PNG for best quality

## How to Take Screenshots

### For Agent View:
1. Start the application (`npm run dev` and `uvicorn api:app --reload`)
2. Open http://localhost:3000
3. Send a message like "I need to schedule an inspection"
4. Wait for agent handoff to complete
5. Take screenshot of full interface

### For Customer View:
1. Hide or minimize the agent panel (if possible) or focus on chat area
2. Show a clean conversation flow
3. Include Housing Authority branding elements

### For Multilingual Demo:
1. Send message: "Necesito programar una inspección"
2. Wait for Spanish response
3. Show the context panel with language set to "spanish"

## Screenshot Guidelines

- **Quality**: Use high-resolution displays for crisp images
- **Format**: PNG for UI screenshots (better quality than JPG)
- **Size**: Optimize for web (compress if over 1MB)
- **Content**: Remove any sensitive information
- **Consistency**: Use consistent browser and zoom level

## Tools for Screenshots

### macOS:
- **Cmd+Shift+4**: Select area
- **Cmd+Shift+5**: Screenshot options with timer
- **CleanShot X**: Professional screenshot tool

### Windows:
- **Windows+Shift+S**: Snipping tool
- **PrtScn**: Full screen
- **Greenshot**: Free screenshot tool

### Linux:
- **gnome-screenshot**: Built-in tool
- **Flameshot**: Feature-rich screenshot tool
- **Shutter**: Advanced screenshot editor

## Adding Screenshots

Once you have the screenshots:

1. **Name them correctly**:
   - `agent-view.png`
   - `customer-view.png`
   - `inspection-flow.png`
   - `spanish-response.png`
   - `video-thumbnail.png`

2. **Place in this directory**: `/docs/screenshots/`

3. **Optimize file size**:
   ```bash
   # Using ImageOptim (macOS) or similar tools
   # Target: < 500KB per image for fast loading
   ```

4. **Commit to git**:
   ```bash
   git add docs/screenshots/
   git commit -m "Add UI screenshots for documentation"
   ```

## Image Optimization

For web use, optimize your screenshots:

```bash
# Using ImageMagick (if installed)
convert input.png -quality 85 -resize 1920x1080> output.png

# Using online tools
# - TinyPNG.com
# - Squoosh.app
# - ImageOptim.com
```

## Updating Documentation

After adding screenshots, the README.md will automatically display them. No additional changes needed - the markdown is already configured to show the images when they exist.

---

**Next Steps:**
1. Take the required screenshots
2. Add them to this directory
3. Commit to git
4. Screenshots will appear in README.md automatically