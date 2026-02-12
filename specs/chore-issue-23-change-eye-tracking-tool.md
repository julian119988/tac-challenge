# Chore: Change Eye Tracking Tool

## Metadata
adw_id: `Issue #23`
prompt: `Could we use this https://github.com/antoinelame/GazeTracking for eye tracking?`

## Chore Description
Evaluate and potentially migrate the current eye tracking implementation from MediaPipe Face Mesh (TensorFlow.js) to the GazeTracking library. The current application is a pure frontend JavaScript web application using TensorFlow.js with MediaPipe Face Mesh for face detection and gaze tracking. The proposed GazeTracking library is a Python-based solution using OpenCV and Dlib.

**Key Challenge**: The GazeTracking library is Python-based while the current application is pure JavaScript running in the browser. This creates an architectural mismatch that requires careful consideration.

**Possible Approaches**:
1. **Keep Current Stack**: Determine that GazeTracking is incompatible with the web-based architecture
2. **Add Python Backend**: Create a Python backend service that processes video frames and communicates with the frontend via WebSocket/HTTP
3. **Find JavaScript Alternative**: Research if GazeTracking has JavaScript ports or similar libraries
4. **WebAssembly**: Investigate compiling Python/OpenCV to WebAssembly (complex, potentially not feasible)

## Relevant Files

### Current Frontend Implementation
- **`apps/frontend/face-detection.js`** (250 lines) - Current MediaPipe Face Mesh implementation using TensorFlow.js; contains `FaceDetector` class with gaze and head pose estimation
- **`apps/frontend/app.js`** (692 lines) - Main application logic with `CameraManager`, `DistractionMonitor`, and `FocusKeeperApp` classes
- **`apps/frontend/config.js`** (42 lines) - Configuration for detection thresholds, camera settings, and intervention videos
- **`apps/frontend/video-player.js`** (173 lines) - Intervention video player with fullscreen overlay
- **`apps/frontend/index.html`** (102 lines) - HTML structure with TensorFlow.js and MediaPipe dependencies loaded via CDN
- **`apps/frontend/styles.css`** (359 lines) - UI styling with glassmorphism design

### Documentation
- **`README.md`** - Project overview and structure
- **`requirements.txt`** - Python dependencies for the ADW server (not the frontend app)

### New Files
- **`apps/backend/eye_tracking_service.py`** - (If approach #2) Python backend service using GazeTracking library
- **`apps/backend/requirements.txt`** - (If approach #2) Python dependencies for eye tracking service
- **`specs/eye-tracking-architecture-decision.md`** - (If needed) Architecture decision record for approach selection

## Step by Step Tasks

### 1. Research and Architecture Decision
- Review the GazeTracking library documentation and implementation details
- Analyze the compatibility between Python-based GazeTracking and JavaScript frontend
- Document the technical constraints:
  - GazeTracking requires Python, OpenCV, and Dlib (not available in browsers)
  - Current app is pure client-side with no backend server (privacy-focused)
  - Privacy requirement: "All video processing happens locally in your browser. No video or images are stored or transmitted"
- Evaluate each possible approach against requirements:
  - **Approach 1 (Keep Current)**: Maintains privacy, no changes needed, but doesn't use GazeTracking
  - **Approach 2 (Python Backend)**: Can use GazeTracking but violates privacy requirement (video must be sent to backend)
  - **Approach 3 (JS Alternative)**: Research JavaScript eye tracking libraries (e.g., WebGazer.js, jeelizGlanceTracker)
  - **Approach 4 (WebAssembly)**: Technically complex, OpenCV WASM exists but Dlib support uncertain
- Create an architecture decision document or prepare recommendations

### 2. Present Findings and Get Direction
- Document the architectural incompatibility between GazeTracking (Python) and the current web app (JavaScript)
- Present the trade-offs of each approach:
  - **Privacy vs Technology**: Using GazeTracking requires sending video to a backend (privacy violation)
  - **Feasibility**: Current implementation is working; GazeTracking provides different API but similar functionality
  - **Complexity**: Adding a backend significantly increases infrastructure and deployment complexity
- Recommend either:
  - Keep current MediaPipe Face Mesh implementation (JavaScript-based, privacy-preserving)
  - Find a JavaScript-based eye tracking alternative with similar capabilities
  - Accept privacy trade-off and implement Python backend with GazeTracking
- Wait for user decision on which approach to pursue

### 3. Implement Selected Approach (Conditional)
**Only execute if user approves a specific approach**

#### If Approach 1 (Keep Current):
- Document that GazeTracking is Python-only and incompatible
- Close the issue or update it with findings
- No code changes required

#### If Approach 2 (Python Backend):
- Create `apps/backend/` directory structure
- Implement Python backend service with GazeTracking library
- Set up WebSocket or HTTP streaming for video frames
- Modify frontend to send frames to backend and receive gaze data
- Update privacy notice to reflect backend processing
- Add deployment documentation for Python service

#### If Approach 3 (JavaScript Alternative):
- Research and select suitable JavaScript eye tracking library
- Create feature-parity comparison with current implementation
- Implement new library replacing MediaPipe Face Mesh in `face-detection.js`
- Test gaze detection accuracy and performance
- Update dependencies in `index.html`

#### If Approach 4 (WebAssembly):
- Research OpenCV.js and Dlib WASM availability
- Attempt to compile or find pre-compiled WASM modules
- Create wrapper to interface with GazeTracking API
- Extensive testing for browser compatibility

### 4. Testing and Validation
**Only execute if implementation occurred**

- Test eye tracking accuracy in various lighting conditions
- Verify real-time performance (target: 60 FPS)
- Test distraction detection thresholds match or improve current behavior
- Validate privacy requirements (if backend approach, document changes)
- Test across browsers: Chrome, Firefox, Safari, Edge
- Verify mobile responsiveness if applicable

### 5. Documentation Updates
**Only execute if implementation occurred**

- Update `README.md` with new technology stack
- Update installation instructions if backend is added
- Update privacy notice if processing location changes
- Document any new dependencies or system requirements
- Create migration notes if API changes affect configuration

## Validation Commands
Execute these commands to validate the chore is complete:

**Research Phase:**
- Manual review of architecture decision document in `specs/` directory
- Confirm all approaches are evaluated with pros/cons documented

**If JavaScript Implementation:**
- `python -m http.server 8000` - Start local server and test frontend at http://localhost:8000/apps/frontend/
- Manual testing: Verify eye tracking works in browser console (no errors)
- Manual testing: Verify distraction detection triggers appropriately
- Browser compatibility test: Test in Chrome, Firefox, Safari

**If Python Backend Implementation:**
- `uv run python -m py_compile apps/backend/*.py` - Verify Python code compiles
- `cd apps/backend && pip install -r requirements.txt` - Install dependencies successfully
- `uv run python apps/backend/eye_tracking_service.py` - Start backend service without errors
- `python -m http.server 8000` - Start frontend and verify WebSocket/HTTP connection to backend
- Manual testing: Verify video streaming and gaze data reception

**General:**
- `git status` - Verify all new files are tracked
- `git diff` - Review all changes to existing files
- Manual review: Confirm privacy notice reflects implementation approach

## Notes

### Critical Constraint
The current application has a strong privacy requirement: "All video processing happens locally in your browser. No video or images are stored or transmitted." Using GazeTracking in its native Python form would violate this constraint unless WebAssembly is used.

### Technology Stack Analysis
- **Current**: TensorFlow.js + MediaPipe Face Mesh (JavaScript, client-side)
- **Proposed**: GazeTracking (Python, requires backend or WASM)

### Recommended Approach
Without additional context about why GazeTracking is preferred, **the recommended approach is to first present the architectural incompatibility to the user** before implementing. The current MediaPipe Face Mesh implementation is:
- Working and functional
- Privacy-preserving (client-side only)
- Cross-browser compatible
- Well-integrated with the application

If the goal is better accuracy or features, exploring **JavaScript alternatives** (Approach 3) might be the best balance of functionality and architecture compatibility.

### Alternative JavaScript Libraries
If the user wants to explore other options:
- **WebGazer.js**: Popular JavaScript eye tracking library
- **jeelizGlanceTracker**: Real-time gaze tracking in JavaScript
- **tracking.js**: General computer vision in JavaScript
- **MediaPipe Face Mesh** (current): Proven, working solution

### Implementation Priority
1. **High Priority**: Research and present findings (Step 1-2)
2. **Medium Priority**: Get user direction on approach
3. **Low Priority**: Implementation (depends on approach selected)

The key deliverable for this chore is the **architectural analysis and recommendation**, not necessarily the implementation.
