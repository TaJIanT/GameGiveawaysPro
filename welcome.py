# -*- coding: utf-8 -*-

import threading
import webbrowser
import customtkinter as ctk

from config import THEMES, APP_TITLE

try:
    from storage import load_settings, save_settings
except Exception:
    load_settings = None
    save_settings = None


class SplashScreen(ctk.CTkToplevel):
    """
    Welcome screen:
    - Friendly intro text
    - Checks updates in background
    - Primary button: Download update OR Start scanning
    - Optional: "Don't show again" (saved if storage.py has helpers)
    """

    def __init__(self, parent, check_update_info_func, on_start_callback):
        super().__init__(parent)

        self.parent = parent
        self.check_update_info_func = check_update_info_func
        self.on_start_callback = on_start_callback
        self.update_url = None

        self.title(APP_TITLE)
        self.geometry("760x440")
        self.configure(fg_color=THEMES["dark"]["bg"])
        self.resizable(False, False)

        # Modal-like behavior
        try:
            self.transient(parent)
            self.grab_set()
            self.lift()
            self.focus_force()
        except Exception:
            pass

        wrap = ctk.CTkFrame(self, fg_color=THEMES["dark"]["fg"], corner_radius=18)
        wrap.pack(fill="both", expand=True, padx=18, pady=18)

        # Top "hero" block
        hero = ctk.CTkFrame(wrap, fg_color=THEMES["dark"]["card"], corner_radius=16)
        hero.pack(fill="x", padx=16, pady=(16, 10))

        title = ctk.CTkLabel(
            hero,
            text="GameGiveawaysPro",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=THEMES["dark"]["text"],
        )
        title.pack(anchor="w", padx=16, pady=(14, 4))

        desc = ctk.CTkLabel(
            hero,
            text="Сканирует бесплатные раздачи и скидки.\nБыстрый старт + автообновление.",
            font=ctk.CTkFont(size=14),
            justify="left",
            text_color=THEMES["dark"]["text_secondary"],
        )
        desc.pack(anchor="w", padx=16, pady=(0, 14))

        self.subtitle = ctk.CTkLabel(
            wrap,
            text="Проверяем обновления",
            font=ctk.CTkFont(size=14),
            text_color=THEMES["dark"]["text_secondary"],
        )
        self.subtitle.pack(anchor="w", padx=20, pady=(6, 10))

        self.progress = ctk.CTkProgressBar(wrap)
        self.progress.pack(fill="x", padx=20, pady=(0, 14))
        self.progress.configure(mode="indeterminate")
        self.progress.start()

        # Buttons row
        btns = ctk.CTkFrame(wrap, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(2, 8))

        self.primary_btn = ctk.CTkButton(
            btns,
            text="Подождите",
            state="disabled",
            fg_color=THEMES["dark"]["primary"],
            hover_color="#00dd6f",
            height=42,
            command=self._on_primary,
        )
        self.primary_btn.pack(side="left")

        # Checkbox
        self.noshow_var = ctk.BooleanVar(value=False)
        self.noshow = ctk.CTkCheckBox(
            wrap,
            text="Не показывать это окно при запуске",
            variable=self.noshow_var,
            text_color=THEMES["dark"]["text_secondary"],
        )
        self.noshow.pack(anchor="w", padx=20, pady=(8, 8))

        # Small footer
        self.footer = ctk.CTkLabel(
            wrap,
            text="Нажмите Начать сканирование, чтобы загрузить актуальные раздачи.",
            font=ctk.CTkFont(size=12),
            text_color=THEMES["dark"]["text_secondary"],
        )
        self.footer.pack(anchor="w", padx=20, pady=(0, 10))

        threading.Thread(target=self._check_bg, daemon=True).start()

    def _check_bg(self):
        info = {}
        try:
            info = self.check_update_info_func() or {}
        except Exception:
            info = {}
        self.after(0, lambda: self._apply(info))

    def _apply(self, info: dict):
        try:
            self.progress.stop()
        except Exception:
            pass

        self.progress.configure(mode="determinate")
        self.progress.set(1)

        if info.get("has_update"):
            self.update_url = info.get("url")
            latest = info.get("latest") or "новая версия"
            self.subtitle.configure(text=f"Доступно обновление: {latest}")
            self.primary_btn.configure(text="Скачать обновление", state="normal")
            self.footer.configure(text="Рекомендуется обновиться перед сканированием.")
        else:
            self.subtitle.configure(text="Обновлений нет. Всё готово.")
            self.primary_btn.configure(text="Начать сканирование", state="normal")
            self.footer.configure(text="Можно начинать: загрузим свежие раздачи и скидки.")

    def _save_noshow_flag(self):
        # optional persistence if your storage.py supports it
        if not (load_settings and save_settings):
            return
        try:
            s = load_settings() or {}
            s["hide_welcome"] = bool(self.noshow_var.get())
            save_settings(s)
        except Exception:
            pass

    def _on_primary(self):
        self._save_noshow_flag()
        if self.update_url:
            webbrowser.open(self.update_url)
        self._start_app()

    def _start_app(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
        self.on_start_callback()
