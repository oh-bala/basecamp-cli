# Basecamp OAuth2 Setup Guide

## Overview

To use the Basecamp CLI, you need to register an OAuth2 application with Basecamp and configure the redirect URI. This guide walks you through the process.

## Step 1: Register Your Application

1. **Log in to Basecamp**
   - Go to your Basecamp account
   - Navigate to your account settings

2. **Create an OAuth2 Application**
   - Go to: https://launchpad.37signals.com/integrations
   - Click "New integration" or "Create a new integration"
   - Fill in the application details:
     - **Name**: Basecamp CLI (or any name you prefer)
     - **Description**: Command-line interface for Basecamp API
     - **Redirect URI**: See options below

## Step 2: Configure Redirect URI

Basecamp supports different types of redirect URIs. For CLI applications, we recommend:

### Option 1: Localhost Redirect - ⭐ Recommended

**Redirect URI**: `http://localhost:8080/callback`

This is the **recommended option** for command-line applications because:
- ✅ Works reliably in all modern browsers
- ✅ Shows authorization code in URL (easy to copy)
- ✅ No browser compatibility issues
- ✅ Simple to use

**How it works:**
1. User authorizes the application in their browser
2. Basecamp redirects to `http://localhost:8080/callback?code=AUTHORIZATION_CODE`
3. User copies the code from the URL and pastes it into the CLI

**Note**: You don't need to run a local server - just copy the code from the redirect URL.

### Option 2: Out-of-Band (OOB) - ⚠️ Not Recommended

**Redirect URI**: `urn:ietf:wg:oauth:2.0:oob`

**⚠️ Warning**: This option has known browser compatibility issues:
- Modern browsers cannot handle `urn:` scheme redirects
- You'll see "scheme does not have a registered handler" errors
- Code extraction is difficult (may need to check browser console)

**Only use if localhost redirect doesn't work for your use case.**

### Option 2: Custom URL (for web apps or local development)

**Redirect URI**: `http://localhost:8080/callback` (or your custom URL)

Use this if you want to:
- Build a web application
- Automatically capture the authorization code
- Test with a local server

**Note**: The redirect URI you register must **exactly match** what you use in the authorization request.

## Step 3: Get Your Credentials

After creating the integration, you'll receive:
- **Client ID**: A public identifier for your application
- **Client Secret**: A secret key (keep this secure!)

## Step 4: Configure the CLI

### Using the Default OOB Redirect URI

```bash
basecamp configure
```

When prompted:
- **OAuth2 Client ID**: Enter your Client ID
- **OAuth2 Client Secret**: Enter your Client Secret
- **Redirect URI**: Press Enter to use default (`urn:ietf:wg:oauth:2.0:oob`)

### Using a Custom Redirect URI

```bash
basecamp configure --redirect-uri http://localhost:8080/callback
```

Or set it interactively:
```bash
basecamp configure
# When prompted for redirect URI, enter: http://localhost:8080/callback
```

## Step 5: Authenticate

After configuration, authenticate:

```bash
basecamp auth
```

Or with a specific account ID:
```bash
basecamp auth --account-id YOUR_ACCOUNT_ID
```

## Redirect URI Examples

### Valid Redirect URIs:

1. **Out-of-band (CLI)**
   ```
   urn:ietf:wg:oauth:2.0:oob
   ```

2. **Local development**
   ```
   http://localhost:8080/callback
   http://127.0.0.1:8080/callback
   ```

3. **Production web app**
   ```
   https://yourdomain.com/oauth/callback
   https://app.yourdomain.com/auth/callback
   ```

### Important Notes:

- ✅ Redirect URI is **case-sensitive**
- ✅ Must match **exactly** (including trailing slashes)
- ✅ For localhost, use `http://` (not `https://`)
- ✅ Custom domains must use `https://`
- ✅ You can register multiple redirect URIs for the same application

## Troubleshooting

### Error: "redirect_uri_mismatch"

**Problem**: The redirect URI in your request doesn't match what's registered.

**Solution**:
1. Check the redirect URI in your Basecamp integration settings
2. Ensure it matches exactly what you're using in the CLI
3. For OOB, use: `urn:ietf:wg:oauth:2.0:oob`

### Error: "invalid_client"

**Problem**: Client ID or Client Secret is incorrect.

**Solution**:
1. Verify your credentials in Basecamp integration settings
2. Re-run `basecamp configure` with correct credentials

### Authorization Code Not Working

**Problem**: Authorization code expires quickly or doesn't work.

**Solution**:
- Authorization codes expire after a few minutes
- Make sure you copy the **entire** code
- Paste it immediately after receiving it

## Where Credentials Are Stored

After running `basecamp configure`, your credentials are stored in:

**Location**: `~/.basecamp/config.json` (or `$HOME/.basecamp/config.json`)

**File Format**:
```json
{
  "oauth": {
    "client_id": "your_client_id_here",
    "client_secret": "your_client_secret_here",
    "redirect_uri": "urn:ietf:wg:oauth:2.0:oob"
  }
}
```

**Security**:
- File permissions: `600` (read/write for owner only)
- Stored in your home directory (not in the project)
- Excluded from git (via `.gitignore`)

**To view the config location**:
```bash
basecamp config-path
```

## Security Best Practices

1. **Never commit credentials**
   - Client Secret should never be in version control
   - Configuration is stored in `~/.basecamp/config.json` (excluded from git)
   - The `.gitignore` file excludes `.basecamp/` directory

2. **Use environment variables (optional)**
   - You can set credentials via environment variables:
     ```bash
     export BASECAMP_CLIENT_ID="your_client_id"
     export BASECAMP_CLIENT_SECRET="your_client_secret"
     ```

3. **Rotate credentials if compromised**
   - If credentials are exposed, regenerate them in Basecamp
   - Update CLI configuration with new credentials

## Additional Resources

- [Basecamp API Documentation](https://github.com/basecamp/api)
- [OAuth2 Specification](https://oauth.net/2/)
- [Basecamp Launchpad](https://launchpad.37signals.com/)
