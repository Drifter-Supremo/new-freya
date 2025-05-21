"""
firebase_config.py - Configuration for Firebase/Firestore integration
"""

import os
import json
from typing import Dict, Any, Optional

# Firebase configuration
FIREBASE_CONFIG = {
    "apiKey": os.environ.get("FIREBASE_API_KEY", "AIzaSyCgy0INKpZMjeNltKCXkoiJoTNWVmlS9EA"),
    "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN", "freya-ai-chat.firebaseapp.com"),
    "projectId": os.environ.get("FIREBASE_PROJECT_ID", "freya-ai-chat"),
    "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET", "freya-ai-chat.firebasestorage.app"),
    "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID", "741580038310"),
    "appId": os.environ.get("FIREBASE_APP_ID", "1:741580038310:web:72df27b8b5bac53c70d467")
}

# Service account credentials path
SERVICE_ACCOUNT_PATH = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH", "/Users/blackcanopy/Documents/Projects/new-freya-who-this/freya-ai-chat-firebase-adminsdk-fbsvc-0af7f65b8e.json")

# Firestore collection names
COLLECTIONS = {
    "users": "users",
    "conversations": "conversations",
    "messages": "messages",
    "user_facts": "userFacts",
    "topics": "topics"
}

def get_service_account_credentials() -> Optional[Dict[str, Any]]:
    """
    Get Firebase service account credentials from environment or file.
    
    Returns:
        Dictionary with service account credentials if available, None otherwise
    """
    # First, check if credentials are provided as a JSON string in environment
    if service_account_json := os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON"):
        try:
            return json.loads(service_account_json)
        except json.JSONDecodeError:
            pass
    
    # Next, check if a path to a credentials file is provided
    if SERVICE_ACCOUNT_PATH and os.path.exists(SERVICE_ACCOUNT_PATH):
        try:
            with open(SERVICE_ACCOUNT_PATH, 'r') as f:
                creds = json.load(f)
                
                # Fix private key if it contains literal \n
                if "private_key" in creds and creds["private_key"]:
                    # Replace literal \n with actual newlines if needed
                    if "\\n" in creds["private_key"] and "\n" not in creds["private_key"]:
                        creds["private_key"] = creds["private_key"].replace("\\n", "\n")
                
                return creds
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading credentials file: {e}")
            pass
    
    # Return None if no valid credentials are found
    return None