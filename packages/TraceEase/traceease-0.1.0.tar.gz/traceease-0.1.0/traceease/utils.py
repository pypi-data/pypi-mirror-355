import os
import json

def load_path(path):
        path = os.path.join(os.path.dirname(__file__), path)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)