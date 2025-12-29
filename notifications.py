# -*- coding: utf-8 -*-

import json
import os
import threading
import tkinter as tk
import webbrowser
from datetime import datetime, timezone


class NotificationManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.history_file = "notification_history.json"
        self.seen = self._load_seen()  # dict: game_id -> first_seen_ts

    def _now_ts(self) -> int:
        return int(datetime.now(timezone.utc).timestamp())

    def _load_seen(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                seen_map = data.get("seen_map")
                if isinstance(seen_map, dict):
                    out = {}
                    for k, v in seen_map.items():
                        try:
                            out[str(k)] = int(v)
                        except Exception:
                            pass
                    return out

                seen_list = data.get("seen", [])
                if isinstance(seen_list, list):
                    now = self._now_ts()
                    return {str(gid): now for gid in seen_list}
        except Exception:
            pass
        return {}

    def _save_seen(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump({"seen_map": self.seen}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _game_id(self, game: dict) -> str:
        title = (game.get("title") or "").strip().lower()
        platform = (game.get("platform") or game.get("platformkey") or "").strip().lower()
        link = (game.get("link") or "").strip().lower()
        return link if link else f"{title}|{platform}"

    def first_seen_ts(self, game: dict):
        return self.seen.get(self._game_id(game))

    def mark_as_seen(self, games):
        now = self._now_ts()
        for g in games or []:
            gid = self._game_id(g)
            if gid not in self.seen:
                self.seen[gid] = now
        self._save_seen()

    def get_new_freebies(self, games):
        new_items = []
        now = self._now_ts()
        for g in games or []:
            price = (g.get("price") or "").strip().upper()
            if price != "FREE":
                continue
            gid = self._game_id(g)
            if gid not in self.seen:
                new_items.append(g)
                self.seen[gid] = now
        if new_items:
            self._save_seen()
        return new_items

    def notify(self, new_games, max_items=3):
        if not new_games:
            return
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONINFORMATION)
        except Exception:
            pass

        open_url = ""
        for g in new_games:
            link = (g.get("link") or "").strip()
            if link:
                open_url = link
                break

        if self.parent is None:
            for g in new_games[:max_items]:
                print("NEW FREE:", g.get("title"), g.get("platform"), g.get("link"))
            if open_url:
                print("OPEN:", open_url)
            return

        lines = []
        for g in new_games[:max_items]:
            t = (g.get("title") or "Новая раздача").strip()
            p = (g.get("platform") or "").strip()
            lines.append(f" {t}" + (f" [{p}]" if p else ""))

        extra = ""
        if len(new_games) > max_items:
            extra = f"\nи ещё {len(new_games) - max_items}"

        text = "Появились новые раздачи:\n" + "\n".join(lines) + extra

        def _show():
            win = tk.Toplevel(self.parent)
            win.title("GameGiveawaysPro  уведомление")
            win.attributes("-topmost", True)
            win.resizable(False, False)

            sw = win.winfo_screenwidth()
            x = sw - 440
            y = 80
            win.geometry(f"420x240+{max(x,0)}+{y}")

            frame = tk.Frame(win, bg="#101018")
            frame.pack(fill="both", expand=True)

            lbl = tk.Label(
                frame, text=text, bg="#101018", fg="#e8e8ff",
                justify="left", anchor="nw", font=("Segoe UI", 10), wraplength=400
            )
            lbl.pack(fill="both", expand=True, padx=10, pady=(10, 6))

            btns = tk.Frame(frame, bg="#101018")
            btns.pack(fill="x", padx=10, pady=(0, 10))

            def do_open():
                if open_url:
                    webbrowser.open(open_url)
                win.destroy()

            if open_url:
                tk.Button(btns, text="Открыть", command=do_open).pack(side="left")
            tk.Button(btns, text="Закрыть", command=win.destroy).pack(side="right")

            win.after(9000, win.destroy)

        try:
            self.parent.after(0, _show)
        except Exception:
            threading.Thread(target=_show, daemon=True).start()

    # aliases for main.py compatibility
    def check_new_games(self, games):
        return self.get_new_freebies(games)

    def notify_new_games(self, new_games, max_notifications=3):
        return self.notify(new_games, max_items=max_notifications)
