import json

def load_settings(filePath='Pi1/settings.json'):
    with open(filePath, 'r') as f:
        return json.load(f)