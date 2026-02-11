# Chore: Fix Camera Access Error on Start Session

## Metadata
adw_id: `Issue #15`
prompt: `Getting an error when clicking on start session button: "Failed to start: Failed to access camera: Cannot read properties of undefined (reading 'getUserMedia')"`

## Chore Description
The Focus Keeper application is failing to access the camera when clicking the "Start Session" button. The error "Cannot read properties of undefined (reading 'getUserMedia')" indicates that `navigator.mediaDevices` is undefined. This occurs because:

1. The FastAPI server is configured to serve static files from `apps/frontend/dist` directory
2. The `dist` directory does not exist - the actual frontend files are in `apps/frontend/`
3. When static files aren't served correctly, the browser may not provide the `navigator.mediaDevices` API
4. The `getUserMedia` API requires a secure context (HTTPS or localhost)

The fix involves updating the server configuration to serve static files from the correct directory (`apps/frontend` instead of `apps/frontend/dist`).

## Relevant Files
Use these files to complete the chore:

- **apps/adw_server/core/config.py** (lines 60-63): Contains the `static_files_dir` configuration that points to the wrong directory (`apps/frontend/dist`)
- **apps/adw_server/server.py** (lines 403-422): Static file mounting logic that uses the configuration
- **apps/frontend/index.html**: Main HTML file that needs to be served
- **apps/frontend/app.js** (line 46): Where `navigator.mediaDevices.getUserMedia` is called
- **.env.example**: May need to document the correct static files directory configuration

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update Static Files Directory Configuration
- Change `static_files_dir` default value in `apps/adw_server/core/config.py` from `"apps/frontend/dist"` to `"apps/frontend"`
- This ensures the server serves files from the correct directory where the actual frontend files exist

### 2. Verify Static File Serving Works
- Start the webhook server using `./scripts/start_webhook_server.sh`
- Check the server logs to confirm static files are mounted from `apps/frontend`
- Navigate to `http://localhost:8000/app` in a browser
- Verify that the index.html page loads correctly

### 3. Test Camera Access
- Open browser DevTools console
- Click the "Start Session" button
- Verify that the browser prompts for camera permissions
- Grant camera access
- Confirm that the camera stream starts without the `getUserMedia` error
- Verify the video canvas displays the camera feed

### 4. Verify Secure Context
- Check that `navigator.mediaDevices` is defined in the browser console
- Confirm the page is served from `localhost` (secure context)
- Test that all face detection features work correctly

## Validation Commands
Execute these commands to validate the chore is complete:

- `ls -la apps/frontend/` - Verify frontend files exist in apps/frontend (not dist)
- `grep "static_files_dir" apps/adw_server/core/config.py` - Confirm the path is set to "apps/frontend"
- `./scripts/start_webhook_server.sh` - Start the server and check logs for "React app mounted from: .../apps/frontend"
- Manual browser test at `http://localhost:8000/app` - Click "Start Session" and verify camera access works

## Notes
- The `getUserMedia` API is only available in secure contexts (HTTPS or localhost)
- Modern browsers require explicit user permission to access camera
- The error message "Cannot read properties of undefined (reading 'getUserMedia')" specifically indicates `navigator.mediaDevices` is undefined, which typically happens when:
  - The page is not served over HTTPS or localhost
  - The page failed to load properly
  - The browser doesn't support the API (unlikely in modern browsers)
- After this fix, users should see a browser permission prompt when clicking "Start Session"
- If the directory path needs to be customizable, users can override it using the `STATIC_FILES_DIR` environment variable in `.env`
