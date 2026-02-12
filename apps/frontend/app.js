import { CONFIG } from './config.js';
import { FaceDetector } from './face-detection.js';
import { AttentionPlayer } from './video-player.js';
import { EyeTracker } from './eye-tracker.js';
import { DatasetManager } from './dataset-manager.js';
import { ModelTrainer } from './model-trainer.js';
import { GazePredictor } from './gaze-predictor.js';
import { UIController } from './ui-controller.js';

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

    // Calculate scale factor from video dimensions to canvas dimensions
    const scaleX = this.canvas.width / this.video.videoWidth;
    const scaleY = this.canvas.height / this.video.videoHeight;

    // Helper function to scale a point from video coordinates to canvas coordinates
    const scalePoint = (point) => ({
      x: point.x * scaleX,
      y: point.y * scaleY
    });

    // Helper function to scale a bounding box
    const scaleBox = (box) => ({
      x: box.x * scaleX,
      y: box.y * scaleY,
      width: box.width * scaleX,
      height: box.height * scaleY
    });

    // Scale the bounding box
    const scaledBox = scaleBox(faceBoundingBox);

    // Draw transparent red rectangle around face
    this.ctx.strokeStyle = CONFIG.visualization.faceBoxColor;
    this.ctx.fillStyle = CONFIG.visualization.faceBoxFillColor;
    this.ctx.lineWidth = CONFIG.visualization.faceBoxLineWidth;

    // Draw face bounding box with fill
    this.ctx.fillRect(scaledBox.x, scaledBox.y, scaledBox.width, scaledBox.height);
    this.ctx.strokeRect(scaledBox.x, scaledBox.y, scaledBox.width, scaledBox.height);

    // Draw landmarks as dots
    this.ctx.fillStyle = CONFIG.visualization.landmarkColor;

    // Draw eye landmarks
    if (leftEyeLandmarks) {
      leftEyeLandmarks.forEach(point => {
        this.drawLandmarkDot(scalePoint(point), CONFIG.visualization.eyeLandmarkRadius);
      });
    }

    if (rightEyeLandmarks) {
      rightEyeLandmarks.forEach(point => {
        this.drawLandmarkDot(scalePoint(point), CONFIG.visualization.eyeLandmarkRadius);
      });
    }

    // Draw nose landmarks
    if (noseLandmarks) {
      noseLandmarks.forEach(point => {
        this.drawLandmarkDot(scalePoint(point), CONFIG.visualization.noseLandmarkRadius);
      });
    }

    // Draw mouth landmarks
    if (mouthLandmarks) {
      mouthLandmarks.forEach(point => {
        this.drawLandmarkDot(scalePoint(point), CONFIG.visualization.mouthLandmarkRadius);
      });
    }

    // Draw face outline landmarks (less prominent)
    if (faceOutlineLandmarks) {
      faceOutlineLandmarks.forEach(point => {
        this.drawLandmarkDot(scalePoint(point), CONFIG.visualization.faceOutlineLandmarkRadius);
      });
    }
  }

  /**
   * Draw a landmark dot at the given point
   */
  drawLandmarkDot(point, radius) {
    if (!point || typeof point.x !== 'number' || typeof point.y !== 'number') {
      return;
    }
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

    // Eye tracking components (initialized if enabled)
    this.eyeTracker = null;
    this.datasetManager = null;
    this.modelTrainer = null;
    this.gazePredictor = null;
    this.uiController = null;

    this.isRunning = false;

    // Attention grabber state tracking for skeleton video feature (Issue #29)
    // Tracks when user is looking away to trigger jumpscare skeleton video
    this.isLookingAway = false;
    this.lookingAwayStartTime = null;
    this.isShowingAttentionGrabber = false;
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

      // Initialize eye tracking if enabled (before starting camera)
      if (CONFIG.eyeTracking.enabled) {
        await this.initializeEyeTracking();
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
   * Initialize eye tracking components
   */
  async initializeEyeTracking() {
    try {
      console.log('Initializing eye tracking...');

      // Get eye canvas
      const eyesCanvas = document.getElementById('eyes');
      const videoElement = this.cameraManager.getVideoElement();

      if (!eyesCanvas) {
        console.warn('Eye canvas not found - eye tracking disabled');
        return;
      }

      console.log('Eye canvas found, video element:', videoElement);

      // Initialize eye tracker
      this.eyeTracker = new EyeTracker();
      this.eyeTracker.initialize(eyesCanvas, videoElement);
      console.log('Eye tracker initialized');

      // Initialize dataset manager
      this.datasetManager = new DatasetManager(this.eyeTracker);
      console.log('Dataset manager initialized');

      // Initialize model trainer
      this.modelTrainer = new ModelTrainer(this.datasetManager);
      console.log('Model trainer initialized');

      // Initialize gaze predictor
      this.gazePredictor = new GazePredictor(this.modelTrainer, this.datasetManager);
      console.log('Gaze predictor initialized');

      // Initialize UI controller
      this.uiController = new UIController();
      this.uiController.initialize(this.datasetManager, this.modelTrainer, this.gazePredictor);
      console.log('UI controller initialized');

      console.log('✓ Eye tracking fully initialized');
    } catch (error) {
      console.error('✗ Failed to initialize eye tracking:', error);
      console.error('Stack trace:', error.stack);
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

      // Notify UI controller that webcam is enabled
      if (this.uiController) {
        this.uiController.onWebcamEnabled();
      }

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

        // Debug: Log detection results occasionally (every 60 frames ~1 second)
        if (Math.random() < 0.016) {
          console.log('Detection result:', {
            faceDetected: detection?.faceDetected,
            hasKeypoints: !!detection?.keypoints,
            uiControllerExists: !!this.uiController
          });
        }

        // Pass detection results to camera manager for visualization
        if (this.cameraManager) {
          this.cameraManager.updateDetection(detection);
        }

        // Update UI controller based on face detection (always, regardless of eye tracking)
        if (this.uiController) {
          if (detection && detection.faceDetected) {
            this.uiController.onFoundFace();
          } else {
            this.uiController.onFaceNotFound();
          }
        } else {
          // UI controller doesn't exist - this is the problem!
          if (Math.random() < 0.016) {
            console.warn('UI controller not initialized - buttons will not enable');
          }
        }

        // Attention grabber logic (Issue #29): trigger skeleton video when user looks away
        // The skeleton video acts as a "jumpscare" attention grabber that:
        // - Appears instantly when user looks away from screen
        // - Closes instantly when user looks back at screen
        // - Does not trigger during calibration or training to avoid interfering with model training
        const isInTrainingPhase = this.uiController &&
                                  (this.uiController.calibrationMode ||
                                   this.uiController.phase === 'training');

        if (CONFIG.attentionGrabber.enabled && !isInTrainingPhase &&
            detection && detection.faceDetected) {
          const lookingAtScreen = detection.lookingAtScreen;

          // User just started looking away (transition from looking → not looking)
          if (!lookingAtScreen && !this.isLookingAway) {
            this.isLookingAway = true;
            this.lookingAwayStartTime = Date.now();

            // Trigger skeleton video immediately (jumpscare effect)
            if (!this.isShowingAttentionGrabber) {
              this.attentionPlayer.playSkeletonVideo();
              this.isShowingAttentionGrabber = true;
              console.log('User looking away - skeleton video triggered');
            }
          }
          // User is looking back at screen
          else if (lookingAtScreen && this.isLookingAway) {
            this.isLookingAway = false;
            this.lookingAwayStartTime = null;

            // Close skeleton video instantly
            if (this.isShowingAttentionGrabber) {
              this.attentionPlayer.stop();
              this.isShowingAttentionGrabber = false;
              console.log('User looking back - skeleton video closed');
            }
          }
        }
        // Handle case when no face is detected or we're in training phase
        else if (CONFIG.attentionGrabber.enabled && this.isShowingAttentionGrabber &&
                 ((!detection || !detection.faceDetected) || isInTrainingPhase)) {
          // Close skeleton video if no face detected or entered training phase
          this.attentionPlayer.stop();
          this.isShowingAttentionGrabber = false;
          this.isLookingAway = false;
          this.lookingAwayStartTime = null;
        }

        // Update eye tracker if enabled and detection successful
        if (this.eyeTracker && detection && detection.keypoints) {
          this.eyeTracker.updateFromDetection(detection);
        }
      } catch (error) {
        console.error('Detection error:', error);
      }

      // Schedule next detection after current one completes
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
