# Chore: Always Not Looking - Debug Eye Detection

## Metadata
adw_id: `Issue #21`
prompt: `Now does not seem to know when I'm looking or when I'm not, maybe now for testing lets not play a video when not looking and if possible show squares arounde the eyes, with green borders when looking and red borders when not looking`

## Chore Description
The Focus Keeper application's eye detection system is not accurately determining when the user is looking at the screen. The current implementation appears to always report "not looking" or has difficulty distinguishing between looking and not looking states.

To debug and improve this:
1. Disable the intervention video playback temporarily for testing purposes
2. Add visual feedback by drawing rectangles around the detected eyes on the canvas
3. Color-code the eye rectangles: green borders when the system detects the user is looking at the screen, red borders when not looking
4. This will allow visual verification of the detection logic and help identify issues with the gaze tracking algorithm

The changes will help diagnose whether the issue is with:
- Eye landmark detection
- Gaze direction calculation
- Head pose estimation
- Threshold values for determining "looking at screen"

## Relevant Files
Use these files to complete the chore:

- **apps/frontend/face-detection.js** (lines 40-86): `detect()` method that performs face and gaze detection - need to extract eye landmark positions for drawing
- **apps/frontend/face-detection.js** (lines 93-130): `calculateGazeDirection()` method that determines if user is looking forward - this logic may need debugging
- **apps/frontend/face-detection.js** (lines 99-103): Eye landmark indices (left: [33, 133, 160, 159, 158, 157, 173], right: [362, 263, 385, 386, 387, 388, 398]) used for detection
- **apps/frontend/app.js** (lines 146-159): `startRendering()` method in CameraManager where canvas drawing happens - add eye rectangle drawing here
- **apps/frontend/app.js** (lines 244-281): `checkDistraction()` method in DistractionMonitor - temporarily disable video intervention
- **apps/frontend/app.js** (lines 286-298): `onDistractionDetected()` method that triggers the intervention video - comment out `this.attentionPlayer.play()`
- **apps/frontend/config.js** (lines 4-11): Detection configuration thresholds that may need adjustment

### New Files
None - all modifications to existing files

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Disable Intervention Video for Testing
- In `apps/frontend/app.js`, locate the `onDistractionDetected()` method in the `DistractionMonitor` class (around line 286)
- Comment out the call to `this.attentionPlayer.play()` to prevent video interventions during testing
- Add a console log to confirm when distraction is detected without triggering the video
- Keep the console log from line 287 and the event dispatch to maintain visibility

### 2. Add Eye Landmark Data to Detection Results
- In `apps/frontend/face-detection.js`, modify the `detect()` method to return eye landmark positions
- Extract the left eye and right eye keypoints from the face detection result
- Add `leftEyeLandmarks` and `rightEyeLandmarks` to the return object
- Also return `keypoints` array for easier debugging
- This will allow the rendering code to access eye positions for drawing rectangles

### 3. Calculate Eye Bounding Boxes
- In `apps/frontend/face-detection.js`, add a helper method `getEyeBoundingBox(eyeLandmarks)` to calculate the bounding box around eye landmarks
- Find the min/max x and y coordinates from the eye landmark points
- Add padding (e.g., 5-10 pixels) to make the boxes more visible
- Return an object with `{x, y, width, height}` for drawing rectangles

### 4. Draw Eye Rectangles on Canvas
- In `apps/frontend/app.js`, modify the `CameraManager.startRendering()` method to draw eye rectangles
- Store the latest face detection result in the CameraManager instance
- After drawing the video frame to canvas (line 152), check if detection data exists
- If eye landmarks are available, draw rectangles around each eye
- Use green stroke (`ctx.strokeStyle = '#4ade80'`) when `lookingAtScreen` is true
- Use red stroke (`ctx.strokeStyle = '#ef4444'`) when `lookingAtScreen` is false
- Set line width to 3 pixels for visibility

### 5. Pass Detection Results to Camera Manager
- Create a way to pass detection results from `DistractionMonitor` to `CameraManager`
- In `FocusKeeperApp`, store the latest detection result
- Update `CameraManager` to accept detection data and use it for rendering
- Ensure the rendering loop has access to the latest `lookingAtScreen` state
- The detection happens in `checkDistraction()` and rendering happens continuously, so sync these appropriately

### 6. Add Debug Console Logging
- In `apps/frontend/face-detection.js`, add detailed console logging to the `calculateGazeDirection()` method
- Log the calculated values: `horizontalDeviation`, `isLookingForward`, `confidence`
- In `calculateHeadPose()`, log the calculated `yaw` angle
- In the main `detect()` method, log the final `lookingAtScreen` determination
- This will help identify if the thresholds in the detection logic are appropriate

### 7. Test Eye Detection Visualization
- Start the Focus Keeper application
- Click "Start Session" to begin face detection
- Verify that rectangles appear around detected eyes
- Test the following scenarios and observe rectangle colors:
  - Looking directly at screen (should be green)
  - Looking away left/right (should turn red)
  - Looking up/down (should turn red)
  - Turning head away (should turn red)
- Check console logs to see the raw detection values
- Verify that intervention videos do NOT play when not looking

### 8. Adjust Thresholds if Needed
- Based on testing, check if threshold values in `config.js` need adjustment:
  - `headTurnThreshold: 30` (degrees) - may need to increase/decrease
  - `horizontalDeviation < 30` in `calculateGazeDirection()` - may need tuning
- If detection is too sensitive or not sensitive enough, adjust these values
- Document any threshold changes with comments explaining why

## Validation Commands
Execute these commands to validate the chore is complete:

- `grep -n "attentionPlayer.play" apps/frontend/app.js` - Verify the intervention video play is commented out
- `grep -n "strokeStyle.*4ade80\|strokeStyle.*ef4444" apps/frontend/app.js` - Confirm green/red eye rectangles are drawn
- `grep -n "getEyeBoundingBox\|leftEyeLandmarks\|rightEyeLandmarks" apps/frontend/face-detection.js` - Verify eye landmark extraction
- `./scripts/start_webhook_server.sh` - Start the server
- Manual browser test at `http://localhost:8000/app` - Verify eye rectangles appear with correct colors
- Check browser console for detection debug logs showing gaze calculations
- Test by looking at/away from screen and verify rectangle colors change appropriately

## Notes
- The MediaPipe Face Mesh model provides 468 facial landmarks, including detailed eye region points
- Eye landmark indices are from the MediaPipe Face Mesh model:
  - Left eye: indices [33, 133, 160, 159, 158, 157, 173]
  - Right eye: indices [362, 263, 385, 386, 387, 388, 398]
- The current gaze detection is simplified and uses:
  - Eye position relative to face center (horizontal deviation)
  - Head yaw angle (left-right rotation)
- More sophisticated gaze tracking would require:
  - Iris detection (MediaPipe supports this with `refineLandmarks: true`)
  - Eye aspect ratio for blink detection
  - More complex head pose estimation
- After debugging with visual feedback, the intervention video can be re-enabled
- Consider adding a "debug mode" toggle to show/hide eye rectangles permanently
- The color coding provides immediate visual feedback for testing the detection algorithm
