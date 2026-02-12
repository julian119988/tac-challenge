/**
 * Model Trainer - TensorFlow.js CNN for gaze prediction
 * Based on HUE Vision training.js
 */

import { CONFIG } from './config.js';

export class ModelTrainer {
  constructor(datasetManager) {
    this.datasetManager = datasetManager;
    this.currentModel = null;
    this.inTraining = false;
    this.epochsTrained = 0;
    this.onProgressCallback = null;
    this.onCompleteCallback = null;
  }

  /**
   * Create CNN model architecture
   * Input 1: Eye image [55, 25, 3]
   * Input 2: Meta info [4] (eye position and size)
   * Output: [2] (x, y gaze coordinates)
   */
  createModel() {
    const inputImage = tf.input({
      name: 'image',
      shape: [
        CONFIG.eyeTracking.visualization.eyeCanvasHeight,
        CONFIG.eyeTracking.visualization.eyeCanvasWidth,
        3,
      ],
    });

    const inputMeta = tf.input({
      name: 'metaInfos',
      shape: [4],
    });

    // Conv2D layer
    const conv = tf.layers
      .conv2d({
        kernelSize: 5,
        filters: 20,
        strides: 1,
        activation: 'relu',
        kernelInitializer: 'varianceScaling',
      })
      .apply(inputImage);

    // MaxPooling layer
    const maxpool = tf.layers
      .maxPooling2d({
        poolSize: [2, 2],
        strides: [2, 2],
      })
      .apply(conv);

    // Flatten
    const flat = tf.layers.flatten().apply(maxpool);

    // Dropout
    const dropout = tf.layers.dropout(0.2).apply(flat);

    // Concatenate with metadata
    const concat = tf.layers.concatenate().apply([dropout, inputMeta]);

    // Dense output layer
    const output = tf.layers
      .dense({
        units: 2,
        activation: 'tanh',
        kernelInitializer: 'varianceScaling',
      })
      .apply(concat);

    const model = tf.model({
      inputs: [inputImage, inputMeta],
      outputs: output,
    });

    console.log('Model created');
    model.summary();

    return model;
  }

  /**
   * Train the model
   */
  async fitModel() {
    if (this.inTraining) {
      console.warn('Already training');
      return;
    }

    const { train, val } = this.datasetManager;

    if (train.n < CONFIG.eyeTracking.calibration.minSamples) {
      throw new Error(`Need at least ${CONFIG.eyeTracking.calibration.minSamples} samples to train`);
    }

    this.inTraining = true;
    const epochs = CONFIG.eyeTracking.modelHyperparams.epochs;

    // Calculate batch size
    let batchSize = Math.floor(train.n * CONFIG.eyeTracking.modelHyperparams.batchSizeRatio);
    batchSize = Math.max(
      CONFIG.eyeTracking.modelHyperparams.minBatchSize,
      Math.min(batchSize, CONFIG.eyeTracking.modelHyperparams.maxBatchSize)
    );

    console.info('Training on', train.n, 'samples with batch size', batchSize);

    // Create model if needed
    if (this.currentModel === null) {
      this.currentModel = this.createModel();
    }

    // Compile model
    this.currentModel.compile({
      optimizer: tf.train.adam(CONFIG.eyeTracking.modelHyperparams.learningRate),
      loss: 'meanSquaredError',
    });

    let bestEpoch = -1;
    let bestTrainLoss = Number.MAX_SAFE_INTEGER;
    let bestValLoss = Number.MAX_SAFE_INTEGER;
    const bestModelPath = 'localstorage://best-model';

    // Train model
    try {
      await this.currentModel.fit(train.x, train.y, {
        batchSize: batchSize,
        epochs: epochs,
        shuffle: true,
        validationData: val.n > 0 ? [val.x, val.y] : undefined,
        callbacks: {
          onEpochBegin: async (epoch) => {
            if (this.onProgressCallback) {
              this.onProgressCallback(
                epoch,
                epochs,
                epoch > 0 ? bestTrainLoss : 0,
                epoch > 0 ? bestValLoss : 0
              );
            }
          },
          onEpochEnd: async (epoch, logs) => {
            console.info('Epoch', epoch, 'losses:', logs);
            this.epochsTrained += 1;

            if (this.onProgressCallback) {
              this.onProgressCallback(epoch + 1, epochs, logs.loss, logs.val_loss || logs.loss);
            }

            // Save best model
            if (val.n > 0 && logs.val_loss < bestValLoss) {
              bestEpoch = epoch;
              bestTrainLoss = logs.loss;
              bestValLoss = logs.val_loss;
              await this.currentModel.save(bestModelPath);
            } else if (val.n === 0 && logs.loss < bestTrainLoss) {
              bestEpoch = epoch;
              bestTrainLoss = logs.loss;
              await this.currentModel.save(bestModelPath);
            }

            return await tf.nextFrame();
          },
          onTrainEnd: async () => {
            console.info('Finished training');

            // Load best model
            this.epochsTrained -= epochs - bestEpoch;
            console.info('Loading best epoch:', this.epochsTrained);

            this.currentModel = await tf.loadLayersModel(bestModelPath);

            this.inTraining = false;

            if (this.onCompleteCallback) {
              this.onCompleteCallback({
                epochs: this.epochsTrained,
                trainLoss: bestTrainLoss,
                valLoss: bestValLoss,
              });
            }
          },
        },
      });
    } catch (error) {
      console.error('Training error:', error);
      this.inTraining = false;
      throw error;
    }
  }

  /**
   * Get prediction for current eye image
   * @returns {Promise<Array>} Predicted [x, y] coordinates in [0, 1] range
   */
  async getPrediction() {
    if (!this.currentModel) {
      throw new Error('Model not trained');
    }

    const img = this.datasetManager.eyeTracker.getCurrentEyeImage();
    const metaInfos = this.datasetManager.eyeTracker.getEyeMetadata();

    if (!img || !metaInfos) {
      return null;
    }

    const convertedImg = await this.datasetManager.convertImage(img);
    const prediction = this.currentModel.predict([convertedImg, metaInfos]);
    const predictionData = await prediction.data();

    tf.dispose([img, metaInfos, convertedImg, prediction]);

    // Convert from [-0.5, 0.5] to [0, 1]
    return [predictionData[0] + 0.5, predictionData[1] + 0.5];
  }

  /**
   * Reset model and training state
   */
  resetModel() {
    if (this.currentModel) {
      this.currentModel.dispose();
      this.currentModel = null;
    }
    this.epochsTrained = 0;
    this.inTraining = false;
    console.log('Model reset');
  }

  /**
   * Save model to file
   */
  async saveModel(filename = 'gaze-model') {
    if (!this.currentModel) {
      throw new Error('No model to save');
    }
    await this.currentModel.save(`downloads://${filename}`);
    console.log('Model saved');
  }

  /**
   * Load model from files
   */
  async loadModel(files) {
    try {
      this.currentModel = await tf.loadLayersModel(tf.io.browserFiles(files));
      console.log('Model loaded');
      return true;
    } catch (error) {
      console.error('Error loading model:', error);
      return false;
    }
  }

  /**
   * Check if model is trained
   */
  isModelTrained() {
    return this.currentModel !== null && !this.inTraining;
  }

  /**
   * Set progress callback
   */
  setProgressCallback(callback) {
    this.onProgressCallback = callback;
  }

  /**
   * Set completion callback
   */
  setCompleteCallback(callback) {
    this.onCompleteCallback = callback;
  }
}
