import { CONFIG } from './config.js';

/**
 * Face detection and gaze tracking using TensorFlow.js
 */
export class FaceDetector {
  constructor() {
    this.model = null;
    this.isModelLoaded = false;
  }

  /**
   * Initialize and load the face detection model
   */
  async initialize() {
    try {
      // Load face-landmarks-detection model
      const model = faceLandmarksDetection.SupportedModels.MediaPipeFaceMesh;
      const detectorConfig = {
        runtime: 'tfjs',
        maxFaces: 1,
        refineLandmarks: true,
      };

      this.model = await faceLandmarksDetection.createDetector(model, detectorConfig);
      this.isModelLoaded = true;
      console.log('Face detection model loaded successfully');
      return true;
    } catch (error) {
      console.error('Failed to load face detection model:', error);
      throw new Error('Failed to initialize face detection: ' + error.message);
    }
  }

  /**
   * Detect faces and analyze gaze direction
   * @param {HTMLVideoElement} video - Video element to analyze
   * @returns {Promise<{faceDetected: boolean, lookingAtScreen: boolean, confidence: number}>}
   */
  async detect(video) {
    if (!this.isModelLoaded || !this.model) {
      return {
        faceDetected: false,
        lookingAtScreen: false,
        confidence: 0,
      };
    }

    try {
      const faces = await this.model.estimateFaces(video, {
        flipHorizontal: false,
      });

      if (faces.length === 0) {
        return {
          faceDetected: false,
          lookingAtScreen: false,
          confidence: 0,
        };
      }

      const face = faces[0];

      // Calculate gaze direction using eye landmarks and head pose
      const gazeInfo = this.calculateGazeDirection(face);
      const headPose = this.calculateHeadPose(face);

      const lookingAtScreen =
        gazeInfo.isLookingForward &&
        Math.abs(headPose.yaw) < CONFIG.detection.headTurnThreshold;

      // Debug logging
      console.log('[Detection] Looking at screen:', lookingAtScreen,
                  '| Gaze forward:', gazeInfo.isLookingForward,
                  '| Head yaw:', Math.abs(headPose.yaw).toFixed(2),
                  '| Threshold:', CONFIG.detection.headTurnThreshold);

      // Extract eye landmarks for visualization
      const keypoints = face.keypoints;
      const leftEyeIndices = [33, 133, 160, 159, 158, 157, 173];
      const rightEyeIndices = [362, 263, 385, 386, 387, 388, 398];

      const leftEyeLandmarks = leftEyeIndices.map(idx => keypoints[idx]);
      const rightEyeLandmarks = rightEyeIndices.map(idx => keypoints[idx]);

      // Calculate face bounding box
      const faceBoundingBox = this.getFaceBoundingBox(keypoints);

      // Extract important facial landmarks for visualization
      // Face outline landmarks (based on MediaPipe Face Mesh)
      const faceOutlineIndices = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109];
      const faceOutlineLandmarks = faceOutlineIndices.map(idx => keypoints[idx]);

      // Nose landmarks
      const noseIndices = [1, 2, 98, 327];
      const noseLandmarks = noseIndices.map(idx => keypoints[idx]);

      // Mouth landmarks
      const mouthIndices = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308];
      const mouthLandmarks = mouthIndices.map(idx => keypoints[idx]);

      return {
        faceDetected: true,
        lookingAtScreen,
        confidence: gazeInfo.confidence,
        headPose,
        leftEyeLandmarks,
        rightEyeLandmarks,
        faceBoundingBox,
        faceOutlineLandmarks,
        noseLandmarks,
        mouthLandmarks,
        keypoints,
      };
    } catch (error) {
      console.error('Face detection error:', error);
      return {
        faceDetected: false,
        lookingAtScreen: false,
        confidence: 0,
      };
    }
  }

  /**
   * Calculate gaze direction from eye landmarks
   * @param {Object} face - Face detection result
   * @returns {Object} Gaze information
   */
  calculateGazeDirection(face) {
    try {
      const keypoints = face.keypoints;

      // Get eye landmarks
      // MediaPipe Face Mesh indices for eyes
      const leftEyeIndices = [33, 133, 160, 159, 158, 157, 173];
      const rightEyeIndices = [362, 263, 385, 386, 387, 388, 398];

      const leftEye = leftEyeIndices.map(idx => keypoints[idx]);
      const rightEye = rightEyeIndices.map(idx => keypoints[idx]);

      // Calculate eye center points
      const leftEyeCenter = this.getCenter(leftEye);
      const rightEyeCenter = this.getCenter(rightEye);

      // Simple heuristic: if eyes are relatively centered in detected region,
      // user is likely looking forward
      const eyeCenterX = (leftEyeCenter.x + rightEyeCenter.x) / 2;
      const faceCenterX = (keypoints[234].x + keypoints[454].x) / 2; // face outline points

      const horizontalDeviation = Math.abs(eyeCenterX - faceCenterX);
      const isLookingForward = horizontalDeviation < 30; // threshold for looking forward

      // Debug logging
      console.log('[Gaze] Horizontal deviation:', horizontalDeviation.toFixed(2),
                  '| Looking forward:', isLookingForward,
                  '| Confidence: 0.8');

      return {
        isLookingForward,
        confidence: 0.8, // placeholder confidence
        horizontalDeviation,
      };
    } catch (error) {
      console.error('Gaze calculation error:', error);
      return {
        isLookingForward: false,
        confidence: 0,
        horizontalDeviation: 0,
      };
    }
  }

  /**
   * Calculate head pose (yaw, pitch, roll)
   * @param {Object} face - Face detection result
   * @returns {Object} Head pose angles
   */
  calculateHeadPose(face) {
    try {
      const keypoints = face.keypoints;

      // Use nose, left ear, right ear to estimate yaw (left-right rotation)
      const nose = keypoints[1]; // nose tip
      const leftFace = keypoints[234]; // left face outline
      const rightFace = keypoints[454]; // right face outline

      const faceWidth = Math.abs(rightFace.x - leftFace.x);
      const noseToCenterX = nose.x - (leftFace.x + rightFace.x) / 2;

      // Calculate yaw angle (simplified)
      const yaw = (noseToCenterX / faceWidth) * 90; // rough estimate in degrees

      // Debug logging
      console.log('[Head Pose] Yaw angle:', yaw.toFixed(2), 'degrees');

      return {
        yaw, // left-right head turn
        pitch: 0, // up-down (not implemented)
        roll: 0, // tilt (not implemented)
      };
    } catch (error) {
      console.error('Head pose calculation error:', error);
      return {
        yaw: 0,
        pitch: 0,
        roll: 0,
      };
    }
  }

  /**
   * Calculate center point of a set of landmarks
   * @param {Array} points - Array of {x, y} points
   * @returns {Object} Center point {x, y}
   */
  getCenter(points) {
    const sum = points.reduce(
      (acc, point) => ({
        x: acc.x + point.x,
        y: acc.y + point.y,
      }),
      { x: 0, y: 0 }
    );

    return {
      x: sum.x / points.length,
      y: sum.y / points.length,
    };
  }

  /**
   * Calculate bounding box around eye landmarks
   * @param {Array} eyeLandmarks - Array of eye landmark points {x, y}
   * @returns {Object} Bounding box {x, y, width, height}
   */
  getEyeBoundingBox(eyeLandmarks) {
    if (!eyeLandmarks || eyeLandmarks.length === 0) {
      return null;
    }

    const xs = eyeLandmarks.map(p => p.x);
    const ys = eyeLandmarks.map(p => p.y);

    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);

    const padding = 8; // pixels of padding around the eye

    return {
      x: minX - padding,
      y: minY - padding,
      width: (maxX - minX) + (padding * 2),
      height: (maxY - minY) + (padding * 2),
    };
  }

  /**
   * Calculate bounding box around all face keypoints
   * @param {Array} keypoints - Array of all face keypoints {x, y}
   * @returns {Object} Bounding box {x, y, width, height}
   */
  getFaceBoundingBox(keypoints) {
    if (!keypoints || keypoints.length === 0) {
      return null;
    }

    const xs = keypoints.map(p => p.x);
    const ys = keypoints.map(p => p.y);

    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);

    const padding = 15; // pixels of padding around the face

    return {
      x: minX - padding,
      y: minY - padding,
      width: (maxX - minX) + (padding * 2),
      height: (maxY - minY) + (padding * 2),
    };
  }

  /**
   * Cleanup resources
   */
  dispose() {
    if (this.model) {
      this.model.dispose();
      this.model = null;
      this.isModelLoaded = false;
    }
  }
}
