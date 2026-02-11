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

      return {
        faceDetected: true,
        lookingAtScreen,
        confidence: gazeInfo.confidence,
        headPose,
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
