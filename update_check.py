# -*- coding: utf-8 -*-

import json
import urllib.request
import urllib.error

from config import APP_VERSION

GITHUB_OWNER = "TaJIanT"
GITHUB_REPO = "GameGiveawaysPro"
RELEASES_LATEST_URL = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"


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

    while len(parts) < 4:
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


def check_update_info():
    """
    Returns dict:
      {
        "has_update": bool,
        "current": APP_VERSION,
        "latest": remote_tag|None,
        "url": RELEASES_LATEST_URL
      }
    Never raises; on any error -> has_update False.
    """
    try:
        data = _gh_latest_release()
        remote_tag = (data.get("tag_name") or "").strip()
        has_update = _ver_tuple(remote_tag) > _ver_tuple(APP_VERSION)
        return {
            "has_update": bool(has_update),
            "current": APP_VERSION,
            "latest": remote_tag or None,
            "url": RELEASES_LATEST_URL,
        }
    except Exception:
        return {
            "has_update": False,
            "current": APP_VERSION,
            "latest": None,
            "url": RELEASES_LATEST_URL,
        }
