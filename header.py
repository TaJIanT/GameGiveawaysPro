# -*- coding: utf-8 -*-
import customtkinter as ctk
from config import THEMES, APP_TITLE

def create_header(parent, refresh_callback):
    # Верхняя тонкая акцент-полоска
    top_accent = ctk.CTkFrame(parent, height=6, fg_color="#00caa0", corner_radius=0)
    top_accent.pack(fill="x")
    top_accent.pack_propagate(False)

    # Основная шапка
    header_frame = ctk.CTkFrame(parent, fg_color="#121a2e", height=58, corner_radius=0)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)

    # Левый блок (название)
    left = ctk.CTkFrame(header_frame, fg_color="transparent")
    left.pack(side="left", fill="y", padx=14)

    title_label = ctk.CTkLabel(
        left,
        text=APP_TITLE,
        font=ctk.CTkFont(size=20, weight="bold"),
        text_color=THEMES["dark"]["text"]
    )
    title_label.pack(anchor="w", pady=(10, 0))

    subtitle = ctk.CTkLabel(
        left,
        text="Бесплатные игры",
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color=THEMES["dark"]["text_secondary"]
    )
    subtitle.pack(anchor="w", pady=(0, 10))

    # Правый блок (статус/кнопки)
    right = ctk.CTkFrame(header_frame, fg_color="transparent")
    right.pack(side="right", fill="y", padx=12, pady=10)

    status_label = ctk.CTkLabel(
        right,
        text="Обновлено: ",
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color=THEMES["dark"]["text_secondary"]
    )
    status_label.grid(row=0, column=0, padx=(0, 10), sticky="e")

    refresh_btn = ctk.CTkButton(
        right,
        text="Обновить",
        font=ctk.CTkFont(size=13, weight="bold"),
        fg_color=THEMES["dark"]["primary"],
        hover_color="#00dd6f",
        width=110,
        height=32,
        command=refresh_callback
    )
    refresh_btn.grid(row=0, column=1, padx=(0, 12), sticky="e")

    gp_checkbox = ctk.CTkCheckBox(
        right,
        text="GamerPower",
        font=ctk.CTkFont(size=13, weight="bold"),
        checkbox_width=18,
        checkbox_height=18,
        fg_color=THEMES["dark"]["accent"],
        hover_color=THEMES["dark"]["primary"],
        text_color=THEMES["dark"]["text_secondary"]
    )
    gp_checkbox.grid(row=0, column=2, sticky="e")

    parent.gp_var = ctk.BooleanVar(value=True)
    gp_checkbox.configure(variable=parent.gp_var, command=parent.on_toggle_gamerpower)

    progress = ctk.CTkProgressBar(
        parent,
        height=6,
        corner_radius=0,
        fg_color="#0b1020",
        progress_color="#00caa0"
    )
    progress.pack(fill="x")
    progress.set(0)
    progress.pack_forget()

    # Полоса меню под шапкой (пока просто фон и линия)
    nav = ctk.CTkFrame(parent, height=34, fg_color="#0f1526", corner_radius=0)
    nav.pack(fill="x", pady=(0, 8))
    nav.pack_propagate(False)

    # Тонкий разделитель под полосой
    divider = ctk.CTkFrame(parent, height=2, fg_color="#1a1f35", corner_radius=0)
    divider.pack(fill="x", pady=(0, 10))
    divider.pack_propagate(False)

    # Возвращаем nav тоже  чтобы потом легко перенести туда твои табы (если захочешь)
    parent.nav_frame = nav

    return header_frame, status_label, refresh_btn, progress
