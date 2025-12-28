# -*- coding: utf-8 -*-

import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import urllib.error

from config import APP_VERSION

GITHUB_OWNER = "TaJIanT"
GITHUB_REPO = "GameGiveawaysPro"

ASSET_NAME_MAIN = "GameGiveawaysPro.exe"
ASSET_NAME_UPDATER = "updater.exe"


def _ver_tuple(v: str):
    v = (v or "").strip()
    if v.startswith("v"):
        v = v[1:]
    parts = []
    for x in v.split("."):
        try:
            parts.append(int(x))
        except Exception:
            parts.append(0)
    return tuple(parts)


def _gh_latest_release():
    api = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
    req = urllib.request.Request(
        api,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "GameGiveawaysPro",
        },
    )
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.loads(r.read().decode("utf-8", errors="ignore"))


def check_and_update():
    # обновляем только собранный exe
    if not getattr(sys, "frozen", False):
        return False

    try:
        data = _gh_latest_release()
    except urllib.error.HTTPError as e:
        # Частый случай: 404 если в репозитории ещё нет ни одного Release.
        # В этом случае просто запускаем приложение без обновления.
        if getattr(e, "code", None) == 404:
            return False
        return False
    except urllib.error.URLError:
        # нет интернета / DNS / таймаут
        return False
    except Exception:
        return False

    remote_tag = data.get("tag_name") or ""
    if _ver_tuple(remote_tag) <= _ver_tuple(APP_VERSION):
        return False

    assets = data.get("assets") or []

    def find_asset(name):
        return next((a for a in assets if a.get("name") == name), None)

    a_main = find_asset(ASSET_NAME_MAIN)
    a_upd = find_asset(ASSET_NAME_UPDATER)
    if not a_main or not a_upd:
        return False

    url_main = a_main.get("browser_download_url")
    url_upd = a_upd.get("browser_download_url")
    if not url_main or not url_upd:
        return False

    current_exe = os.path.abspath(sys.executable)
    app_dir = os.path.dirname(current_exe)

    # updater лежит рядом с приложением; если нет  скачиваем во временную папку
    updater_path = os.path.join(app_dir, ASSET_NAME_UPDATER)
    if not os.path.exists(updater_path):
        tmp = os.path.join(tempfile.gettempdir(), ASSET_NAME_UPDATER)
        try:
            urllib.request.urlretrieve(url_upd, tmp)
            updater_path = tmp
        except Exception:
            return False

    subprocess.Popen([updater_path, current_exe, url_main], close_fds=True)
    return True
