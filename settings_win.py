# -*- coding: utf-8 -*-
import customtkinter as ctk
from config import THEMES
from storage import load_settings, save_settings

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, on_save_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.on_save_callback = on_save_callback
        self.settings = load_settings()

        self.title("Настройки — GameGiveawaysPro")
        self.geometry("640x560")
        self.configure(fg_color=THEMES["dark"]["bg"])
        self.resizable(False, False)

        try:
            self.transient(parent)
            self.grab_set()
            self.lift()
            self.focus_force()
        except Exception:
            pass

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=(16, 10))

        # --- Секция: Автозапуск и системный трей ---
        self._create_header(scroll, "🚀 Автозапуск и системный трей")
        
        self.autorun_var = ctk.BooleanVar(value=self.settings.get("autorun", False))
        ctk.CTkSwitch(
            scroll, text="Запускать вместе с Windows", variable=self.autorun_var,
            progress_color=THEMES["dark"]["primary"]
        ).pack(anchor="w", padx=20, pady=6)

        self.minimized_var = ctk.BooleanVar(value=self.settings.get("start_minimized", False))
        ctk.CTkSwitch(
            scroll, text="Запускать свернутым в трей", variable=self.minimized_var,
            progress_color=THEMES["dark"]["primary"]
        ).pack(anchor="w", padx=20, pady=6)

        self.tray_close_var = ctk.BooleanVar(value=self.settings.get("minimize_to_tray", True))
        ctk.CTkSwitch(
            scroll, text="Сворачивать в трей при нажатии «Закрыть» (X)", variable=self.tray_close_var,
            progress_color=THEMES["dark"]["primary"]
        ).pack(anchor="w", padx=20, pady=6)

        # --- Секция: Тихий снайпер и уведомления ---
        self._create_header(scroll, "🎯 Тихий снайпер и Уведомления")

        self.auto_refresh_var = ctk.BooleanVar(value=self.settings.get("auto_refresh_enabled", True))
        ctk.CTkSwitch(
            scroll, text="Автоматически искать новые раздачи в фоновом режиме", variable=self.auto_refresh_var,
            progress_color=THEMES["dark"]["primary"]
        ).pack(anchor="w", padx=20, pady=6)

        self.sound_var = ctk.BooleanVar(value=self.settings.get("sound_notifications", True))
        ctk.CTkSwitch(
            scroll, text="Звуковое оповещение при нахождении халявы", variable=self.sound_var,
            progress_color=THEMES["dark"]["primary"]
        ).pack(anchor="w", padx=20, pady=6)

        interval_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        interval_frame.pack(fill="x", padx=20, pady=6)
        ctk.CTkLabel(interval_frame, text="Периодичность проверки:", font=ctk.CTkFont(size=13)).pack(side="left")
        
        self.interval_menu = ctk.CTkOptionMenu(
            interval_frame,
            values=["15 минут", "30 минут", "1 час", "2 часа"],
            fg_color="#1a2235",
            button_color=THEMES["dark"]["primary"],
            button_hover_color="#00dd6f"
        )
        self.interval_menu.pack(side="left", padx=10)
        curr_int = self.settings.get("auto_refresh_interval", 30)
        int_map = {15: "15 минут", 30: "30 минут", 60: "1 час", 120: "2 часа"}
        self.interval_menu.set(int_map.get(curr_int, "30 минут"))

        # --- Секция: Фильтры платформ ---
        self._create_header(scroll, "🎮 Отслеживаемые платформы")
        
        plat_cfg = self.settings.get("platforms", {})
        self.plat_steam = ctk.BooleanVar(value=plat_cfg.get("steam", True))
        self.plat_epic = ctk.BooleanVar(value=plat_cfg.get("epic", True))
        self.plat_gog = ctk.BooleanVar(value=plat_cfg.get("gog", True))
        self.plat_loot = ctk.BooleanVar(value=plat_cfg.get("loot", True))

        ctk.CTkCheckBox(scroll, text="Steam раздачи", variable=self.plat_steam).pack(anchor="w", padx=20, pady=4)
        ctk.CTkCheckBox(scroll, text="Epic Games раздачи", variable=self.plat_epic).pack(anchor="w", padx=20, pady=4)
        ctk.CTkCheckBox(scroll, text="GOG раздачи", variable=self.plat_gog).pack(anchor="w", padx=20, pady=4)
        ctk.CTkCheckBox(scroll, text="Ключи и промокоды (Loot)", variable=self.plat_loot).pack(anchor="w", padx=20, pady=4)

        # Нижняя панель кнопок
        btn_bar = ctk.CTkFrame(self, fg_color="#101420", height=60, corner_radius=0)
        btn_bar.pack(fill="x", side="bottom")

        ctk.CTkButton(
            btn_bar, text="Сохранить", fg_color=THEMES["dark"]["primary"], hover_color="#00dd6f",
            text_color="#0b1020", font=ctk.CTkFont(size=13, weight="bold"),
            command=self._save
        ).pack(side="right", padx=16, pady=12)

        ctk.CTkButton(
            btn_bar, text="Отмена", fg_color="#333333", hover_color="#555555",
            command=self.destroy
        ).pack(side="right", padx=4, pady=12)

    def _create_header(self, parent, text):
        f = ctk.CTkFrame(parent, fg_color="#171a33", corner_radius=6)
        f.pack(fill="x", pady=(14, 8))
        ctk.CTkLabel(f, text=text, font=ctk.CTkFont(size=14, weight="bold"), text_color="#00d4aa").pack(anchor="w", padx=10, pady=6)

    def _save(self):
        int_str = self.interval_menu.get()
        int_val = 30
        if "15" in int_str: int_val = 15
        elif "1" in int_str: int_val = 60
        elif "2" in int_str: int_val = 120

        new_st = {
            "autorun": self.autorun_var.get(),
            "start_minimized": self.minimized_var.get(),
            "minimize_to_tray": self.tray_close_var.get(),
            "sound_notifications": self.sound_var.get(),
            "auto_refresh_enabled": self.auto_refresh_var.get(),
            "auto_refresh_interval": int_val,
            "platforms": {
                "steam": self.plat_steam.get(),
                "epic": self.plat_epic.get(),
                "gog": self.plat_gog.get(),
                "loot": self.plat_loot.get()
            },
            "hide_welcome": self.settings.get("hide_welcome", False)
        }
        save_settings(new_st)
        if self.on_save_callback:
            self.on_save_callback(new_st)
        self.destroy()