# Chore: Big changes on the frontend

## Metadata
adw_id: `Issue #25`
prompt: `Lets change the UI of the frontend and the behaviour.

1. Lets delete the "Session Statistics" section
2. Delete the "Distracted - Get back to work!" I don't want this to track a session per se
3. Display a red transparent box on the face in real time + dots on face in important places
4. As soon as we arrive to the page we ask for video permissions, don't wait for the user to click start session, in fact lets delete that button too.`

## Chore Description
This chore transforms the Focus Keeper app from a session-based distraction tracker to a real-time face detection visualization tool. The changes remove session statistics tracking and start/stop controls, replacing them with automatic camera activation and enhanced face landmark visualization. The app will now display a transparent red box around the detected face with dots on important facial landmarks, and will remove all distraction messaging and session-based UI elements.

## Relevant Files
Use these files to complete the chore:

- **apps/frontend/index.html** - Main HTML structure containing UI elements to be removed (Session Statistics section, Start Session button, status messages) and updated camera canvas setup
- **apps/frontend/app.js** - Main application logic that needs to be modified to:
  - Auto-start camera on page load instead of waiting for button click
  - Remove session start/stop functionality
  - Remove "Distracted - Get back to work!" status messages
  - Update the rendering logic to draw face box and landmarks
- **apps/frontend/face-detection.js** - Face detection module that needs to be updated to return face bounding box and all facial landmarks for visualization
- **apps/frontend/styles.css** - CSS styles to be updated by removing stats section styles and potentially adding styles for the new face visualization overlay
- **apps/frontend/config.js** - Configuration file that may need updates to visualization settings (colors, landmark points to display, etc.)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Remove Session Statistics Section from HTML
- Open `apps/frontend/index.html`
- Delete the entire `<div class="stats-section">` element (lines 43-67) including all stat cards for Session Time, Focus Time, Distractions, Interventions, and Focus Score
- Remove the Start Session button from the controls section (line 39)
- Remove or update the status section to remove session-related messaging

### 2. Update Face Detection to Return Face Bounding Box and All Landmarks
- Open `apps/frontend/face-detection.js`
- Modify the `detect()` method to return the face bounding box coordinates
- Add face outline landmarks to the return value (not just eye landmarks)
- Include important facial landmarks (eyes, nose, mouth, face contour) in the detection results
- Return all keypoints needed for visualization

### 3. Implement Face Box and Landmark Visualization in Camera Rendering
- Open `apps/frontend/app.js`
- Update `CameraManager.drawEyeRectangles()` method or create new method `drawFaceVisualization()`
- Draw a transparent red rectangle around the entire detected face using face bounding box
- Draw dots/circles on important facial landmarks (eyes, nose, mouth corners, face outline points)
- Use semi-transparent red color (rgba) for the face box overlay
- Ensure visualization updates in real-time with face detection

### 4. Auto-start Camera on Page Load
- Open `apps/frontend/app.js`
- Modify `FocusKeeperApp.initialize()` method to automatically start the camera after initialization completes
- Remove the button click event listener for session toggle
- Call `this.startCamera()` or equivalent method directly in the initialize flow
- Handle camera permission errors gracefully with error messages

### 5. Remove Session-Based Functionality and Distraction Messages
- Open `apps/frontend/app.js`
- Remove the `DistractionMonitor` class or disable distraction detection logic
- Remove all references to "Distracted - Get back to work!" status messages
- Remove session statistics tracking (session time, focus time, distraction count)
- Remove the `updateStatsDisplay()` method and related stats update intervals
- Clean up any intervention video logic if not needed

### 6. Update Status Display Logic
- Open `apps/frontend/app.js`
- Modify `updateStatus()` method to only show camera/loading states, not distraction states
- Remove status messages like "Focused - Keep your eyes on the screen!" and "Distracted - Get back to work!"
- Keep only technical status messages: "Loading face detection model...", "Camera active", error messages
- Update status indicator colors to reflect camera/detection state only

### 7. Clean Up CSS Styles
- Open `apps/frontend/styles.css`
- Remove or comment out styles for `.stats-section`, `.stats-grid`, `.stat-card`, `.stat-label`, `.stat-value`
- Remove styles for the start button if completely removed
- Ensure camera canvas styles support the new visualization overlay
- Consider adding styles for face landmark dots if needed (e.g., `.face-landmark` class)

### 8. Update Configuration
- Open `apps/frontend/config.js`
- Add configuration for face visualization (face box color, landmark dot size, transparency)
- Remove or update detection timeout settings if session tracking is removed
- Update any UI-related config values to match new behavior

### 9. Test and Validate
- Open the app in a browser (via localhost or HTTPS)
- Verify camera starts automatically on page load
- Confirm camera permission prompt appears immediately
- Check that red transparent box appears around detected face
- Verify dots appear on facial landmarks
- Confirm Session Statistics section is removed
- Verify no "Distracted - Get back to work!" messages appear
- Test that face visualization updates in real-time as face moves

## Validation Commands
Execute these commands to validate the chore is complete:

- **Visual inspection**: Open `apps/frontend/index.html` in a browser and verify:
  - Camera starts automatically on page load
  - No Session Statistics section visible
  - No Start Session button visible
  - Red transparent box appears around face
  - Dots appear on facial landmarks in real-time
  - No distraction messages appear

- **Code verification**:
  - `grep -n "Session Statistics" apps/frontend/index.html` - Should return no results
  - `grep -n "Start Session" apps/frontend/index.html` - Should return no results
  - `grep -n "Distracted - Get back to work" apps/frontend/app.js` - Should return no results
  - `grep -n "stats-section" apps/frontend/styles.css` - Should return no results or only commented code

- **File validation**: Ensure all modified files have no syntax errors
  - Open browser console and check for JavaScript errors
  - Verify CSS renders correctly without broken styles

## Notes
- The app is currently using TensorFlow.js MediaPipe Face Mesh model which provides 468 facial landmarks - we can use these for detailed visualization
- Current eye detection already draws rectangles around eyes (app.js:170-190), this pattern can be extended for the full face
- The detection loop is already running via `requestAnimationFrame` (app.js:289-305), so real-time updates are already in place
- Camera permission handling is already implemented (app.js:62-129), we just need to trigger it on page load
- The `latestDetection` object already contains landmark data that can be used for visualization
- Consider using important MediaPipe Face Mesh landmark indices for face outline: 10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109
