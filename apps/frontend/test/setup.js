/**
 * Jest test setup - Mock browser APIs and dependencies.
 *
 * This file is run before each test suite to set up the testing environment
 * with mocked browser APIs that aren't available in jsdom.
 */

// Mock MediaDevices API for camera access
global.navigator.mediaDevices = {
  getUserMedia: jest.fn().mockResolvedValue({
    getTracks: () => [
      {
        stop: jest.fn(),
        getSettings: () => ({ width: 640, height: 480 })
      }
    ],
    getVideoTracks: () => [
      {
        stop: jest.fn(),
        getSettings: () => ({ width: 640, height: 480 })
      }
    ]
  }),
  enumerateDevices: jest.fn().mockResolvedValue([
    {
      deviceId: 'camera1',
      kind: 'videoinput',
      label: 'Mock Camera'
    }
  ])
};

// Mock HTMLMediaElement methods
HTMLMediaElement.prototype.play = jest.fn().mockResolvedValue();
HTMLMediaElement.prototype.pause = jest.fn();
HTMLMediaElement.prototype.load = jest.fn();

// Mock HTMLVideoElement
if (typeof HTMLVideoElement !== 'undefined') {
  Object.defineProperty(HTMLVideoElement.prototype, 'videoWidth', {
    get: jest.fn().mockReturnValue(640)
  });
  Object.defineProperty(HTMLVideoElement.prototype, 'videoHeight', {
    get: jest.fn().mockReturnValue(480)
  });
}

// Mock canvas and 2D context
HTMLCanvasElement.prototype.getContext = jest.fn().mockReturnValue({
  fillRect: jest.fn(),
  clearRect: jest.fn(),
  getImageData: jest.fn().mockReturnValue({
    data: new Uint8ClampedArray(640 * 480 * 4)
  }),
  putImageData: jest.fn(),
  createImageData: jest.fn().mockReturnValue({
    data: new Uint8ClampedArray(640 * 480 * 4)
  }),
  setTransform: jest.fn(),
  drawImage: jest.fn(),
  save: jest.fn(),
  restore: jest.fn(),
  scale: jest.fn(),
  rotate: jest.fn(),
  translate: jest.fn(),
  transform: jest.fn(),
  beginPath: jest.fn(),
  closePath: jest.fn(),
  moveTo: jest.fn(),
  lineTo: jest.fn(),
  bezierCurveTo: jest.fn(),
  quadraticCurveTo: jest.fn(),
  arc: jest.fn(),
  arcTo: jest.fn(),
  ellipse: jest.fn(),
  rect: jest.fn(),
  fill: jest.fn(),
  stroke: jest.fn(),
  clip: jest.fn(),
  isPointInPath: jest.fn(),
  isPointInStroke: jest.fn(),
  fillText: jest.fn(),
  strokeText: jest.fn(),
  measureText: jest.fn().mockReturnValue({ width: 0 }),
  createLinearGradient: jest.fn(),
  createRadialGradient: jest.fn(),
  createPattern: jest.fn(),
  font: '10px sans-serif',
  fillStyle: '#000000',
  strokeStyle: '#000000',
  lineWidth: 1
});

// Mock TensorFlow.js
global.tf = {
  ready: jest.fn().mockResolvedValue(),
  loadGraphModel: jest.fn().mockResolvedValue({
    predict: jest.fn().mockReturnValue({
      dataSync: jest.fn().mockReturnValue(new Float32Array([0.1, 0.2, 0.3, 0.4]))
    }),
    dispose: jest.fn()
  }),
  browser: {
    fromPixels: jest.fn().mockReturnValue({
      expandDims: jest.fn().mockReturnThis(),
      toFloat: jest.fn().mockReturnThis(),
      div: jest.fn().mockReturnThis(),
      dispose: jest.fn()
    })
  },
  tensor2d: jest.fn().mockReturnValue({
    dispose: jest.fn()
  }),
  tidy: jest.fn((fn) => fn()),
  dispose: jest.fn()
};

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  length: 0,
  key: jest.fn()
};

global.localStorage = localStorageMock;

// Mock sessionStorage
global.sessionStorage = { ...localStorageMock };

// Mock requestAnimationFrame
global.requestAnimationFrame = jest.fn((callback) => {
  return setTimeout(callback, 16);
});

global.cancelAnimationFrame = jest.fn((id) => {
  clearTimeout(id);
});

// Mock performance API
global.performance = {
  now: jest.fn(() => Date.now())
};

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
  takeRecords() {
    return [];
  }
};

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
};

// Console warnings for unimplemented features
const originalWarn = console.warn;
console.warn = (...args) => {
  // Filter out known warnings from jsdom/testing
  const warningStr = args.join(' ');
  if (
    warningStr.includes('Not implemented') ||
    warningStr.includes('could not be cloned')
  ) {
    return;
  }
  originalWarn(...args);
};
