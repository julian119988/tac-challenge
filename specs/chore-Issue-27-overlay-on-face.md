# Chore: Overlay on Face

## Metadata
adw_id: `Issue #27`
prompt: `We are not showing any overlays on the face right now.

I would like to show something to know if the tracking is working.`

## Chore Description
Fix the face overlay visualization that is currently not displaying despite the code being implemented. The application has visualization code to draw a red transparent box around detected faces along with landmark dots on important facial features (eyes, nose, mouth, face outline), but these overlays are not currently showing on the screen. This chore will debug and fix the visualization rendering issue to provide visual feedback that face tracking is working.

The code in `apps/frontend/app.js` already contains the `drawFaceVisualization()` method (lines 170-220) that should render the face overlay, but it's not being triggered properly. The detection system is returning face data including `faceBoundingBox`, `leftEyeLandmarks`, `rightEyeLandmarks`, `noseLandmarks`, `mouthLandmarks`, and `faceOutlineLandmarks` from the `FaceDetector.detect()` method (in `face-detection.js` lines 102-114), but something is preventing this data from being rendered on the canvas.

## Relevant Files
Use these files to complete the chore:

- **apps/frontend/app.js** (lines 145-220) - Contains the `CameraManager.startRendering()` method and `drawFaceVisualization()` method that should render the face overlay; the rendering logic checks for `latestDetection.faceBoundingBox` (line 156) before drawing
- **apps/frontend/face-detection.js** (lines 34-123) - Contains the `FaceDetector.detect()` method that returns detection results including `faceBoundingBox` and all facial landmarks
- **apps/frontend/config.js** (lines 37-47) - Contains visualization configuration including colors, line width, and landmark radius settings
- **apps/frontend/index.html** (lines 28-29) - Contains the canvas element where visualization should be rendered

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Debug Detection Data Flow
- Add console logging to `apps/frontend/app.js` in the `startContinuousDetection()` method to log the detection results
- Add console logging to verify if `detection.faceBoundingBox` is present in the detection results
- Add console logging in `updateDetection()` method to confirm `latestDetection` is being set
- Run the app and check browser console to see if detection data includes `faceBoundingBox`
- Identify if the issue is:
  - Detection not returning `faceBoundingBox` data
  - Detection data not being passed to `updateDetection()`
  - Rendering loop not accessing `latestDetection` properly
  - Canvas context issues

### 2. Fix Face Detection Return Data
- Open `apps/frontend/face-detection.js`
- Verify that the `detect()` method is calculating `faceBoundingBox` using `getFaceBoundingBox()` (line 87)
- Ensure `getFaceBoundingBox()` is being called with the correct `keypoints` parameter
- Confirm that the return statement (lines 102-114) includes `faceBoundingBox` in the returned object
- If `faceBoundingBox` is missing from the return, add it
- Verify all landmark arrays are being properly extracted and returned

### 3. Fix Rendering Data Flow
- Open `apps/frontend/app.js`
- In `startContinuousDetection()` method (lines 372-396), verify that `this.cameraManager.updateDetection(detection)` is being called with the detection results
- In `updateDetection()` method (lines 260-262), verify that `this.latestDetection = detection` is properly storing the detection data
- In `startRendering()` method (lines 147-165), verify the condition on line 156 (`if (this.latestDetection && this.latestDetection.faceBoundingBox)`) is being met
- Add defensive null checks if needed
- Ensure the rendering loop is calling `drawFaceVisualization()` with the correct data

### 4. Verify Canvas Context and Drawing Logic
- Open `apps/frontend/app.js`
- In `drawFaceVisualization()` method (lines 170-220), verify:
  - Canvas context (`this.ctx`) is properly initialized
  - Canvas is not being cleared after drawing the overlay
  - Drawing happens after the video frame is drawn (line 153) but before the next animation frame
  - Color values from CONFIG are valid rgba strings
  - All coordinate values are numbers, not undefined
- Check that the drawing order is correct: video frame → face overlay
- Ensure the canvas is visible and properly sized

### 5. Test Visualization Configuration
- Open `apps/frontend/config.js`
- Verify visualization settings (lines 37-47) have valid values:
  - `faceBoxColor`: should be a valid rgba color string
  - `faceBoxFillColor`: should be a valid rgba color string with low opacity
  - `landmarkColor`: should be a valid rgba color string
  - `faceBoxLineWidth`: should be a positive number
  - Landmark radius values should be positive numbers
- Test with more visible colors if needed (e.g., increase opacity)
- Adjust landmark sizes to make them more visible

### 6. Manual Testing and Validation
- Open the app in a browser at http://localhost:8000/apps/frontend/
- Grant camera permissions
- Observe the camera canvas for:
  - Red transparent box around detected face
  - Red dots on eye landmarks
  - Red dots on nose landmarks
  - Red dots on mouth landmarks
  - Smaller red dots on face outline
- Move face around to verify overlay follows face in real-time
- Check browser console for any errors or warnings
- Test in different lighting conditions
- Verify overlay updates smoothly without flickering

### 7. Cleanup and Finalize
- Remove any debug console.log statements added during debugging
- Ensure code is clean and well-formatted
- Verify all visualization features are working as expected
- Test that overlay doesn't interfere with face detection performance

## Validation Commands
Execute these commands to validate the chore is complete:

- **Start local server**:
  ```bash
  python -m http.server 8000
  ```
  Then navigate to http://localhost:8000/apps/frontend/

- **Visual verification**:
  - Confirm red transparent box appears around face
  - Confirm red dots appear on eyes (larger dots, radius 3)
  - Confirm red dots appear on nose (radius 3)
  - Confirm red dots appear on mouth (radius 3)
  - Confirm smaller red dots appear on face outline (radius 2)
  - Verify overlay updates in real-time as face moves

- **Browser console check**:
  - Open browser DevTools console (F12)
  - Verify no JavaScript errors are present
  - Check that detection logs show `faceDetected: true` when face is visible
  - Verify `faceBoundingBox` object is present in detection results

- **Code verification**:
  ```bash
  grep -n "faceBoundingBox" apps/frontend/face-detection.js
  ```
  Should show `faceBoundingBox` in the return statement

  ```bash
  grep -n "drawFaceVisualization" apps/frontend/app.js
  ```
  Should show the method definition and call site

- **Performance check**:
  - Verify face detection runs smoothly without lag
  - Check that overlay rendering doesn't reduce frame rate significantly
  - Confirm camera feed remains responsive

## Notes

### Current Implementation Status
The visualization code was implemented in Issue #25 and includes:
- `drawFaceVisualization()` method in `app.js` (lines 170-220)
- Face bounding box calculation in `face-detection.js` (lines 265-286)
- Landmark extraction and return data (lines 79-114 in `face-detection.js`)
- Visualization config in `config.js` (lines 37-47)

However, the overlay is not currently displaying, suggesting a data flow or rendering issue.

### Likely Root Causes
Based on code analysis, the issue is likely one of:
1. **Missing return data**: The `detect()` method might not be returning `faceBoundingBox` in all cases
2. **Timing issue**: The detection data might not be set before the first render
3. **Canvas clearing**: The overlay might be drawn but immediately cleared
4. **Visibility issue**: Colors might be too transparent or canvas z-index issues

### Detection Flow
Current flow should be:
1. `FaceDetector.detect(video)` → returns detection object with `faceBoundingBox` and landmarks
2. `startContinuousDetection()` → calls `this.cameraManager.updateDetection(detection)`
3. `CameraManager.updateDetection()` → stores in `this.latestDetection`
4. `CameraManager.startRendering()` → checks `this.latestDetection.faceBoundingBox` and calls `drawFaceVisualization()`
5. `drawFaceVisualization()` → draws red box and landmark dots on canvas

### MediaPipe Face Mesh Landmarks
The app uses MediaPipe Face Mesh which provides 468 facial landmarks. Important indices used:
- **Left eye**: indices 33, 133, 160, 159, 158, 157, 173
- **Right eye**: indices 362, 263, 385, 386, 387, 388, 398
- **Nose**: indices 1, 2, 98, 327
- **Mouth**: indices 61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308
- **Face outline**: indices 10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109

### Privacy Note
All processing remains client-side in the browser - no changes to privacy model required.
