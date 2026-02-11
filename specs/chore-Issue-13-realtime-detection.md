# Chore: Realtime Detection

## Metadata
adw_id: `Issue #13`
prompt: `901becdb Issue #13: Realtime detection

I would like to be realtime detection, not every 5 seconds.

And I think the video modal should be closed after we get our sight back to the monitor.`

## Chore Description
The Focus Keeper app currently runs face detection at a fixed interval of 200ms (5 FPS) as configured in `CONFIG.detection.detectionInterval`. This creates a delay between when distraction occurs and when it's detected. Additionally, the intervention video modal does not automatically close when the user returns their attention to the screen - they must manually close it using the X button or ESC key.

This chore will enhance the app to provide truly realtime detection by:
1. Switching from interval-based polling to continuous frame-by-frame detection using `requestAnimationFrame`
2. Implementing automatic video modal closure when the user's attention returns to the screen

These changes will make the app more responsive and create a better user experience by immediately detecting when focus is lost or regained.

## Relevant Files
Use these files to complete the chore:

- **apps/frontend/app.js** (lines 109-156, 159-196, 215-228) - Contains the `DistractionMonitor` class which currently uses `setInterval` for periodic detection. This needs to be refactored to use continuous detection with `requestAnimationFrame`.
  - Lines 130-142: `start()` method that initiates interval-based detection
  - Lines 147-155: `stop()` method that clears the interval
  - Lines 159-196: `checkDistraction()` method that performs the actual detection logic
  - Lines 199-228: `onDistractionDetected()` and `onFocusRestored()` methods that handle state changes

- **apps/frontend/config.js** (lines 1-42) - Contains configuration constants including `CONFIG.detection.detectionInterval` (line 10). This interval config will become obsolete with continuous detection, but should be kept for backwards compatibility or repurposed.

- **apps/frontend/video-player.js** (lines 1-173) - Contains the `AttentionPlayer` class that manages intervention video playback. The automatic close functionality needs to be added here.
  - Lines 84-110: `play()` method that shows the intervention video
  - Lines 112-136: `stop()` method that hides the video
  - Lines 20-26: `initialize()` method where we might need to set up event listeners

- **apps/frontend/README.md** (lines 56-100) - Documentation that describes the detection logic and configuration. Should be updated to reflect the new realtime detection behavior.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Refactor DistractionMonitor to Use Continuous Detection
- Replace the `setInterval` approach in `app.js:138-140` with a `requestAnimationFrame` loop
- Store the animation frame ID instead of interval ID in `app.js:118`
- Modify the `start()` method (lines 130-142) to initiate a continuous detection loop
- Update the `stop()` method (lines 147-155) to cancel the animation frame instead of clearing the interval
- Ensure the detection loop runs smoothly without blocking the UI thread
- Keep the same debouncing logic for state transitions to avoid false positives

### 2. Implement Frame-Based Detection Loop
- Create a new `startContinuousDetection()` method in `DistractionMonitor` class
- Use `requestAnimationFrame` to call `checkDistraction()` continuously
- Ensure the loop continues until explicitly stopped
- Store the current `requestAnimationFrame` ID for cleanup
- Call the next frame at the end of each detection cycle

### 3. Add Automatic Modal Closure on Focus Restoration
- Modify the `onFocusRestored()` method in `app.js:217-228` to automatically close the intervention video
- Ensure the video is stopped when attention is detected again
- The video should already be closing via `this.attentionPlayer.stop()` on line 223, but verify this works correctly
- Add appropriate logging for debugging

### 4. Add State Tracking for Auto-Close Behavior
- In `video-player.js`, ensure the video modal responds to focus restoration
- The existing `stop()` method (lines 115-136) should work, but verify it's called appropriately
- Consider adding a flag to track whether auto-close occurred vs manual close for statistics

### 5. Update Configuration Documentation
- Remove or repurpose the `detectionInterval` config in `config.js:10`
- Update the comment to reflect that it's no longer used for detection timing
- Alternatively, repurpose it as a throttle value to prevent excessive detection calls
- Update `README.md` lines 84-91 to reflect the new realtime detection behavior
- Update the "Performance" section (lines 177-180) since we're no longer running at "~5 FPS"

### 6. Test Realtime Detection Performance
- Verify that continuous detection doesn't cause performance issues
- Ensure the UI remains responsive
- Check that detection happens immediately when looking away
- Verify automatic video closure works when returning attention to screen
- Test on different browsers (Chrome, Firefox, Safari) for compatibility

### 7. Validate Implementation
- Ensure no breaking changes to existing functionality
- Verify all state transitions work correctly (focused → distracted → focused)
- Test that manual video closure (X button and ESC key) still works
- Confirm statistics tracking remains accurate
- Check browser console for any errors or warnings

## Validation Commands
Execute these commands to validate the chore is complete:

- `grep -n "requestAnimationFrame" apps/frontend/app.js` - Verify that continuous detection using requestAnimationFrame is implemented
- `grep -n "setInterval.*checkDistraction" apps/frontend/app.js` - Ensure old interval-based detection is removed (should return no results)
- `grep -n "stop()" apps/frontend/app.js` - Verify that attentionPlayer.stop() is called in onFocusRestored
- `cat apps/frontend/config.js | grep -A 2 "detectionInterval"` - Check that config documentation is updated
- `grep -n "realtime\|continuous\|frame" apps/frontend/README.md` - Verify documentation reflects new realtime detection

## Notes
- The current `setInterval` approach runs detection every 200ms, which creates noticeable lag in detecting distractions
- Using `requestAnimationFrame` will sync detection with the browser's render cycle (~60 FPS), providing much faster response times
- However, running face detection at 60 FPS may be computationally expensive - consider throttling to every 2-3 frames if performance is an issue
- The automatic video closure should feel natural - the user looks back at the screen and the interruption immediately disappears
- Existing debouncing logic (3s for no face, 4s for gaze away) should be maintained to prevent false positives
- The video modal auto-close should work seamlessly with the existing manual close methods (X button, ESC, click outside)
- Consider the user experience: auto-closing too quickly might be jarring, but the current timeouts (3-4s) should provide good balance
