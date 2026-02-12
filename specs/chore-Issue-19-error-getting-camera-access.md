# Chore: Error Getting Camera Access

## Metadata
adw_id: `Issue #19`
prompt: `I'm still getting this error when clicking on "Start Session". Here's a log: app.js:363 Failed to start session: Error: Failed to access camera: Cannot read properties of undefined (reading 'getUserMedia')`

## Chore Description
The Focus Keeper application is still failing to access the camera when clicking the "Start Session" button, despite the fix in Issue #15. The error "Cannot read properties of undefined (reading 'getUserMedia')" indicates that `navigator.mediaDevices` is undefined in the browser context.

The `navigator.mediaDevices` API is only available in secure contexts (HTTPS or localhost). While the server is running on localhost, there are several potential issues:

1. **Browser compatibility check missing**: The code doesn't verify if `navigator.mediaDevices` exists before trying to use it
2. **No user-friendly error handling**: When the API is unavailable, users see a cryptic error instead of helpful guidance
3. **Missing feature detection**: The app should check for API availability during initialization and show appropriate warnings
4. **Potential insecure context**: The page might be accessed via IP address (e.g., 127.0.0.1) instead of "localhost", which some browsers don't consider secure

The fix involves adding proper feature detection, graceful error handling, and clear user messaging when camera access is unavailable.

## Relevant Files
Use these files to complete the chore:

- **apps/frontend/app.js** (lines 34-66): `CameraManager.start()` method where `navigator.mediaDevices.getUserMedia` is called without checking if the API exists
- **apps/frontend/app.js** (lines 297-328): `FocusKeeperApp.initialize()` method where we should add feature detection
- **apps/frontend/app.js** (lines 473-486): `showError()` method that displays error messages to users
- **apps/frontend/index.html**: HTML structure that might need additional error messaging elements
- **apps/frontend/config.js**: Configuration that might need to document browser requirements

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Add MediaDevices API Feature Detection
- Add a helper method in `CameraManager` class to check if `navigator.mediaDevices` and `getUserMedia` are available
- Create a method like `isSupported()` that returns boolean indicating if the browser supports camera access
- This check should verify:
  - `navigator` exists
  - `navigator.mediaDevices` exists
  - `navigator.mediaDevices.getUserMedia` exists
  - The page is in a secure context (`window.isSecureContext`)

### 2. Update CameraManager.start() with Feature Detection
- Before calling `getUserMedia`, check if the API is supported using the new `isSupported()` method
- If not supported, throw a descriptive error indicating:
  - The browser doesn't support camera access, OR
  - The page must be accessed via HTTPS or localhost, OR
  - The browser version is too old
- Update the error message to be more user-friendly and actionable

### 3. Add Feature Detection to App Initialization
- In `FocusKeeperApp.initialize()`, add camera API availability check before allowing users to start
- If the API is not available:
  - Disable the "Start Session" button
  - Show a warning message explaining the issue
  - Provide guidance on how to fix (use localhost, enable HTTPS, update browser)
- Update the status display to show "Camera API not available" or similar message

### 4. Improve Error Messages
- Update error handling to distinguish between:
  - API not available (show browser/security context issue)
  - User denied permissions (show permission denied message)
  - Camera not found (show hardware issue message)
  - Other errors (show generic error with details)
- Make error messages actionable with clear next steps

### 5. Add Browser Compatibility Information
- Update the footer or add a notice about browser requirements
- Document that the app requires:
  - Modern browser (Chrome 53+, Firefox 36+, Safari 11+, Edge 79+)
  - HTTPS or localhost access
  - Camera permissions granted
- Consider adding a compatibility check that shows warnings for unsupported browsers

### 6. Test Camera Access Flow
- Start the server and access via `http://localhost:8000/app`
- Verify feature detection works correctly
- Test error scenarios:
  - Access via IP address (127.0.0.1) to trigger insecure context
  - Deny camera permissions
  - Test in different browsers if possible
- Confirm error messages are clear and helpful

## Validation Commands
Execute these commands to validate the chore is complete:

- `grep -n "isSupported\|navigator.mediaDevices" apps/frontend/app.js` - Verify feature detection was added
- `grep -n "isSecureContext" apps/frontend/app.js` - Confirm secure context check exists
- `./scripts/start_webhook_server.sh` - Start the server
- Manual browser test at `http://localhost:8000/app` - Verify proper error handling when accessing camera
- Manual browser test at `http://127.0.0.1:8000/app` - Test insecure context error message
- Check browser console for clear error messages instead of "Cannot read properties of undefined"

## Notes
- The `navigator.mediaDevices` API requires a secure context:
  - HTTPS (for production)
  - localhost or 127.0.0.1 (for development) - Note: some browsers treat 127.0.0.1 as secure, others don't
  - file:// protocol (limited support)
- Modern browsers require explicit user permission for camera access
- The error "Cannot read properties of undefined (reading 'getUserMedia')" is a JavaScript error that occurs when trying to access a property on undefined
- After this fix:
  - Users with unsupported browsers will see clear guidance
  - Users in insecure contexts will understand they need HTTPS or localhost
  - Users who deny permissions will get a helpful message
  - The app will gracefully degrade instead of showing cryptic errors
- Consider adding a fallback UI for browsers without camera support
- The secure context requirement is a browser security feature and cannot be bypassed
