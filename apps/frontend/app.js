import { CONFIG } from './config.js';
import { FaceDetector } from './face-detection.js';
import { AttentionPlayer } from './video-player.js';

/**
 * Camera Manager - handles getUserMedia and video streaming
 */
class CameraManager {
  constructor() {
    this.stream = null;
    this.video = document.createElement('video');
    this.video.autoplay = true;
    this.video.playsInline = true;
    this.canvas = null;
    this.ctx = null;
    this.isActive = false;
    this.latestDetection = null;
  }

  /**
   * Check if MediaDevices API is supported
   */
  isSupported() {
    // Check if navigator exists
    if (typeof navigator === 'undefined') {
      return { supported: false, reason: 'navigator_missing' };
    }

    // Check if navigator.mediaDevices exists
    if (!navigator.mediaDevices) {
      return { supported: false, reason: 'mediadevices_missing' };
    }

    // Check if getUserMedia exists
    if (!navigator.mediaDevices.getUserMedia) {
      return { supported: false, reason: 'getusermedia_missing' };
    }

    // Check if in secure context
    if (typeof window !== 'undefined' && !window.isSecureContext) {
      return { supported: false, reason: 'insecure_context' };
    }

    return { supported: true, reason: null };
  }

  /**
   * Initialize camera with canvas element
   */
  async initialize(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');

    // Set canvas size
    this.canvas.width = CONFIG.camera.width;
    this.canvas.height = CONFIG.camera.height;
  }

  /**
   * Start camera stream
   */
  async start() {
    try {
      // Check if camera API is supported
      const supportCheck = this.isSupported();
      if (!supportCheck.supported) {
        let errorMessage;
        switch (supportCheck.reason) {
          case 'navigator_missing':
            errorMessage = 'Browser environment not detected. Camera access requires a web browser.';
            break;
          case 'mediadevices_missing':
            errorMessage = 'Your browser does not support camera access. Please update to a modern browser (Chrome 53+, Firefox 36+, Safari 11+, Edge 79+).';
            break;
          case 'getusermedia_missing':
            errorMessage = 'getUserMedia API is not available. Please update your browser to the latest version.';
            break;
          case 'insecure_context':
            errorMessage = 'Camera access requires a secure connection. Please access this page via HTTPS or localhost (not via IP address like 127.0.0.1).';
            break;
          default:
            errorMessage = 'Camera access is not supported in this environment.';
        }
        throw new Error(errorMessage);
      }

      const constraints = {
        video: {
          width: { ideal: CONFIG.camera.width },
          height: { ideal: CONFIG.camera.height },
          facingMode: CONFIG.camera.facingMode,
          frameRate: { ideal: CONFIG.camera.frameRate },
        },
        audio: false,
      };

      this.stream = await navigator.mediaDevices.getUserMedia(constraints);
      this.video.srcObject = this.stream;

      // Wait for video to be ready
      await new Promise((resolve) => {
        this.video.onloadedmetadata = () => {
          this.video.play();
          resolve();
        };
      });

      this.isActive = true;
      this.startRendering();

      console.log('Camera started successfully');
      return true;
    } catch (error) {
      console.error('Camera access error:', error);

      // Provide user-friendly error messages
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        throw new Error('Camera permission denied. Please allow camera access in your browser settings and try again.');
      } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
        throw new Error('No camera found. Please connect a camera and try again.');
      } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
        throw new Error('Camera is already in use by another application. Please close other apps using the camera and try again.');
      } else if (error.message) {
        // Re-throw custom error messages from our support check
        throw error;
      } else {
        throw new Error('Failed to access camera: ' + error.message);
      }
    }
  }

  /**
   * Stop camera stream
   */
  stop() {
    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }
    this.isActive = false;
    console.log('Camera stopped');
  }

  /**
   * Render video to canvas
   */
  startRendering() {
    const render = () => {
      if (!this.isActive) return;

      if (this.video.readyState === this.video.HAVE_ENOUGH_DATA) {
        // Draw video frame to canvas
        this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);

        // Draw face visualization if available
        if (this.latestDetection && this.latestDetection.faceBoundingBox) {
          this.drawFaceVisualization(this.latestDetection);
        }
      }

      requestAnimationFrame(render);
    };

    render();
  }

  /**
   * Draw face visualization with bounding box and landmarks
   */
  drawFaceVisualization(detection) {
    const { faceBoundingBox, leftEyeLandmarks, rightEyeLandmarks, noseLandmarks, mouthLandmarks, faceOutlineLandmarks } = detection;

    if (!faceBoundingBox) return;

    // Draw transparent red rectangle around face
    this.ctx.strokeStyle = CONFIG.visualization.faceBoxColor;
    this.ctx.fillStyle = CONFIG.visualization.faceBoxFillColor;
    this.ctx.lineWidth = CONFIG.visualization.faceBoxLineWidth;

    // Draw face bounding box with fill
    this.ctx.fillRect(faceBoundingBox.x, faceBoundingBox.y, faceBoundingBox.width, faceBoundingBox.height);
    this.ctx.strokeRect(faceBoundingBox.x, faceBoundingBox.y, faceBoundingBox.width, faceBoundingBox.height);

    // Draw landmarks as dots
    this.ctx.fillStyle = CONFIG.visualization.landmarkColor;

    // Draw eye landmarks
    if (leftEyeLandmarks) {
      leftEyeLandmarks.forEach(point => {
        this.drawLandmarkDot(point, CONFIG.visualization.eyeLandmarkRadius);
      });
    }

    if (rightEyeLandmarks) {
      rightEyeLandmarks.forEach(point => {
        this.drawLandmarkDot(point, CONFIG.visualization.eyeLandmarkRadius);
      });
    }

    // Draw nose landmarks
    if (noseLandmarks) {
      noseLandmarks.forEach(point => {
        this.drawLandmarkDot(point, CONFIG.visualization.noseLandmarkRadius);
      });
    }

    // Draw mouth landmarks
    if (mouthLandmarks) {
      mouthLandmarks.forEach(point => {
        this.drawLandmarkDot(point, CONFIG.visualization.mouthLandmarkRadius);
      });
    }

    // Draw face outline landmarks (less prominent)
    if (faceOutlineLandmarks) {
      faceOutlineLandmarks.forEach(point => {
        this.drawLandmarkDot(point, CONFIG.visualization.faceOutlineLandmarkRadius);
      });
    }
  }

  /**
   * Draw a landmark dot at the given point
   */
  drawLandmarkDot(point, radius) {
    this.ctx.beginPath();
    this.ctx.arc(point.x, point.y, radius, 0, 2 * Math.PI);
    this.ctx.fill();
  }

  /**
   * Calculate bounding box around eye landmarks
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

    const padding = 8;

    return {
      x: minX - padding,
      y: minY - padding,
      width: (maxX - minX) + (padding * 2),
      height: (maxY - minY) + (padding * 2),
    };
  }

  /**
   * Update detection results for rendering
   */
  updateDetection(detection) {
    this.latestDetection = detection;
  }

  /**
   * Get video element for face detection
   */
  getVideoElement() {
    return this.video;
  }
}

/**
 * Main Application
 */
class FocusKeeperApp {
  constructor() {
    this.cameraManager = new CameraManager();
    this.faceDetector = new FaceDetector();
    this.attentionPlayer = new AttentionPlayer();

    this.isRunning = false;
  }

  /**
   * Initialize the application
   */
  async initialize() {
    try {
      // Get UI elements
      const canvas = document.getElementById('camera-canvas');
      const statusElement = document.getElementById('status');

      if (!canvas || !statusElement) {
        throw new Error('Required UI elements not found');
      }

      // Show loading status
      this.updateStatus('loading', 'Loading face detection model...');

      // Initialize components
      await this.cameraManager.initialize(canvas);
      this.attentionPlayer.initialize();
      await this.faceDetector.initialize();

      // Check camera API availability
      const supportCheck = this.cameraManager.isSupported();
      if (!supportCheck.supported) {
        // Show warning message
        let warningMessage;
        switch (supportCheck.reason) {
          case 'navigator_missing':
            warningMessage = 'Camera access not available: Browser environment not detected.';
            break;
          case 'mediadevices_missing':
            warningMessage = 'Camera access not available: Please update to a modern browser (Chrome 53+, Firefox 36+, Safari 11+, Edge 79+).';
            break;
          case 'getusermedia_missing':
            warningMessage = 'Camera access not available: Please update your browser to the latest version.';
            break;
          case 'insecure_context':
            warningMessage = 'Camera access requires HTTPS or localhost. Please use https:// or access via localhost instead of an IP address.';
            break;
          default:
            warningMessage = 'Camera access is not supported in this environment.';
        }

        this.updateStatus('error', warningMessage);
        this.showError(warningMessage);
        console.warn('Camera API not available:', supportCheck.reason);
        return;
      }

      // Auto-start camera on page load
      this.updateStatus('loading', 'Requesting camera access...');
      await this.startCamera();

      console.log('Focus Keeper App initialized');
    } catch (error) {
      console.error('Initialization error:', error);
      this.updateStatus('error', 'Error: ' + error.message);
      this.showError(error.message);
    }
  }

  /**
   * Start camera and face detection
   */
  async startCamera() {
    try {
      // Start camera
      await this.cameraManager.start();

      // Start continuous face detection
      const videoElement = this.cameraManager.getVideoElement();
      this.startContinuousDetection(videoElement);

      // Update UI
      this.isRunning = true;
      this.updateStatus('focused', 'Camera active - Face detection running');

      console.log('Camera started and face detection active');
    } catch (error) {
      console.error('Failed to start camera:', error);
      this.showError('Failed to start camera: ' + error.message);
      this.updateStatus('error', 'Camera error: ' + error.message);
    }
  }

  /**
   * Start continuous face detection loop
   */
  startContinuousDetection(videoElement) {
    const detectLoop = async () => {
      if (!this.isRunning) {
        return;
      }

      try {
        // Perform face detection
        const detection = await this.faceDetector.detect(videoElement);

        // Pass detection results to camera manager for visualization
        if (this.cameraManager) {
          this.cameraManager.updateDetection(detection);
        }
      } catch (error) {
        console.error('Detection error:', error);
      }

      // Schedule next frame
      requestAnimationFrame(detectLoop);
    };

    // Start the loop
    requestAnimationFrame(detectLoop);
  }

  /**
   * Update status display
   */
  updateStatus(state, message) {
    const statusElement = document.getElementById('status');
    const statusIndicator = document.getElementById('status-indicator');

    if (statusElement) {
      statusElement.textContent = message;
    }

    if (statusIndicator) {
      statusIndicator.className = 'status-indicator status-' + state;
    }
  }

  /**
   * Show error message
   */
  showError(message) {
    const errorContainer = document.getElementById('error-message');
    if (errorContainer) {
      errorContainer.textContent = message;
      errorContainer.classList.remove('hidden');

      // Auto-hide after 5 seconds
      setTimeout(() => {
        errorContainer.classList.add('hidden');
      }, 5000);
    }
  }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
  const app = new FocusKeeperApp();
  await app.initialize();

  // Expose app instance for debugging
  window.focusKeeperApp = app;
});
