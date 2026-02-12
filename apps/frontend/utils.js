/**
 * Utility functions for eye tracking implementation
 */

export function downloadJSON(data, filename) {
  const content = JSON.stringify(data);
  const blob = new Blob([content], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function tensorToArray(tensor) {
  const typedArray = tensor.dataSync();
  return Array.prototype.slice.call(typedArray);
}

export function arrayToTensor(array, shape) {
  return tf.tensor(array, shape);
}

export function normalizeCoordinates(x, y, width, height) {
  return {
    x: x / width,
    y: y / height
  };
}

export function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

export function getMousePosition() {
  // Returns normalized mouse position [0-1]
  return {
    x: window.mouseX || 0.5,
    y: window.mouseY || 0.5
  };
}

// Track mouse position globally
if (typeof window !== 'undefined') {
  window.mouseX = 0.5;
  window.mouseY = 0.5;

  document.addEventListener('mousemove', (event) => {
    window.mouseX = event.clientX / window.innerWidth;
    window.mouseY = event.clientY / window.innerHeight;
  });
}
