# Architecture Decision: Eye Tracking Technology Migration

## Issue
**Issue #23**: Evaluate migration from MediaPipe Face Mesh (TensorFlow.js) to GazeTracking library

**Original Request**: "Could we use this https://github.com/antoinelame/GazeTracking for eye tracking?"

## Context

### Current Implementation
The Focus Keeper application is a **pure client-side JavaScript web application** with the following architecture:
- **Technology**: TensorFlow.js + MediaPipe Face Mesh
- **Execution**: Browser-based, client-side only
- **Privacy**: All video processing happens locally in the browser
- **Dependencies**: Loaded via CDN (TensorFlow.js, MediaPipe models)
- **Features**:
  - Face detection with 468 facial landmarks
  - Gaze direction estimation (forward/not forward)
  - Head pose estimation (yaw angle)
  - Real-time processing from webcam feed

**Current Implementation Analysis** (apps/frontend/face-detection.js:1-250):
- Uses MediaPipe Face Mesh with refined landmarks
- Detects single face with 468 keypoints
- Calculates gaze direction using eye landmark positions
- Estimates head pose using nose and face outline points
- Returns looking state based on gaze + head pose combination
- Simple heuristic-based approach with 0.8 confidence

### Proposed Technology: GazeTracking
**Repository**: https://github.com/antoinelame/GazeTracking

**Technology Stack**:
- **Language**: Python (2 and 3 compatible)
- **Dependencies**:
  - NumPy for numerical operations
  - OpenCV for computer vision
  - Dlib for facial landmark detection (requires Boost, Boost.Python, CMake, X11/XQuartz)

**Features**:
- Pupil position tracking (left/right eyes separately)
- Gaze direction classification (left, right, center)
- Continuous directional ratios (horizontal/vertical, 0.0-1.0)
- Blink detection
- Annotated frame output with visual overlays

**Limitations**:
- Python-only (no browser/JavaScript version)
- Requires system-level dependencies (Dlib, OpenCV)
- 49 open issues
- Requests video samples for accuracy improvements

## Critical Constraint

**Privacy Requirement** (apps/frontend/index.html:76-77):
> "All video processing happens locally in your browser. No video or images are stored or transmitted."

This is a **non-negotiable requirement** that eliminates any approach requiring video transmission to a backend server.

## Approach Evaluation

### Approach 1: Keep Current Stack (MediaPipe Face Mesh)
**Feasibility**: ✅ Already implemented and working
**Privacy**: ✅ Fully preserved (client-side processing)
**Complexity**: ✅ Low (no changes needed)
**GazeTracking Usage**: ❌ Does not use requested library

**Pros**:
- Already implemented and functional
- Privacy-preserving architecture
- Cross-browser compatible
- Well-documented TensorFlow.js ecosystem
- No infrastructure changes needed
- Lightweight deployment (static HTML/JS/CSS)

**Cons**:
- Does not satisfy user's request to use GazeTracking
- Current gaze detection is heuristic-based (0.8 fixed confidence)
- May have lower accuracy than dedicated gaze tracking libraries

**Recommendation**: This is the **default fallback** if other approaches are infeasible.

---

### Approach 2: Python Backend with GazeTracking
**Feasibility**: ⚠️ Technically feasible but architecturally disruptive
**Privacy**: ❌ **VIOLATES privacy requirement**
**Complexity**: ❌ High (new backend, deployment, streaming)
**GazeTracking Usage**: ✅ Uses library as intended

**Architecture**:
```
Browser (Frontend)          Python Backend
    │                            │
    ├─ Capture video frames ────>│
    │                            ├─ GazeTracking.refresh(frame)
    │<─── Gaze data (JSON) ──────┤
    │                            │
    └─ Display results           └─ Process with OpenCV/Dlib
```

**Required Changes**:
1. Create `apps/backend/eye_tracking_service.py` with WebSocket/HTTP server
2. Install Python, OpenCV, Dlib, GazeTracking on server
3. Modify frontend to send video frames to backend
4. Receive gaze data and update UI
5. **Update privacy notice**: Video now transmitted to backend

**Pros**:
- Uses GazeTracking library as intended
- Access to Python ecosystem for computer vision
- Potentially more accurate pupil tracking

**Cons**:
- **Violates core privacy requirement** (video must be sent to server)
- Adds infrastructure complexity (Python backend deployment)
- Requires network connection (no offline usage)
- Latency from frame transmission
- Dlib installation complexity (requires compilation, system dependencies)
- Significantly increased deployment complexity

**Recommendation**: ❌ **NOT RECOMMENDED** due to privacy violation unless user explicitly accepts trade-off.

---

### Approach 3: Find JavaScript Alternative
**Feasibility**: ✅ Multiple JavaScript eye tracking libraries exist
**Privacy**: ✅ Can maintain client-side processing
**Complexity**: ⚠️ Medium (library migration, API changes)
**GazeTracking Usage**: ❌ Different library (but similar functionality)

**JavaScript Eye Tracking Libraries**:

1. **WebGazer.js** (https://webgazer.cs.brown.edu/)
   - Popular JavaScript eye tracking library
   - Uses TensorFlow.js + Ridge regression
   - Calibration-based approach
   - Active development

2. **jeelizGlanceTracker** (https://github.com/jeeliz/jeelizGlanceTracker)
   - Real-time gaze tracking
   - Lightweight and fast
   - Works on mobile

3. **tracking.js** (https://trackingjs.com/)
   - General computer vision library
   - Includes face and eye tracking
   - Pure JavaScript

**Required Changes**:
1. Replace MediaPipe Face Mesh import with chosen library
2. Update `FaceDetector` class API to match new library
3. Test gaze accuracy against current implementation
4. Update HTML dependencies

**Pros**:
- Maintains client-side architecture
- Preserves privacy requirements
- Potentially better accuracy than current heuristics
- JavaScript ecosystem compatibility

**Cons**:
- Still not using GazeTracking library specifically
- Requires testing/validation of new library
- May need calibration step (user experience change)
- Different API/integration effort

**Recommendation**: ⚠️ **VIABLE ALTERNATIVE** if goal is improved accuracy while maintaining architecture.

---

### Approach 4: WebAssembly (WASM)
**Feasibility**: ❌ Very difficult, potentially infeasible
**Privacy**: ✅ Can maintain client-side processing
**Complexity**: ❌ Very high (compilation, debugging, compatibility)
**GazeTracking Usage**: ⚠️ Partial (OpenCV WASM exists, Dlib WASM uncertain)

**Technical Challenges**:
1. **OpenCV.js exists** but has limited features vs full OpenCV
2. **Dlib WASM support**: Uncertain, may not exist or be outdated
3. **Python-to-WASM**: Could use Pyodide, but performance concerns
4. **GazeTracking itself**: Would need significant modifications
5. **File size**: WASM binaries can be very large (megabytes)
6. **Debugging**: WASM debugging is complex

**Pros**:
- Could theoretically run Python code in browser
- Maintains client-side architecture
- No backend needed

**Cons**:
- Extremely complex implementation
- Uncertain feasibility (Dlib WASM support unclear)
- Large bundle sizes (poor performance)
- Difficult to debug and maintain
- May not be performant enough for real-time video

**Recommendation**: ❌ **NOT RECOMMENDED** due to complexity and uncertain feasibility.

## Decision Matrix

| Approach | Privacy | Complexity | Uses GazeTracking | Feasibility | Deployment |
|----------|---------|------------|-------------------|-------------|------------|
| 1. Keep Current | ✅ | ✅ Low | ❌ | ✅ | ✅ Simple |
| 2. Python Backend | ❌ | ❌ High | ✅ | ⚠️ | ❌ Complex |
| 3. JS Alternative | ✅ | ⚠️ Medium | ❌ | ✅ | ✅ Simple |
| 4. WebAssembly | ✅ | ❌ Very High | ⚠️ | ❌ | ⚠️ Large bundles |

## Recommendations

### Primary Recommendation: Clarify Requirements
Before proceeding with implementation, **clarify the motivation** for switching to GazeTracking:

**Questions to answer**:
1. **Why GazeTracking specifically?**
   - Is it for better accuracy?
   - Specific features (pupil tracking, blink detection)?
   - Or just a general preference?

2. **Privacy trade-off acceptance?**
   - Is the user willing to accept video transmission to backend?
   - Or must processing remain client-side?

3. **Performance/accuracy issues with current implementation?**
   - Are there specific problems with MediaPipe Face Mesh?
   - What accuracy/features are missing?

### If Privacy Must Be Maintained:
**Recommended Path**: **Approach 3 - JavaScript Alternative**
- Research and evaluate WebGazer.js or jeelizGlanceTracker
- Compare accuracy against current MediaPipe implementation
- Implement as replacement if superior

**Fallback**: **Approach 1 - Keep Current**
- Current implementation is functional and privacy-preserving
- Can improve accuracy by tuning existing heuristics

### If Privacy Can Be Compromised:
**Recommended Path**: **Approach 2 - Python Backend**
- Implement GazeTracking as backend service
- Update privacy notice to reflect backend processing
- Document deployment requirements

## Implementation Priority

**Immediate Actions**:
1. ✅ Document architectural incompatibility (this document)
2. 🔄 Present findings to user
3. ⏸️ Wait for user decision on approach
4. ⏸️ Implement selected approach

**Do NOT implement without user approval** of the approach and acknowledgment of trade-offs.

## Technical Notes

### Current Implementation Quality
The existing MediaPipe Face Mesh implementation (apps/frontend/face-detection.js:1-250) is:
- Well-structured with clear separation of concerns
- Properly handles errors and edge cases
- Provides useful debug logging
- Uses industry-standard MediaPipe model (468 facial landmarks)
- Simple heuristic-based gaze detection with room for improvement

### Improvement Opportunities (Without Library Change)
If keeping current stack, could improve:
1. **Gaze detection algorithm**: Replace simple horizontal deviation with iris/pupil tracking using MediaPipe iris landmarks
2. **Confidence calculation**: Implement dynamic confidence based on face detection quality
3. **Vertical gaze**: Add up/down gaze detection (currently only horizontal)
4. **Calibration**: Add optional user calibration for personalized thresholds

## Conclusion

**GazeTracking is fundamentally incompatible with the current client-side architecture** due to being Python-based. Using it would require either:
- Adding a Python backend (violates privacy requirement)
- Complex WASM compilation (likely infeasible)

**Recommended next step**: Present this analysis to the user and get direction on whether to:
1. Keep current implementation (no changes)
2. Explore JavaScript alternatives (WebGazer.js, etc.)
3. Accept privacy trade-off and implement Python backend
4. Close issue as incompatible with architecture

## References
- GazeTracking Library: https://github.com/antoinelame/GazeTracking
- Current Implementation: apps/frontend/face-detection.js
- Privacy Notice: apps/frontend/index.html:76-77
- MediaPipe Face Mesh: https://github.com/google/mediapipe
- WebGazer.js: https://webgazer.cs.brown.edu/
