// Configuration for Focus Keeper App

export const CONFIG = {
  // Detection thresholds
  detection: {
    noFaceTimeout: 3000, // milliseconds - time before triggering distraction when no face detected
    gazeAwayTimeout: 4000, // milliseconds - time before triggering distraction when looking away
    headTurnThreshold: 30, // degrees - head turn angle threshold
    confidenceThreshold: 0.5, // minimum confidence for face detection
    detectionInterval: 200, // DEPRECATED - no longer used; detection now runs continuously via requestAnimationFrame
  },

  // Camera settings
  camera: {
    width: 640,
    height: 480,
    facingMode: 'user', // front-facing camera
    frameRate: 30,
  },

  // Video intervention sources
  videos: [
    // Using YouTube embeds for attention-grabbing videos
    'https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1', // Classic attention grabber
    'https://www.youtube.com/embed/ZZ5LpwO-An4?autoplay=1', // Another engaging video
    'https://www.youtube.com/embed/y6120QOlsfU?autoplay=1', // Darude - Sandstorm
  ],

  // Attention grabber configuration (Issue #29)
  // Displays a skeleton video as a "jumpscare" when user looks away from screen
  attentionGrabber: {
    enabled: true, // enable/disable skeleton video feature
    videoPath: 'assets/skeleton-attention.mp4', // path to skeleton video
    triggerDelay: 0, // milliseconds before triggering (0 for instant jumpscare)
    instantClose: true, // close immediately when user looks back
  },

  // UI settings
  ui: {
    statusUpdateInterval: 1000, // milliseconds - update stats every second (deprecated, no longer used)
    focusColor: '#4ade80', // green
    distractedColor: '#ef4444', // red
    loadingColor: '#fbbf24', // yellow
  },

  // Face visualization settings
  visualization: {
    faceBoxColor: 'rgba(239, 68, 68, 0.8)', // semi-transparent red
    faceBoxFillColor: 'rgba(239, 68, 68, 0.1)', // very transparent red fill
    landmarkColor: 'rgba(239, 68, 68, 0.9)', // semi-transparent red for dots
    faceBoxLineWidth: 3,
    eyeLandmarkRadius: 3,
    noseLandmarkRadius: 3,
    mouthLandmarkRadius: 3,
    faceOutlineLandmarkRadius: 2,
  },

  // Statistics persistence
  storage: {
    statsKey: 'focus_keeper_stats',
    persistStats: true,
  },

  // Eye tracking configuration
  eyeTracking: {
    enabled: true,
    modelHyperparams: {
      epochs: 20,
      batchSizeRatio: 0.1, // 10% of training data
      learningRate: 0.0005,
      minBatchSize: 2,
      maxBatchSize: 64,
    },
    calibration: {
      targetSize: 40,
      gridPoints: 9, // 3x3 grid
      autoMoveDelay: 2000, // milliseconds between calibration points
      minSamples: 20, // minimum samples needed before training
    },
    prediction: {
      updateInterval: 100, // milliseconds - 10 FPS
      confidenceThreshold: 0.7,
    },
    visualization: {
      heatmapOpacity: 0.7,
      colorScheme: 'hot', // hot, cool, rainbow
      eyeCanvasWidth: 55,
      eyeCanvasHeight: 25,
    },
  },
};
