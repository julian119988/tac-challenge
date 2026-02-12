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

        // Draw eye detection rectangles if available
        if (this.latestDetection && this.latestDetection.leftEyeLandmarks && this.latestDetection.rightEyeLandmarks) {
          this.drawEyeRectangles(this.latestDetection);
        }
      }

      requestAnimationFrame(render);
    };

    render();
  }

  /**
   * Draw rectangles around detected eyes
   */
  drawEyeRectangles(detection) {
    const { leftEyeLandmarks, rightEyeLandmarks, lookingAtScreen } = detection;

    // Calculate bounding boxes
    const leftEyeBox = this.getEyeBoundingBox(leftEyeLandmarks);
    const rightEyeBox = this.getEyeBoundingBox(rightEyeLandmarks);

    if (!leftEyeBox || !rightEyeBox) return;

    // Set color based on whether user is looking at screen
    const color = lookingAtScreen ? '#4ade80' : '#ef4444'; // green : red

    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = 3;

    // Draw left eye rectangle
    this.ctx.strokeRect(leftEyeBox.x, leftEyeBox.y, leftEyeBox.width, leftEyeBox.height);

    // Draw right eye rectangle
    this.ctx.strokeRect(rightEyeBox.x, rightEyeBox.y, rightEyeBox.width, rightEyeBox.height);
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
 * Distraction Monitor - tracks user attention state
 */
class DistractionMonitor {
  constructor(faceDetector, attentionPlayer, cameraManager) {
    this.faceDetector = faceDetector;
    this.attentionPlayer = attentionPlayer;
    this.cameraManager = cameraManager;

    // State tracking
    this.currentState = 'not-started'; // 'focused', 'distracted', 'intervention', 'not-started'
    this.lastFaceDetectedTime = Date.now();
    this.lastLookingAtScreenTime = Date.now();
    this.animationFrameId = null;
    this.videoElement = null;

    // Stats
    this.sessionStartTime = null;
    this.totalFocusTime = 0;
    this.distractionCount = 0;
    this.lastUpdateTime = Date.now();
  }

  /**
   * Start monitoring
   */
  start(videoElement) {
    this.sessionStartTime = Date.now();
    this.lastUpdateTime = Date.now();
    this.lastFaceDetectedTime = Date.now();
    this.lastLookingAtScreenTime = Date.now();
    this.currentState = 'focused';
    this.videoElement = videoElement;

    // Start continuous detection using requestAnimationFrame
    this.startContinuousDetection();

    console.log('Distraction monitoring started (realtime detection)');
  }

  /**
   * Stop monitoring
   */
  stop() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    this.videoElement = null;
    this.currentState = 'not-started';
    console.log('Distraction monitoring stopped');
  }

  /**
   * Start continuous detection loop using requestAnimationFrame
   */
  startContinuousDetection() {
    const detectLoop = async () => {
      // Only continue if monitoring is active
      if (this.currentState === 'not-started' || !this.videoElement) {
        return;
      }

      // Perform detection
      await this.checkDistraction(this.videoElement);

      // Schedule next frame
      this.animationFrameId = requestAnimationFrame(detectLoop);
    };

    // Start the loop
    this.animationFrameId = requestAnimationFrame(detectLoop);
  }

  /**
   * Check for distraction
   */
  async checkDistraction(videoElement) {
    const now = Date.now();
    const detection = await this.faceDetector.detect(videoElement);

    // Pass detection results to camera manager for visualization
    if (this.cameraManager) {
      this.cameraManager.updateDetection(detection);
    }

    // Update last seen times
    if (detection.faceDetected) {
      this.lastFaceDetectedTime = now;
    }

    if (detection.lookingAtScreen) {
      this.lastLookingAtScreenTime = now;
    }

    // Calculate time since last attention
    const timeSinceLastFace = now - this.lastFaceDetectedTime;
    const timeSinceLastLooking = now - this.lastLookingAtScreenTime;

    // Determine if distracted
    const isDistracted =
      timeSinceLastFace > CONFIG.detection.noFaceTimeout ||
      timeSinceLastLooking > CONFIG.detection.gazeAwayTimeout;

    // Update state and trigger intervention if needed
    if (isDistracted && this.currentState === 'focused') {
      this.onDistractionDetected();
    } else if (!isDistracted && this.currentState === 'distracted') {
      this.onFocusRestored();
    }

    // Update focus time
    if (this.currentState === 'focused') {
      const timeSinceLastUpdate = now - this.lastUpdateTime;
      this.totalFocusTime += timeSinceLastUpdate;
    }

    this.lastUpdateTime = now;
  }

  /**
   * Handle distraction detected
   */
  onDistractionDetected() {
    console.log('Distraction detected!');
    this.currentState = 'distracted';
    this.distractionCount++;

    // Play intervention video (commented out for testing eye detection)
    // this.attentionPlayer.play();
    console.log('Intervention video disabled for testing - distraction count:', this.distractionCount);

    // Dispatch event
    this.dispatchEvent('distraction-detected', {
      distractionCount: this.distractionCount,
    });
  }

  /**
   * Handle focus restored
   */
  onFocusRestored() {
    console.log('Focus restored - auto-closing intervention video');
    this.currentState = 'focused';

    // Stop intervention video if playing (auto-close)
    this.attentionPlayer.stop();

    // Dispatch event
    this.dispatchEvent('focus-restored', {});
  }

  /**
   * Get current statistics
   */
  getStats() {
    const now = Date.now();
    const sessionDuration = this.sessionStartTime ? now - this.sessionStartTime : 0;

    return {
      state: this.currentState,
      sessionDuration,
      totalFocusTime: this.totalFocusTime,
      distractionCount: this.distractionCount,
      focusPercentage:
        sessionDuration > 0 ? (this.totalFocusTime / sessionDuration) * 100 : 0,
    };
  }

  /**
   * Dispatch custom events
   */
  dispatchEvent(eventName, detail) {
    const event = new CustomEvent(eventName, { detail });
    window.dispatchEvent(event);
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
    this.distractionMonitor = new DistractionMonitor(
      this.faceDetector,
      this.attentionPlayer,
      this.cameraManager
    );

    this.isRunning = false;
    this.statsIntervalId = null;
  }

  /**
   * Initialize the application
   */
  async initialize() {
    try {
      // Get UI elements
      const canvas = document.getElementById('camera-canvas');
      const startBtn = document.getElementById('start-btn');
      const statusElement = document.getElementById('status');

      if (!canvas || !startBtn || !statusElement) {
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
        // Disable start button
        startBtn.disabled = true;
        startBtn.classList.add('disabled');

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

      // Setup button event
      startBtn.addEventListener('click', () => this.toggleSession());

      // Ready
      this.updateStatus('ready', 'Ready - Click Start to begin');

      console.log('Focus Keeper App initialized');
    } catch (error) {
      console.error('Initialization error:', error);
      this.updateStatus('error', 'Error: ' + error.message);
      this.showError(error.message);
    }
  }

  /**
   * Toggle session start/stop
   */
  async toggleSession() {
    if (this.isRunning) {
      this.stopSession();
    } else {
      await this.startSession();
    }
  }

  /**
   * Start a focus session
   */
  async startSession() {
    try {
      // Start camera
      await this.cameraManager.start();

      // Start monitoring
      const videoElement = this.cameraManager.getVideoElement();
      this.distractionMonitor.start(videoElement);

      // Update UI
      this.isRunning = true;
      document.getElementById('start-btn').textContent = 'Stop Session';
      this.updateStatus('focused', 'Focused - Keep your eyes on the screen!');

      // Start stats updates
      this.startStatsUpdates();

      console.log('Session started');
    } catch (error) {
      console.error('Failed to start session:', error);
      this.showError('Failed to start: ' + error.message);
    }
  }

  /**
   * Stop the focus session
   */
  stopSession() {
    // Stop monitoring
    this.distractionMonitor.stop();

    // Stop camera
    this.cameraManager.stop();

    // Stop stats updates
    this.stopStatsUpdates();

    // Update UI
    this.isRunning = false;
    document.getElementById('start-btn').textContent = 'Start Session';
    this.updateStatus('ready', 'Session ended - Click Start to begin again');

    // Save stats
    this.saveStats();

    console.log('Session stopped');
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
   * Start periodic stats updates
   */
  startStatsUpdates() {
    this.updateStatsDisplay();

    this.statsIntervalId = setInterval(() => {
      this.updateStatsDisplay();
    }, CONFIG.ui.statusUpdateInterval);
  }

  /**
   * Stop stats updates
   */
  stopStatsUpdates() {
    if (this.statsIntervalId) {
      clearInterval(this.statsIntervalId);
      this.statsIntervalId = null;
    }
  }

  /**
   * Update statistics display
   */
  updateStatsDisplay() {
    const stats = this.distractionMonitor.getStats();
    const videoStats = this.attentionPlayer.getStats();

    // Update session duration
    document.getElementById('session-time').textContent = this.formatTime(
      stats.sessionDuration
    );

    // Update focus time
    document.getElementById('focus-time').textContent = this.formatTime(stats.totalFocusTime);

    // Update distraction count
    document.getElementById('distraction-count').textContent = stats.distractionCount;

    // Update intervention count
    document.getElementById('intervention-count').textContent = videoStats.interventionCount;

    // Update focus percentage
    document.getElementById('focus-percentage').textContent =
      stats.focusPercentage.toFixed(1) + '%';

    // Update status based on current state
    if (stats.state === 'focused') {
      this.updateStatus('focused', 'Focused - Great job!');
    } else if (stats.state === 'distracted') {
      this.updateStatus('distracted', 'Distracted - Get back to work!');
    }
  }

  /**
   * Format milliseconds to MM:SS
   */
  formatTime(ms) {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
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

  /**
   * Save statistics to localStorage
   */
  saveStats() {
    if (!CONFIG.storage.persistStats) return;

    const stats = this.distractionMonitor.getStats();
    const videoStats = this.attentionPlayer.getStats();

    const data = {
      ...stats,
      interventionCount: videoStats.interventionCount,
      savedAt: Date.now(),
    };

    localStorage.setItem(CONFIG.storage.statsKey, JSON.stringify(data));
  }

  /**
   * Load statistics from localStorage
   */
  loadStats() {
    if (!CONFIG.storage.persistStats) return null;

    const data = localStorage.getItem(CONFIG.storage.statsKey);
    return data ? JSON.parse(data) : null;
  }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
  const app = new FocusKeeperApp();
  await app.initialize();

  // Expose app instance for debugging
  window.focusKeeperApp = app;
});
