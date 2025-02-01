import os
import base64
import json

# Load Firebase credentials from the environment variable
FIREBASE_CREDENTIALS_BASE64 = os.getenv("FIREBASE_CREDENTIALS")

if not FIREBASE_CREDENTIALS_BASE64:
    raise ValueError("Missing Firebase credentials in environment variables.")

# Decode the base64 string into JSON
FIREBASE_CREDENTIALS = json.loads(base64.b64decode(FIREBASE_CREDENTIALS_BASE64).decode())


# Game settings
MIN_NUMBER = 0
MAX_NUMBER = 100
DEFAULT_ROUNDS = 3  # Default to best of 3 rounds
