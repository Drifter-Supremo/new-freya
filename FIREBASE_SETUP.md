# Firebase Setup Instructions

## Service Account Credentials

The Firebase service account credentials file is **NOT** included in this repository for security reasons.

### To set up Firebase integration:

1. **Download your Firebase service account credentials:**
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Select your project (`freya-ai-chat`)
   - Go to Project Settings > Service Accounts
   - Click "Generate new private key"
   - Save the downloaded JSON file

2. **Place the credentials file in the project root:**
   ```bash
   # The file should be named exactly:
   freya-ai-chat-firebase-adminsdk-fbsvc-0af7f65b8e.json
   
   # Or update the path in app/core/firebase_config.py if you use a different name
   ```

3. **Verify the file is ignored by git:**
   ```bash
   git status
   # The credentials file should NOT appear in git status
   ```

## Security Notes

- **NEVER** commit Firebase service account credentials to git
- Keep the credentials file local to your development environment
- For production deployments, use environment variables or secure secret management

## File Structure

Your project should have:
```
/Users/blackcanopy/Documents/Projects/new-freya-who-this/
├── freya-ai-chat-firebase-adminsdk-fbsvc-0af7f65b8e.json  # ← This file (not in git)
├── app/
├── scripts/
└── ...
```

## Testing

Once the credentials are in place, test the connection:
```bash
python scripts/test_firebase_connection.py
```