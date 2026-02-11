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

  // UI settings
  ui: {
    statusUpdateInterval: 1000, // milliseconds - update stats every second
    focusColor: '#4ade80', // green
    distractedColor: '#ef4444', // red
    loadingColor: '#fbbf24', // yellow
  },

  // Statistics persistence
  storage: {
    statsKey: 'focus_keeper_stats',
    persistStats: true,
  },
};
