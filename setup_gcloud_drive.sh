#!/usr/bin/env bash
#./setup_gcloud_drive.sh "My Project2" "nizar.ajroud@gmail.com"    
# Parameters
PROJECT_NAME=${1:-"Drive API Project"}
EMAIL=${2:-""}
MY_SECRETS_FILES_PATH="/home/nizar/my-secrets-files"

# Generate credentials filename from email
if [ -n "$EMAIL" ]; then
    EMAIL_PREFIX=$(echo "$EMAIL" | cut -d'@' -f1 | tr '.' '-')
    CREDENTIALS_FILENAME="${EMAIL_PREFIX}-gdrive-creds.json"
else
    CREDENTIALS_FILENAME="drive-credentials.json"
fi
CREDENTIALS_PATH=${3:-"$MY_SECRETS_FILES_PATH/$CREDENTIALS_FILENAME"}

# Authenticate
gcloud auth login

# Create project
PROJECT_ID="drive-api-$(openssl rand -hex 3)"
gcloud projects create $PROJECT_ID --name="$PROJECT_NAME"
gcloud config set project $PROJECT_ID

# Enable Drive API
gcloud services enable drive.googleapis.com

# Get project ID
PROJECT_ID=$(gcloud config get-value project)

# Create service account
gcloud iam service-accounts create drive-service \
    --display-name="$PROJECT_NAME"

# Create and download OAuth key (Desktop Application)
echo "Creating OAuth 2.0 credentials (Desktop Application)..."
echo "Opening Google Cloud Console credentials page..."

# Open the credentials page in browser with incognito
if command -v xdg-open > /dev/null; then
    xdg-settings set default-web-browser google-chrome.desktop
    google-chrome --incognito "https://console.cloud.google.com/apis/credentials?project=${PROJECT_ID}" 2>/dev/null || xdg-open "https://console.cloud.google.com/apis/credentials?project=${PROJECT_ID}"
elif command -v open > /dev/null; then
    open -a "Google Chrome" --args --incognito "https://console.cloud.google.com/apis/credentials?project=${PROJECT_ID}"
else
    echo "Please open: https://console.cloud.google.com/apis/credentials?project=${PROJECT_ID}"
fi

echo ""
echo "MANUAL STEPS REQUIRED:"
echo "1. Click 'Create Credentials' > 'OAuth 2.0 Client IDs'"
echo "2. Choose 'Desktop application'"
echo "3. Download the JSON file and save it as: $CREDENTIALS_PATH"
echo ""
echo "Note: OAuth credentials cannot be created via CLI - manual web console step required."
echo "Project ID: $PROJECT_ID"
