# Chore: Add Testing

## Metadata
adw_id: `6c574e8a`
prompt: `Issue #37: Add testing

I would like to add some tests.

How can we test this app?`

## Chore Description
Add comprehensive testing infrastructure to the TAC Challenge project. The project has two main testable components:

1. **Python Backend/ADW Server** - FastAPI webhook server and ADW modules that need unit and integration tests
2. **JavaScript Frontend** - Browser-based attention tracking app that needs unit and integration tests

Currently, the project has minimal testing (4 basic Python tests in `tests/` directory). This chore will establish a complete testing framework with examples for both backend and frontend, along with documentation on how to run and write tests.

## Relevant Files
Use these files to complete the chore:

- `README.md` - Main project documentation that should be updated with testing instructions
- `requirements.txt` - Python dependencies where test frameworks should be added
- `tests/` - Existing test directory with 4 Python tests:
  - `test_adw_workflow.py` - Example of testing ADW workflows
  - `test_deduplication.py` - Example of unit testing
  - `test_git_ops.py` - Example of testing git operations with temp repos
  - `test_github_comment.py` - Example of integration testing
- `apps/adw_server/server.py` - FastAPI server that needs API endpoint tests
- `apps/adw_server/core/handlers.py` - Webhook handlers that need unit tests
- `apps/adw_server/core/config.py` - Configuration module that needs unit tests
- `apps/adw_server/core/adw_integration.py` - ADW integration that needs unit tests
- `adws/adw_modules/` - Core ADW modules that need unit tests:
  - `agent.py` - Agent execution logic
  - `git_ops.py` - Git operations (partially tested)
  - `github.py` - GitHub API integration
  - `workflow_ops.py` - Workflow orchestration
  - `state.py` - State management
- `apps/frontend/` - JavaScript frontend files that need tests:
  - `app.js` - Main application orchestration
  - `face-detection.js` - Face detection logic
  - `eye-tracker.js` - Eye tracking logic
  - `dataset-manager.js` - Dataset management
  - `model-trainer.js` - ML model training
  - `gaze-predictor.js` - Gaze prediction
  - `ui-controller.js` - UI state management
  - `video-player.js` - Video playback logic
  - `config.js` - Configuration

### New Files
- `tests/test_server.py` - FastAPI endpoint tests using pytest and httpx
- `tests/test_handlers.py` - Webhook handler unit tests
- `tests/test_config.py` - Configuration loading tests
- `tests/test_adw_integration.py` - ADW integration tests
- `tests/test_agent.py` - Agent module unit tests
- `tests/test_github.py` - GitHub API integration tests (with mocking)
- `tests/conftest.py` - Pytest configuration and shared fixtures
- `apps/frontend/test/` - Frontend test directory
- `apps/frontend/test/app.test.js` - Main app orchestration tests
- `apps/frontend/test/face-detection.test.js` - Face detection unit tests
- `apps/frontend/test/dataset-manager.test.js` - Dataset management tests
- `apps/frontend/test/ui-controller.test.js` - UI controller tests
- `apps/frontend/package.json` - npm package file with test dependencies (Jest, etc.)
- `apps/frontend/jest.config.js` - Jest test configuration
- `scripts/run_tests.sh` - Convenience script to run all tests (Python + JavaScript)
- `docs/TESTING.md` - Comprehensive testing documentation

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update Python Dependencies
- Add pytest, pytest-asyncio, pytest-cov to requirements.txt
- Add httpx[test] for FastAPI testing
- Add pytest-mock for mocking support
- Add coverage for code coverage reporting
- Uncomment or add commented development dependencies

### 2. Create Pytest Configuration
- Create `tests/conftest.py` with shared fixtures
- Add fixtures for temporary directories, test config, mock GitHub API
- Add fixtures for FastAPI test client
- Configure pytest settings (async mode, markers, etc.)

### 3. Add FastAPI Server Tests
- Create `tests/test_server.py` for API endpoint testing
- Test health check endpoints (`/health`, `/health/ready`)
- Test webhook signature validation (valid, invalid, missing)
- Test webhook event routing (issues, pull_request, unsupported)
- Test CORS middleware if enabled
- Test static file serving
- Use FastAPI TestClient or httpx AsyncClient

### 4. Add Handler Unit Tests
- Create `tests/test_handlers.py` for webhook handler testing
- Test `validate_webhook_signature()` with various inputs
- Test `handle_issue_event()` with mocked ADW integration
- Test `handle_pull_request_event()` with mocked ADW integration
- Test label-based workflow routing logic
- Mock subprocess calls to ADW scripts

### 5. Add Configuration Tests
- Create `tests/test_config.py` for configuration testing
- Test loading configuration from environment variables
- Test default values
- Test configuration validation
- Test path resolution for static files and working directory

### 6. Add ADW Integration Tests
- Create `tests/test_adw_integration.py` for ADW integration testing
- Test `generate_adw_id()` generates valid IDs
- Test `trigger_chore_workflow()` with mocked subprocess
- Test `trigger_chore_implement_workflow()` with mocked subprocess
- Test WorkflowResult parsing
- Mock agent.py execution

### 7. Add ADW Module Tests
- Create `tests/test_agent.py` for agent module testing
- Test `prompt_claude_code()` with mocked subprocess
- Test `prompt_claude_code_with_retry()` retry logic
- Test `execute_template()` slash command execution
- Test JSONL parsing and result extraction
- Expand `tests/test_git_ops.py` with additional git operation tests
- Create `tests/test_github.py` for GitHub API testing (mock requests)

### 8. Add Frontend Testing Infrastructure
- Create `apps/frontend/package.json` with Jest, @testing-library, jsdom
- Add test scripts: `npm test`, `npm run test:watch`, `npm run test:coverage`
- Create `apps/frontend/jest.config.js` with ES module support
- Configure Jest for browser environment (jsdom)
- Add mock implementations for MediaDevices, canvas, TensorFlow.js

### 9. Add Frontend Unit Tests
- Create `apps/frontend/test/face-detection.test.js`
  - Test FaceDetector initialization
  - Test detection with mocked TensorFlow.js
  - Test error handling
- Create `apps/frontend/test/dataset-manager.test.js`
  - Test dataset storage and retrieval
  - Test localStorage mocking
- Create `apps/frontend/test/ui-controller.test.js`
  - Test UI state management
  - Test event handlers
  - Test DOM manipulation
- Create `apps/frontend/test/app.test.js`
  - Test CameraManager initialization
  - Test module integration
  - Test error handling for unsupported browsers

### 10. Create Test Runner Scripts
- Create `scripts/run_tests.sh` to run all tests
- Add Python test command: `uv run pytest tests/ -v --cov=adws --cov=apps --cov-report=term-missing`
- Add frontend test command: `cd apps/frontend && npm test`
- Add option to run Python only, frontend only, or both
- Add option for coverage reports
- Make script executable

### 11. Create Testing Documentation
- Create `docs/TESTING.md` with comprehensive testing guide
- Document how to run tests (Python, JavaScript, all)
- Document how to write new tests (examples, patterns, best practices)
- Document test structure and organization
- Document mocking strategies for external dependencies
- Document coverage requirements and how to generate reports
- Add examples for common test scenarios:
  - Testing FastAPI endpoints
  - Testing webhook handlers
  - Testing ADW workflows
  - Testing frontend components
  - Testing with mocked dependencies

### 12. Update Main README
- Add "Testing" section to README.md after "Development" section
- Reference `docs/TESTING.md` for detailed testing guide
- Add quick commands for running tests:
  - `./scripts/run_tests.sh` - Run all tests
  - `uv run pytest tests/ -v` - Run Python tests
  - `cd apps/frontend && npm test` - Run frontend tests
- Add badge placeholders for test coverage (optional)

### 13. Validate Testing Setup
- Install Python test dependencies: `pip install -r requirements.txt` or `uv pip install pytest pytest-asyncio httpx pytest-mock coverage`
- Run Python tests: `uv run pytest tests/ -v`
- Verify all Python tests pass
- Install frontend dependencies: `cd apps/frontend && npm install`
- Run frontend tests: `cd apps/frontend && npm test`
- Verify all frontend tests pass
- Run test coverage reports and verify reasonable coverage
- Test the run_tests.sh script

## Validation Commands
Execute these commands to validate the chore is complete:

- `cat requirements.txt | grep -E "pytest|httpx"` - Verify pytest dependencies added
- `ls -la tests/conftest.py tests/test_*.py` - Verify Python test files created
- `ls -la apps/frontend/package.json apps/frontend/jest.config.js` - Verify frontend test setup
- `ls -la apps/frontend/test/*.test.js` - Verify frontend test files created
- `ls -la scripts/run_tests.sh` - Verify test runner script created
- `ls -la docs/TESTING.md` - Verify testing documentation created
- `uv run pytest tests/ -v --tb=short` - Run all Python tests (should pass)
- `cd apps/frontend && npm test -- --passWithNoTests` - Run frontend tests (should pass or pass with no tests)
- `./scripts/run_tests.sh --help` - Verify test script is executable and shows help
- `grep -i "testing" README.md` - Verify README updated with testing section

## Notes
- Focus on creating a solid testing foundation with examples rather than 100% coverage
- Prioritize testing critical paths: webhook handling, ADW integration, face detection
- Use mocking extensively to avoid external dependencies (GitHub API, Claude API, camera access)
- Frontend tests may need to mock browser APIs (MediaDevices, canvas, TensorFlow.js)
- Keep tests fast and isolated - no network calls, no file system writes (except temp dirs)
- Follow existing test patterns in `tests/test_git_ops.py` (temp repo setup, cleanup)
- Consider adding GitHub Actions CI workflow in future to run tests automatically
- For frontend, ES modules may need special Jest configuration (transform, moduleNameMapper)
