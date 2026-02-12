/**
 * Dataset Manager - Handle training data collection and management
 * Based on HUE Vision dataset.js
 */

import { CONFIG } from './config.js';
import { tensorToArray, getMousePosition } from './utils.js';

export class DatasetManager {
  constructor(eyeTracker) {
    this.eyeTracker = eyeTracker;

    this.train = {
      n: 0,
      x: null,
      y: null,
    };

    this.val = {
      n: 0,
      x: null,
      y: null,
    };

    this.session = {
      n: 0,
      x: [],
      y: [],
    };
  }

  /**
   * Clear session data
   */
  clearSession() {
    this.session = {
      n: 0,
      x: [],
      y: [],
    };
  }

  /**
   * Determine which dataset to add to (train or val)
   * 80% train, 20% validation
   */
  whichDataset() {
    if (this.train.n === 0) {
      return 'train';
    }
    if (this.val.n === 0) {
      return 'val';
    }
    return Math.random() < 0.2 ? 'val' : 'train';
  }

  /**
   * Convert RGB to grayscale with spatial coordinates
   */
  rgbToGrayscale(imageArray, n, x, y) {
    let r = (imageArray[n][x][y][0] + 1) / 2;
    let g = (imageArray[n][x][y][1] + 1) / 2;
    let b = (imageArray[n][x][y][2] + 1) / 2;

    // Gamma correction
    const exponent = 1 / 2.2;
    r = Math.pow(r, exponent);
    g = Math.pow(g, exponent);
    b = Math.pow(b, exponent);

    // Gleam
    const gleam = (r + g + b) / 3;
    return gleam * 2 - 1;
  }

  /**
   * Convert image to grayscale and add spatial info
   */
  async convertImage(image) {
    const imageShape = image.shape;
    const imageArray = await image.array();
    const w = imageShape[1];
    const h = imageShape[2];

    const data = [new Array(w)];
    for (let x = 0; x < w; x++) {
      data[0][x] = new Array(h);
      for (let y = 0; y < h; y++) {
        const grayValue = this.rgbToGrayscale(imageArray, 0, x, y);
        data[0][x][y] = [grayValue, (x / w) * 2 - 1, (y / h) * 2 - 1];
      }
    }

    return tf.tensor(data);
  }

  /**
   * Add data to specific dataset (train or val)
   */
  addToDataset(image, metaInfos, target, key) {
    const set = this[key];

    if (set.x === null) {
      set.x = [tf.keep(image), tf.keep(metaInfos)];
      set.y = tf.keep(target);
    } else {
      const oldImage = set.x[0];
      set.x[0] = tf.keep(oldImage.concat(image, 0));

      const oldEyePos = set.x[1];
      set.x[1] = tf.keep(oldEyePos.concat(metaInfos, 0));

      const oldY = set.y;
      set.y = tf.keep(oldY.concat(target, 0));

      tf.dispose([oldImage, oldEyePos, oldY, target]);
    }

    set.n += 1;
  }

  /**
   * Add example to dataset
   * @param {tf.Tensor} image - Eye image tensor
   * @param {tf.Tensor} metaInfos - Eye metadata tensor
   * @param {Array} targetCoords - [x, y] normalized coordinates (0-1)
   */
  async addExample(image, metaInfos, targetCoords, dontDispose = false) {
    // Normalize target coordinates to [-0.5, 0.5] range
    targetCoords[0] = targetCoords[0] - 0.5;
    targetCoords[1] = targetCoords[1] - 0.5;

    const target = tf.keep(
      tf.tidy(() => {
        return tf.tensor1d(targetCoords).expandDims(0);
      })
    );

    const key = this.whichDataset();
    const convertedImage = await this.convertImage(image);

    this.addToDataset(convertedImage, metaInfos, target, key);

    if (!dontDispose) {
      tf.dispose([image, metaInfos]);
    }

    return { train: this.train.n, val: this.val.n };
  }

  /**
   * Capture example from current eye tracker state
   * @param {Array} targetCoords - Optional target coordinates, defaults to mouse position
   */
  async captureExample(targetCoords = null) {
    if (!targetCoords) {
      const mousePos = getMousePosition();
      targetCoords = [mousePos.x, mousePos.y];
    }

    const img = this.eyeTracker.getCurrentEyeImage();
    const metaInfos = this.eyeTracker.getEyeMetadata();

    if (!img || !metaInfos) {
      console.warn('Cannot capture example - missing eye data');
      return null;
    }

    const counts = await this.addExample(img, metaInfos, targetCoords);
    console.log('Example added:', counts);
    return counts;
  }

  /**
   * Export dataset to JSON
   */
  toJSON() {
    const tensorToArray = (t) => {
      const typedArray = t.dataSync();
      return Array.prototype.slice.call(typedArray);
    };

    return {
      inputWidth: CONFIG.eyeTracking.visualization.eyeCanvasWidth,
      inputHeight: CONFIG.eyeTracking.visualization.eyeCanvasHeight,
      train: {
        shapes: {
          x0: this.train.x ? this.train.x[0].shape : null,
          x1: this.train.x ? this.train.x[1].shape : null,
          y: this.train.y ? this.train.y.shape : null,
        },
        n: this.train.n,
        x: this.train.x && [
          tensorToArray(this.train.x[0]),
          tensorToArray(this.train.x[1]),
        ],
        y: this.train.y && tensorToArray(this.train.y),
      },
      val: {
        shapes: {
          x0: this.val.x ? this.val.x[0].shape : null,
          x1: this.val.x ? this.val.x[1].shape : null,
          y: this.val.y ? this.val.y.shape : null,
        },
        n: this.val.n,
        x: this.val.x && [
          tensorToArray(this.val.x[0]),
          tensorToArray(this.val.x[1]),
        ],
        y: this.val.y && tensorToArray(this.val.y),
      },
    };
  }

  /**
   * Import dataset from JSON
   */
  fromJSON(data) {
    this.train.n = data.train.n;
    this.train.x = data.train.x && [
      tf.tensor(data.train.x[0], data.train.shapes.x0),
      tf.tensor(data.train.x[1], data.train.shapes.x1),
    ];
    this.train.y = data.train.y && tf.tensor(data.train.y, data.train.shapes.y);

    this.val.n = data.val.n;
    this.val.x = data.val.x && [
      tf.tensor(data.val.x[0], data.val.shapes.x0),
      tf.tensor(data.val.x[1], data.val.shapes.x1),
    ];
    this.val.y = data.val.y && tf.tensor(data.val.y, data.val.shapes.y);

    console.log('Dataset loaded:', { train: this.train.n, val: this.val.n });
  }

  /**
   * Get dataset counts
   */
  getCounts() {
    return {
      train: this.train.n,
      val: this.val.n,
      total: this.train.n + this.val.n,
    };
  }
}
