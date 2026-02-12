/**
 * UI Controller - Manage eye tracking UI state and interactions
 * Based on HUE Vision ui.js
 */

import { CONFIG } from './config.js';

export class UIController {
  constructor() {
    this.state = 'initial';
    this.phase = 'training';
    this.readyToCollect = false;
    this.calibrationMode = false;
    this.calibrationPoints = [];
    this.currentCalibrationPoint = 0;
    this.calibrationInterval = null;

    this.datasetManager = null;
    this.modelTrainer = null;
    this.gazePredictor = null;
  }

  /**
   * Initialize UI controller with managers
   */
  initialize(datasetManager, modelTrainer, gazePredictor) {
    this.datasetManager = datasetManager;
    this.modelTrainer = modelTrainer;
    this.gazePredictor = gazePredictor;

    this.setupEventListeners();
    this.showPhase('training');
  }

  /**
   * Setup button event listeners
   */
  setupEventListeners() {
    // Calibration
    const calibrateBtn = document.getElementById('start-calibration');
    if (calibrateBtn) {
      calibrateBtn.addEventListener('click', () => this.startCalibration());
    }

    // Training
    const trainBtn = document.getElementById('start-training');
    if (trainBtn) {
      trainBtn.addEventListener('click', () => this.startTraining());
    }

    // Reset model
    const resetBtn = document.getElementById('reset-model');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => this.resetModel());
    }

    // Tracking
    const startTrackBtn = document.getElementById('start-tracking');
    if (startTrackBtn) {
      startTrackBtn.addEventListener('click', () => this.startTracking());
    }

    const stopTrackBtn = document.getElementById('stop-tracking');
    if (stopTrackBtn) {
      stopTrackBtn.addEventListener('click', () => this.stopTracking());
    }

    // Heatmap
    const heatmapBtn = document.getElementById('draw-heatmap');
    if (heatmapBtn) {
      heatmapBtn.addEventListener('click', () => this.drawHeatmap());
    }

    // Session controls
    const startSessionBtn = document.getElementById('start-session');
    if (startSessionBtn) {
      startSessionBtn.addEventListener('click', () => this.showPhase('session'));
    }

    const newSessionBtn = document.getElementById('new-session');
    if (newSessionBtn) {
      newSessionBtn.addEventListener('click', () => this.newSession());
    }

    const retrainBtn = document.getElementById('retrain-model');
    if (retrainBtn) {
      retrainBtn.addEventListener('click', () => this.showPhase('training'));
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => this.handleKeyboard(e));
  }

  /**
   * Handle keyboard shortcuts
   */
  handleKeyboard(event) {
    // Space - capture example
    if (event.code === 'Space' && this.readyToCollect && !this.calibrationMode) {
      event.preventDefault();
      this.captureExample();
    }

    // C - start calibration
    if (event.code === 'KeyC' && this.readyToCollect && !this.calibrationMode) {
      event.preventDefault();
      this.startCalibration();
    }

    // T - start training
    if (event.code === 'KeyT' && !this.modelTrainer.inTraining) {
      const trainBtn = document.getElementById('start-training');
      if (trainBtn && !trainBtn.disabled) {
        event.preventDefault();
        this.startTraining();
      }
    }

    // R - reset model
    if (event.code === 'KeyR') {
      const resetBtn = document.getElementById('reset-model');
      if (resetBtn && !resetBtn.disabled) {
        event.preventDefault();
        this.resetModel();
      }
    }
  }

  /**
   * Show specific UI phase
   */
  showPhase(phase) {
    this.phase = phase;

    const trainingPhase = document.getElementById('training-phase');
    const sessionPhase = document.getElementById('session-phase');
    const heatmapPhase = document.getElementById('heatmap-phase');

    if (trainingPhase) trainingPhase.classList.add('hidden');
    if (sessionPhase) sessionPhase.classList.add('hidden');
    if (heatmapPhase) heatmapPhase.classList.add('hidden');

    const currentPhase = document.getElementById(`${phase}-phase`);
    if (currentPhase) {
      currentPhase.classList.remove('hidden');
    }
  }

  /**
   * Update UI when webcam is enabled
   */
  onWebcamEnabled() {
    console.log('Webcam enabled - waiting for face detection');
    const status = document.querySelector('[data-status="webcam"]');
    if (status) {
      status.textContent = 'Connected';
      status.classList.add('status-connected');
    } else {
      console.warn('Webcam status element not found');
    }
  }

  /**
   * Update UI when face is found
   */
  onFoundFace() {
    if (!this.readyToCollect) {
      console.log('Face detected - enabling calibration button');
    }

    this.readyToCollect = true;

    const faceStatus = document.querySelector('[data-status="face"]');
    if (faceStatus) {
      faceStatus.textContent = 'Detected';
      faceStatus.classList.add('status-detected');
    }

    const calibrateBtn = document.getElementById('start-calibration');
    if (calibrateBtn) {
      console.log('Enabling calibration button');
      calibrateBtn.disabled = false;
    } else {
      console.error('Calibration button not found!');
    }

    // Enable training button if we have enough samples
    if (this.datasetManager) {
      try {
        const counts = this.datasetManager.getCounts();
        if (counts.total >= CONFIG.eyeTracking.calibration.minSamples) {
          const trainBtn = document.getElementById('start-training');
          if (trainBtn) {
            trainBtn.disabled = false;
          }
        }
      } catch (error) {
        console.error('Error checking dataset counts:', error);
      }
    } else {
      console.warn('DatasetManager not initialized');
    }
  }

  /**
   * Update UI when face is lost
   */
  onFaceNotFound() {
    this.readyToCollect = false;

    const faceStatus = document.querySelector('[data-status="face"]');
    if (faceStatus) {
      faceStatus.textContent = 'Not Detected';
      faceStatus.classList.remove('status-detected');
    }
  }

  /**
   * Capture calibration example
   */
  async captureExample() {
    if (!this.readyToCollect) {
      console.log('Not ready to collect - face not detected');
      return;
    }

    try {
      const counts = await this.datasetManager.captureExample();
      if (counts) {
        this.updateDataCounts(counts.train, counts.val);
        console.log('Example captured:', counts);
      }
    } catch (error) {
      console.error('Failed to capture example:', error);
    }
  }

  /**
   * Update data point counters
   */
  updateDataCounts(trainCount, valCount) {
    const trainEl = document.querySelector('[data-count="train"]');
    if (trainEl) {
      trainEl.textContent = trainCount;
    }

    const valEl = document.querySelector('[data-count="val"]');
    if (valEl) {
      valEl.textContent = valCount;
    }

    const totalEl = document.querySelector('[data-count="total"]');
    if (totalEl) {
      totalEl.textContent = trainCount + valCount;
    }

    // Enable training if we have enough samples
    if (trainCount >= CONFIG.eyeTracking.calibration.minSamples) {
      const trainBtn = document.getElementById('start-training');
      if (trainBtn) {
        trainBtn.disabled = false;
      }
    }
  }

  /**
   * Start calibration mode
   */
  startCalibration() {
    if (!this.readyToCollect || this.calibrationMode) {
      return;
    }

    this.calibrationMode = true;

    // Create calibration grid (3x3)
    const width = window.innerWidth;
    const height = window.innerHeight;
    const padding = 100;

    this.calibrationPoints = [
      { x: padding, y: padding },
      { x: width / 2, y: padding },
      { x: width - padding, y: padding },
      { x: padding, y: height / 2 },
      { x: width / 2, y: height / 2 },
      { x: width - padding, y: height / 2 },
      { x: padding, y: height - padding },
      { x: width / 2, y: height - padding },
      { x: width - padding, y: height - padding },
    ];

    this.currentCalibrationPoint = 0;
    this.showCalibrationTarget();

    // Auto-capture at each point
    this.calibrationInterval = setInterval(async () => {
      if (!this.readyToCollect) {
        return;
      }

      const point = this.calibrationPoints[this.currentCalibrationPoint];
      const coords = [point.x / width, point.y / height];

      await this.datasetManager.captureExample(coords);

      this.currentCalibrationPoint++;

      if (this.currentCalibrationPoint >= this.calibrationPoints.length) {
        this.stopCalibration();
      } else {
        this.showCalibrationTarget();
      }
    }, CONFIG.eyeTracking.calibration.autoMoveDelay);

    console.log('Calibration started');
  }

  /**
   * Show calibration target
   */
  showCalibrationTarget() {
    const point = this.calibrationPoints[this.currentCalibrationPoint];
    let target = document.getElementById('calibration-target');

    if (!target) {
      target = document.createElement('div');
      target.id = 'calibration-target';
      document.body.appendChild(target);
    }

    target.style.left = `${point.x}px`;
    target.style.top = `${point.y}px`;
    target.style.display = 'block';
  }

  /**
   * Stop calibration
   */
  stopCalibration() {
    if (this.calibrationInterval) {
      clearInterval(this.calibrationInterval);
      this.calibrationInterval = null;
    }

    this.calibrationMode = false;

    const target = document.getElementById('calibration-target');
    if (target) {
      target.style.display = 'none';
    }

    console.log('Calibration complete');
  }

  /**
   * Start model training
   */
  async startTraining() {
    if (this.modelTrainer.inTraining) {
      return;
    }

    const trainBtn = document.getElementById('start-training');
    if (trainBtn) {
      trainBtn.disabled = true;
      trainBtn.textContent = 'Training...';
    }

    try {
      // Set callbacks
      this.modelTrainer.setProgressCallback((epoch, total, loss, valLoss) => {
        this.showTrainingProgress(epoch, total, loss, valLoss);
      });

      this.modelTrainer.setCompleteCallback((results) => {
        this.onTrainingComplete(results);
      });

      await this.modelTrainer.fitModel();
    } catch (error) {
      console.error('Training failed:', error);
      alert('Training failed: ' + error.message);

      if (trainBtn) {
        trainBtn.disabled = false;
        trainBtn.textContent = 'Start Training';
      }
    }
  }

  /**
   * Show training progress
   */
  showTrainingProgress(epoch, totalEpochs, loss, valLoss) {
    let progress = document.getElementById('training-progress');

    if (!progress) {
      progress = document.createElement('div');
      progress.id = 'training-progress';
      document.body.appendChild(progress);
    }

    const percent = Math.round((epoch / totalEpochs) * 100);

    progress.innerHTML = `
      <div>Training Progress: ${epoch}/${totalEpochs} epochs (${percent}%)</div>
      <div class="progress-bar">
        <div class="progress-fill" style="width: ${percent}%"></div>
      </div>
      <div>Loss: ${loss.toFixed(5)}${valLoss ? ` | Val Loss: ${valLoss.toFixed(5)}` : ''}</div>
    `;

    progress.style.display = 'block';
  }

  /**
   * Handle training completion
   */
  onTrainingComplete(results) {
    console.log('Training complete:', results);

    const trainBtn = document.getElementById('start-training');
    if (trainBtn) {
      trainBtn.disabled = false;
      trainBtn.textContent = 'Start Training';
    }

    const progress = document.getElementById('training-progress');
    if (progress) {
      setTimeout(() => {
        progress.style.display = 'none';
      }, 3000);
    }

    // Enable session controls
    const sessionBtn = document.getElementById('start-session');
    if (sessionBtn) {
      sessionBtn.disabled = false;
    }

    const startTrackBtn = document.getElementById('start-tracking');
    if (startTrackBtn) {
      startTrackBtn.disabled = false;
    }

    const resetBtn = document.getElementById('reset-model');
    if (resetBtn) {
      resetBtn.disabled = false;
    }

    alert('Training complete! Click "Start Session" to switch to tracking mode.');
  }

  /**
   * Reset model
   */
  resetModel() {
    if (confirm('Reset model and training data?')) {
      this.modelTrainer.resetModel();

      const sessionBtn = document.getElementById('start-session');
      if (sessionBtn) {
        sessionBtn.disabled = true;
      }

      const resetBtn = document.getElementById('reset-model');
      if (resetBtn) {
        resetBtn.disabled = true;
      }

      console.log('Model reset');
    }
  }

  /**
   * Start tracking
   */
  startTracking() {
    this.gazePredictor.start();

    const startBtn = document.getElementById('start-tracking');
    if (startBtn) {
      startBtn.disabled = true;
    }

    const stopBtn = document.getElementById('stop-tracking');
    if (stopBtn) {
      stopBtn.disabled = false;
    }

    const heatmapBtn = document.getElementById('draw-heatmap');
    if (heatmapBtn) {
      heatmapBtn.disabled = true;
    }
  }

  /**
   * Stop tracking
   */
  stopTracking() {
    this.gazePredictor.stop();

    const startBtn = document.getElementById('start-tracking');
    if (startBtn) {
      startBtn.disabled = false;
    }

    const stopBtn = document.getElementById('stop-tracking');
    if (stopBtn) {
      stopBtn.disabled = true;
    }

    const heatmapBtn = document.getElementById('draw-heatmap');
    if (heatmapBtn) {
      heatmapBtn.disabled = false;
    }
  }

  /**
   * Draw heatmap
   */
  drawHeatmap() {
    this.showPhase('heatmap');

    // Import heatmap module dynamically
    import('./heatmap-viz.js').then((module) => {
      const heatmap = new module.HeatmapVisualizer();
      const sessionData = this.gazePredictor.getSessionData();
      heatmap.drawHeatmap(sessionData);
    });
  }

  /**
   * Start new session
   */
  newSession() {
    this.datasetManager.clearSession();
    this.showPhase('session');
  }
}
