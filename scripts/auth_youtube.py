"""
scripts/auth_youtube.py
Run this script locally to complete the Google OAuth2 authentication flow.
Outputs a 'token.json' file containing your OAuth2 refresh token.
Save the contents of client_secret.json and token.json to GitHub Secrets
to enable headless uploads via GitHub Actions.
"""

import os
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

# Request full YouTube access scope
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]


def main():
    client_secret_file = Path("client_secret.json")
    token_file = Path("token.json")

    if not client_secret_file.exists():
        print("[-] Error: client_secret.json not found in current directory!")
        print("Please download it from the Google Cloud Console:")
        print("1. Go to console.cloud.google.com")
        print("2. Enable YouTube Data API v3")
        print("3. Go to Credentials -> Create Credentials -> OAuth Client ID (Desktop App)")
        print("4. Download the JSON, rename it to client_secret.json, and put it here.")
        return

    print("[+] Found client_secret.json. Starting local OAuth flow...")
    
    # Initialize the OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(
        str(client_secret_file),
        scopes=SCOPES
    )

    # Run local webserver to authenticate user
    creds = flow.run_local_server(
        port=8080,
        prompt="consent",
        authorization_prompt_message="Please visit this URL to authorize the app:"
    )

    # Save credentials (including refresh token)
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes
    }

    with open(token_file, "w") as f:
        json.dump(token_data, f, indent=2)

    print("[+] Success! Created token.json.")
    print("\n=== SETUP INFORMATION ===")
    print("To configure GitHub Actions, add these repository secrets:")
    print("1. YOUTUBE_CLIENT_ID:     ", creds.client_id)
    print("2. YOUTUBE_CLIENT_SECRET: ", creds.client_secret)
    print("3. YOUTUBE_REFRESH_TOKEN: ", creds.refresh_token)
    print("=========================")


if __name__ == "__main__":
    main()
