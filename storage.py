# -*- coding: utf-8 -*-
import json
import os
import sys

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "autorun": False,
    "start_minimized": False,
    "minimize_to_tray": True,
    "sound_notifications": True,
    "auto_refresh_enabled": True,
    "auto_refresh_interval": 30,
    "platforms": {
        "steam": True,
        "epic": True,
        "gog": True,
        "loot": True
    },
    "hide_welcome": False
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = DEFAULT_SETTINGS.copy()
            merged.update(data)
            return merged
    except Exception:
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        set_windows_autorun(settings.get("autorun", False))
    except Exception as e:
        print("Save settings error:", e)

def set_windows_autorun(enable: bool):
    if sys.platform != "win32":
        return
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_ALL_ACCESS
        )
        app_name = "GameGiveawaysPro"
        if enable:
            if getattr(sys, 'frozen', False):
                exe_path = f'"{sys.executable}" --minimized'
            else:
                script_path = os.path.abspath(sys.argv[0])
                exe_path = f'"{sys.executable}" "{script_path}" --minimized'
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        print("Autorun error:", e)