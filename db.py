import json
import os

DB_FILE = "users.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_user_buffer(user_id, api_key, profile_id):
    db = load_db()
    db[str(user_id)] = {
        "buffer_api_key": api_key,
        "buffer_profile_id": profile_id
    }
    save_db(db)

def get_user_buffer(user_id):
    db = load_db()
    return db.get(str(user_id))

def delete_user_buffer(user_id):
    db = load_db()
    if str(user_id) in db:
        del db[str(user_id)]
        save_db(db)