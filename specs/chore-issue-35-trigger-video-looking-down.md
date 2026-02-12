# Chore: Trigger video when looking down

## Metadata
adw_id: `Issue #35`
prompt: `4bd3c826 Issue #35: Trigger video when looking down

Right now the video plays if we look to the sides, but is very important to play the video when we look down, since is most likely that we are looking at the phone`

## Chore Description
Modify the face detection and gaze tracking system to trigger the skeleton attention-grabbing video when the user looks down (in addition to looking to the sides). This is important because users commonly look down when checking their phones, which is a key distraction pattern to detect.

Currently, the system detects when users look away horizontally (to the sides) using:
1. Horizontal iris deviation from face center
2. Head yaw angle (left-right rotation)

This chore requires adding vertical gaze detection to identify when users look down by:
1. Calculating head pitch (up-down rotation)
2. Detecting vertical iris/pupil position relative to eye region
3. Integrating these metrics into the `lookingAtScreen` determination

The skeleton video will then trigger for both:
- Looking to the sides (existing behavior)
- Looking down (new behavior)

## Relevant Files
Use these files to complete the chore:

- **apps/frontend/face-detection.js** (lines 212-248) - Contains the `calculateHeadPose()` method that currently only calculates yaw (left-right). Needs to implement pitch calculation (up-down) to detect head tilting down. Also contains `calculateGazeDirection()` (lines 148-210) which needs vertical gaze component.
- **apps/frontend/config.js** (lines 4-11) - Contains `CONFIG.detection` with `headTurnThreshold` for horizontal turning. Needs to add configuration for vertical gaze thresholds (e.g., `headPitchThreshold` for detecting downward head tilt).
- **apps/frontend/app.js** (lines 443-474) - Contains the attention grabber logic in `startContinuousDetection()` that uses the `lookingAtScreen` boolean. May need minor updates if detection result structure changes, but likely requires no changes since it already uses the `lookingAtScreen` flag.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Research MediaPipe Face Mesh Landmarks
- Review MediaPipe Face Mesh documentation to identify landmarks that indicate vertical head pose and downward gaze
- Key landmarks to consider:
  - Nose tip (landmark 1) and nose bridge landmarks
  - Forehead landmarks vs chin landmarks (vertical face ratio)
  - Upper and lower eye landmarks (eye openness and iris vertical position)
  - Iris landmarks (468-477) - vertical position within eye region
- Document which landmarks will be used for pitch calculation
- Consider using the vertical distance ratio between:
  - Nose to forehead vs nose to chin
  - Iris center to upper eyelid vs iris center to lower eyelid

### 2. Implement Head Pitch Calculation
- Open `apps/frontend/face-detection.js`
- Locate the `calculateHeadPose()` method (lines 217-248)
- Add pitch (up-down rotation) calculation using vertical landmarks:
  - Option 1: Use nose vertical position relative to eye and chin landmarks
  - Option 2: Calculate vertical distance ratio between upper and lower face
  - Option 3: Use eyebrow landmarks vs mouth landmarks vertical distance
- Calculate pitch angle in degrees (positive when looking up, negative when looking down)
- Add debug logging to verify pitch values: `console.log('[Head Pose] Pitch angle:', pitch.toFixed(2), 'degrees')`
- Update the return statement to include the calculated pitch value
- Test by looking up and down to verify pitch values change correctly

### 3. Add Vertical Gaze Component to Gaze Direction
- In `apps/frontend/face-detection.js`, locate the `calculateGazeDirection()` method (lines 153-210)
- Add vertical gaze detection using iris landmarks:
  - Calculate iris center Y position relative to eye region bounds
  - Get upper eye landmarks (indices: 159, 158, 157) and lower eye landmarks (indices: 160, 133, 173)
  - Calculate vertical deviation: how far iris is from eye center vertically
  - If iris is positioned toward bottom of eye region → looking down
  - If iris is positioned toward top of eye region → looking up
- Calculate vertical deviation metric similar to existing horizontal deviation
- Add to return object: `verticalDeviation`, `isLookingDown` boolean
- Add debug logging: `console.log('[Gaze] Vertical deviation:', verticalDeviation.toFixed(2), '| Looking down:', isLookingDown)`
- Test by looking down at desk to verify values

### 4. Update Configuration with Pitch Threshold
- Open `apps/frontend/config.js`
- Locate the `detection` configuration section (lines 4-11)
- Add new threshold: `headPitchThreshold: 15` (degrees - threshold for detecting downward head tilt)
- Add comment explaining: `// degrees - head pitch (down) angle threshold`
- Consider also adding: `verticalGazeThreshold: 0.3` for iris-based vertical gaze detection (normalized value)
- These thresholds may need tuning based on testing

### 5. Integrate Vertical Detection into lookingAtScreen Logic
- Open `apps/frontend/face-detection.js`
- Locate the `detect()` method around lines 90-92 where `lookingAtScreen` is calculated
- Current logic: `lookingAtScreen = gazeInfo.isLookingForward && Math.abs(headPose.yaw) < threshold`
- Update to include vertical components:
  ```javascript
  const lookingAtScreen =
    gazeInfo.isLookingForward &&
    Math.abs(headPose.yaw) < CONFIG.detection.headTurnThreshold &&
    headPose.pitch > -CONFIG.detection.headPitchThreshold &&
    !gazeInfo.isLookingDown;
  ```
- Logic: User is looking at screen only if:
  - Eyes are looking forward horizontally (existing)
  - Head is not turned to sides (existing)
  - Head is not tilted down below threshold (new)
  - Eyes are not looking down (new)
- Add comprehensive debug logging showing all components:
  ```javascript
  console.log('[Detection] Looking at screen:', lookingAtScreen,
              '| Gaze forward:', gazeInfo.isLookingForward,
              '| Head yaw:', Math.abs(headPose.yaw).toFixed(2),
              '| Head pitch:', headPose.pitch.toFixed(2),
              '| Looking down:', gazeInfo.isLookingDown);
  ```

### 6. Test Vertical Gaze Detection
- Start the application: `python -m http.server 8000`
- Navigate to `http://localhost:8000/apps/frontend/`
- Open browser DevTools Console to monitor debug logs
- Test scenarios:
  - **Look straight at screen** → `lookingAtScreen: true`, skeleton video should NOT play
  - **Look down at desk/phone** → `lookingAtScreen: false`, skeleton video should play
  - **Look up at ceiling** → `lookingAtScreen: false`, skeleton video should play
  - **Look left/right** → `lookingAtScreen: false`, skeleton video should play (existing behavior)
  - **Tilt head down slightly** → verify threshold sensitivity
- Monitor console logs for pitch and vertical deviation values
- Take notes on typical values for different head positions

### 7. Tune Detection Thresholds
- Based on testing, adjust thresholds in `apps/frontend/config.js`:
  - If too sensitive (triggers when still looking at screen):
    - Increase `headPitchThreshold` (try 20-25 degrees)
    - Increase `verticalGazeThreshold` if using iris-based detection
  - If not sensitive enough (doesn't detect looking down):
    - Decrease `headPitchThreshold` (try 10-12 degrees)
    - Decrease `verticalGazeThreshold`
- Test different head positions and distances from camera
- Verify detection works consistently across multiple trials
- Consider adding slight delay/smoothing to prevent flickering

### 8. Handle Edge Cases
- Test edge cases and add handling if needed:
  - **Extreme head angles** - very far down, chin touching chest
  - **Partial face visibility** - only top of head visible when looking down
  - **Camera angle variations** - laptop camera vs external camera
  - **User distance from camera** - close vs far
  - **Lighting conditions** - ensure landmarks are detected reliably
- Add bounds checking to pitch calculation to prevent extreme values
- Consider adding confidence scoring based on landmark detection quality

### 9. Update Debug Logging and Comments
- Review all console.log statements added during implementation
- Keep important state transition logs: when looking down is detected
- Remove excessive per-frame logging (or reduce frequency with `Math.random()` check)
- Add comments explaining the vertical detection logic:
  - In `calculateHeadPose()`: explain how pitch is calculated
  - In `calculateGazeDirection()`: explain vertical deviation calculation
  - In `detect()`: explain the combined `lookingAtScreen` logic
- Document landmark indices used and why they were chosen

### 10. Validate Implementation
- Perform final validation testing:
  - [ ] Looking straight at screen → no video
  - [ ] Looking down at phone/desk → skeleton video appears instantly
  - [ ] Looking back up at screen → skeleton video closes instantly
  - [ ] Looking left/right → skeleton video appears (existing behavior still works)
  - [ ] Rapid up/down head movements → no flickering or crashes
  - [ ] Multiple transitions → stable behavior
- Check browser console for errors or warnings
- Verify face detection performance remains stable (no FPS drop)
- Test on different browsers (Chrome, Firefox, Safari)
- Test with different lighting conditions and camera angles

## Validation Commands
Execute these commands to validate the chore is complete:

- **Verify pitch calculation added**:
  ```bash
  grep -n "pitch" apps/frontend/face-detection.js
  ```
  Should show pitch calculation in `calculateHeadPose()` and usage in `detect()`

- **Verify vertical gaze detection**:
  ```bash
  grep -n "verticalDeviation\|isLookingDown" apps/frontend/face-detection.js
  ```
  Should show vertical deviation calculation in `calculateGazeDirection()`

- **Verify configuration updates**:
  ```bash
  grep -n "headPitchThreshold\|verticalGazeThreshold" apps/frontend/config.js
  ```
  Should show new threshold configuration values

- **Verify lookingAtScreen logic updated**:
  ```bash
  grep -A 5 "lookingAtScreen =" apps/frontend/face-detection.js
  ```
  Should show the updated logic including pitch and vertical gaze checks

- **Manual testing checklist**:
  - [ ] Face detected, looking at screen → `lookingAtScreen: true`, no video
  - [ ] Look down at phone → `lookingAtScreen: false`, skeleton video plays
  - [ ] Look back up → `lookingAtScreen: true`, skeleton video closes
  - [ ] Look left → skeleton video plays (existing behavior works)
  - [ ] Look right → skeleton video plays (existing behavior works)
  - [ ] Debug logs show pitch values changing when tilting head up/down
  - [ ] Debug logs show vertical deviation when looking down
  - [ ] No errors in console
  - [ ] Detection feels natural and not overly sensitive

- **Performance validation**:
  ```bash
  # Run application and monitor in browser DevTools
  # - Performance tab should show stable FPS
  # - No memory leaks during extended use
  # - Face detection remains responsive
  ```

- **Cross-browser testing**:
  - Test in Chrome (primary browser)
  - Test in Firefox (secondary browser)
  - Test in Safari if available (macOS)
  - Verify MediaPipe Face Mesh landmarks work consistently

## Notes

### Understanding Head Pose vs Eye Gaze
Two complementary approaches for detecting "looking down":

1. **Head Pose (Pitch)** - Physical head orientation
   - Measures head angle relative to camera
   - Detects head tilting down (looking at phone, desk)
   - More reliable for gross movements
   - Less accurate for subtle eye movements

2. **Eye Gaze (Vertical Deviation)** - Eye direction within eye socket
   - Measures iris/pupil position within eye region
   - Detects eyes looking down even if head is straight
   - More precise for subtle gaze shifts
   - Can be affected by eyelid detection

**Recommendation**: Implement both and combine them. User is "looking down" if:
- Head pitch is below threshold (head tilted down) OR
- Vertical gaze deviation indicates eyes looking down

This provides robust detection across different user behaviors:
- User tilts head down to look at phone → caught by pitch
- User keeps head still but shifts eyes down to read → caught by gaze
- User does both → caught by both metrics

### MediaPipe Face Mesh Landmark Reference
Key landmarks for vertical detection:

**Nose landmarks** (for pitch):
- Landmark 1: Nose tip
- Landmark 2: Nose bridge
- Landmarks 98, 327: Nose sides

**Forehead/Upper Face**:
- Landmarks 10, 151: Top of face

**Chin/Lower Face**:
- Landmarks 152, 175: Bottom of face

**Eye Region** (for vertical gaze):
- Upper eyelid: 159, 158, 157, 173, 133
- Lower eyelid: 144, 145, 153, 154, 155
- Iris center: average of landmarks 468-477
- Eye center: average of all eye landmarks

**Iris Landmarks** (468-477):
- Left iris: 468, 469, 470, 471, 472
- Right iris: 473, 474, 475, 476, 477
- Use vertical position relative to eye bounds

### Pitch Calculation Strategy
Recommended approach:

```javascript
// Get vertical landmarks
const noseTop = keypoints[168]; // Nose bridge/upper nose
const noseBottom = keypoints[1]; // Nose tip
const foreheadRef = keypoints[10]; // Forehead reference
const chinRef = keypoints[152]; // Chin reference

// Calculate vertical ratios
const faceHeight = chinRef.y - foreheadRef.y;
const noseToForehead = noseTop.y - foreheadRef.y;
const noseVerticalRatio = noseToForehead / faceHeight;

// When looking down, nose appears higher in face (smaller ratio)
// When looking up, nose appears lower in face (larger ratio)
// Neutral: ratio around 0.3-0.4
// Looking down: ratio < 0.25
// Looking up: ratio > 0.45

const pitch = (noseVerticalRatio - 0.35) * 100; // Normalize to degrees
// Negative pitch = looking down
// Positive pitch = looking up
```

Alternative approach using nose angle:
```javascript
const leftFace = keypoints[234];
const rightFace = keypoints[454];
const noseTip = keypoints[1];
const noseBridge = keypoints[6];

const noseVector = {
  y: noseTip.y - noseBridge.y
};

// When looking down, noseTip.y > noseBridge.y (positive y)
// When looking up, noseTip.y < noseBridge.y (negative y)

const faceWidth = Math.abs(rightFace.x - leftFace.x);
const pitch = (noseVector.y / faceWidth) * 90; // Rough angle
```

### Vertical Gaze Calculation Strategy
Recommended approach:

```javascript
// Get iris and eye bounds
const leftIrisCenter = getCenter(LEFT_IRIS.map(idx => keypoints[idx]));
const rightIrisCenter = getCenter(RIGHT_IRIS.map(idx => keypoints[idx]));

// Get eye vertical bounds
const upperEyeLandmarks = [159, 158, 157]; // Top of eye
const lowerEyeLandmarks = [160, 145, 153]; // Bottom of eye

const upperEyeY = getCenter(upperEyeLandmarks.map(idx => keypoints[idx])).y;
const lowerEyeY = getCenter(lowerEyeLandmarks.map(idx => keypoints[idx])).y;
const eyeHeight = lowerEyeY - upperEyeY;

// Calculate iris vertical position
const eyeCenterY = (leftIrisCenter.y + rightIrisCenter.y) / 2;
const eyeRegionCenterY = (upperEyeY + lowerEyeY) / 2;

const verticalDeviation = (eyeCenterY - eyeRegionCenterY) / eyeHeight;
// verticalDeviation > 0 → looking down
// verticalDeviation < 0 → looking up
// verticalDeviation ≈ 0 → looking straight

const isLookingDown = verticalDeviation > 0.2; // Threshold to tune
```

### Threshold Tuning Guidelines
Start with these values and adjust based on testing:

```javascript
CONFIG.detection = {
  headTurnThreshold: 30, // degrees - horizontal (existing)
  headPitchThreshold: 15, // degrees - vertical (new)
  verticalGazeThreshold: 0.2, // normalized - iris vertical position (new)
}
```

**If detection is too sensitive** (triggers when looking at screen):
- Increase `headPitchThreshold` to 20-25 degrees
- Increase `verticalGazeThreshold` to 0.3-0.4
- Add minimum duration requirement (e.g., 500ms of looking down)

**If detection is not sensitive enough** (doesn't detect phone checking):
- Decrease `headPitchThreshold` to 10-12 degrees
- Decrease `verticalGazeThreshold` to 0.15
- Use OR logic instead of AND (trigger if pitch OR gaze indicates down)

### Testing Different Scenarios
Key scenarios to test:

1. **Reading phone on desk** - head tilted down ~30-45 degrees
2. **Reading phone at eye level** - head mostly straight, eyes looking down
3. **Taking notes** - head tilted down, eyes down
4. **Resting chin on hand** - head tilted but might be looking at screen
5. **Slouching** - head angle changes but might still be looking at screen
6. **Looking at keyboard** - brief downward glances
7. **Reading bottom of screen** - eyes down but still looking at screen

Fine-tune thresholds to maximize detection of #1-3 while avoiding false positives on #4-7.

### Performance Considerations
- Head pose calculation adds minimal overhead (simple geometric calculations)
- Vertical gaze calculation reuses existing iris landmarks (already computed)
- No additional ML models needed (uses MediaPipe Face Mesh)
- Debug logging should be reduced in production to avoid console spam
- Consider caching intermediate calculations if performance becomes an issue

### Future Enhancements
Potential improvements for future iterations:
- Machine learning model trained on user-specific "looking down" patterns
- Temporal smoothing to prevent flickering (rolling average of pitch)
- Different sensitivity modes (strict vs lenient)
- Configurable detection profiles (work vs study vs gaming)
- Statistics on how often user looks down
- Gentle reminders vs jumpscare based on duration
