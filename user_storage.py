import json
import os

USERS_FILE = "users.json"

def load_users():
    """
    Load user IDs from a JSON file.
    Returns a set of user IDs.
    """
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                users_list = json.load(f)
                return set(users_list)
        except Exception:
            return set()
    return set()

def save_users(users):
    """
    Save user IDs (set) to a JSON file.
    """
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(list(users), f)
    except Exception as e:
        print(f"Error saving users: {e}")
