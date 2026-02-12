/**
 * Gaze Predictor - Real-time gaze prediction using trained model
 * Based on HUE Vision main.js tracking functionality
 */

import { CONFIG } from './config.js';

export class GazePredictor {
  constructor(modelTrainer, datasetManager) {
    this.modelTrainer = modelTrainer;
    this.datasetManager = datasetManager;
    this.active = false;
    this.interval = null;
    this.lastPrediction = null;
    this.onPredictionCallback = null;
  }

  /**
   * Start gaze prediction loop
   */
  start() {
    if (this.active) {
      console.warn('Gaze prediction already active');
      return;
    }

    if (!this.modelTrainer.isModelTrained()) {
      throw new Error('Model not trained - cannot start prediction');
    }

    this.datasetManager.clearSession();
    this.active = true;

    console.log('Starting gaze prediction at', 1000 / CONFIG.eyeTracking.prediction.updateInterval, 'FPS');

    this.interval = setInterval(() => {
      this.predict();
    }, CONFIG.eyeTracking.prediction.updateInterval);
  }

  /**
   * Stop gaze prediction loop
   */
  stop() {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }
    this.active = false;
    console.log('Gaze prediction stopped');
  }

  /**
   * Perform single prediction
   */
  async predict() {
    if (!this.active || !this.modelTrainer.isModelTrained()) {
      return;
    }

    try {
      const prediction = await this.modelTrainer.getPrediction();

      if (prediction) {
        this.lastPrediction = prediction;

        // Store in session data
        this.datasetManager.session.n += 1;
        this.datasetManager.session.x.push(prediction[0]);
        this.datasetManager.session.y.push(prediction[1]);

        // Call callback if set
        if (this.onPredictionCallback) {
          this.onPredictionCallback(prediction);
        }
      }
    } catch (error) {
      console.error('Prediction error:', error);
    }
  }

  /**
   * Get last prediction
   * @returns {Array|null} [x, y] coordinates in [0, 1] range
   */
  getLastPrediction() {
    return this.lastPrediction;
  }

  /**
   * Get session data for heatmap
   */
  getSessionData() {
    return this.datasetManager.session;
  }

  /**
   * Check if prediction is active
   */
  isActive() {
    return this.active;
  }

  /**
   * Set prediction callback
   */
  setPredictionCallback(callback) {
    this.onPredictionCallback = callback;
  }

  /**
   * Get predicted screen coordinates
   * @returns {Object|null} {x, y} in pixels
   */
  getScreenCoordinates() {
    if (!this.lastPrediction) {
      return null;
    }

    return {
      x: this.lastPrediction[0] * window.innerWidth,
      y: this.lastPrediction[1] * window.innerHeight,
    };
  }
}
