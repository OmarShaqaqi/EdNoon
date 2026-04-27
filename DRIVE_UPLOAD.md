# Google Drive Upload

The pipeline can upload facilitator-specific CSVs to a Google Drive folder watched by Zapier.

For a normal personal **My Drive** folder, use OAuth user auth. Service accounts have no storage quota for My Drive uploads.

## One-Time Setup

## Recommended: OAuth User Upload

1. Create or choose a Google Cloud project.
2. Enable the Google Drive API.
3. Configure OAuth consent screen.
4. Create OAuth Client ID credentials for a Desktop app.
5. Download the OAuth client JSON.

`.env`:

```text
GOOGLE_OAUTH_CLIENT_SECRET=/absolute/path/to/oauth-client.json
GOOGLE_OAUTH_TOKEN=token.json
GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id
OPENAI_API_KEY=your_openai_key
```

On the first run, your browser opens and asks you to authorize Drive access. The token is saved to `token.json` for future runs.

## Alternative: Service Account With Shared Drive

Service accounts can work if you upload into a Google Shared Drive or use domain-wide delegation. For normal My Drive folders, use OAuth above.

For service account mode, set:

```text
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service-account.json
GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id
```

## Install Dependencies

```bash
.venv/bin/pip install -r requirements.txt
```

## Run With Upload

Create a `.env` file:

```text
GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id
GOOGLE_OAUTH_CLIENT_SECRET=/absolute/path/to/oauth-client.json
GOOGLE_OAUTH_TOKEN=token.json
OPENAI_API_KEY=your_openai_key
```

Then run:

```bash
.venv/bin/python run_pipeline.py --as-of 2025-10-14 --upload-drive
```

You can also pass values directly:

```bash
.venv/bin/python run_pipeline.py \
  --as-of 2025-10-14 \
  --upload-drive \
  --drive-folder-id "your_drive_folder_id" \
  --drive-service-account "/absolute/path/to/service-account.json"
```

## What Gets Uploaded

Only the facilitator-specific CSVs are uploaded:

```text
outputs/interventions/facilitators/*.csv
```

Zapier can trigger on each new CSV file in that Drive folder, copy the Google Sheet template, insert rows, and email the facilitator.
