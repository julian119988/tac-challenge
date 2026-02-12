# Chore: Skeleton Video Sound

## Metadata
adw_id: `Issue #33`
prompt: `e749723d Issue #33: Skeleton video sound

Works perfectly but the video has no sound`

## Chore Description
Enable audio playback for the skeleton attention-grabber video that displays when users look away from the screen. The feature (Issue #29) is currently working perfectly - the skeleton video appears instantly as a "jumpscare" when users look away and closes when they look back. However, the video plays without sound because the HTML5 `<video>` element has the `muted` attribute enabled.

The skeleton video is located at `apps/frontend/assets/skeleton-attention.mp4` and is played through the `AttentionPlayer` class when gaze detection determines the user is looking away from the screen.

## Relevant Files
Use these files to complete the chore:

- **apps/frontend/video-player.js:50** - Contains the `<video>` element creation with `muted` attribute that needs to be removed to enable audio playback for the skeleton video

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Verify Video Has Audio Track
- Use ffprobe or a media player to confirm the skeleton video file has an audio track
- Command: `ffprobe -i apps/frontend/assets/skeleton-attention.mp4 -show_streams -select_streams a`
- If no audio stream exists, this chore cannot be completed (video file needs audio added)
- If audio stream exists, proceed to next step

### 2. Remove Muted Attribute from Video Element
- Open `apps/frontend/video-player.js`
- Locate the `createVideoContainer()` method (around line 32)
- Find the `<video>` element creation (line 47-53)
- Remove the `muted` attribute from line 50
- Keep all other attributes: `autoplay`, `loop`, `id`, `style`
- The video element should now play with audio enabled

### 3. Test Audio Playback in Browser
- Start local development server: `python -m http.server 8000` from project root
- Navigate to `http://localhost:8000/apps/frontend/`
- Grant camera permissions when prompted
- Ensure speakers/headphones are connected and volume is audible
- Look at the screen (skeleton video should NOT play)
- Look away from the screen (skeleton video should appear)
- Verify audio plays along with the video
- Look back at screen (video should close)
- Repeat test multiple times to ensure consistency

### 4. Consider Browser Autoplay Policies
- Test in different browsers (Chrome, Firefox, Safari)
- Modern browsers block autoplay with audio unless user has interacted with the page
- If audio doesn't play, add user interaction requirement:
  - Option A: Require user to click "Start Session" button before skeleton video can play with audio
  - Option B: Play first skeleton video muted, subsequent plays unmuted
  - Option C: Display message asking user to enable audio/interact with page
- Document any browser-specific behavior in code comments

### 5. Update Code Documentation
- Add comment in `video-player.js` explaining why `muted` was removed
- Reference Issue #33 in the comment
- Note any browser autoplay policy considerations

### 6. Validate Complete Functionality
- Test skeleton video triggers correctly when looking away
- Test skeleton video closes correctly when looking back
- Test audio plays at appropriate volume
- Test no errors appear in browser console
- Verify face detection continues working during video with audio
- Verify video loops correctly with audio while user is looking away

## Validation Commands
Execute these commands to validate the chore is complete:

- **Check if video has audio stream**:
  ```bash
  ffprobe -i apps/frontend/assets/skeleton-attention.mp4 -show_streams -select_streams a 2>&1 | grep -i "codec_name\|codec_type"
  ```
  Should show audio stream information (e.g., `codec_name=aac`, `codec_type=audio`)

- **Verify muted attribute is removed**:
  ```bash
  grep -n "muted" apps/frontend/video-player.js
  ```
  Should NOT show `muted` attribute in the `<video>` element around line 50

- **Check video element structure**:
  ```bash
  sed -n '47,53p' apps/frontend/video-player.js
  ```
  Should show video element with `autoplay`, `loop`, but NO `muted` attribute

- **Manual browser testing checklist**:
  - [ ] Video has audio track (verified with ffprobe)
  - [ ] `muted` attribute removed from video element
  - [ ] Skeleton video plays with audio when looking away
  - [ ] Audio is audible and at reasonable volume
  - [ ] Video closes properly when looking back
  - [ ] No browser console errors
  - [ ] Face detection continues working during audio playback
  - [ ] Works in Chrome
  - [ ] Works in Firefox
  - [ ] Works in Safari (if available)

- **Browser autoplay policy test**:
  - Open browser in incognito/private mode
  - Navigate to app without any user interaction
  - Verify if audio plays or is blocked
  - If blocked, implement workaround from Step 4

## Notes

### Browser Autoplay Policies
Modern browsers have strict autoplay policies to prevent intrusive audio. Key considerations:

**Chrome/Edge:**
- Autoplay with audio is blocked unless:
  - User has interacted with the domain (click, tap, key press)
  - User's Media Engagement Index (MEI) is high enough (frequently plays media on the site)
  - Site has been added to home screen on mobile

**Firefox:**
- Similar to Chrome, blocks autoplay with audio unless user has interacted with the page
- Can be configured in `about:config` with `media.autoplay.default`

**Safari:**
- Strictest autoplay policy
- Requires explicit user gesture for audio playback
- May require `video.play()` to be called directly from a click event handler

### Recommended Solution
The app already requires users to click the "Start Session" button before face detection begins. This user interaction should satisfy browser autoplay policies, allowing the skeleton video to play with audio when triggered.

### Audio Volume Considerations
- Browser may play video at system volume
- Consider adding volume control in future enhancement
- Default HTML5 video volume is 1.0 (100%)
- Can programmatically adjust with `video.volume = 0.5` for 50% volume

### Alternative: Unmute on User Interaction
If autoplay policies block audio, implement fallback:
```javascript
// In playSkeletonVideo() method
video.muted = false; // Try to unmute
video.play().catch(err => {
  if (err.name === 'NotAllowedError') {
    console.warn('Audio autoplay blocked by browser - playing muted');
    video.muted = true;
    video.play();
  }
});
```

### Testing Without Audio Track
If the video file doesn't have an audio track, you'll need to:
1. Add audio to the video file using video editing software
2. Re-export the video with audio track
3. Replace `apps/frontend/assets/skeleton-attention.mp4`

You can check if the video has audio by:
- Opening in VLC or media player (check audio track info)
- Using ffprobe: `ffprobe apps/frontend/assets/skeleton-attention.mp4`
- Opening in browser DevTools → Network tab → check media type

### Performance Impact
Enabling audio should have minimal performance impact:
- Audio decoding is hardware-accelerated on most devices
- Small audio streams (typically 128-256 kbps) add minimal overhead
- Face detection performance should remain unaffected
- Monitor frame rate in DevTools to confirm

### Future Enhancements
- Add volume slider for skeleton video
- Add audio on/off toggle in settings
- Multiple skeleton videos with different sounds
- Fade in/out audio instead of abrupt start/stop
- Adjust audio volume based on time of day (quieter at night)
