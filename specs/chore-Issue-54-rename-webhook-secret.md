# Chore: Rename GH_WB_SECRET to GH_WB_SECRET

## Metadata
adw_id: `Issue #54`
prompt: `Lets change GH_WB_SECRET to GH_WB_SECRET since seems to be bringing issues with vercel. Be SURE to not add env variables to any commits.`

## Chore Description
Rename the environment variable `GH_WB_SECRET` to `GH_WB_SECRET` throughout the entire codebase to resolve compatibility issues with Vercel deployment. This change affects configuration files, source code, documentation, and example files. The shorter name should work better with Vercel's environment variable handling.

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
- **tests/conftest.py** - Test configuration that may use the environment variable
- **tests/test_config.py** - Configuration tests that validate the environment variable

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update Core Configuration
- Modify `apps/adw_server/core/config.py` to change the field name from `github_webhook_secret` to `gh_wb_secret`
- Update the Field definition, description, and validator function name
- Update error messages in the validator to reference `GH_WB_SECRET`
- Ensure the Pydantic settings will read from `GH_WB_SECRET` environment variable

### 2. Update Environment Example Files
- Update `.env.example` to rename `GH_WB_SECRET` to `GH_WB_SECRET`
- Update all comments and documentation in the file to reference the new name
- Update `apps/adw_server/.env.example` similarly
- Keep the instructions about generating a strong secret and minimum length requirements

### 3. Update Vercel Configuration
- Modify `vercel.json` to change the env variable reference from `GH_WB_SECRET` to `GH_WB_SECRET`
- Ensure the Vercel secret reference is updated accordingly (from `@github-webhook-secret` to appropriate format)

### 4. Update Documentation Files
- Update `README.md` to replace all occurrences of `GH_WB_SECRET` with `GH_WB_SECRET`
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
- Update `tests/test_server.py` if it references the webhook secret
- Ensure all test mocking and fixtures use the new variable name

### 8. Verify No Hardcoded Secrets
- Double-check that no actual secret values are hardcoded anywhere
- Ensure only example placeholders exist in .env.example files
- Verify that the actual .env file (if it exists) is in .gitignore

### 9. Search for Remaining References
- Use grep to search for any remaining case-insensitive references to the old name
- Update any missed occurrences in comments, strings, or documentation
- Check for variations like "GitHub webhook secret", "github-webhook-secret", etc.

### 10. Validate Changes
- Run all tests to ensure configuration loading works correctly
- Verify that the ServerConfig class properly reads the new environment variable
- Check that error messages and validation still work as expected
- Ensure documentation is consistent throughout

## Validation Commands
Execute these commands to validate the chore is complete:

- `grep -r "GH_WB_SECRET" --exclude-dir=.git --exclude-dir=__pycache__ --exclude="*.pyc" .` - Should return NO results (or only in this spec file)
- `grep -r "github_webhook_secret" --exclude-dir=.git --exclude-dir=__pycache__ --exclude="*.pyc" .` - Should return NO results (or only in this spec file)
- `grep -r "GH_WB_SECRET" --exclude-dir=.git --exclude-dir=__pycache__ --exclude="*.pyc" . | wc -l` - Should return multiple results across all updated files
- `uv run pytest tests/ -v` - All tests should pass
- `uv run python -c "from apps.adw_server.core.config import ServerConfig; print('Config loads correctly')"` - Should execute without errors (may fail on missing env var, which is expected)

## Notes
- This is a breaking change for anyone with existing deployments - they will need to update their environment variables
- The Vercel deployment will need the environment variable to be renamed in the Vercel dashboard
- Consider creating a migration note or announcement about this change
- The change improves compatibility with Vercel's environment variable handling system
- Ensure that no actual secrets are committed to the repository during this change
