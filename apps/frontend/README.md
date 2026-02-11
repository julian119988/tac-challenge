# Focus Keeper - Anti-Procrastination App

A browser-based anti-procrastination focus app that uses your device camera to detect when you're distracted and plays attention-grabbing videos to bring you back on task.

## Features

- **Real-time Face Detection**: Uses TensorFlow.js with MediaPipe Face Mesh to detect your face and track your gaze
- **Distraction Monitoring**: Automatically detects when you look away from the screen or leave your seat
- **Attention Interventions**: Plays engaging videos when distraction is detected to grab your attention
- **Session Statistics**: Tracks focus time, distractions, and overall productivity
- **Privacy-First**: All processing happens locally in your browser - no video is ever stored or transmitted
- **No Backend Required**: Runs entirely client-side with no server-side ML processing

## Browser Compatibility

Works best in modern browsers with WebRTC and WebGL support:

- **Chrome** (recommended) - v90+
- **Firefox** - v88+
- **Safari** - v14+
- **Edge** - v90+

**Requirements:**
- Camera access permissions
- JavaScript enabled
- WebGL support (for TensorFlow.js)

## Quick Start

### 1. Access the App

If running locally with the FastAPI server:

```bash
# From project root
./scripts/start_webhook_server.sh
```

Then navigate to: http://localhost:8000/app

### 2. Grant Camera Permissions

When you click "Start Session", your browser will request camera access. Click "Allow" to enable face detection.

### 3. Position Yourself

- Sit facing your screen
- Ensure good lighting (face should be clearly visible)
- Keep your face centered in the camera view

### 4. Start Focusing

Click "Start Session" and get to work! The app will monitor your attention and alert you if you get distracted.

## How It Works

### Detection Logic

The app detects distraction using the following criteria:

1. **No Face Detected**: If no face is visible for more than 3 seconds, you're considered distracted
2. **Looking Away**: If your gaze is away from the screen for more than 4 seconds, distraction is triggered
3. **Head Turned**: If your head is turned more than 30 degrees, it's detected as distraction

### Intervention System

When distraction is detected:
- An attention-grabbing video plays in fullscreen overlay
- You can close it by clicking the X button or pressing ESC
- The app continues monitoring after you close the video

### Statistics Tracked

- **Session Time**: Total time since you started the session
- **Focus Time**: Total time you were actively focused
- **Distractions**: Number of times distraction was detected
- **Interventions**: Number of times intervention videos were played
- **Focus Score**: Percentage of session time spent focused

## Configuration

Edit `config.js` to customize detection thresholds and behavior:

```javascript
export const CONFIG = {
  detection: {
    noFaceTimeout: 3000,        // ms before distraction when no face
    gazeAwayTimeout: 4000,      // ms before distraction when looking away
    headTurnThreshold: 30,      // degrees for head turn detection
    detectionInterval: 200,     // ms between face detection checks (5 FPS)
  },

  videos: [
    // Add your own YouTube embed URLs here
    'https://www.youtube.com/embed/VIDEO_ID?autoplay=1',
  ],

  // ... other settings
};
```

### Adding Custom Attention Videos

To add your own intervention videos:

1. Get a YouTube video URL (e.g., `https://www.youtube.com/watch?v=dQw4w9WgXcQ`)
2. Convert to embed format: `https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1`
3. Add to `CONFIG.videos` array in `config.js`

**Tips for good intervention videos:**
- High energy, engaging content
- 30-60 seconds long
- Bright colors and movement
- Upbeat music or surprising sounds

### Using Local Video Files

Alternatively, you can use local video files:

1. Add `.mp4` files to `apps/frontend/assets/`
2. Update `video-player.js` to use HTML5 video instead of YouTube embeds
3. Reference local files: `assets/attention-video-1.mp4`

## Project Structure

```
apps/frontend/
├── index.html              # Main HTML structure
├── app.js                  # Main application logic
├── face-detection.js       # Face detection and gaze tracking
├── video-player.js         # Intervention video management
├── config.js               # Configuration constants
├── styles.css              # UI styling
├── README.md               # This file
├── assets/                 # Video and image assets
│   └── .gitkeep
└── test/                   # Testing files
    └── manual-test-guide.md
```

## Architecture

### CameraManager
Handles webcam access using `getUserMedia` API and renders video feed to canvas.

### FaceDetector
Uses TensorFlow.js Face-Landmarks-Detection to:
- Detect face presence
- Calculate gaze direction
- Estimate head pose (yaw/pitch/roll)

### DistractionMonitor
State machine that:
- Tracks user attention state (focused/distracted)
- Applies debouncing to avoid false positives
- Triggers interventions when thresholds exceeded

### AttentionPlayer
Manages intervention video playback with fullscreen overlay.

## Known Limitations

### Lighting Conditions
- Works best in well-lit environments
- Poor lighting may cause false distraction detections
- Avoid backlighting (window behind you)

### Multiple Faces
- Currently only tracks one face
- Additional faces in frame may cause confusion

### Head Position
- Works best when facing camera directly
- Looking at second monitor may trigger false distraction
- Extreme head angles may lose tracking

### Performance
- Face detection runs at ~5 FPS to balance accuracy and performance
- Older devices may experience lag
- Close other intensive browser tabs for best performance

### Browser Quirks
- Safari may require HTTPS for camera access (works on localhost)
- Some browsers block autoplay videos - user may need to interact first
- Mobile browsers have limited camera API support

## Troubleshooting

### Camera Not Working

**Problem**: "Failed to access camera" error

**Solutions**:
- Check browser permissions (Settings → Privacy → Camera)
- Ensure no other app is using the camera
- Try a different browser
- On macOS: System Preferences → Security & Privacy → Camera

### Face Not Detected

**Problem**: Status shows "Distracted" even when present

**Solutions**:
- Improve lighting (add desk lamp, open curtains)
- Remove glasses if causing reflection
- Move closer to camera
- Ensure face is centered in frame

### Model Loading Failed

**Problem**: "Failed to load face detection model" error

**Solutions**:
- Check internet connection (TensorFlow.js loads from CDN)
- Clear browser cache and reload
- Disable ad blockers that might block CDN requests
- Try a different browser

### Poor Performance / Lag

**Problem**: App is slow or unresponsive

**Solutions**:
- Close other browser tabs
- Reduce `CONFIG.detection.detectionInterval` (e.g., 300ms instead of 200ms)
- Use Chrome (best WebGL performance)
- Close other applications using GPU

### False Distraction Detections

**Problem**: Getting distraction alerts while focused

**Solutions**:
- Increase `CONFIG.detection.gazeAwayTimeout` (e.g., 6000ms)
- Improve lighting conditions
- Ensure face is clearly visible and centered
- Reduce head movement while working

## Development

### Local Development

No build step required! Just open `index.html` in a browser or serve via HTTP:

```bash
# Using Python
python -m http.server 8000

# Using Node.js
npx serve .

# Using FastAPI (from project root)
./scripts/start_webhook_server.sh
```

### Debugging

Open browser DevTools console to see:
- Face detection results
- State changes (focused → distracted)
- Intervention triggers
- Error messages

Access the app instance in console:
```javascript
window.focusKeeperApp
```

### Testing

See `test/manual-test-guide.md` for comprehensive testing checklist.

## Privacy & Security

- **No data transmission**: All processing happens locally in your browser
- **No storage**: Video feed is never saved to disk or sent to servers
- **No cookies**: No tracking or analytics
- **No accounts**: No sign-up or authentication required
- **Open source**: All code is visible and auditable

The app only uses:
- Local camera access (with explicit permission)
- localStorage for session statistics (optional)
- TensorFlow.js models from official CDN

## Future Enhancements

Potential improvements (not yet implemented):

- Multiple monitor support
- Custom detection zones
- Break reminders and Pomodoro timer
- Sound-based distraction detection
- Mobile app version
- Custom intervention types (sounds, notifications, etc.)
- Focus session history and analytics
- Export statistics to CSV

## Contributing

This is part of the TAC Challenge project. See main project README for contribution guidelines.

## License

Part of the TAC Challenge educational project.

## Support

For issues or questions:
- Check the Troubleshooting section above
- Review the Known Limitations
- See the main project README at project root
- Check browser console for error messages
