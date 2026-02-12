# Chore: Remove Browser Requirements Section

## Metadata
adw_id: `f505b30c Issue #42`
prompt: `I would like to delete:

Browser Requirements: This app requires a modern browser with camera support:

Chrome 53+ / Edge 79+ / Firefox 36+ / Safari 11+
HTTPS connection or localhost access (camera API requires secure context)
Camera permissions must be granted when prompted
Note: If accessing via IP address (e.g., 127.0.0.1), use localhost instead to ensure secure context.`

## Chore Description
Remove the "Browser Requirements" section from the frontend footer. This section currently displays technical requirements about browser compatibility, HTTPS/localhost requirements, and camera permissions. The section to be removed includes:
- A paragraph header with "Browser Requirements:"
- A bulleted list of browser version requirements
- HTTPS/localhost security context requirements
- Camera permission requirements
- A note about using localhost vs IP addresses

The privacy notice in the footer should be preserved.

## Relevant Files
Use these files to complete the chore:

- `apps/frontend/index.html` (lines 58-67) - Contains the footer with the browser requirements section that needs to be deleted. The section starts with `<strong>Browser Requirements:</strong>` and includes the unordered list and note paragraph.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Remove Browser Requirements Section
- Open `apps/frontend/index.html`
- Locate the footer section (lines 52-68)
- Delete the paragraph containing "Browser Requirements:" (line 58-59)
- Delete the unordered list with browser requirements (lines 60-64)
- Delete the note paragraph about IP address vs localhost (lines 65-67)
- Preserve the privacy notice paragraph (lines 53-56)
- Ensure the footer closing tag remains intact

### 2. Validate HTML Structure
- Verify the footer still contains the privacy notice
- Ensure no broken HTML tags or structure issues
- Check that the closing `</footer>` tag is properly in place
- Confirm the container and body closing tags remain intact

### 3. Test Frontend Rendering
- Open the frontend application in a browser
- Verify the footer displays only the privacy notice
- Confirm no visual or layout issues in the footer area
- Ensure no console errors related to HTML structure

## Validation Commands
Execute these commands to validate the chore is complete:

- `grep -n "Browser Requirements" apps/frontend/index.html` - Should return no results, confirming the section is removed
- `grep -n "Privacy Notice" apps/frontend/index.html` - Should still return a result, confirming privacy notice is preserved
- Open `apps/frontend/index.html` in a browser and verify the footer displays correctly with only the privacy notice

## Notes
This is a simple UI cleanup task. The browser requirements information may be considered redundant or unnecessary for the user experience. The privacy notice remains important and should be preserved.
