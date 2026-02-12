# Focus Keeper - Anti-Procrastination App

**Focus Keeper** is an anti-procrastination web application that uses your device's camera to detect when you're distracted and plays attention videos to keep you focused. This project was built entirely using **Tactical Agentic Coding (TAC)** - demonstrating how AI agents can autonomously develop complex applications.

## What is Focus Keeper?

Focus Keeper is a browser-based attention tracking application that:

- **Detects when you're distracted** using machine learning for facial recognition
- **Plays attention videos** when it detects you've stopped focusing
- **Processes everything locally** in your browser - no data transmission, privacy first
- **Works completely on the client** - no backend ML processing required

**Built using Tactical Agentic Coding**: This project demonstrates TAC in action - a development paradigm where engineering patterns are templated and AI agents learn to operate the codebase, scaling impact through computation rather than direct programming.

## Technologies Used

- **Frontend**: Vanilla JavaScript, TensorFlow.js, MediaPipe Face Mesh
- **Backend**: Python, FastAPI, Uvicorn
- **AI/ML**: Claude Sonnet (via Anthropic API), TensorFlow.js for face detection
- **Deployment**: Vercel serverless functions
- **Testing**: Pytest (Python), Jest (JavaScript)
- **CI/CD**: GitHub webhooks, automated workflows
- **Tools**: uv (Python package management), gh CLI (GitHub operations)

## Focus Keeper Features

### Main Features

- **Real-time face detection**: Uses TensorFlow.js with MediaPipe Face Mesh to detect your face and track your gaze
- **Distraction monitoring**: Automatically detects when you look away from the screen or leave your seat
- **Attention interventions**: Plays engaging videos when distraction is detected to capture your attention
- **Privacy-first design**: All processing happens locally in your browser - no video is stored or transmitted
- **No backend required**: Runs completely client-side without server ML processing

### Browser Compatibility

Works best on modern browsers with WebRTC and WebGL support:

- **Chrome** (recommended) - v90+
- **Firefox** - v88+
- **Safari** - v14+
- **Edge** - v90+

**Requirements**: Camera access permissions, JavaScript enabled, WebGL support

For more details about Focus Keeper, see the [Frontend README](apps/frontend/README.md).

## Project Structure

```
tac-challenge/
├── .claude/              # Claude configuration and commands
├── adws/                 # AI Developer Workflows - AI workflows for automation
│   ├── adw_modules/      # Core modules (agent, github, etc.)
│   └── adw_*.py          # Workflow scripts
├── apps/                 # Application layer - application code
│   ├── adw_server/       # ADW automation server
│   │   ├── core/         # Core modules (config, handlers, integration)
│   │   ├── server.py     # FastAPI application
│   │   └── main.py       # Entry point
│   └── frontend/         # Focus Keeper - anti-procrastination application
│       ├── index.html    # Main web application
│       ├── app.js        # Application logic
│       ├── face-detection.js  # Face detection and gaze tracking
│       ├── video-player.js    # Intervention video handling
│       └── test/         # Frontend tests (Jest)
├── api/                  # Vercel deployment - serverless functions
├── docs/                 # Additional documentation
│   └── TESTING.md        # Complete testing guide
├── specs/                # Implementation specifications - plans for agents
├── scripts/              # Startup and utility scripts
├── tests/                # Python backend tests (Pytest)
├── .env.example          # Configuration template
├── requirements.txt      # Python dependencies
├── vercel.json           # Vercel deployment configuration
└── VERCEL_DEPLOYMENT.md  # Deployment guide
```

## Quick Start - Running the Application

### 1. Setup Environment

```bash
# Copy configuration template
cp apps/adw_server/.env.example .env

# Edit .env and configure:
# - GH_WB_SECRET (for GitHub webhooks)
# - ANTHROPIC_API_KEY (for ADW workflows)
```

### 2. Start the Server

The FastAPI server serves both the Focus Keeper application and the ADW automation system:

```bash
# From the project root
./scripts/start_webhook_server.sh
```

**Alternative methods:**

<details>
<summary>Using uv (recommended - handles dependencies automatically)</summary>

```bash
PYTHONPATH=. uv run \
  --with fastapi \
  --with "uvicorn[standard]" \
  --with pydantic \
  --with pydantic-settings \
  --with python-dotenv \
  uvicorn apps.adw_server.server:app --host 0.0.0.0 --port 8000
```
</details>

<details>
<summary>Using Python directly</summary>

```bash
pip install -r requirements.txt
python apps/adw_server/main.py
```
</details>

### 3. Access Focus Keeper

Once the server is running:

1. Open your browser and navigate to: **http://localhost:8000/app**
2. The browser will request camera permissions - click "Allow"
3. Click "Start Session" to begin tracking your focus
4. Get to work! The app will monitor your attention and alert you if you get distracted

### 4. Available Endpoints

- **Focus Keeper app**: http://localhost:8000/app - The main application
- **Health check**: http://localhost:8000/health
- **Readiness check**: http://localhost:8000/health/ready
- **GitHub webhooks**: http://localhost:8000/ (POST)

## Tactical Agentic Coding (TAC)

### What is TAC?

TAC is a paradigm where:
- Engineering patterns are templated
- AI agents learn to operate the codebase
- Impact scales through computation, not direct effort

### Project Layers

#### Agentic Layer

Responsible for agentic coding - where engineering patterns are templated:

- **`.claude/commands/`**: Reusable command templates
- **`adws/`**: Executable AI Developer Workflows
- **`specs/`**: Specifications that guide agent actions

#### Application Layer

Your actual application code - what the agents operate on:

- **`apps/`**: Application code
  - `adw_server/`: ADW automation tool (NOT the main app server)

## ADW Server

The ADW Server is an **automation tool**, not the main application server.

**Purpose:**
- GitHub → ADW workflows integration
- Development task automation
- Health monitoring

**GitHub Webhook Configuration:**

1. Go to Settings → Webhooks → Add webhook
2. Payload URL: `https://your-server.com/`
3. Content type: `application/json`
4. Secret: (same as `GH_WB_SECRET` in `.env`)
5. Events: Select "Issues" and "Pull requests"

**Supported Labels:**
- `implement` / `bug` → Full workflow (plan + implementation)
- `feature` → Planning only
- `chore` / `plan` → Planning only

**Pull Request Review Workflow:**

When a Pull Request is created or updated that references an issue (with "Closes #N", "Fixes #N", or "Resolves #N"), a review workflow automatically executes that:
- Analyzes code using Claude
- Runs project tests
- Captures screenshots if there are UI changes (future)
- Determines approval status based on analysis
- Posts results to the issue thread

**Review States:**

The review workflow can result in three states:
- **APPROVED**: Code meets standards, tests pass, no issues detected
- **CHANGES REQUESTED**: Problems found that require corrections
- **NEEDS DISCUSSION**: Requires manual review or discussion (ambiguous cases)

**Post-Review Automated Actions:**

The system can perform automatic actions based on review results:

- **APPROVED**:
  - **Auto-merge** of PR (configurable with `AUTO_MERGE_ON_APPROVAL=true`)
  - PR automatically merges to base branch
  - Configurable merge method (squash, merge, rebase)

- **CHANGES REQUESTED**:
  - **Auto-reimplement** with review feedback (configurable with `AUTO_REIMPLEMENT_ON_CHANGES=true`)
  - Agent reads review feedback
  - Automatically implements requested corrections
  - Creates a new commit with changes
  - Updated PR triggers new automatic review

- **NEEDS DISCUSSION**:
  - Only posts results
  - Requires manual developer intervention

**Post-Review Actions Configuration:**

Automatic actions can be configured in `.env`:
```bash
AUTO_MERGE_ON_APPROVAL=true          # Automatic merge on approval
AUTO_REIMPLEMENT_ON_CHANGES=true     # Automatic re-implementation on requested changes
MERGE_METHOD=squash                  # Merge method (squash, merge, rebase)
MAX_REIMPLEMENT_ATTEMPTS=3           # Maximum attempts to prevent loops
```

**Infinite Loop Protection:**

The system implements robust protection against re-implementation loops:
- **Tracks attempts per issue**: Counts how many times re-implementation has been attempted
- **Configurable limit**: After reaching `MAX_REIMPLEMENT_ATTEMPTS` (default: 3), stops auto-reimplementation
- **Requires manual intervention**: After the limit, changes must be made manually
- **Reset on successful merge**: Counter resets when a PR successfully merges
- **Prevents repeated failure scenarios**: Prevents agent from generating code that fails review indefinitely

For more details on review workflow and post-review automation, see the [ADW Server README](apps/adw_server/README.md).

## Testing

The project includes comprehensive testing infrastructure for both Python backend and JavaScript frontend, ensuring code quality and reliability.

### Test Structure

- **Python Tests** (`tests/`): Backend tests using Pytest
  - Configuration tests
  - Event handler tests
  - GitHub integration tests
  - ADW workflow tests

- **Frontend Tests** (`apps/frontend/test/`): JavaScript tests using Jest
  - Face detection tests
  - Distraction monitoring tests
  - Video playback tests
  - Session management tests

- **Unified Script**: `scripts/run_tests.sh` - Run all tests with a single command

### Running Tests

**All tests:**

```bash
./scripts/run_tests.sh
```

**Python tests only:**

```bash
./scripts/run_tests.sh --python-only
# Or directly:
uv run pytest tests/ -v
```

**Frontend tests only:**

```bash
./scripts/run_tests.sh --frontend-only
# Or directly:
cd apps/frontend && npm test
```

**With coverage:**

```bash
./scripts/run_tests.sh --coverage
```

### Coverage Goals

- **Python Backend**: >80% coverage
- **Frontend JavaScript**: >75% coverage

To view coverage reports:
```bash
# Python coverage report
uv run pytest tests/ --cov=apps --cov=adws --cov-report=html
open htmlcov/index.html

# Frontend coverage report
cd apps/frontend && npm test -- --coverage
```

For complete testing guide, see the [Testing Guide](docs/TESTING.md).

## Deployment

The project includes full support for production deployment using Vercel.

### Vercel Deployment

The project is configured for serverless deployment on Vercel:

- **Serverless FastAPI app**: ADW server runs as a serverless function
- **Static frontend**: Focus Keeper is served as static files
- **Automatic configuration**: `vercel.json` configures routes and rewrites
- **Environment variables**: Configurable in Vercel dashboard

### Quick Deploy

```bash
# See VERCEL_DEPLOYMENT.md for detailed instructions
vercel deploy
```

### Required Configuration

Environment variables in Vercel dashboard:

```bash
GH_WB_SECRET=your_webhook_secret_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
AUTO_MERGE_ON_APPROVAL=true                    # Optional
AUTO_REIMPLEMENT_ON_CHANGES=true              # Optional
MERGE_METHOD=squash                           # Optional
MAX_REIMPLEMENT_ATTEMPTS=3                    # Optional
```

### Deployment Considerations

- **Serverless function limits**: Vercel has execution timeouts (10s hobby, 60s pro)
- **Ephemeral filesystem**: Only `/tmp` is writable, files are deleted between invocations
- **Cold starts**: First execution may be slower
- **Automatic scaling**: Vercel handles scaling automatically

For complete deployment guide, see the [Vercel Deployment Guide](VERCEL_DEPLOYMENT.md).

## Development

### Environment Setup

The project uses comprehensive testing infrastructure for both backend and frontend, ensuring code quality across all components.

### Hot Reload

- **FastAPI Backend**: Auto-reload enabled in development mode (uvicorn with `--reload`)
- **Frontend**: Served as static files, automatic reload on changes (use live server or similar)

### Available Scripts

```bash
# Startup and utility scripts are in scripts/
ls scripts/

# Examples:
./scripts/start_webhook_server.sh     # Start the server
./scripts/run_tests.sh                # Run all tests
```

### Directory Structure

- **`adws/`**: AI workflows for development - automation scripts
- **`apps/frontend/`**: Focus Keeper app - anti-procrastination application
- **`apps/adw_server/`**: ADW automation server
- **`specs/`**: Implementation specifications - plans for agents
- **`scripts/`**: Utility and startup scripts
- **`tests/`**: Python backend tests
- **`docs/`**: Additional documentation

## 12 Leverage Points of Agentic Coding

### In the Agent (Core Four)

1. Context
2. Model
3. Prompt
4. Tools

### Through the Agent

5. Standard Output
6. Types
7. Docs
8. Tests
9. Architecture
10. Plans
11. Templates
12. AI Developer Workflows

## Flexibility

This is *one way* to organize the agentic layer. The key principle is creating a structured environment where:
- Engineering patterns are reusable templates
- Agents have clear instructions on how to operate the codebase
- Workflows are composable and scalable
- Output is observable and debuggable

Feel free to adapt this structure to your specific needs.

## Troubleshooting

### Focus Keeper Issues

#### Camera not working

**Problem**: "Failed to access camera" error

**Solutions**:
- Check browser permissions (Settings → Privacy → Camera)
- Ensure no other app is using the camera
- Try another browser
- On macOS: System Preferences → Security & Privacy → Camera

#### Face not detected

**Problem**: Status shows "Distracted" even when you're present

**Solutions**:
- Improve lighting (add desk lamp, open curtains)
- Remove glasses if causing reflections
- Move closer to the camera
- Ensure your face is centered in the frame

#### Model won't load

**Problem**: "Failed to load face detection model" error

**Solutions**:
- Check internet connection (TensorFlow.js loads from CDN)
- Clear browser cache and reload
- Disable ad blockers that may block CDN requests
- Try another browser

#### Poor performance / lag

**Problem**: App is slow or unresponsive

**Solutions**:
- Close other browser tabs
- Use Chrome (better WebGL performance)
- Close other GPU-using applications
- Verify your device has sufficient resources

### ADW Automation Issues

#### Webhook signature validation fails

**Problem**: Webhooks rejected with validation error

**Solutions**:
- Verify `GH_WB_SECRET` in `.env` matches GitHub settings
- Ensure the secret has no spaces or special characters
- Regenerate the secret if necessary

#### ADW workflows not triggering

**Problem**: Issues with labels don't activate workflows

**Solutions**:
- Verify the issue has the correct label (`implement`, `bug`, `feature`, `chore`)
- Check server logs for errors
- Ensure webhooks are configured correctly in GitHub
- Verify `ANTHROPIC_API_KEY` is configured

#### Auto-merge fails

**Problem**: PR approved but doesn't merge automatically

**Solutions**:
- Verify `AUTO_MERGE_ON_APPROVAL=true` in `.env`
- Ensure there are no merge conflicts
- Check GitHub token permissions (must be able to merge)
- Review branch protections in GitHub settings

#### Re-implementation loops

**Problem**: Agent attempts to re-implement indefinitely

**Solutions**:
- Check `MAX_REIMPLEMENT_ATTEMPTS` in `.env` (default: 3)
- Provide clearer feedback in reviews
- Consider increasing the limit if changes are complex
- Review attempt counter in logs

For more detailed troubleshooting, see the READMEs of each component:
- [Frontend Troubleshooting](apps/frontend/README.md#troubleshooting)
- [ADW Server README](apps/adw_server/README.md)

## Additional Documentation

### User Documentation

- **[Focus Keeper App](apps/frontend/README.md)** - Complete anti-procrastination application documentation
  - Features and functionality
  - Usage guide
  - Configuration
  - Troubleshooting

### Development Documentation

- **[ADW README](adws/README.md)** - AI Developer Workflows documentation
  - SDK support
  - Workflow patterns
  - Observability

- **[ADW Server README](apps/adw_server/README.md)** - Automation server
  - PR review workflow
  - Auto-merge and auto-reimplement
  - Loop protection
  - Configuration

- **[Testing Guide](docs/TESTING.md)** - Complete testing guide
  - Python tests
  - Frontend tests
  - Coverage goals
  - Best practices

- **[Deployment Guide](VERCEL_DEPLOYMENT.md)** - Vercel deployment guide
  - Serverless configuration
  - Environment variables
  - Production considerations

- **Specifications** (`specs/`) - Implementation plans and feature specifications

## License

This project is an educational challenge to demonstrate Tactical Agentic Coding.
