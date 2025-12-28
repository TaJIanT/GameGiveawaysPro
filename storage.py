# -*- coding: utf-8 -*-
import json
import os

class Storage:
    def __init__(self):
        self.favorites_file = "favorites.json"

    def load_favorites(self):
        try:
            if os.path.exists(self.favorites_file):
                with open(self.favorites_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except:
            pass
        return []

    def save_favorites(self, favorites):
        try:
            with open(self.favorites_file, "w", encoding="utf-8") as f:
                json.dump(favorites, f, ensure_ascii=False, indent=2)
        except:
            pass
