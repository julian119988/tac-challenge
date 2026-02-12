/**
 * Heatmap Visualizer - Render gaze concentration heatmap
 * Based on HUE Vision heat.js
 */

import { CONFIG } from './config.js';

export class HeatmapVisualizer {
  constructor() {
    this.canvas = null;
    this.ctx = null;
  }

  /**
   * Get heat color from value (0-1)
   * Blue (cold) to Red (hot)
   */
  getHeatColor(value, alpha = 1.0) {
    // HSL color: 0 = red (hot), 120 = green, 240 = blue (cold)
    const hue = ((1 - value) * 120).toString(10);
    return `hsla(${hue}, 100%, 50%, ${alpha})`;
  }

  /**
   * Fill heatmap with gaze points
   */
  fillHeatmap(data, ctx, width, height, radius = 15) {
    if (!data || data.n === 0) {
      console.warn('No session data to visualize');
      return;
    }

    for (let i = 0; i < data.n; i++) {
      const pointX = Math.floor(data.x[i] * width);
      const pointY = Math.floor(data.y[i] * height);

      ctx.beginPath();
      ctx.fillStyle = this.getHeatColor(0.5, CONFIG.eyeTracking.visualization.heatmapOpacity);
      ctx.arc(pointX, pointY, radius, 0, 2 * Math.PI);
      ctx.fill();
    }
  }

  /**
   * Draw heatmap overlay
   */
  drawHeatmap(sessionData) {
    // Get or create heatmap canvas
    this.canvas = document.getElementById('heatMap');

    if (!this.canvas) {
      console.error('Heatmap canvas not found');
      return;
    }

    this.ctx = this.canvas.getContext('2d');

    // Clear previous heatmap
    this.clearHeatmap();

    // Set canvas size to window size
    const width = window.innerWidth;
    const height = window.innerHeight;

    this.canvas.width = width;
    this.canvas.height = height;

    // Draw heatmap
    this.fillHeatmap(sessionData, this.ctx, width, height, 15);

    // Make canvas visible
    this.canvas.style.opacity = CONFIG.eyeTracking.visualization.heatmapOpacity;

    console.log(`Heatmap drawn with ${sessionData.n} points`);
  }

  /**
   * Clear heatmap
   */
  clearHeatmap() {
    if (!this.canvas || !this.ctx) {
      this.canvas = document.getElementById('heatMap');
      if (!this.canvas) return;
      this.ctx = this.canvas.getContext('2d');
    }

    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.canvas.style.opacity = 0;
  }
}
