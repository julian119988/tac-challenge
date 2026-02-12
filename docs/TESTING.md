# Testing Guide

Comprehensive testing guide for the TAC Challenge project.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Python Testing](#python-testing)
- [Frontend Testing](#frontend-testing)
- [Writing Tests](#writing-tests)
- [Test Coverage](#test-coverage)
- [Continuous Integration](#continuous-integration)
- [Troubleshooting](#troubleshooting)

## Overview

This project has comprehensive test coverage for both the Python backend (FastAPI server, ADW workflows) and the JavaScript frontend (attention tracking app).

### Test Structure

```
tac-challenge/
├── tests/                          # Python tests
│   ├── conftest.py                # Pytest configuration and fixtures
│   ├── test_server.py             # FastAPI endpoint tests
│   ├── test_handlers.py           # Webhook handler tests
│   ├── test_config.py             # Configuration tests
│   ├── test_adw_integration.py    # ADW workflow tests
│   ├── test_agent.py              # Agent module tests
│   └── test_github.py             # GitHub API tests
│
├── apps/frontend/test/            # Frontend tests
│   ├── setup.js                   # Jest test setup and mocks
│   ├── app.test.js                # Main app tests
│   ├── face-detection.test.js     # Face detection tests
│   ├── dataset-manager.test.js    # Dataset management tests
│   └── ui-controller.test.js      # UI controller tests
│
└── scripts/
    └── run_tests.sh               # Unified test runner
```

## Quick Start

### Run All Tests

```bash
./scripts/run_tests.sh
```

### Run Python Tests Only

```bash
./scripts/run_tests.sh --python-only
```

### Run Frontend Tests Only

```bash
./scripts/run_tests.sh --frontend-only
```

### Run Tests with Coverage

```bash
./scripts/run_tests.sh --coverage
```

## Python Testing

### Setup

Install test dependencies:

```bash
pip install -r requirements.txt
# or with uv:
uv pip install -r requirements.txt
```

### Running Tests

#### Run all Python tests:

```bash
uv run pytest tests/ -v
```

#### Run specific test file:

```bash
uv run pytest tests/test_server.py -v
```

#### Run specific test function:

```bash
uv run pytest tests/test_server.py::test_health_check -v
```

#### Run tests with markers:

```bash
# Run only unit tests
uv run pytest tests/ -m unit

# Run only integration tests
uv run pytest tests/ -m integration

# Run async tests
uv run pytest tests/ -m asyncio
```

### Test Coverage

Generate coverage report:

```bash
uv run pytest tests/ --cov=adws --cov=apps --cov-report=term-missing
```

Generate HTML coverage report:

```bash
uv run pytest tests/ --cov=adws --cov=apps --cov-report=html
open htmlcov/index.html
```

### Python Test Examples

#### Testing FastAPI Endpoints

```python
@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    """Test basic health check endpoint."""
    response = await async_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
```

#### Testing with Mocked Dependencies

```python
def test_validate_webhook_signature_valid():
    """Test webhook signature validation with valid signature."""
    secret = "test_secret_12345678"
    payload = b'{"action": "opened"}'

    # Generate valid signature
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()
    signature_header = f"sha256={expected_sig}"

    is_valid = validate_webhook_signature(payload, signature_header, secret)
    assert is_valid is True
```

#### Testing Async Functions

```python
@pytest.mark.asyncio
async def test_trigger_chore_workflow_success(temp_dir):
    """Test successful chore workflow execution."""
    mock_response = AgentPromptResponse(
        success=True,
        output="Planning complete",
        session_id="session-12345"
    )

    with patch("apps.adw_server.core.adw_integration.execute_template") as mock_exec:
        mock_exec.return_value = mock_response

        result = await trigger_chore_workflow(
            prompt="Add feature X",
            working_dir=temp_dir
        )

        assert result.success is True
```

## Frontend Testing

### Setup

Install frontend test dependencies:

```bash
cd apps/frontend
npm install
```

### Running Tests

#### Run all frontend tests:

```bash
cd apps/frontend
npm test
```

#### Run tests in watch mode:

```bash
npm run test:watch
```

#### Run tests with coverage:

```bash
npm run test:coverage
open coverage/lcov-report/index.html
```

### Frontend Test Examples

#### Testing Browser APIs

```javascript
describe('Camera Access', () => {
  test('should request camera access', async () => {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: true
    });

    expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({
      video: true
    });
    expect(stream).toBeDefined();
  });
});
```

#### Testing DOM Manipulation

```javascript
describe('UI Element Access', () => {
  test('should find UI elements by ID', () => {
    const button = document.getElementById('startBtn');

    expect(button).not.toBeNull();
    expect(button.textContent).toBe('Start');
  });
});
```

#### Testing with Mocked TensorFlow.js

```javascript
describe('Face Detection', () => {
  test('should detect faces from video frame', async () => {
    const model = await tf.loadGraphModel('mock-model');

    const tensor = tf.browser.fromPixels(mockVideo);
    const prediction = model.predict(tensor);
    const results = prediction.dataSync();

    expect(results).toBeInstanceOf(Float32Array);
  });
});
```

## Writing Tests

### Best Practices

1. **Descriptive test names**: Use clear, descriptive names that explain what is being tested
2. **Arrange-Act-Assert pattern**: Structure tests with clear setup, execution, and assertion phases
3. **One assertion per test**: Focus each test on a single behavior
4. **Use fixtures**: Leverage pytest fixtures for shared setup
5. **Mock external dependencies**: Avoid real network calls, file I/O, or external services
6. **Test edge cases**: Include tests for error conditions, boundary values, and edge cases

### Test Patterns

#### Python: Using Fixtures

```python
@pytest.fixture
def mock_config(temp_dir: str):
    """Provide a mock ServerConfig for testing."""
    return ServerConfig(
        server_host="127.0.0.1",
        server_port=8000,
        github_webhook_secret="test_secret_1234567890",
        adw_working_dir=temp_dir
    )

def test_with_fixture(mock_config):
    """Test using shared fixture."""
    assert mock_config.server_host == "127.0.0.1"
```

#### Python: Mocking Subprocess Calls

```python
def test_with_mocked_subprocess(mocker):
    """Test with mocked subprocess."""
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

    # Call function that uses subprocess
    result = some_function_that_calls_subprocess()

    mock_run.assert_called_once()
    assert result is True
```

#### Frontend: Testing Event Handlers

```javascript
test('should attach click event listener', () => {
  const button = document.getElementById('startBtn');
  const mockHandler = jest.fn();

  button.addEventListener('click', mockHandler);
  button.click();

  expect(mockHandler).toHaveBeenCalledTimes(1);
});
```

### Common Testing Scenarios

#### Testing Webhook Handlers

```python
@pytest.mark.asyncio
async def test_webhook_valid_signature(async_client, mock_config):
    """Test webhook with valid signature is accepted."""
    payload = json.dumps(mock_github_issue_payload).encode("utf-8")
    signature = generate_github_signature(payload, mock_config.github_webhook_secret)

    response = await async_client.post(
        "/",
        content=payload,
        headers={
            "X-GitHub-Event": "issues",
            "X-Hub-Signature-256": signature,
        }
    )

    assert response.status_code == 200
```

#### Testing ADW Workflows

```python
@pytest.mark.asyncio
async def test_full_workflow(temp_dir):
    """Test complete chore + implement workflow."""
    with patch("adws.adw_modules.agent.execute_template") as mock_exec:
        # Mock chore planning
        mock_exec.return_value = AgentPromptResponse(
            success=True,
            output="Plan created at specs/chore-abc-feature.md"
        )

        result = await trigger_chore_workflow(
            prompt="Add feature",
            working_dir=temp_dir
        )

        assert result.success is True
```

#### Testing Frontend Components

```javascript
describe('DatasetManager', () => {
  test('should store data in localStorage', () => {
    const testData = { gaze: [100, 200], timestamp: Date.now() };
    const key = 'testDataset';

    localStorage.setItem(key, JSON.stringify(testData));

    expect(localStorage.setItem).toHaveBeenCalledWith(
      key,
      JSON.stringify(testData)
    );
  });
});
```

## Test Coverage

### Coverage Goals

- **Statements**: 70%+
- **Branches**: 60%+
- **Functions**: 70%+
- **Lines**: 70%+

### Viewing Coverage Reports

#### Python:

```bash
uv run pytest tests/ --cov=adws --cov=apps --cov-report=html
open htmlcov/index.html
```

#### Frontend:

```bash
cd apps/frontend
npm run test:coverage
open coverage/lcov-report/index.html
```

### Coverage Reports Location

- Python: `htmlcov/index.html`
- Frontend: `apps/frontend/coverage/lcov-report/index.html`

## Continuous Integration

### GitHub Actions (Future)

Add `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install Python dependencies
        run: pip install -r requirements.txt

      - name: Run Python tests
        run: pytest tests/ --cov

      - name: Install frontend dependencies
        run: cd apps/frontend && npm install

      - name: Run frontend tests
        run: cd apps/frontend && npm test
```

## Troubleshooting

### Common Issues

#### Python Tests

**Issue**: `ModuleNotFoundError: No module named 'apps'`

**Solution**: Ensure you're running tests from the project root:

```bash
cd /path/to/tac-challenge
uv run pytest tests/
```

**Issue**: `ValidationError` when testing configuration

**Solution**: Ensure test environment variables are set:

```python
@pytest.fixture
def test_env_vars(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "test_secret_1234567890")
```

#### Frontend Tests

**Issue**: `Cannot find module 'jest'`

**Solution**: Install frontend dependencies:

```bash
cd apps/frontend
npm install
```

**Issue**: `ReferenceError: tf is not defined`

**Solution**: Ensure `test/setup.js` is loaded (configured in `jest.config.js`):

```javascript
setupFilesAfterEnv: ['<rootDir>/test/setup.js']
```

**Issue**: Tests pass but with warnings about `getUserMedia`

**Solution**: This is expected - the tests mock these APIs. Warnings can be suppressed in `test/setup.js`.

### Debug Mode

Run tests with verbose output:

```bash
# Python
uv run pytest tests/ -v -s

# Frontend
npm test -- --verbose
```

### Selective Test Execution

Run specific test patterns:

```bash
# Python - run only tests matching "webhook"
uv run pytest tests/ -k webhook

# Frontend - run only tests matching "camera"
npm test -- --testNamePattern="camera"
```

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Testing Library](https://testing-library.com/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

## Contributing

When adding new features:

1. Write tests first (TDD approach recommended)
2. Ensure all tests pass before committing
3. Maintain or improve test coverage
4. Update this documentation if adding new test patterns
