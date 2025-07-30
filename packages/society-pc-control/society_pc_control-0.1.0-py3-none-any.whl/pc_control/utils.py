import json
import os

def load_json_file(path):
    if not os.path.exists(path):
        with open(path, 'w') as f:
            json.dump({}, f)
    with open(path, 'r') as f:
        return json.load(f)

def save_json_file(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def generate_token():
    import secrets
    return secrets.token_hex(16)
