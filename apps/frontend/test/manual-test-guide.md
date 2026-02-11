# Manual Test Guide - Focus Keeper App

This guide provides a comprehensive testing checklist for the Focus Keeper anti-procrastination app.

## Prerequisites

- Modern browser (Chrome, Firefox, Safari, or Edge)
- Working webcam
- Good lighting conditions
- Internet connection (for TensorFlow.js model loading)

## Test Environment Setup

1. Start the FastAPI server:
   ```bash
   cd /path/to/tac-challenge
   ./scripts/start_webhook_server.sh
   ```

2. Verify server is running:
   - Open http://localhost:8000/health
   - Should see: `{"status":"ok","service":"adw-webhook-server","environment":"development"}`

3. Access the app:
   - Navigate to http://localhost:8000/app
   - Should see "Focus Keeper" title and "Start Session" button

## Test Cases

### 1. Initial Load and UI

**Test 1.1: Page Loads Successfully**
- [ ] Page loads without errors
- [ ] "Focus Keeper" title is displayed
- [ ] "Ready - Click Start to begin" status message shown
- [ ] Yellow status indicator visible in top-right of camera area
- [ ] "Start Session" button is visible and enabled
- [ ] All statistics show initial values (00:00, 0, 0.0%)
- [ ] Footer with privacy notice is visible

**Test 1.2: Browser Console Check**
- [ ] Open browser DevTools (F12)
- [ ] Check console for errors (should be none)
- [ ] Should see: "Face detection model loaded successfully"
- [ ] Should see: "Focus Keeper App initialized"

### 2. Camera Access and Permissions

**Test 2.1: Camera Permission Request**
- [ ] Click "Start Session" button
- [ ] Browser prompts for camera permission
- [ ] Grant camera permission
- [ ] Video feed appears in canvas

**Test 2.2: Camera Permission Denied**
- [ ] (Use a fresh browser profile or reset permissions)
- [ ] Click "Start Session"
- [ ] Deny camera permission
- [ ] Error message should be displayed
- [ ] Session should not start
- [ ] Status should remain "Ready"

**Test 2.3: No Camera Available**
- [ ] (Test on device without camera or with camera disabled)
- [ ] Click "Start Session"
- [ ] Error message should indicate no camera found
- [ ] Session should not start

### 3. Face Detection

**Test 3.1: Face Detection Success**
- [ ] Start session with camera permission granted
- [ ] Position face in front of camera
- [ ] Face should be visible in video feed
- [ ] Status indicator should turn green
- [ ] Status message should show "Focused - Great job!"
- [ ] Check console: should see detection results

**Test 3.2: No Face Detected**
- [ ] Start session
- [ ] Move out of camera frame completely
- [ ] Wait 3-4 seconds
- [ ] Status indicator should turn red
- [ ] Status should show "Distracted - Get back to work!"
- [ ] Intervention video should appear

**Test 3.3: Poor Lighting**
- [ ] Start session in low light
- [ ] Face may not be detected
- [ ] Note behavior (may trigger false distraction)
- [ ] Improve lighting and verify detection works

### 4. Distraction Detection

**Test 4.1: Looking Away from Screen**
- [ ] Start session while facing camera
- [ ] Status should be "Focused"
- [ ] Turn head to look to the left or right
- [ ] Wait 4-5 seconds while looking away
- [ ] Distraction should be detected
- [ ] Status should change to "Distracted"
- [ ] Intervention video should play

**Test 4.2: Looking at Phone**
- [ ] Start session
- [ ] Look down at phone or desk
- [ ] Keep head down for 4-5 seconds
- [ ] Distraction should be detected
- [ ] Intervention should trigger

**Test 4.3: Leaving Seat**
- [ ] Start session
- [ ] Stand up and walk away from camera
- [ ] Wait 3-4 seconds
- [ ] Distraction should be detected (no face)
- [ ] Intervention video should play
- [ ] Return to seat
- [ ] Status should return to "Focused"

**Test 4.4: Brief Glances Away**
- [ ] Start session
- [ ] Look away briefly (1-2 seconds)
- [ ] Look back at screen
- [ ] Should NOT trigger distraction (debouncing)
- [ ] Status should remain "Focused"

### 5. Intervention Video System

**Test 5.1: Video Plays on Distraction**
- [ ] Trigger a distraction (look away for 4+ seconds)
- [ ] Fullscreen overlay should appear
- [ ] YouTube video should load and autoplay
- [ ] Message "Hey! Get back to work!" should be visible
- [ ] Close button (X) should be visible in top-right

**Test 5.2: Close Button**
- [ ] Trigger intervention video
- [ ] Click the X button in top-right
- [ ] Video should stop and close
- [ ] Should return to normal camera view
- [ ] Status should update based on current position

**Test 5.3: ESC Key to Close**
- [ ] Trigger intervention video
- [ ] Press ESC key
- [ ] Video should stop and close
- [ ] Should return to normal view

**Test 5.4: Click Outside to Close**
- [ ] Trigger intervention video
- [ ] Click on dark background (not on video)
- [ ] Video should close

**Test 5.5: Multiple Interventions**
- [ ] Trigger distraction multiple times
- [ ] Each time should play a video (may be different)
- [ ] Intervention count should increment
- [ ] All methods of closing should work each time

### 6. Statistics Tracking

**Test 6.1: Session Time**
- [ ] Start session
- [ ] Wait 60 seconds
- [ ] Session Time should show ~01:00
- [ ] Should update every second

**Test 6.2: Focus Time**
- [ ] Start session while facing camera
- [ ] Stay focused for 30 seconds
- [ ] Focus Time should increment
- [ ] Look away to trigger distraction
- [ ] Focus Time should stop incrementing
- [ ] Return to focused state
- [ ] Focus Time should resume incrementing

**Test 6.3: Distraction Count**
- [ ] Start session
- [ ] Note initial distraction count (0)
- [ ] Trigger distraction by looking away
- [ ] Distraction count should increment to 1
- [ ] Return to focused state
- [ ] Trigger distraction again
- [ ] Distraction count should be 2

**Test 6.4: Intervention Count**
- [ ] Start session
- [ ] Trigger multiple distractions
- [ ] Intervention count should match number of videos shown
- [ ] Should increment each time video plays

**Test 6.5: Focus Score**
- [ ] Start session
- [ ] Stay focused for entire session
- [ ] Focus Score should approach 100%
- [ ] Look away for half the session
- [ ] Focus Score should be around 50%

### 7. Session Control

**Test 7.1: Stop Session**
- [ ] Start session
- [ ] Wait a few seconds
- [ ] Click "Stop Session" button
- [ ] Camera should stop (video feed freezes/clears)
- [ ] Status should show "Session ended"
- [ ] Statistics should stop updating
- [ ] Button should change to "Start Session"

**Test 7.2: Restart Session**
- [ ] Start and stop a session
- [ ] Click "Start Session" again
- [ ] Camera should restart
- [ ] Previous session stats should be preserved or reset
- [ ] New session should track separately

**Test 7.3: Stop During Intervention**
- [ ] Start session
- [ ] Trigger intervention video
- [ ] While video is playing, stop session
- [ ] Video should close
- [ ] Camera should stop
- [ ] Session should end cleanly

### 8. Performance and Stability

**Test 8.1: Long Session**
- [ ] Start session
- [ ] Run for 10+ minutes
- [ ] Monitor browser memory usage
- [ ] App should remain responsive
- [ ] No memory leaks or crashes
- [ ] Statistics should update correctly

**Test 8.2: Rapid State Changes**
- [ ] Start session
- [ ] Rapidly move in and out of frame
- [ ] Look away and back multiple times
- [ ] App should handle transitions smoothly
- [ ] No crashes or errors

**Test 8.3: Multiple Browser Tabs**
- [ ] Open app in two browser tabs
- [ ] Start session in both
- [ ] Both should work independently
- [ ] Camera may only work in one (browser limitation)

### 9. Browser Compatibility

**Test 9.1: Chrome**
- [ ] Test all features in Chrome
- [ ] Note any issues or differences

**Test 9.2: Firefox**
- [ ] Test all features in Firefox
- [ ] Note any issues or differences

**Test 9.3: Safari**
- [ ] Test all features in Safari
- [ ] Note any issues or differences

**Test 9.4: Edge**
- [ ] Test all features in Edge
- [ ] Note any issues or differences

### 10. Error Handling

**Test 10.1: TensorFlow.js Load Failure**
- [ ] Block CDN requests (use ad blocker or firewall)
- [ ] Try to start session
- [ ] Should show error about model loading
- [ ] Should provide clear error message

**Test 10.2: Network Disconnection**
- [ ] Start session successfully
- [ ] Disconnect network
- [ ] App should continue to work (models already loaded)
- [ ] Intervention videos may fail to load

**Test 10.3: Camera Disconnection**
- [ ] Start session
- [ ] Physically disconnect or disable camera mid-session
- [ ] App should handle gracefully
- [ ] Error message should be displayed

### 11. Edge Cases

**Test 11.1: Multiple Faces**
- [ ] Start session with another person visible
- [ ] App currently only tracks one face
- [ ] Note behavior (may cause confusion)

**Test 11.2: Wearing Glasses**
- [ ] Test with glasses on
- [ ] Face detection should still work
- [ ] Reflections may cause issues in bright light

**Test 11.3: Hat or Headwear**
- [ ] Test wearing a hat
- [ ] Face detection should still work
- [ ] Extreme coverage may cause issues

**Test 11.4: Side Profile**
- [ ] Turn head to show side profile
- [ ] Should detect as looking away or no face
- [ ] Should trigger distraction

**Test 11.5: Very Close to Camera**
- [ ] Move face very close to camera
- [ ] Face detection may still work
- [ ] Note any issues

**Test 11.6: Far from Camera**
- [ ] Sit far from camera (small face)
- [ ] Face detection may be less accurate
- [ ] Note minimum effective distance

## Test Results Template

Use this template to document test results:

```
Date: __________
Browser: __________
OS: __________
Camera: __________

| Test Case | Status | Notes |
|-----------|--------|-------|
| 1.1 Page Load | ☐ Pass ☐ Fail | |
| 1.2 Console | ☐ Pass ☐ Fail | |
| 2.1 Permission | ☐ Pass ☐ Fail | |
| ... | | |

Issues Found:
1.
2.
3.

Overall Assessment:
☐ Ready for release
☐ Needs fixes
☐ Major issues

Tester: __________
```

## Common Issues and Expected Behavior

### False Distraction Detections
**Expected**: Can occur in poor lighting or with extreme head angles
**Workaround**: Improve lighting, increase thresholds in config.js

### Video Autoplay Blocked
**Expected**: Some browsers block autoplay
**Workaround**: User interaction may be required, check browser settings

### Camera Already in Use
**Expected**: Only one app can use camera at a time
**Workaround**: Close other apps using camera (Zoom, Teams, etc.)

### Slow Performance
**Expected**: On older devices or with many browser tabs
**Workaround**: Close other tabs, use Chrome for best performance

## Success Criteria

The app passes testing if:
- [ ] All core features work in at least Chrome and Firefox
- [ ] Face detection works in good lighting conditions
- [ ] Distraction detection triggers appropriately (3-4 second delay)
- [ ] Intervention videos play and can be closed
- [ ] Statistics track accurately
- [ ] No crashes during normal use
- [ ] Error messages are clear and helpful
- [ ] Privacy notice is visible

## Additional Notes

- Test in a quiet environment to avoid distractions during testing
- Keep a notebook to document unexpected behaviors
- Take screenshots of any errors for debugging
- Test both successful and failure paths
- Consider accessibility (keyboard navigation, screen readers)
