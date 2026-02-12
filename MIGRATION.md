# Migration Guide: GITHUB_WEBHOOK_SECRET → GH_WB_SECRET

This guide helps you migrate from the old `GITHUB_WEBHOOK_SECRET` environment variable to the new `GH_WB_SECRET` variable.

## Why This Change?

The shorter environment variable name (`GH_WB_SECRET`) improves compatibility with Vercel's environment variable handling system, which can have issues with longer variable names.

## Breaking Change Notice

⚠️ **This is a breaking change.** Your application will not start until you update your environment variables.

## Migration Steps

### 1. Local Development Environment

Update your local `.env` file:

1. **Open your `.env` file** in the project root
2. **Find the line** with `GITHUB_WEBHOOK_SECRET`:
   ```bash
   GITHUB_WEBHOOK_SECRET=your-secret-here
   ```
3. **Replace it** with `GH_WB_SECRET`:
   ```bash
   GH_WB_SECRET=your-secret-here
   ```
4. **Save the file**

**Example:**
```bash
# Before
GITHUB_WEBHOOK_SECRET=my_super_secret_webhook_key_12345

# After
GH_WB_SECRET=my_super_secret_webhook_key_12345
```

### 2. Vercel Deployment

If you're deploying to Vercel, update your environment variables:

1. **Go to your Vercel dashboard**
2. **Select your project**
3. **Navigate to Settings → Environment Variables**
4. **Remove the old variable:**
   - Find `GITHUB_WEBHOOK_SECRET`
   - Click the three dots → Delete
5. **Add the new variable:**
   - Click "Add New"
   - Name: `GH_WB_SECRET`
   - Value: (use the same value as before)
   - Select environments (Production, Preview, Development)
   - Click "Save"
6. **Redeploy your application** to apply the changes

### 3. Update Vercel Secret (if using secret references)

If you're using Vercel secret references (e.g., `@github-webhook-secret`), update them:

1. **Remove the old secret:**
   ```bash
   vercel secrets rm github-webhook-secret
   ```
2. **Add the new secret:**
   ```bash
   vercel secrets add gh-wb-secret your-secret-value-here
   ```
3. **Update `vercel.json`** (this should already be done in the codebase):
   ```json
   {
     "env": {
       "GH_WB_SECRET": "@gh-wb-secret"
     }
   }
   ```

### 4. GitHub Webhook Configuration

**No changes needed** to your GitHub webhook settings. The webhook secret value remains the same; only the environment variable name in your application changes.

However, to verify everything is working:

1. **Go to your GitHub repository**
2. **Navigate to Settings → Webhooks**
3. **Click on your webhook**
4. **Verify the Secret** matches the value in your new `GH_WB_SECRET` environment variable
5. **Test the webhook** by creating a test issue or PR

## Verification

After migration, verify everything works:

### Local Development

1. **Start your server:**
   ```bash
   ./scripts/start_webhook_server.sh
   ```

2. **Check the health endpoint:**
   ```bash
   curl http://localhost:8000/health
   ```

   Expected response:
   ```json
   {
     "status": "ok",
     "service": "adw-webhook-server",
     "environment": "development"
   }
   ```

3. **If you get an error** about missing `GH_WB_SECRET`, double-check your `.env` file.

### Vercel Deployment

1. **Deploy your application:**
   ```bash
   vercel deploy
   ```

2. **Check the health endpoint:**
   ```bash
   curl https://your-app.vercel.app/health
   ```

3. **Test a webhook** by creating a test issue with an appropriate label

4. **Check Vercel logs** for any errors related to configuration

## Troubleshooting

### Error: "GH_WB_SECRET must be set"

**Cause:** The environment variable is not set or is empty.

**Solution:**
- Verify your `.env` file has `GH_WB_SECRET` (not `GITHUB_WEBHOOK_SECRET`)
- Ensure there are no typos in the variable name
- Restart your server after updating `.env`

### Error: Webhook signature validation failed

**Cause:** The secret in GitHub doesn't match the value in `GH_WB_SECRET`.

**Solution:**
- Verify the secret value is exactly the same in both GitHub webhook settings and your environment variable
- Check for extra whitespace or hidden characters
- Regenerate the secret if necessary (update both GitHub and your env var)

### Vercel deployment fails

**Cause:** Environment variable not set in Vercel.

**Solution:**
- Verify `GH_WB_SECRET` is set in Vercel project settings
- Ensure it's set for the correct environments (Production/Preview/Development)
- Redeploy after adding the variable

### Tests failing

**Cause:** Tests may reference the old variable name.

**Solution:**
- Run the test suite to verify everything passes:
  ```bash
  uv run pytest tests/ -v
  ```
- All tests should now use `GH_WB_SECRET`

## Rollback (Not Recommended)

If you absolutely need to rollback, you can temporarily support both variable names by modifying `apps/adw_server/core/config.py`. However, this is not recommended as the change is intended to improve Vercel compatibility.

## Questions?

If you encounter any issues during migration:

1. Check the [README.md](README.md) for setup instructions
2. Review the [ADW Server README](apps/adw_server/README.md) for configuration details
3. Check [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md) for Vercel-specific guidance
4. Open an issue if you encounter problems not covered in this guide

## Summary Checklist

- [ ] Updated local `.env` file: `GITHUB_WEBHOOK_SECRET` → `GH_WB_SECRET`
- [ ] Tested local development server
- [ ] Updated Vercel environment variables (if using Vercel)
- [ ] Updated Vercel secrets (if using secret references)
- [ ] Verified GitHub webhook still has the correct secret
- [ ] Tested webhook delivery
- [ ] Ran test suite to verify everything works

Once you've completed all steps, you're migrated! 🎉
