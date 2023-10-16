import json
import os

with open(os.path.join(os.getcwd(), 'config', 'config.json'), 'r', encoding='utf-8') as f:
    config_file = json.load(f)
