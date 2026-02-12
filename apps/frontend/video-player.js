import { CONFIG } from './config.js';

/**
 * Manages attention-grabbing video playback when user is distracted
 */
export class AttentionPlayer {
  constructor() {
    this.videoContainer = null;
    this.currentVideoIndex = 0;
    this.interventionCount = 0;
    this.isPlaying = false;
  }

  /**
   * Initialize the video player
   */
  initialize() {
    // Create video container if it doesn't exist
    this.videoContainer = document.getElementById('intervention-video-container');
    if (!this.videoContainer) {
      this.videoContainer = this.createVideoContainer();
      document.body.appendChild(this.videoContainer);
    }

    // Setup event listeners
    this.setupEventListeners();
  }

  /**
   * Create the video container element
   */
  createVideoContainer() {
    const container = document.createElement('div');
    container.id = 'intervention-video-container';
    container.className = 'intervention-container hidden';
    container.innerHTML = `
      <div class="intervention-content">
        <button class="close-btn" id="close-intervention">✕</button>
        <iframe
          id="intervention-iframe"
          width="800"
          height="450"
          frameborder="0"
          allow="autoplay; encrypted-media"
          allowfullscreen
        ></iframe>
        <video
          id="intervention-video"
          autoplay
          muted
          loop
          style="display: none; width: 100%; height: 100%; object-fit: contain;"
        ></video>
        <div class="intervention-message">
          <h2>Hey! Get back to work!</h2>
          <p>Click the X or press ESC to continue</p>
        </div>
      </div>
    `;
    return container;
  }

  /**
   * Setup event listeners for closing the video
   */
  setupEventListeners() {
    // Close button
    const closeBtn = document.getElementById('close-intervention');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.stop());
    }

    // ESC key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isPlaying) {
        this.stop();
      }
    });

    // Click outside to close
    this.videoContainer.addEventListener('click', (e) => {
      if (e.target === this.videoContainer) {
        this.stop();
      }
    });
  }

  /**
   * Play a random attention-grabbing video
   */
  play() {
    if (this.isPlaying) {
      return; // Already playing
    }

    // Select a random video
    const videoUrl = this.getRandomVideo();

    // Set iframe source
    const iframe = document.getElementById('intervention-iframe');
    if (iframe) {
      iframe.src = videoUrl;
    }

    // Show container
    this.videoContainer.classList.remove('hidden');
    this.isPlaying = true;
    this.interventionCount++;

    console.log(`Playing intervention video #${this.interventionCount}`);

    // Dispatch event
    this.dispatchEvent('intervention-started', {
      count: this.interventionCount,
      videoUrl,
    });
  }

  /**
   * Stop video playback
   */
  stop() {
    if (!this.isPlaying) {
      return;
    }

    // Clear iframe source to stop video
    const iframe = document.getElementById('intervention-iframe');
    if (iframe) {
      iframe.src = '';
    }

    // Pause and reset video element
    const video = document.getElementById('intervention-video');
    if (video) {
      video.pause();
      video.currentTime = 0;
      video.src = '';
    }

    // Hide container
    this.videoContainer.classList.add('hidden');
    this.isPlaying = false;

    console.log('Intervention video stopped');

    // Dispatch event
    this.dispatchEvent('intervention-stopped', {
      count: this.interventionCount,
    });
  }

  /**
   * Get a random video URL from the config
   */
  getRandomVideo() {
    const videos = CONFIG.videos;
    const randomIndex = Math.floor(Math.random() * videos.length);
    this.currentVideoIndex = randomIndex;
    return videos[randomIndex];
  }

  /**
   * Get intervention statistics
   */
  getStats() {
    return {
      interventionCount: this.interventionCount,
      isPlaying: this.isPlaying,
    };
  }

  /**
   * Reset statistics
   */
  resetStats() {
    this.interventionCount = 0;
  }

  /**
   * Play the skeleton video for attention grabbing (instant jumpscare)
   * Issue #29: Displays a skeleton video when user is looking away from screen
   * The video appears instantly (no fade-in) for maximum attention-grabbing effect
   * and automatically closes when the user looks back at the screen
   */
  playSkeletonVideo() {
    if (this.isPlaying) {
      return; // Already playing
    }

    if (!CONFIG.attentionGrabber.enabled) {
      return; // Feature disabled
    }

    // Get video element
    const video = document.getElementById('intervention-video');
    const iframe = document.getElementById('intervention-iframe');

    if (video && iframe) {
      // Hide iframe, show video
      iframe.style.display = 'none';
      video.style.display = 'block';

      // Set video source and play
      video.src = CONFIG.attentionGrabber.videoPath;
      video.play().catch(err => {
        console.error('Failed to play skeleton video:', err);
      });
    }

    // Show container (instant, no fade)
    this.videoContainer.classList.remove('hidden');
    this.isPlaying = true;
    this.interventionCount++;

    console.log(`Playing skeleton video (attention grabber #${this.interventionCount})`);

    // Dispatch event
    this.dispatchEvent('attention-grabber-started', {
      count: this.interventionCount,
    });
  }

  /**
   * Check if video is currently playing
   */
  isVideoPlaying() {
    return this.isPlaying;
  }

  /**
   * Dispatch custom events
   */
  dispatchEvent(eventName, detail) {
    const event = new CustomEvent(eventName, { detail });
    window.dispatchEvent(event);
  }
}
