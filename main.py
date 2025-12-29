# -*- coding: utf-8 -*-

from update_check import check_and_update

import customtkinter as ctk
import threading
from datetime import datetime, timezone

from config import THEMES, APP_TITLE
from api import GameAPI
from header import create_header
from tabs import create_tabs
from cards import create_game_card

from notifications import NotificationManager
from tray_icon import TrayController


def _parse_dt(value):
    if not value:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)

    s = str(value).strip()
    try:
        s2 = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s2)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        pass

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return None


def enrich_ending_flags(games, hours=24):
    now = datetime.now(timezone.utc)
    for g in games or []:
        end_raw = None
        for k in ("end_date", "endDate", "end_date_utc", "end_time", "endTime", "endtime", "expiry", "expires"):
            if g.get(k):
                end_raw = g.get(k)
                break

        dt = _parse_dt(end_raw)
        if dt:
            delta_h = (dt - now).total_seconds() / 3600.0
            g["ends_in_hours"] = round(delta_h, 2)
            g["ending_soon"] = (0 <= delta_h <= hours)
        else:
            g["ends_in_hours"] = None
            g["ending_soon"] = False
    return games


class GameGiveawaysApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        self.title(APP_TITLE)
        self.geometry("1800x1100")
        self.configure(fg_color=THEMES["dark"]["bg"])

        self.api = GameAPI(usegamerpower=True)
        self.games = {}
        self._loading = False

        # уведомления (окна)
        self.notification_manager = NotificationManager(parent=self)
        self.first_load = True

        # трей
        self.tray = TrayController(self)
        self.tray.start()

        # крестик -> скрыть в трей
        try:
            self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        except Exception:
            pass

        # UI
        self.header, self.status_label, self.refresh_btn, self.progress = create_header(
            self, self.refresh_games_async
        )
        self.tabview, self.tab_frames = create_tabs(self)

        # автообновление каждые 30 минут
        self._schedule_auto_refresh()

        self.refresh_games_async(first_start=True)

    # header.py вызывает это по чекбоксу
    def on_toggle_gamerpower(self):
        try:
            self.api.set_use_gamerpower(bool(self.gp_var.get()))
        except Exception:
            pass
        self.refresh_games_async()

    # tray_icon.py вызывает это через after
    def show_window(self):
        try:
            self.deiconify()
            self.lift()
            self.focus_force()
        except Exception:
            pass

    def exit_app(self):
        try:
            self.tray.stop()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass

    def hide_to_tray(self):
        try:
            self.withdraw()
        except Exception:
            pass

    def _schedule_auto_refresh(self):
        try:
            self.after(30 * 60 * 1000, self._auto_refresh_tick)
        except Exception:
            pass

    def _auto_refresh_tick(self):
        try:
            self.refresh_games_async()
        finally:
            self._schedule_auto_refresh()

    def set_loading(self, value: bool):
        self._loading = value
        if value:
            self.status_label.configure(text="Обновляем")
            self.refresh_btn.configure(state="disabled")
            self.progress.pack(fill="x")
            self.progress.start()
        else:
            self.refresh_btn.configure(state="normal")
            try:
                self.progress.stop()
            except Exception:
                pass
            self.progress.pack_forget()
            self.progress.set(0)

    def refresh_games_async(self, first_start=False):
        if self._loading:
            return
        self.set_loading(True)
        threading.Thread(target=self.load_games, daemon=True).start()

    def load_games(self):
        try:
            all_games = self.api.fetch_all_games(limit=40)

            # пометка "скоро закончится"
            enrich_ending_flags(all_games, hours=24)

            # уведомления о новых FREE
            if not self.first_load:
                free_games = [g for g in all_games if (g.get("price") or "").strip().upper() == "FREE"]
                new_games = self.notification_manager.check_new_games(free_games)
                if new_games:
                    self.notification_manager.notify_new_games(new_games, max_notifications=3)
            else:
                self.notification_manager.mark_as_seen(all_games)

            self.first_load = False
            self.games = self.distribute_games(all_games)
            self.after(0, lambda: self.on_games_loaded(len(all_games)))

        except Exception as e:
            print("ERROR:", e)
            self.after(0, self.on_games_error)

    def on_games_loaded(self, count):
        self.render_all_games()
        self.status_label.configure(text=f"Обновлено: {count} игр")
        self.set_loading(False)

    def on_games_error(self):
        self.status_label.configure(text="Ошибка обновления")
        self.set_loading(False)

    def distribute_games(self, games):
        discounts, freebies = [], []
        for g in games:
            price = (g.get("price") or "").strip().upper()
            (discounts if (price and price != "FREE") else freebies).append(g)

        distributed = {"all": freebies[:40]}
        distributed["steam"] = [g for g in freebies if (g.get("platformkey") or "").lower() == "steam"][:40]
        distributed["epic"] = [g for g in freebies if (g.get("platformkey") or "").lower() == "epicgames"][:40]
        distributed["gog"] = [g for g in freebies if (g.get("platformkey") or "").lower() == "gog"][:40]
        distributed["deals"] = discounts[:80]
        return distributed

    def render_all_games(self):
        for key, games_list in self.games.items():
            frame = self.tab_frames.get(key)
            if frame is not None:
                self.render_games(frame, games_list)

    def render_games(self, frame, games):
        for widget in frame.winfo_children():
            widget.destroy()

        if not games:
            ctk.CTkLabel(
                frame,
                text="Ничего не найдено",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=THEMES["dark"]["text_secondary"],
            ).pack(expand=True, pady=50)
            return

        for game in games:
            create_game_card(frame, game, self.show_details)

    def show_details(self, game):
        win = ctk.CTkToplevel(self)
        win.title(game.get("title", "Подробнее"))
        win.geometry("980x720")
        win.configure(fg_color=THEMES["dark"]["bg"])

        right = ctk.CTkFrame(win, fg_color="#181820", corner_radius=8)
        right.pack(fill="both", expand=True, padx=20, pady=20)
        right.grid_columnconfigure(0, weight=1)

        title = game.get("title", "Unknown")
        platform = game.get("platform", "")

        header = ctk.CTkLabel(
            right,
            text=f"{title} [{platform}]" if platform else title,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=THEMES["dark"]["text"],
        )
        header.grid(row=0, column=0, sticky="w", pady=(0, 6))

        price = (game.get("price") or "FREE").strip()
        price_show = "Бесплатно" if price.upper() == "FREE" else price
        info = f"{price_show} {game.get('source','')}".strip(" ")

        ctk.CTkLabel(
            right,
            text=info,
            font=ctk.CTkFont(size=13),
            text_color=THEMES["dark"]["text_secondary"],
        ).grid(row=1, column=0, sticky="w", pady=(0, 10))

        desc = game.get("description", "Описания нет.")
        link = (game.get("link") or "").strip()

        textbox = ctk.CTkTextbox(
            right,
            width=540,
            height=470,
            fg_color="#111111",
            text_color=THEMES["dark"]["text"],
            font=ctk.CTkFont(size=13),
            wrap="word",
        )
        textbox.grid(row=2, column=0, sticky="nsew")
        textbox.insert("1.0", desc + (f"\n\nСсылка: {link}" if link else ""))
        textbox.configure(state="disabled")

        btn_row = ctk.CTkFrame(right, fg_color="transparent")
        btn_row.grid(row=3, column=0, sticky="e", pady=(12, 0))

        if link:
            ctk.CTkButton(
                btn_row,
                text="Открыть в браузере",
                fg_color=THEMES["dark"]["primary"],
                hover_color="#00dd6f",
                command=lambda: __import__("webbrowser").open(link),
            ).pack(side="right", padx=(0, 10))

        ctk.CTkButton(
            btn_row,
            text="Закрыть",
            fg_color="#444444",
            hover_color="#666666",
            command=win.destroy,
        ).pack(side="right")


if __name__ == "__main__":
    import sys

    try:
        if check_and_update():
            sys.exit(0)
    except Exception:
        pass

    app = GameGiveawaysApp()
    app.mainloop()

