# Chore: Create Simple Frontend App

## Metadata
adw_id: `ab0a0f6c`
prompt: `Issue #5: Create simple frontend app - Lets create a simple frontend app with the tech stack you think is better to achive the goal we have in mind in the readme file.`

## Chore Description
Create a browser-based anti-procrastination focus app that uses the device camera to detect when the user is distracted and plays attention-grabbing videos to bring them back on task. The app should be simple, modern, and work directly in the browser without complex backend dependencies.

**Core Functionality:**
- Camera access and real-time video feed display
- Face detection and gaze tracking to identify when user is looking away
- Automatic distraction detection (looking at phone, looking away from screen)
- Attention-grabbing video playback as intervention when distraction is detected
- Simple, clean UI with start/stop controls
- Browser-based with no server-side processing required for ML

**Tech Stack Recommendation:**
- **Frontend Framework:** Vanilla JavaScript with modern ES6+ (simple, no build step required)
- **Face Detection:** TensorFlow.js with Face-Landmarks-Detection model (runs in browser, no backend needed)
- **Video Playback:** HTML5 video element with embedded attention-grabbing videos
- **Styling:** CSS3 with modern flexbox/grid layout
- **Deployment:** Static files served by existing FastAPI server

This approach prioritizes simplicity and immediate functionality while keeping the entire stack client-side.

## Relevant Files

### Existing Files to Reference
- `apps/adw_server/server.py:28-34` - Current static file serving setup (camera app route at `/app`)
- `apps/adw_server/README.md:46-50` - Documentation mentions camera app endpoint
- `apps/adw_server/core/config.py` - Configuration includes `STATIC_FILES_DIR` setting
- `README.md:1-30` - Project description includes anti-procrastination focus app goals
- `.env.example:43-46` - Static files directory configuration

### New Files to Create

#### Frontend Application (`apps/frontend/`)
- `index.html` - Main HTML structure with camera feed, status display, and controls
- `app.js` - Core application logic (camera access, face detection, distraction monitoring)
- `styles.css` - Modern styling with responsive design
- `config.js` - Configuration constants (detection thresholds, video URLs, timing)
- `face-detection.js` - Face detection and gaze tracking module using TensorFlow.js
- `video-player.js` - Attention video playback management
- `README.md` - Frontend app documentation with setup and usage instructions

#### Assets (`apps/frontend/assets/`)
- `attention-video-1.mp4` - Sample attention-grabbing video (or use embedded YouTube links)
- `.gitkeep` - Ensure directory exists in repo

#### Testing (`apps/frontend/test/`)
- `test.html` - Simple browser-based tests for core functions
- `manual-test-guide.md` - Manual testing checklist

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create Frontend Directory Structure
- Create `apps/frontend/` directory
- Create `apps/frontend/assets/` directory for video files
- Create `apps/frontend/test/` directory for testing files
- Verify existing static file serving configuration in `apps/adw_server/server.py`

### 2. Build Core HTML Structure
- Create `apps/frontend/index.html` with:
  - DOCTYPE and semantic HTML5 structure
  - Meta tags for viewport and UTF-8 encoding
  - Title: "Focus Keeper - Anti-Procrastination App"
  - Canvas element for video feed display
  - Status display area showing current state (focused/distracted)
  - Start/Stop button for camera control
  - Hidden video element for attention-grabbing playback
  - Settings panel (optional) for threshold configuration
- Include TensorFlow.js and Face-Landmarks-Detection from CDN
- Link to `styles.css` and module scripts (`app.js`, `face-detection.js`, etc.)

### 3. Implement Camera Access Module
- Create `apps/frontend/app.js` with:
  - `CameraManager` class to handle `getUserMedia` API
  - Request camera permissions with error handling
  - Stream video to canvas element at 30fps
  - Handle camera start/stop lifecycle
  - Display appropriate error messages for denied permissions
  - Responsive canvas sizing to fit viewport

### 4. Implement Face Detection Module
- Create `apps/frontend/face-detection.js` with:
  - `FaceDetector` class using TensorFlow.js Face-Landmarks-Detection
  - Load face detection model on initialization
  - Detect face landmarks in real-time from camera feed
  - Calculate gaze direction using eye landmarks and head pose
  - Return detection results: `{ faceDetected: boolean, lookingAtScreen: boolean, confidence: number }`
  - Handle cases where no face is detected
  - Optimize performance (run detection every 2-3 frames, not every frame)

### 5. Implement Distraction Detection Logic
- Extend `apps/frontend/app.js` with:
  - `DistractionMonitor` class to track user attention state
  - Define distraction criteria:
    - No face detected for > 3 seconds
    - Gaze away from screen for > 4 seconds
    - Head turned significantly (> 30 degrees)
  - State machine: focused → distracted → intervention
  - Debouncing to avoid false positives (require consistent state for threshold period)
  - Emit events when state changes (focused ↔ distracted)

### 6. Implement Video Intervention System
- Create `apps/frontend/video-player.js` with:
  - `AttentionPlayer` class to manage intervention videos
  - Array of attention-grabbing video sources (YouTube embeds or local files)
  - Play random video when distraction detected
  - Fullscreen playback with auto-exit after video ends
  - User can manually close video with ESC or click
  - Track intervention count and effectiveness

### 7. Create Configuration Module
- Create `apps/frontend/config.js` with:
  - Detection thresholds (time delays, angle thresholds)
  - Video sources array (URLs to attention videos)
  - Camera settings (resolution, framerate)
  - Export as ES6 module for use in other scripts

### 8. Implement UI and Styling
- Create `apps/frontend/styles.css` with:
  - Modern, clean design with dark theme option
  - Centered layout with camera feed as focus
  - Status indicator with color coding (green=focused, red=distracted, yellow=loading)
  - Large, accessible start/stop button
  - Smooth transitions and animations
  - Responsive design (mobile-friendly, though camera may not work on all mobile browsers)
  - Loading spinner while models load

### 9. Add Status Display and Statistics
- Extend `apps/frontend/app.js` with:
  - Real-time status display showing:
    - Current state (Focused / Distracted / Not Started)
    - Session duration
    - Total focus time
    - Number of distractions caught
    - Effectiveness score
  - Update UI every second
  - Persist stats to localStorage for session continuity

### 10. Error Handling and User Feedback
- Add comprehensive error handling:
  - Camera permission denied → show clear instructions
  - Browser not supported → show upgrade/alternative browser message
  - TensorFlow.js model load failure → show retry button
  - No face detected initially → show positioning guidance
- User-friendly error messages in UI (not console only)
- Fallback behavior for each failure scenario

### 11. Create Documentation
- Create `apps/frontend/README.md` with:
  - Feature overview and screenshots (describe UI flow)
  - Browser compatibility list (Chrome, Firefox, Safari, Edge)
  - Setup instructions for local development
  - How to add custom attention videos
  - Configuration options explanation
  - Known limitations (lighting conditions, multiple faces, etc.)
  - Troubleshooting common issues

### 12. Integration with FastAPI Server
- Verify `apps/adw_server/server.py` serves static files from `apps/frontend/`
- Update `STATIC_FILES_DIR` configuration if needed
- Ensure `/app` endpoint correctly routes to `index.html`
- Test access at http://localhost:8000/app

### 13. Create Manual Test Guide
- Create `apps/frontend/test/manual-test-guide.md` with:
  - Test camera access and permission flow
  - Test face detection accuracy
  - Test distraction detection (look away, look at phone, leave seat)
  - Test video intervention triggers
  - Test start/stop functionality
  - Test statistics tracking
  - Test error scenarios (deny camera, cover camera, poor lighting)
  - Browser compatibility testing checklist

### 14. Validate and Test
- Start FastAPI server: `./scripts/start_webhook_server.sh`
- Access app at http://localhost:8000/app
- Execute all manual tests from test guide
- Verify camera feed displays correctly
- Verify face detection works in various lighting conditions
- Verify distraction detection triggers appropriately
- Verify attention videos play when expected
- Test in at least 2 different browsers
- Document any issues or limitations discovered

## Validation Commands
Execute these commands to validate the chore is complete:

- `ls apps/frontend/` - Verify frontend directory exists with all files
- `ls apps/frontend/index.html apps/frontend/app.js apps/frontend/styles.css apps/frontend/config.js apps/frontend/face-detection.js apps/frontend/video-player.js` - Verify all core files exist
- `grep -q "getUserMedia" apps/frontend/app.js` - Verify camera access implementation
- `grep -q "Face-Landmarks-Detection" apps/frontend/index.html` - Verify TensorFlow.js integration
- `grep -q "DistractionMonitor" apps/frontend/app.js` - Verify distraction detection implementation
- `grep -q "AttentionPlayer" apps/frontend/video-player.js` - Verify video intervention implementation
- `./scripts/start_webhook_server.sh &` - Start server in background
- `sleep 3 && curl -f http://localhost:8000/app` - Verify app endpoint returns HTML
- `pkill -f "uvicorn apps.adw_server.server:app"` - Stop background server

## Notes

### Why This Tech Stack?

**Vanilla JavaScript (no framework):**
- Zero build step, instant development
- No dependencies to install or maintain
- Small bundle size
- Easy to understand and modify
- Modern ES6+ modules for code organization

**TensorFlow.js with Face-Landmarks-Detection:**
- Runs entirely in browser (no backend ML server needed)
- Pre-trained models available via CDN
- Good accuracy for face and gaze detection
- Active community and documentation
- Free and open source

**Static File Serving:**
- FastAPI already configured for static files
- No additional backend setup required
- Can deploy anywhere (GitHub Pages, Netlify, Vercel)

### Alternative Considerations

If TensorFlow.js is too heavy or slow:
- Use simpler face detection like `face-api.js`
- Use WebGazer.js specifically for gaze tracking
- Reduce model complexity or detection frequency

For video sources:
- Start with YouTube embed links (no storage needed)
- Later can add local video files to `assets/`
- Consider copyright-free meme compilation videos

### Privacy Considerations
- All processing happens client-side (camera feed never leaves browser)
- No video/images are stored or transmitted
- Include privacy notice in UI
- User must explicitly grant camera permissions

### Performance Optimization
- Run face detection at lower frequency (5-10 FPS) instead of matching camera framerate
- Use requestAnimationFrame for smooth rendering
- Lazy-load TensorFlow.js models only when needed
- Consider Web Worker for face detection to avoid blocking UI thread
