# Setup Guide: Automated YouTube Channel Pipeline

This guide walks you through setting up credentials, authenticating with YouTube Data API v3, and configuring GitHub Actions.

---

## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g. `Automated Youtube Channel`).
3. Search for **YouTube Data API v3** in the search bar at the top and click **Enable**.

---

## Step 2: Configure OAuth Consent Screen

1. In the left sidebar, navigate to **APIs & Services** > **OAuth consent screen**.
2. Select **External** and click **Create**.
3. Fill out the required App Information (App name, support email, developer email).
4. Click **Save and Continue** until you reach **Test users**.
5. Under **Test users**, click **ADD USERS** and enter your YouTube Channel's Google account email. Click **Save**.
6. **Important**: Keep the Publishing status as **Testing**. This allows you to log in without submitting the app for Google's official verification process.

---

## Step 3: Create OAuth Client Credentials

1. Navigate to **APIs & Services** > **Credentials**.
2. Click **+ CREATE CREDENTIALS** at the top and select **OAuth client ID**.
3. Set Application Type to **Desktop app**.
4. Give it a name (e.g., `YT Uploader CLI`) and click **Create**.
5. Download the credentials JSON: click the download icon next to your client ID.
6. Rename this file to `client_secret.json` and place it in the root folder of this repository on your local computer.

---

## Step 4: Generate Refresh Token (Run Locally)

Since GitHub Actions runs headlessly, we must authenticate once locally to generate a persistent **refresh token**.

1. Open a terminal in this project directory on your local machine.
2. Install the OAuth helper libraries:
   ```bash
   pip install google-auth-oauthlib
   ```
3. Run the authentication script:
   ```bash
   python scripts/auth_youtube.py
   ```
4. This opens a browser window. Sign in with the Google Account that owns your YouTube channel.
5. Click **Advanced** > **Go to ... (unsafe)** to bypass the warning.
6. Check the box to grant full YouTube API permissions, then click **Continue**.
7. Close the browser tab. The script will save your credentials to `token.json` and output the values you need to configure in GitHub.

---

## Step 5: Save Secrets on GitHub

1. Go to your GitHub repository.
2. Navigate to **Settings** > **Secrets and variables** > **Actions**.
3. Click **New repository secret** for each of the following:

| Secret Name | Value Location / Instructions |
| :--- | :--- |
| `YOUTUBE_CLIENT_ID` | From console output or `client_id` inside `token.json` |
| `YOUTUBE_CLIENT_SECRET` | From console output or `client_secret` inside `token.json` |
| `YOUTUBE_REFRESH_TOKEN` | From console output or `refresh_token` inside `token.json` |
| `OPENAI_API_KEY` | Create a key at [platform.openai.com](https://platform.openai.com) |
| `ELEVENLABS_API_KEY` | *(Optional)* From profile page on [elevenlabs.io](https://elevenlabs.io) |

---

## Step 6: Test and Enable Pipeline

1. In your GitHub repository, click the **Actions** tab.
2. Select **Test Video Rendering Pipeline (Dry Run)** in the left menu.
3. Click **Run workflow** > **Run workflow**.
4. Once completed, inspect the `test-assets` artifact folder to verify text readability, subtitle speed, and overall aesthetics.
5. Now, the daily cron schedule in `.github/workflows/daily_short.yml` will automatically post content. You can manually run it via `Daily Automated YouTube Shorts Upload` > **Run workflow** anytime.
