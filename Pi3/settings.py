import json

def load_settings(filePath='Pi3/settings.json'):
    with open(filePath, 'r') as f:
        return json.load(f)