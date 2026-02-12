# Chore: Rename GITHUB_WEBHOOK_SECRET to GH_WB_SECRET

## Metadata
adw_id: `Issue #54`
prompt: `Lets change GITHUB_WEBHOOK_SECRET to GH_WB_SECRET since seems to be bringing issues with vercel. Be SURE to not add env variables to any commits.`

## Chore Description
Rename the environment variable `GITHUB_WEBHOOK_SECRET` to `GH_WB_SECRET` throughout the entire codebase to resolve compatibility issues with Vercel deployment. This change affects configuration files, source code, documentation, tests, and example files. The shorter name should work better with Vercel's environment variable handling system.

**This is a breaking change** - users will need to update their environment variable configurations in both local `.env` files and Vercel dashboard settings.

## Relevant Files
Files that need to be updated to use the new environment variable name:

- **apps/adw_server/core/config.py** - ServerConfig class definition where the environment variable is defined and validated
- **apps/adw_server/.env.example** - Example environment configuration template for the ADW server
- **.env.example** - Root-level example environment configuration
- **README.md** - Main project README with setup instructions and environment variable references
- **apps/adw_server/README.md** - ADW server README with webhook configuration instructions
- **VERCEL_DEPLOYMENT.md** - Vercel deployment guide with environment variable setup
- **vercel.json** - Vercel configuration file that references the environment variable
- **api/index.py** - Vercel serverless entry point documentation
- **docs/TESTING.md** - Testing documentation that may reference the secret
- **scripts/start_webhook_server.sh** - Startup script that may reference environment variables
- **specs/chore-Issue-45-vercel-compatibility.md** - Previous Vercel compatibility spec
- **specs/chore-436b10a8-fastapi-webhook-server.md** - FastAPI webhook server spec
- **specs/chore-issue-52-update-readme.md** - README update spec
- **tests/conftest.py** - Test configuration that uses the environment variable
- **tests/test_config.py** - Configuration tests that validate the environment variable

### New Files
- **MIGRATION.md** - Migration guide for users upgrading from GITHUB_WEBHOOK_SECRET to GH_WB_SECRET

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update Core Configuration
- Modify `apps/adw_server/core/config.py` to change the field name from `github_webhook_secret` to `gh_wb_secret`
- Update the Field definition, description, and validator function name
- Update error messages in the validator to reference `GH_WB_SECRET`
- Ensure the Pydantic settings will read from `GH_WB_SECRET` environment variable

### 2. Update Environment Example Files
- Update `.env.example` to rename `GITHUB_WEBHOOK_SECRET` to `GH_WB_SECRET`
- Update all comments and documentation in the file to reference the new name
- Update `apps/adw_server/.env.example` similarly
- Keep the instructions about generating a strong secret and minimum length requirements

### 3. Update Vercel Configuration
- Modify `vercel.json` to change the env variable reference from `GITHUB_WEBHOOK_SECRET` to `GH_WB_SECRET`
- Update the Vercel secret reference from `@github-webhook-secret` to `@gh-wb-secret`

### 4. Update Documentation Files
- Update `README.md` to replace all occurrences of `GITHUB_WEBHOOK_SECRET` with `GH_WB_SECRET`
- Update `apps/adw_server/README.md` to use the new variable name in webhook setup instructions
- Update `VERCEL_DEPLOYMENT.md` to reference `GH_WB_SECRET` in environment configuration sections
- Update `docs/TESTING.md` if it contains references to the webhook secret
- Update `api/index.py` comments and docstrings to use the new name

### 5. Update Specification Files
- Update `specs/chore-Issue-45-vercel-compatibility.md` to reference the new variable name
- Update `specs/chore-436b10a8-fastapi-webhook-server.md` to use `GH_WB_SECRET`
- Update `specs/chore-issue-52-update-readme.md` if it contains references
- Update any other spec files found by grep that reference the old name

### 6. Update Scripts
- Review and update `scripts/start_webhook_server.sh` if it references the environment variable
- Ensure any script comments or documentation use the new name

### 7. Update Tests
- Update `tests/conftest.py` to use `GH_WB_SECRET` when setting up test environment
- Update `tests/test_config.py` to test the new field name and environment variable
- **CRITICAL FIX**: Fix `test_config_requires_webhook_secret` to properly isolate from `.env` file by using `monkeypatch.delenv("GH_WB_SECRET", raising=False)` to ensure the environment variable is not set during the test
- Update `tests/test_server.py` if it references the webhook secret
- Ensure all test mocking and fixtures use the new variable name

### 8. Create Migration Documentation
- Create `MIGRATION.md` in the project root with clear migration instructions
- Include steps for updating local `.env` files from `GITHUB_WEBHOOK_SECRET` to `GH_WB_SECRET`
- Include steps for updating Vercel environment variables in the dashboard
- Include steps for updating the Vercel secret reference from `@github-webhook-secret` to `@gh-wb-secret`
- Warn about the breaking nature of this change

### 9. Verify No Hardcoded Secrets
- Double-check that no actual secret values are hardcoded anywhere
- Ensure only example placeholders exist in .env.example files
- Verify that the actual .env file is in .gitignore
- Ensure `.env` file is not staged or committed with actual secrets

### 10. Search for Remaining References
- Use grep to search for any remaining case-insensitive references to `GITHUB_WEBHOOK_SECRET`
- Update any missed occurrences in comments, strings, or documentation
- Check for variations like "GitHub webhook secret", "github-webhook-secret", etc.
- Note: Historical references in archived `agents/` and `example/` directories can remain as-is since they represent historical snapshots

### 11. Validate Changes
- Run all tests to ensure configuration loading works correctly
- Verify that the ServerConfig class properly reads the new environment variable
- Check that error messages and validation still work as expected
- Ensure documentation is consistent throughout
- Verify the test fix for `test_config_requires_webhook_secret` resolves the test failure

## Validation Commands
Execute these commands to validate the chore is complete:

- `grep -ri "GITHUB_WEBHOOK_SECRET" --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=agents --exclude-dir=example --exclude="*.pyc" --exclude="*.md" . | grep -v "specs/chore-Issue-54-rename-webhook-secret.md" | grep -v "MIGRATION.md"` - Should return NO results in active code (spec files excluded)
- `grep -r "github_webhook_secret" --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=agents --exclude-dir=example --exclude="*.pyc" --exclude="*.md" . | grep -v "specs/chore-Issue-54-rename-webhook-secret.md"` - Should return NO results in active code
- `grep -r "GH_WB_SECRET" --exclude-dir=.git --exclude-dir=__pycache__ --exclude="*.pyc" .env.example apps/adw_server/.env.example README.md apps/adw_server/core/config.py vercel.json` - Should return multiple results across all key files
- `uv run pytest tests/test_config.py::test_config_requires_webhook_secret -v` - Should pass (tests that env var is required when not in .env)
- `uv run pytest tests/ -v` - All tests should pass
- `uv run python -c "from apps.adw_server.core.config import ServerConfig; print('Config loads correctly')"` - Should execute without errors (may fail on missing env var, which is expected)

## Notes

### Breaking Change Notice
This is a **breaking change** for anyone with existing deployments. Users will need to:
1. Update their local `.env` files to use `GH_WB_SECRET` instead of `GITHUB_WEBHOOK_SECRET`
2. Update Vercel environment variables in the Vercel dashboard
3. Update Vercel secret references from `@github-webhook-secret` to `@gh-wb-secret`

### Why This Change?
The shorter environment variable name improves compatibility with Vercel's environment variable handling system, which can have issues with longer variable names.

### Security Considerations
- Ensure that no actual secrets are committed to the repository during this change
- All secret values should only exist in:
  - Local `.env` files (gitignored)
  - Vercel dashboard environment variables
  - GitHub webhook settings
- Never commit `.env` files or hardcode secret values in code

### Historical References
Historical references to `GITHUB_WEBHOOK_SECRET` in archived directories (`agents/`, `example/`) can remain as-is since they represent historical snapshots of the project and are not actively used.

### Test Infrastructure Issues
The test suite has some pre-existing infrastructure issues (pytest async fixture warnings in test_server.py) that are unrelated to this change. These can be addressed in a separate issue if needed.
