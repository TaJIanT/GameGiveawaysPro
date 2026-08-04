# -*- coding: utf-8 -*-
import threading
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw

def _default_image():
    import os, sys
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    icon_path = os.path.join(base_path, "icon.ico")
    if os.path.exists(icon_path):
        try:
            return Image.open(icon_path)
        except Exception:
            pass

    # Fallback (если файл случайно удален)
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((8, 8, 56, 56), fill=(0, 212, 170, 255))
    d.ellipse((22, 22, 42, 42), fill=(15, 20, 30, 255))
    return img

class TrayController:
    def __init__(self, app):
        self.app = app
        self.icon = None
        self.thread = None

    def start(self):
        if self.thread and self.thread.is_alive():
            return

        menu = pystray.Menu(
            item("Открыть", self.on_show),
            item("Обновить сейчас", self.on_refresh),
            item("Выход", self.on_exit),
        )
        self.icon = pystray.Icon("GameGiveawaysPro", _default_image(), "GameGiveawaysPro", menu)

        self.thread = threading.Thread(target=self.icon.run, daemon=True)
        self.thread.start()

    def stop(self):
        try:
            if self.icon:
                self.icon.stop()
        except Exception:
            pass

    def on_show(self, icon=None, item=None):
        # показать окно из потока трея -> через after
        self.app.after(0, self.app.show_window)

    def on_refresh(self, icon=None, item=None):
        self.app.after(0, lambda: self.app.refresh_games_async())

    def on_exit(self, icon=None, item=None):
        self.app.after(0, self.app.exit_app)
