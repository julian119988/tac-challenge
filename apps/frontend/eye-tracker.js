/**
 * Eye Tracker - Extract eye region from face landmarks using iris detection
 * Based on HUE Vision facetracker.js
 */

import { CONFIG } from './config.js';

export class EyeTracker {
  constructor() {
    this.currentEyeRect = null;
    this.eyesCanvas = null;
    this.eyesCtx = null;
    this.videoElement = null;
    this.videoWidthInternal = 640;
    this.videoHeightInternal = 480;
  }

  /**
   * Initialize eye tracker with canvas and video elements
   */
  initialize(eyesCanvas, videoElement) {
    this.eyesCanvas = eyesCanvas;
    this.eyesCtx = eyesCanvas.getContext('2d');
    this.videoElement = videoElement;

    // Set canvas dimensions from config
    this.eyesCanvas.width = CONFIG.eyeTracking.visualization.eyeCanvasWidth;
    this.eyesCanvas.height = CONFIG.eyeTracking.visualization.eyeCanvasHeight;

    console.log('Eye tracker initialized');
  }

  /**
   * Extract eye region from iris landmarks
   * @param {Array} keypoints - Face mesh keypoints
   * @returns {Object|null} Eye region rect {x, y, width, height}
   */
  extractEyeRegion(keypoints) {
    if (!keypoints || keypoints.length === 0) {
      return null;
    }

    try {
      // Iris landmark indices
      const LEFT_IRIS = [468, 469, 470, 471, 472];
      const RIGHT_IRIS = [473, 474, 475, 476, 477];

      // Calculate iris centers
      const leftIrisCenter = this.calculateCenter(LEFT_IRIS.map(idx => keypoints[idx]));
      const rightIrisCenter = this.calculateCenter(RIGHT_IRIS.map(idx => keypoints[idx]));

      // Calculate eye region center
      const eyeCenterX = (leftIrisCenter.x + rightIrisCenter.x) / 2;
      const eyeCenterY = (leftIrisCenter.y + rightIrisCenter.y) / 2;

      // Calculate eye width and height
      const irisDistance = Math.abs(rightIrisCenter.x - leftIrisCenter.x);
      const eyeWidth = irisDistance * this.videoWidthInternal * 1.5;
      const eyeHeight = eyeWidth * 0.6;

      // Calculate crop coordinates
      const cropX = eyeCenterX * this.videoWidthInternal - eyeWidth / 2;
      const cropY = eyeCenterY * this.videoHeightInternal - eyeHeight / 2;

      return {
        x: cropX,
        y: cropY,
        width: eyeWidth,
        height: eyeHeight
      };
    } catch (error) {
      console.error('Error extracting eye region:', error);
      return null;
    }
  }

  /**
   * Calculate center point of landmarks
   */
  calculateCenter(landmarks) {
    if (!landmarks || landmarks.length === 0) {
      return { x: 0, y: 0 };
    }

    const sum = landmarks.reduce(
      (acc, point) => ({
        x: acc.x + point.x,
        y: acc.y + point.y,
      }),
      { x: 0, y: 0 }
    );

    return {
      x: sum.x / landmarks.length,
      y: sum.y / landmarks.length,
    };
  }

  /**
   * Crop eye region to canvas
   * @param {Object} eyeRect - Eye region rectangle
   */
  cropEyeToCanvas(eyeRect) {
    if (!eyeRect || !this.videoElement || !this.eyesCanvas) {
      return;
    }

    try {
      // Update video dimensions
      this.videoWidthInternal = this.videoElement.videoWidth;
      this.videoHeightInternal = this.videoElement.videoHeight;

      // Clear canvas
      this.eyesCtx.clearRect(0, 0, this.eyesCanvas.width, this.eyesCanvas.height);

      // Draw eye region to canvas
      this.eyesCtx.drawImage(
        this.videoElement,
        eyeRect.x,
        eyeRect.y,
        eyeRect.width,
        eyeRect.height,
        0,
        0,
        this.eyesCanvas.width,
        this.eyesCanvas.height
      );

      // Store current eye rect
      this.currentEyeRect = eyeRect;
    } catch (error) {
      console.error('Error cropping eye to canvas:', error);
    }
  }

  /**
   * Update eye region from face detection results
   * @param {Object} detection - Face detection result with keypoints
   */
  updateFromDetection(detection) {
    if (!detection || !detection.keypoints) {
      return null;
    }

    const eyeRect = this.extractEyeRegion(detection.keypoints);
    if (eyeRect) {
      this.cropEyeToCanvas(eyeRect);
    }
    return eyeRect;
  }

  /**
   * Get current eye image as tensor
   */
  getCurrentEyeImage() {
    if (!this.eyesCanvas) {
      return null;
    }

    return tf.tidy(() => {
      const image = tf.browser.fromPixels(this.eyesCanvas);
      const batchedImage = image.expandDims(0);
      return batchedImage.toFloat().div(tf.scalar(127)).sub(tf.scalar(1));
    });
  }

  /**
   * Get current eye rect
   */
  getCurrentEyeRect() {
    return this.currentEyeRect;
  }

  /**
   * Get eye metadata as normalized tensor
   * @returns {tf.Tensor} Metadata tensor [centerX, centerY, width, height]
   */
  getEyeMetadata() {
    if (!this.currentEyeRect) {
      return null;
    }

    try {
      const rect = this.currentEyeRect;

      // Calculate normalized center and size
      let x = rect.x + rect.width / 2;
      let y = rect.y + rect.height / 2;

      x = (x / this.videoWidthInternal) * 2 - 1;
      y = (y / this.videoHeightInternal) * 2 - 1;

      const rectWidth = rect.width / this.videoWidthInternal;
      const rectHeight = rect.height / this.videoHeightInternal;

      return tf.tidy(() => {
        return tf.tensor1d([x, y, rectWidth, rectHeight]).expandDims(0);
      });
    } catch (error) {
      console.error('Error getting eye metadata:', error);
      return null;
    }
  }
}
