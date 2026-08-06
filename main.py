# -*- coding: utf-8 -*-
# --- early self-update (must be before any heavy imports) ---
try:
    from update_check import check_and_update
    import sys
    if check_and_update():
        raise SystemExit(0)
except Exception:
    pass
# -----------------------------------------------------------

import sys
import customtkinter as ctk
import threading

from config import THEMES, APP_TITLE
from api import GameAPI
from header import create_header
from tabs import create_tabs, LABELS
from cards import create_game_card
from tray_icon import TrayController
from notifications import NotificationManager
from storage import load_settings
from update_check import check_update_info
from welcome import SplashScreen
from settings_win import SettingsWindow

class GameGiveawaysApp(ctk.CTk):
    def resource_path(self, relative_path):
        import os, sys
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def __init__(self):
        super().__init__()
        
        self.settings = load_settings()

        ctk.set_appearance_mode("dark")
        self.title(APP_TITLE)
        try:
            self.iconbitmap(self.resource_path("icon.ico"))
        except Exception:
            pass
        self.geometry("1800x1100")
        self.configure(fg_color=THEMES["dark"]["bg"])

        self.api = GameAPI(usegamerpower=True)
        self.gp_var = ctk.IntVar(value=1)  # ВЕРНУЛИ ПЕРЕМЕННУЮ ДЛЯ ГАЛОЧКИ
        
        # Инициализируем хранилище для всех вкладок
        self.games = {key: [] for _, key in LABELS}
        self.loaded_tabs = {key: False for _, key in LABELS} # Флаги для "ленивой загрузки"
        
        self._loading = False

        self.notification_manager = NotificationManager(parent=self)
        self.first_load = True
        
        self.tray = TrayController(self)
        self.tray.start()

        try:
            self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        except Exception:
            pass

        self.header, self.status_label, self.refresh_btn, self.progress = create_header(
            self, self.refresh_games_async
        )

        # Передаем on_tab_changed для обработки кликов по вкладкам
        self.tabview, self.tab_frames = create_tabs(self, on_tab_change=self.on_tab_changed)

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            self.nav_frame,
            textvariable=self.search_var,
            placeholder_text="🔍 Поиск игр...",
            width=250,
            height=28,
            border_width=0,
            fg_color="#1a2235",
            text_color="white"
        )
        self.search_entry.pack(side="right", padx=14, pady=3)
        self.search_var.trace_add("write", lambda *args: self.render_all_games())

        self.savings_label = ctk.CTkLabel(self.nav_frame, text="", font=ctk.CTkFont(size=14, weight="bold"), text_color="#00dd6f")
        self.savings_label.pack(side="left", padx=14)

    def open_settings(self):
        SettingsWindow(self, on_save_callback=self.on_settings_saved)

    def on_settings_saved(self, new_settings):
        self.settings = new_settings
        self.refresh_games_async()

    # ВЕРНУЛИ ФУНКЦИЮ ДЛЯ ГАЛОЧКИ GAMERPOWER
    def on_toggle_gamerpower(self):
        self.api.set_use_gamerpower(bool(self.gp_var.get()))
        self.refresh_games_async()

    def set_loading(self, value: bool):
        self._loading = value
        if value:
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

    def auto_refresh(self):
        if self.settings.get("auto_refresh_enabled", True):
            self.refresh_games_async()
            
        interval_mins = self.settings.get("auto_refresh_interval", 30)
        self.after(interval_mins * 60000, self.auto_refresh)

    def refresh_games_async(self, first_start=False):
        if self._loading:
            return
        self.set_loading(True)
        # Сбрасываем флаги загрузки: заставляем прогу обновить вкладки при следующем клике
        self.loaded_tabs = {key: False for _, key in LABELS}
        threading.Thread(target=self.load_games, daemon=True).start()

    def on_tab_changed(self, key):
        # Если вкладка еще не загружена - грузим её (Lazy Load)
        if not self.loaded_tabs.get(key, False):
            if key in ["vkplay", "roblox", "mobile"]:
                threading.Thread(target=self.load_lazy_tab, args=(key,), daemon=True).start()

    def load_lazy_tab(self, key):
        if self._loading: return
        self.set_loading(True)
        
        names = {"vkplay": "VK Play", "roblox": "Roblox", "mobile": "Мобилки"}
        self.after(0, lambda: self.status_label.configure(text=f"Загрузка: {names.get(key)}..."))
        
        try:
            if key == "vkplay":
                data = self.api.fetch_vkplay_discounts(limit=25)
            elif key == "roblox":
                data = self.api.fetch_roblox_loot(limit=25)
            elif key == "mobile":
                data = self.api.fetch_gacha_mobile_loot(limit=25)
            else:
                data = []

            self.games[key] = data
            self.loaded_tabs[key] = True
            
            # Отрисовываем только эту вкладку
            self.after(0, lambda: self.render_games(self.tab_frames[key], data))
            self.after(0, lambda: self.status_label.configure(text="Успешно обновлено"))
        except Exception as e:
            print(f"Lazy load error ({key}):", e)
            self.after(0, self.on_games_error)
        finally:
            self.after(0, lambda: self.set_loading(False))

    def load_games(self):
        try:
            # Очищаем только базовые ПК-вкладки
            for k in ["all", "steam", "epic", "deals", "loot"]:
                self.games[k] = []
                
            self.after(0, self.render_all_games)
            all_games = []

            tasks = [
                ("Загрузка: Бесплатные...", lambda: self.api.fetch_cheapshark_free(12)),
                ("Загрузка: PC (Steam, Epic, GOG)...", lambda: getattr(self.api, 'fetch_gamerpower_pc', lambda x: getattr(self.api, 'fetch_gamerpower_steam', lambda y: [])(x))(15) if self.api.usegamerpower else []),
                ("Загрузка: Ключи...", lambda: self.api.fetch_gamerpower_loot(15)),
                ("Загрузка: Скидки...", lambda: self.api.fetch_cheapshark_discounts(35))
            ]

            for msg, func in tasks:
                self.after(0, lambda m=msg: self.status_label.configure(text=m))
                try:
                    chunk = func()
                    all_games.extend(chunk)
                    self.distribute_and_render(chunk)
                except Exception as e:
                    print("Task error:", e)

            # Отмечаем базовые вкладки как загруженные
            for k in ["all", "steam", "epic", "deals", "loot"]:
                self.loaded_tabs[k] = True

            try:
                if not self.first_load:
                    free_games = [g for g in all_games if (g.get("price") or "").strip().upper() == "FREE"]
                    new_games = self.notification_manager.check_new_games(free_games)
                    if new_games and self.settings.get("auto_refresh_enabled", True): 
                        self.notification_manager.notify_new_games(new_games, 3)
                else:
                    self.notification_manager.mark_as_seen(all_games)
                    self.first_load = False
            except: pass

            self.after(0, lambda: self.on_games_loaded(len(all_games)))
        except Exception as e:
            print("ERROR:", e)
            self.after(0, self.on_games_error)

    def distribute_and_render(self, chunk):
        platforms_cfg = self.settings.get("platforms", {})
        steam_en = platforms_cfg.get("steam", True)
        epic_en = platforms_cfg.get("epic", True)
        loot_en = platforms_cfg.get("loot", True)

        for g in chunk:
            platkey = (g.get("platformkey") or "").lower()
            genre = (g.get("genre") or "").lower()
            source = (g.get("source") or "").lower()
            title = (g.get("title") or "").lower()
            
            is_steam = "steam" in platkey or "steam" in source or "steam" in title
            is_epic = "epic" in platkey or "epic" in source or "epic" in title
            is_loot = genre == "loot" or platkey == "loot" or "loot" in source

            if is_steam and not steam_en: continue
            if is_epic and not epic_en: continue
            if is_loot and not loot_en: continue

            price = (g.get("price") or "").strip().upper()
            if price and price != "FREE":
                if g not in self.games["deals"]: self.games["deals"].append(g)
            else:
                if g not in self.games["all"]: self.games["all"].append(g)
                if is_steam and g not in self.games["steam"]: self.games["steam"].append(g)
                elif is_epic and g not in self.games["epic"]: self.games["epic"].append(g)
                if is_loot and g not in self.games["loot"]: self.games["loot"].append(g)
        
        self.after(0, self.render_all_games)

    def on_games_loaded(self, count):
        self.render_all_games()
        self.status_label.configure(text=f"Обновлено: {count} шт.")
        self.set_loading(False)
        if hasattr(self, 'savings_label'):
            total = sum(float(g.get("worth", 0)) for g in self.games.get("all", []) if str(g.get("price", "")).strip().upper() == "FREE")
            self.savings_label.configure(text=f"🔥 Вы экономите: ${total:.2f}" if total > 0 else "")

    def on_games_error(self):
        self.status_label.configure(text="Ошибка обновления")
        self.set_loading(False)

    def render_all_games(self):
        for key, games_list in self.games.items():
            frame = self.tab_frames.get(key)
            if frame is not None:
                self.render_games(frame, games_list)

    def render_games(self, frame, games):
        for widget in frame.winfo_children():
            widget.destroy()

        if hasattr(self, 'search_var'):
            q = self.search_var.get().lower().strip()
            if q:
                games = [g for g in games if q in (g.get("title") or "").lower()]

        if not games:
            ctk.CTkLabel(
                frame,
                text="Ничего не найдено (или загружается...)",
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
            right, text=f"{title} [{platform}]" if platform else title,
            font=ctk.CTkFont(size=22, weight="bold"), text_color=THEMES["dark"]["text"]
        )
        header.grid(row=0, column=0, sticky="w", pady=(0, 6))

        price = (game.get("price") or "FREE").strip()
        price_show = "Бесплатно" if price.upper() == "FREE" else price
        info = f"{price_show} {game.get('source','')}".strip(" ")

        ctk.CTkLabel(
            right, text=info, font=ctk.CTkFont(size=13), text_color=THEMES["dark"]["text_secondary"]
        ).grid(row=1, column=0, sticky="w", pady=(0, 10))

        desc = game.get("description", "Описания нет.")
        link = (game.get("link") or "").strip()

        textbox = ctk.CTkTextbox(
            right, width=540, height=470, fg_color="#111111", text_color=THEMES["dark"]["text"],
            font=ctk.CTkFont(size=13), wrap="word"
        )
        textbox.grid(row=2, column=0, sticky="nsew")
        textbox.insert("1.0", desc + (f"\n\nСсылка: {link}" if link else ""))
        textbox.configure(state="disabled")

        btn_row = ctk.CTkFrame(right, fg_color="transparent")
        btn_row.grid(row=3, column=0, sticky="e", pady=(12, 0))

        if link:
            if "store.steampowered.com/app/" in link:
                try:
                    app_id = link.split("app/")[1].split("/")[0]
                    ctk.CTkButton(
                        btn_row, text="В Steam", fg_color="#1b2838", hover_color="#2a475e", text_color="#66c0f4",
                        command=lambda id=app_id: __import__("webbrowser").open(f"steam://store/app/{id}")
                    ).pack(side="right", padx=(0, 10))
                except: pass

            ctk.CTkButton(
                btn_row, text="В браузере", fg_color=THEMES["dark"]["primary"], hover_color="#00dd6f",
                command=lambda: __import__("webbrowser").open(link),
            ).pack(side="right", padx=(0, 10))
            
            ctk.CTkButton(
                btn_row, text="Копировать", fg_color="#1a2235", hover_color="#2a3a5a", text_color="#d6d9e6",
                command=lambda: (win.clipboard_clear(), win.clipboard_append(link))
            ).pack(side="right", padx=(0, 10))

        ctk.CTkButton(
            btn_row, text="Закрыть", fg_color="#444444", hover_color="#666666", command=win.destroy
        ).pack(side="right")

    def show_window(self):
        try:
            self.deiconify()
            self.lift()
            self.focus_force()
        except Exception:
            pass

    def exit_app(self):
        try: self.tray.stop()
        except Exception: pass
        try: self.destroy()
        except Exception: pass

    def hide_to_tray(self):
        if self.settings.get("minimize_to_tray", True):
            try: self.withdraw()
            except Exception: pass
        else:
            self.exit_app()


if __name__ == "__main__":
    app = GameGiveawaysApp()
    app.withdraw()

    is_autorun = "--minimized" in sys.argv
    start_hidden = is_autorun or app.settings.get("start_minimized", False)
    skip_splash = app.settings.get("hide_welcome", False) or is_autorun

    def start_main():
        if not start_hidden:
            app.deiconify()
            app.lift()
            app.focus_force()
        
        app.refresh_games_async(first_start=True)
        interval_mins = app.settings.get("auto_refresh_interval", 30)
        app.after(interval_mins * 60000, app.auto_refresh)

    if skip_splash:
        app.after(100, start_main)
    else:
        SplashScreen(app, check_update_info_func=check_update_info, on_start_callback=start_main)

    app.mainloop()