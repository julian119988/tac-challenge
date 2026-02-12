# Chore: Implement Eye Tracking Solution Based on HUE Vision Example

## Metadata
adw_id: `at`
prompt: `Looking at the example/hue-vision lets implement an eye tracking solution similar to the example`

## Chore Description

Implement a comprehensive eye tracking solution for the Focus Keeper frontend application, modeled after the HUE Vision example found in `example/hue-vision/`. This will transform the current basic face detection system into a fully-featured gaze tracking system with machine learning capabilities.

The implementation will add:
- **Calibration System**: User trains the model by looking at target points across the screen
- **ML-Powered Gaze Prediction**: TensorFlow.js CNN model for accurate gaze coordinate prediction
- **Real-time Eye Tracking**: Continuous gaze prediction using trained model
- **Dataset Management**: Collection, export, and import of training data
- **Multi-Phase UI**: Training → Session → Heatmap visualization workflow
- **Heatmap Visualization**: Visual representation of where user looked during session

This enhances the current simple heuristic-based gaze detection with a personalized, machine-learning approach that adapts to each user's unique eye characteristics.

## Relevant Files

### Existing Files to Modify

- **apps/frontend/index.html** - Add new UI panels (training, calibration, heatmap), TensorFlow.js script, jQuery dependency, hidden canvases for eye extraction and heatmap overlay
- **apps/frontend/face-detection.js** - Enable iris landmarks (`refineLandmarks: true`), extract iris landmark indices (468-477), return iris positions in detection results
- **apps/frontend/app.js** - Integrate new eye tracking modules, replace simple gaze heuristics with ML predictions
- **apps/frontend/config.js** - Add eye tracking configuration (model hyperparameters, calibration settings, prediction thresholds)
- **apps/frontend/styles.css** - Add styles for training panel, calibration target, heatmap overlay, progress indicators, button states

### Reference Files (HUE Vision Example)

- **example/hue-vision/index.html** - UI structure reference (lines 20-189)
- **example/hue-vision/js/facetracker.js** - MediaPipe FaceMesh + iris tracking implementation (lines 77-187)
- **example/hue-vision/js/dataset.js** - Dataset collection and management (lines 1-229)
- **example/hue-vision/js/training.js** - TensorFlow.js CNN model architecture and training (lines 6-200)
- **example/hue-vision/js/main.js** - Real-time prediction loop and event handlers (lines 26-287)
- **example/hue-vision/js/ui.js** - Multi-phase UI state management
- **example/hue-vision/js/heat.js** - Heatmap visualization
- **example/hue-vision/style.css** - Styling reference

### New Files

- **apps/frontend/eye-tracker.js** - Eye region extraction, iris landmark processing, MediaPipe FaceMesh integration with iris detection enabled
- **apps/frontend/dataset-manager.js** - Training data collection, train/validation split (80/20), tensor management, JSON export/import
- **apps/frontend/model-trainer.js** - TensorFlow.js CNN model creation (Conv2D → MaxPool → Flatten → Dropout → Concatenate → Dense), model training with validation, model persistence (localStorage/file export)
- **apps/frontend/gaze-predictor.js** - Real-time gaze prediction loop (10 FPS), model inference, coordinate conversion, session data collection
- **apps/frontend/ui-controller.js** - Multi-phase UI state management (training → session → heatmap), button state management, progress indicators
- **apps/frontend/heatmap-viz.js** - Gaze heatmap rendering, density gradient visualization, session replay
- **apps/frontend/utils.js** - Shared utility functions (tensor operations, coordinate normalization, file download)

## Step by Step Tasks

### 1. Setup Dependencies and HTML Structure

- Update `apps/frontend/index.html` to add TensorFlow.js CDN script tag (v4.15.0) in `<head>` section
- Add jQuery CDN script tag (v3.3.1) for UI manipulation
- Create hidden canvas element `<canvas id="eyes" width="55" height="25"></canvas>` for eye region cropping
- Create heatmap canvas overlay `<canvas id="heatMap"></canvas>` positioned absolute over content
- Create calibration target element `<div id="target"></div>` for user to follow
- Add training panel UI with status table, data collection buttons, model training controls
- Add session panel UI with start/stop tracking buttons, draw heatmap button
- Add heatmap panel UI with new session and retrain model buttons
- Include module script tags for all new JavaScript files in correct dependency order

### 2. Enable Iris Landmark Detection

- Modify `apps/frontend/face-detection.js` detector config to set `refineLandmarks: true` (enables iris tracking)
- Update `calculateGazeDirection()` to extract iris landmark indices (LEFT_IRIS: 468-472, RIGHT_IRIS: 473-477)
- Calculate iris centers by averaging iris landmark positions
- Return iris positions and landmarks in detection result object
- Add iris landmarks to visualization in `drawFaceVisualization()`

### 3. Implement Eye Tracker Module

- Create `apps/frontend/eye-tracker.js` based on `example/hue-vision/js/facetracker.js`
- Implement `extractEyeRegion(landmarks)` function to calculate eye bounding box from iris centers
- Calculate eye center X/Y as average of left and right iris centers
- Set eye width as 1.5x distance between irises, height as 0.6 aspect ratio
- Implement `cropEyeToCanvas(videoElement, eyeRect)` to draw eye region to hidden canvas
- Store current eye rect metadata [x, y, width, height] for dataset
- Export functions: `getCurrentEyeImage()`, `getCurrentEyeRect()`, `getEyeMetadata()`

### 4. Implement Dataset Manager Module

- Create `apps/frontend/dataset-manager.js` based on `example/hue-vision/js/dataset.js`
- Initialize dataset structure with train/val objects containing {n: count, x: [images, metadata], y: coordinates}
- Implement `getImage()` to capture eye canvas as normalized tensor (toFloat().div(127).sub(1))
- Implement `getMetaInfos()` to return eye rect metadata as normalized tensor [centerX, centerY, width, height]
- Implement `convertImage()` to convert RGB to grayscale with spatial coordinates
- Implement `whichDataset()` to randomly split 80% train, 20% validation
- Implement `addExample(image, metadata, targetCoords)` to add data point to dataset
- Implement `captureExample()` to capture current eye image + mouse position
- Implement `toJSON()` and `fromJSON()` for dataset persistence
- Implement `clearSession()` to reset session tracking data

### 5. Implement Model Trainer Module

- Create `apps/frontend/model-trainer.js` based on `example/hue-vision/js/training.js`
- Implement `createModel()` CNN architecture:
  - Input 1: Eye image tensor [55, 25, 3]
  - Input 2: Meta info tensor [4] (eye position and size)
  - Conv2D layer: 5x5 kernel, 20 filters, ReLU activation
  - MaxPooling2D: 2x2 pool size, 2x2 strides
  - Flatten layer
  - Dropout: 0.2 rate
  - Concatenate: Flattened features + meta info
  - Dense output: 2 units (x, y), tanh activation
- Implement `fitModel()` with Adam optimizer (lr=0.0005), MSE loss, 20 epochs
- Calculate dynamic batch size: 10% of training data (min 2, max 64)
- Implement early stopping: save best model based on validation loss
- Add callbacks for `onEpochBegin`, `onEpochEnd`, `onTrainEnd` to update UI
- Implement `getPrediction()` to run model inference on current eye image
- Implement `resetModel()` to clear model and training state
- Implement model save/load using `tf.loadLayersModel()` and `model.save()`

### 6. Implement Gaze Predictor Module

- Create `apps/frontend/gaze-predictor.js` based on `example/hue-vision/js/main.js:26-47`
- Implement prediction loop using `setInterval(100)` for 10 FPS prediction rate
- In each iteration: get current eye image, get metadata, run model prediction
- Convert model output from [-0.5, 0.5] range to screen coordinates [0, 1]
- Store session predictions in arrays for heatmap: `{x: [], y: [], n: count}`
- Implement `startTracking()` to begin prediction loop and clear session data
- Implement `stopTracking()` to pause prediction loop
- Implement `getSessionData()` to return collected gaze coordinates

### 7. Implement UI Controller Module

- Create `apps/frontend/ui-controller.js` based on `example/hue-vision/js/ui.js`
- Implement state machine with phases: 'initial', 'training', 'session', 'heatmap'
- Implement `showPhase(phaseName)` to toggle visibility of UI panels
- Implement `onWebcamEnabled()` to enable calibration button when camera ready
- Implement `onFoundFace()` to update face detection status indicator
- Implement `onAddExample(trainCount, valCount)` to update data point counters
- Implement `showTrainingProgress(epoch, totalEpochs, trainLoss, valLoss)` with progress bar
- Implement `onFinishTraining()` to enable session controls and show completion message
- Implement `startCalibration()` to show moving target and capture data on spacebar
- Implement button state management: enable/disable based on current state
- Add keyboard shortcuts: Space (capture), C (calibrate), T (train), H (heatmap), R (reset)

### 8. Implement Heatmap Visualization Module

- Create `apps/frontend/heatmap-viz.js` based on `example/hue-vision/js/heat.js`
- Initialize heatmap canvas with same dimensions as window
- Implement `drawHeatmap(sessionData)` to render gaze concentration
- Create density map by binning gaze coordinates into grid cells
- Apply Gaussian blur for smooth gradient effect
- Map density values to color gradient (blue → green → yellow → red)
- Render to heatmap canvas with opacity overlay
- Implement `clearHeatmap()` to hide and reset heatmap canvas

### 9. Implement Utility Functions Module

- Create `apps/frontend/utils.js` for shared helper functions
- Implement `downloadJSON(data, filename)` for dataset export
- Implement `downloadModel(model, filename)` for model export
- Implement `normalizeCoordinates(x, y, width, height)` for coordinate conversion
- Implement `tensorToArray(tensor)` for tensor serialization
- Implement `arrayToTensor(array, shape)` for tensor deserialization
- Implement `clamp(value, min, max)` for value bounds checking

### 10. Update Configuration

- Modify `apps/frontend/config.js` to add eye tracking section:
  - `eyeTracking.enabled`: Enable/disable eye tracking features
  - `eyeTracking.modelHyperparams`: {epochs: 20, batchSizeRatio: 0.1, learningRate: 0.0005}
  - `eyeTracking.calibration`: {targetSize: 40, gridPoints: 9, autoMoveDelay: 2000}
  - `eyeTracking.prediction`: {updateInterval: 100, confidenceThreshold: 0.7}
  - `eyeTracking.visualization`: {heatmapOpacity: 0.7, colorScheme: 'hot'}

### 11. Integrate Eye Tracking with Main App

- Modify `apps/frontend/app.js` to import all new modules
- Initialize eye tracker, dataset manager, model trainer, gaze predictor, UI controller
- Replace simple gaze heuristics in `FaceDetector.calculateGazeDirection()` with ML prediction when model available
- Add fallback: use heuristics if model not trained, use ML prediction if model available
- Update `DistractionMonitor` to use predicted gaze coordinates for distraction detection
- Wire up event handlers for calibration, training, tracking buttons
- Update camera rendering to visualize eye region bounding box during calibration
- Add model initialization on app startup: attempt to load saved model from localStorage

### 12. Update Styles

- Modify `apps/frontend/styles.css` to add training panel styles
- Add calibration target styles: circular, animated pulse, position absolute
- Add heatmap canvas styles: full screen overlay, pointer-events none
- Add progress bar styles for training visualization
- Add button state styles: enabled, disabled, in-progress
- Add panel toggle animations for smooth transitions
- Add status indicator colors for different states
- Add responsive design for smaller screens

### 13. Test Calibration Workflow

- Open app in browser and grant camera permissions
- Verify face detection initializes with iris landmarks visible
- Click "Start Calibration" button and verify target appears
- Follow target with eyes and press spacebar to capture data points
- Verify data point counter increments (target: 50+ samples)
- Check browser console for successful tensor creation and dataset addition
- Verify train/validation split (approximately 80/20 ratio)

### 14. Test Model Training

- After collecting calibration data, click "Start Training" button
- Verify training progress updates in UI (epoch counter, loss metrics)
- Monitor browser console for training logs (loss should decrease)
- Wait for training completion (20 epochs, ~30-60 seconds)
- Verify model accuracy displayed (target: >80% accuracy = <0.2 loss)
- Check that best model is saved to localStorage
- Test "Reset Model" button clears training state

### 15. Test Real-Time Prediction

- After training completes, click "Start Tracking" button
- Move eyes around screen and verify prediction indicator follows gaze
- Check browser console for prediction coordinates (should be [0-1] range)
- Verify prediction updates at approximately 10 FPS
- Test "Stop Tracking" button pauses predictions
- Verify session data collection for heatmap

### 16. Test Heatmap Visualization

- After tracking session, click "Draw Heatmap" button
- Verify heatmap overlay renders with color gradient
- Check that high-concentration areas show warmer colors (red/yellow)
- Verify low-concentration areas show cooler colors (blue/green)
- Test "Clear Heatmap" to hide visualization
- Test "New Session" to reset and start fresh tracking session

### 17. Test Dataset and Model Persistence

- Click "Save Dataset" and verify JSON file downloads
- Clear page data and click "Load Dataset" to import saved file
- Verify data point counters restore correctly
- Click "Save Model" and verify model files download (.json + .bin)
- Reset model and click "Load Model" to import saved files
- Verify model works for predictions after loading

### 18. Integration Testing

- Test full workflow: calibration → training → tracking → heatmap
- Verify smooth transitions between UI phases
- Test keyboard shortcuts work correctly
- Test with different lighting conditions
- Test with/without glasses
- Test model performance degrades gracefully with poor data
- Verify error handling for missing camera, failed model loading
- Test on multiple browsers (Chrome, Firefox, Safari)

### 19. Validate Performance

- Monitor browser performance during training (should complete in <2 minutes)
- Check prediction latency (should be <100ms per prediction)
- Verify no memory leaks during long sessions (check with Chrome DevTools)
- Ensure smooth animations and UI responsiveness
- Test with lower-end devices if possible

## Validation Commands

Execute these commands to validate the chore is complete:

- `cd apps/frontend && python -m http.server 8080` - Start local server
- Navigate to `http://localhost:8080` in Chrome browser
- Open DevTools console and verify no JavaScript errors on page load
- Grant camera permissions and verify face detection initializes
- Complete calibration (collect 50+ data points) and verify console shows "Adding example" logs
- Start training and verify console shows epoch progress and loss decreasing
- After training, start tracking and verify console shows prediction coordinates
- Draw heatmap and verify canvas overlay renders with colors
- Save dataset and verify JSON file downloads with correct structure
- Save model and verify .json and .bin files download
- Check browser console Memory tab - verify no memory leaks after 5-minute session
- Test on Firefox and Safari - verify cross-browser compatibility

## Notes

### Key Differences from HUE Vision

- **Integration**: Eye tracking is integrated into existing Focus Keeper app, not standalone
- **Purpose**: Used for distraction detection, not general gaze tracking demo
- **Fallback**: Simple heuristics available if model not trained
- **UI**: Embedded in Focus Keeper interface, not full-screen demo

### Performance Considerations

- Eye region extraction happens every frame (60 FPS)
- Model prediction runs at 10 FPS to balance accuracy and performance
- Training can be computationally intensive - may take 1-2 minutes
- Tensor memory management critical - use `tf.dispose()` and `tf.tidy()`

### User Experience

- Calibration requires user cooperation (follow target, press spacebar)
- Training provides visual feedback (progress bar, epoch counter)
- Model improves with more calibration data (recommend 50+ points)
- Per-user calibration needed for best accuracy
- Model can be saved/loaded to avoid re-calibration

### Future Enhancements

- Auto-calibration using known screen interactions
- Continuous learning during use
- Multi-person model training
- Advanced calibration patterns (smooth pursuit, saccades)
- Gaze-controlled UI elements
