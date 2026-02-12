# Chore: UI changes + skeleton - Remove eye tracking training, add overlay toggle

## Metadata
adw_id: `Issue #31`
prompt: `Lets remove the "Eye Tracking Training" section, I would only like a button to toggle the red overlay over the face. The overlay should be defaulted to not show.`

## Chore Description
Simplify the Focus Keeper UI by removing the entire "Eye Tracking Training" section (calibration, training, session controls, heatmap visualization) and replacing it with a single toggle button that controls the red face overlay visualization. The overlay should be hidden by default and only show when the user explicitly enables it via the toggle button.

This simplification removes the ML eye tracking features while keeping the core face detection and overlay functionality.

## Relevant Files
Use these files to complete the chore:

- **apps/frontend/index.html** - Contains the eye tracking training panel HTML that needs to be removed (lines 45-97) and needs a new toggle button added for the overlay control
- **apps/frontend/styles.css** - Contains CSS for eye tracking panels (.eye-tracking-panel, .training-status, .calibration-target, .training-progress, .heatmap-canvas) that should be removed or kept minimal for future use
- **apps/frontend/app.js** - Main application file that initializes eye tracking components (lines 310-436) and updates the camera overlay visualization. Need to disable eye tracking initialization and add overlay toggle control
- **apps/frontend/ui-controller.js** - Manages the eye tracking UI interactions. This file may no longer be needed, but we'll keep it in case of future use
- **apps/frontend/config.js** - Contains eyeTracking.enabled flag (line 66) that should be set to false by default
- **apps/frontend/face-detection.js** - Handles face detection; no changes needed, just verify it continues working
- **apps/frontend/video-player.js** - Handles skeleton video playback; no changes needed

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update Configuration
- Set `CONFIG.eyeTracking.enabled` to `false` in apps/frontend/config.js:66
- Set `CONFIG.visualization.faceBoxFillColor` to transparent initially so overlay is hidden by default
- Add a new config option `CONFIG.visualization.overlayVisible` set to `false`

### 2. Remove Eye Tracking Training UI from HTML
- Remove the entire "Eye Tracking Training Panel" section (lines 45-77 in apps/frontend/index.html)
- Remove the "Eye Tracking Session Panel" section (lines 80-88)
- Remove the "Eye Tracking Heatmap Panel" section (lines 91-97)
- Remove hidden canvases for eye tracking (lines 121-122): `#eyes` and `#heatMap`
- Remove calibration target element (line 125): `#calibration-target`
- Remove training progress overlay element (line 128): `#training-progress`

### 3. Add Overlay Toggle Button to HTML
- Add a new simple control panel after the status section in apps/frontend/index.html
- Create a toggle button with id `toggle-overlay` to control face overlay visibility
- Style it as a single centered button with clear labeling ("Show Face Overlay" / "Hide Face Overlay")

### 4. Disable Eye Tracking Initialization in app.js
- Comment out or remove the eye tracking initialization code in apps/frontend/app.js (lines 376-436)
- Remove eye tracking component properties (eyeTracker, datasetManager, modelTrainer, gazePredictor, uiController) from constructor (lines 310-315)
- Remove the conditional check for `CONFIG.eyeTracking.enabled` and its associated initialization call (lines 376-378)
- Remove the UI controller notification in startCamera method (lines 456-458)

### 5. Remove Eye Tracking Detection Updates in app.js
- Remove eye tracker update logic in startContinuousDetection (lines 558-560)
- Remove UI controller face detection callbacks (lines 495-507)
- Keep only the camera manager detection updates (lines 491-493)

### 6. Add Overlay Toggle Functionality
- Add overlay toggle button event listener in apps/frontend/app.js initialize method
- Create a method `toggleOverlay()` that switches between showing/hiding the red face overlay
- Update the overlay by modifying `CONFIG.visualization.overlayVisible` and conditionally rendering the overlay in `CameraManager.drawFaceVisualization()`
- Modify `CameraManager.drawFaceVisualization()` to check `CONFIG.visualization.overlayVisible` before drawing (lines 175-246)

### 7. Update drawFaceVisualization to Respect Toggle
- Add a check at the beginning of `drawFaceVisualization()` method in apps/frontend/app.js:175
- If `CONFIG.visualization.overlayVisible` is false, return early without drawing anything
- Keep all existing drawing logic intact when overlay is visible

### 8. Clean Up CSS (Optional)
- Keep eye tracking CSS classes for potential future use, but they won't be referenced anymore
- Add simple styling for the new overlay toggle button panel

### 9. Test the Implementation
- Open apps/frontend/index.html in a browser
- Verify the eye tracking training section is gone
- Verify the overlay toggle button is visible
- Verify the overlay is hidden by default when page loads
- Click the toggle button and verify the red overlay appears over detected faces
- Click again and verify the overlay disappears
- Verify skeleton video still works when looking away (attention grabber feature from Issue #29)

## Validation Commands
Execute these commands to validate the chore is complete:

- `grep -n "eye-tracking-panel" apps/frontend/index.html` - Should return no results (verify training panels removed)
- `grep -n "toggle-overlay" apps/frontend/index.html` - Should return results showing new toggle button exists
- `grep -n "eyeTracking.enabled" apps/frontend/config.js` - Should show it's set to false
- `grep -n "overlayVisible" apps/frontend/config.js` - Should show new config option exists
- `grep -n "initializeEyeTracking" apps/frontend/app.js` - Should show the method is commented out or removed from initialize()
- Manual browser test - Open apps/frontend/index.html and verify:
  - No eye tracking training UI visible
  - Toggle button is present
  - Overlay is hidden by default
  - Toggle button shows/hides the red overlay
  - Face detection and skeleton video still work

## Notes
- The eye tracking JavaScript modules (eye-tracker.js, dataset-manager.js, model-trainer.js, gaze-predictor.js, ui-controller.js, heatmap-viz.js) are being kept in the codebase but will not be initialized or used. They can be removed in a future cleanup if desired.
- The attention grabber skeleton video feature (Issue #29) should continue working as it only depends on face detection, not eye tracking.
- The face detection overlay visualization code in CameraManager is preserved and just made conditional based on the toggle state.
