# Chore: Skeleton Video Attention Grabber

## Metadata
adw_id: `Issue #29`
prompt: `778a12f4 Issue #29: Skeleton video

I want to show this video every time the face is detected but is not looking at the screen, in a jumpscare way.

The video should close as soon as the person looks back at the screen, kinda like a attention grabber.

https://github.com/user-attachments/assets/c00e781e-3225-467e-9df6-3f5ef7894ebf`

## Chore Description
Implement a "jumpscare" attention-grabbing feature that displays a skeleton video when the user's face is detected but they are not looking at the screen. The video should:
- Display immediately when the system detects the user is looking away (jumpscare style)
- Play the skeleton video from the provided GitHub asset URL
- Automatically close as soon as the user looks back at the screen
- Act as an attention grabber to keep users focused

The application already has:
1. Face detection system (`FaceDetector` in `face-detection.js`) that determines if a face is detected and if the user is `lookingAtScreen`
2. Video player infrastructure (`AttentionPlayer` in `video-player.js`) that displays intervention videos in a fullscreen overlay
3. Detection flow in `app.js` that continuously monitors face detection and gaze direction

This chore requires integrating the skeleton video into the existing video player system and modifying the detection flow to trigger the video when the user looks away, then close it when they look back.

## Relevant Files
Use these files to complete the chore:

- **apps/frontend/video-player.js** - Contains the `AttentionPlayer` class that manages intervention video playback; needs modification to support instant video playback/closing based on gaze detection
- **apps/frontend/app.js** - Contains the `FocusKeeperApp` class with `startContinuousDetection()` method (lines 465-517) that processes face detection results; needs logic to trigger/stop video based on `lookingAtScreen` status
- **apps/frontend/config.js** - Contains the CONFIG object with the `videos` array (lines 22-27); needs to add the skeleton video URL from the GitHub asset
- **apps/frontend/face-detection.js** - Contains face detection logic that returns `lookingAtScreen` boolean; already implemented, may need review for accuracy
- **apps/frontend/index.html** - Contains the video container structure; may need minor adjustments for video element instead of iframe

### New Files
None - all changes will be made to existing files.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Download and Host Skeleton Video Asset
- Download the skeleton video from the GitHub asset URL: `https://github.com/user-attachments/assets/c00e781e-3225-467e-9df6-3f5ef7894ebf`
- Save the video file to `apps/frontend/assets/` directory (create directory if it doesn't exist)
- Name the file appropriately (e.g., `skeleton-attention.mp4` or keep original name)
- Verify the video file format is web-compatible (mp4, webm, or ogv)
- Test that the video can be played in the browser

### 2. Update Configuration with Skeleton Video
- Open `apps/frontend/config.js`
- Add a new configuration section for attention-grabbing behavior:
  - `attentionGrabber.enabled` - boolean to enable/disable the feature
  - `attentionGrabber.videoPath` - path to the skeleton video asset
  - `attentionGrabber.triggerDelay` - milliseconds to wait before triggering (0 for instant jumpscare)
  - `attentionGrabber.instantClose` - boolean to close immediately when user looks back
- Update the configuration to use local video files instead of YouTube embeds for better control and instant playback

### 3. Modify AttentionPlayer for Direct Video Playback
- Open `apps/frontend/video-player.js`
- Modify `createVideoContainer()` method to support both iframe (for existing videos) and `<video>` element for the skeleton video:
  - Add a `<video>` element with attributes: `autoplay`, `muted`, `loop`
  - Keep iframe for backward compatibility if needed
  - Toggle visibility based on video source type
- Update `play()` method to accept an optional parameter for instant playback mode:
  - If using local video, set the `<video>` src and play immediately
  - Add `autoplay` and no user interaction requirement
  - Ensure jumpscare effect by removing any fade-in delays
- Update `stop()` method to pause and reset the video element
- Add a method `isPlaying()` to check current playback status
- Add a method `playSkeletonVideo()` specifically for the attention-grabbing skeleton video

### 4. Implement Gaze-Based Trigger Logic
- Open `apps/frontend/app.js`
- In the `FocusKeeperApp` class constructor, add state tracking:
  - `this.isLookingAway` - boolean to track if user is currently looking away
  - `this.lookingAwayStartTime` - timestamp when user started looking away
  - `this.isShowingAttentionGrabber` - boolean to track if skeleton video is playing
- In `startContinuousDetection()` method (around line 465-517), add logic after face detection:
  - Check if face is detected and `lookingAtScreen` is false
  - If user just started looking away (transition from looking → not looking):
    - Store the timestamp
    - Immediately trigger `attentionPlayer.playSkeletonVideo()` for jumpscare effect
    - Set `this.isShowingAttentionGrabber = true`
  - If user is looking at screen and attention grabber is playing:
    - Call `attentionPlayer.stop()` to close the video instantly
    - Set `this.isShowingAttentionGrabber = false`
- Add debouncing logic to prevent flickering if detection oscillates

### 5. Handle Edge Cases and State Management
- Add logic to handle no face detected scenario:
  - If no face is detected for extended period, should skeleton video play?
  - Decision: Only show skeleton video if face is detected but not looking at screen
- Add logic to handle model training/calibration mode:
  - Don't trigger skeleton video during calibration
  - Check if UI is in training phase before triggering
- Add state reset logic when camera stops or page visibility changes
- Handle multiple rapid transitions (looking away → looking back → looking away)

### 6. Update Status Display and UI Feedback
- Open `apps/frontend/app.js`
- Update the `updateStatus()` calls to reflect when attention grabber is active:
  - When skeleton video plays: update status to indicate attention grabber triggered
  - When user looks back: update status to indicate user refocused
- Add optional console logging for debugging:
  - Log when skeleton video is triggered
  - Log when skeleton video is closed
  - Log detection state transitions

### 7. Test Video Integration and Behavior
- Start the local server: `python -m http.server 8000` from project root
- Navigate to `http://localhost:8000/apps/frontend/`
- Grant camera permissions
- Test the jumpscare behavior:
  - Look at the screen → verify no video plays
  - Look away from the screen → verify skeleton video appears immediately (jumpscare)
  - Look back at the screen → verify skeleton video closes immediately
  - Repeat multiple times to test stability
- Test edge cases:
  - Turn head away from camera → verify behavior
  - Move out of camera view → verify behavior
  - Cover camera → verify behavior
  - Rapid look away/look back transitions
- Verify video plays smoothly without stuttering
- Check browser console for any errors or warnings

### 8. Optimize Performance and Polish
- Ensure video playback doesn't impact face detection performance
- Verify frame rate remains stable during video playback
- Test memory usage - ensure video resources are properly cleaned up
- Add smooth transitions if needed (though jumpscare should be instant)
- Verify video loops correctly while user is looking away
- Test on different browsers (Chrome, Firefox, Safari)

### 9. Code Cleanup and Documentation
- Remove any debug console.log statements (keep only important state transition logs)
- Add comments explaining the gaze-based trigger logic
- Ensure code follows existing style and conventions
- Update any relevant code comments in `video-player.js` and `app.js`
- Verify all error handling is in place

## Validation Commands
Execute these commands to validate the chore is complete:

- **Start local server**:
  ```bash
  python -m http.server 8000
  ```
  Then navigate to http://localhost:8000/apps/frontend/

- **Verify video asset exists**:
  ```bash
  ls -lh apps/frontend/assets/skeleton*
  ```
  Should show the skeleton video file

- **Verify configuration updates**:
  ```bash
  grep -A 5 "attentionGrabber" apps/frontend/config.js
  ```
  Should show the new attention grabber configuration section

- **Verify AttentionPlayer modifications**:
  ```bash
  grep -n "playSkeletonVideo\|<video" apps/frontend/video-player.js
  ```
  Should show new video element and skeleton video method

- **Verify gaze trigger logic**:
  ```bash
  grep -n "lookingAtScreen\|isShowingAttentionGrabber" apps/frontend/app.js
  ```
  Should show the gaze-based trigger implementation

- **Manual testing checklist**:
  - [ ] Face detected and looking at screen → no video plays
  - [ ] Face detected and looking away → skeleton video appears instantly
  - [ ] Look back at screen → skeleton video closes instantly
  - [ ] Video loops while looking away
  - [ ] No flickering or rapid on/off switching
  - [ ] No errors in browser console
  - [ ] Face detection continues working during video playback
  - [ ] Video quality is acceptable
  - [ ] Jumpscare effect is effective (instant, no delays)

- **Performance validation**:
  - Open browser DevTools → Performance tab
  - Record performance while triggering skeleton video
  - Verify frame rate stays above 20 FPS
  - Check that no memory leaks occur

- **Browser compatibility**:
  - Test in Chrome/Edge
  - Test in Firefox
  - Test in Safari (if available)
  - Verify video format is supported across browsers

## Notes

### Video Format Considerations
The GitHub asset URL provides a video file that needs to be downloaded and hosted locally. Web-compatible formats include:
- **MP4 (H.264)** - Best cross-browser support
- **WebM** - Good support, smaller file sizes
- **OGV** - Older format, wider compatibility

Consider providing multiple formats for better browser compatibility using the `<source>` element.

### Jumpscare Implementation
For an effective jumpscare effect:
1. **Instant trigger** - No delay between detection and video display (remove any transition delays)
2. **Autoplay** - Video must start playing immediately without user interaction
3. **Fullscreen** - Use existing fullscreen overlay for maximum impact
4. **Audio** - If skeleton video has audio, ensure it's enabled for jumpscare effect
5. **Close instantly** - When user looks back, close immediately (no fade-out)

### Detection Accuracy
The face detection system (MediaPipe Face Mesh) provides:
- `faceDetected` - whether a face is found
- `lookingAtScreen` - boolean based on gaze direction and head pose
- Head yaw angle threshold is set to 30 degrees in config

Current implementation uses:
- Horizontal deviation of iris landmarks for gaze detection
- Head yaw angle (left-right rotation) for head pose

If the detection is too sensitive or not sensitive enough:
- Adjust `CONFIG.detection.headTurnThreshold` (currently 30 degrees)
- Adjust `horizontalDeviation` threshold in `calculateGazeDirection()` (currently 30 pixels)

### Debouncing Strategy
To prevent flickering when detection oscillates:
1. Use a small time window (e.g., 200ms) before triggering
2. OR require 2-3 consecutive frames with same state
3. OR use a confidence threshold

However, for jumpscare effect, instant trigger is more important than debouncing. Consider accepting some minor flickering for better user experience.

### Alternative: Eye Tracking Integration
The application has an ML-powered eye tracking system (`EyeTracker`, `GazePredictor`) that could provide more accurate gaze detection. However:
- Requires calibration before use
- More complex implementation
- Current face detection system is sufficient for this use case

Stick with the existing face detection `lookingAtScreen` boolean for simplicity.

### Privacy and Performance
- All processing remains client-side (no privacy concerns)
- Video is played locally (no external requests after download)
- Face detection continues running during video playback
- Monitor performance impact of video playback on detection frame rate

### Future Enhancements
Potential improvements for future iterations:
- Multiple skeleton videos (random selection)
- Configurable trigger delay (immediate vs. after N seconds)
- Sound effects for jumpscare
- Statistics tracking (how many times triggered)
- User settings to enable/disable feature
- Different videos based on time of day or focus duration
