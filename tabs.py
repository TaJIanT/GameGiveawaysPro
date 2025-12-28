# -*- coding: utf-8 -*-
import customtkinter as ctk

BAR_BG = "#26334a"
BAR_BORDER = "#1a2235"

TAB_BG = "#2b3a55"
TAB_HOVER = "#334766"
TAB_BORDER = "#22314a"

ACTIVE_BG = "#2fb7a6"
ACTIVE_BORDER = "#bffcff"
ACTIVE_TEXT = "#06131a"
TEXT = "#d6d9e6"

LABELS = [
    ("Все", "all"),
    ("Steam", "steam"),
    ("Epic", "epic"),
    ("GOG", "gog"),
    ("Скидки", "deals"),
]

def create_tabs(parent):
    # общий контейнер вкладок
    wrapper = ctk.CTkFrame(parent, fg_color="transparent")
    wrapper.pack(fill="both", expand=True, padx=20, pady=(6, 0))

    # панель-кнопки
    bar = ctk.CTkFrame(
        wrapper,
        fg_color=BAR_BG,
        corner_radius=10,
        border_width=2,
        border_color=BAR_BORDER
    )
    bar.pack(anchor="center", pady=(0, 10))
    bar.grid_columnconfigure(tuple(range(len(LABELS))), weight=1)

    # контейнер для страниц (ниже панели)
    pages = ctk.CTkFrame(wrapper, fg_color="transparent")
    pages.pack(fill="both", expand=True)

    tab_frames = {}
    buttons = {}
    active = {"key": "all"}

    def show_tab(key: str):
        active["key"] = key
        # показать нужную страницу, остальные скрыть
        for k, fr in tab_frames.items():
            if k == key:
                fr.pack(fill="both", expand=True)
            else:
                fr.pack_forget()

        # перекрасить кнопки
        for k, b in buttons.items():
            if k == key:
                b.configure(fg_color=ACTIVE_BG, hover_color=ACTIVE_BG,
                            border_color=ACTIVE_BORDER, text_color=ACTIVE_TEXT)
            else:
                b.configure(fg_color=TAB_BG, hover_color=TAB_HOVER,
                            border_color=TAB_BORDER, text_color=TEXT)

    # создаём кнопки и фреймы страниц
    for i, (text, key) in enumerate(LABELS):
        btn = ctk.CTkButton(
            bar,
            text=text,
            width=78,
            height=26,
            corner_radius=8,
            fg_color=TAB_BG,
            hover_color=TAB_HOVER,
            border_width=2,
            border_color=TAB_BORDER,
            text_color=TEXT,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda k=key: show_tab(k)
        )
        btn.grid(row=0, column=i, padx=4, pady=4)
        buttons[key] = btn

        frame = ctk.CTkScrollableFrame(pages, fg_color="transparent")
        tab_frames[key] = frame

    show_tab("all")

    # возвращаем:
    # tabview -> здесь wrapper (чтобы main.py ничего не сломал и мог хранить ссылку)
    return wrapper, tab_frames
