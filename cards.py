# -*- coding: utf-8 -*-
import customtkinter as ctk
from config import THEMES

import threading
import requests
from io import BytesIO
from PIL import Image
from customtkinter import CTkImage

_IMG_CACHE = {}
_INFLIGHT = set()

CARD_BORDER = "#252a46"
CARD_BORDER_HOVER = "#3a4a8a"

# Чуть светлее, чем THEMES["dark"]["fg"]
CARD_FG = THEMES["dark"]["fg"]
CARD_FG_HOVER = "#1b2238"

CARD_H = 160
CARD_H_HOVER = 170   # насколько увеличиваем (подбери 168..176)
CARD_PADX = 12
CARD_PADY = 10
CARD_PADX_HOVER = 10
CARD_PADY_HOVER = 8

def _apply_card_style(frame: ctk.CTkFrame, hover: bool):
    frame.configure(
        border_color=(CARD_BORDER_HOVER if hover else CARD_BORDER),
        fg_color=(CARD_FG_HOVER if hover else CARD_FG)
    )

def _bind_hover_recursive(root_widget, enter_cb, leave_cb):
    try:
        root_widget.bind("<Enter>", enter_cb)
        root_widget.bind("<Leave>", leave_cb)
    except Exception:
        pass
    try:
        for child in root_widget.winfo_children():
            _bind_hover_recursive(child, enter_cb, leave_cb)
    except Exception:
        pass

def _bind_card_hover(card: ctk.CTkFrame, extra_widgets=None):
    extra_widgets = extra_widgets or []

    def on_enter(_=None):
        _apply_card_style(card, True)

    def on_leave(_=None):
        _apply_card_style(card, False)

    # только безопасные контейнеры, не рекурсивно
    for w in [card, *extra_widgets]:
        try:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
        except Exception:
            pass

    return on_enter, on_leave

def create_game_card(parent, game, details_callback):
    card = ctk.CTkFrame(
        parent,
        fg_color=CARD_FG,
        height=CARD_H,
        corner_radius=16,
        border_width=2,
        border_color=CARD_BORDER
    )
    card.pack(fill="x", padx=12, pady=10)
    card.pack_propagate(False)

    img_frame = ctk.CTkFrame(card, fg_color="#2a2a3a", width=120, height=140, corner_radius=12)
    img_frame.place(x=15, y=10)
    img_frame.pack_propagate(False)

    img_label = ctk.CTkLabel(img_frame, text="IMG", text_color="#888888", font=ctk.CTkFont(size=14, weight="bold"))
    img_label.place(relx=0.5, rely=0.5, anchor="center")

    img_url = (game.get("image") or "").strip()
    if img_url and img_url in _IMG_CACHE:
        img_label.configure(image=_IMG_CACHE[img_url], text="")
        img_label.image = _IMG_CACHE[img_url]
    else:
        def _worker():
            try:
                resp = requests.get(img_url, timeout=(1.5, 3.0))
                resp.raise_for_status()
                pil_img = Image.open(BytesIO(resp.content)).convert("RGB")
                pil_img.thumbnail((110, 130))

                def _apply():
                    try:
                        ctk_img = CTkImage(light_image=pil_img, size=pil_img.size)
                        _IMG_CACHE[img_url] = ctk_img
                        img_label.configure(image=ctk_img, text="")
                        img_label.image = ctk_img
                    finally:
                        _INFLIGHT.discard(img_url)

                img_label.after(0, _apply)
            except Exception:
                _INFLIGHT.discard(img_url)

        if img_url and img_url not in _INFLIGHT:
            _INFLIGHT.add(img_url)
            threading.Thread(target=_worker, daemon=True).start()

    content = ctk.CTkFrame(card, fg_color="transparent")
    content.place(x=155, y=15, relwidth=0.75, relheight=0.9)

    title = (game.get("title") or "Unknown").strip()
    title_show = title[:65] + ("..." if len(title) > 65 else "")
    ctk.CTkLabel(
        content,
        text=title_show,
        font=ctk.CTkFont(size=18, weight="bold"),
        text_color=THEMES["dark"]["text"]
    ).place(x=0, y=0)

    platform = (game.get("platform") or "").strip()
    if platform:
        ctk.CTkLabel(
            content,
            text=platform,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="white",
            fg_color="#4da3ff",
            padx=12, pady=4,
            corner_radius=6
        ).place(x=0, y=30)

    price_raw = (game.get("price") or "FREE").strip()
    price_show = "Бесплатно" if price_raw.upper() == "FREE" else price_raw

    ctk.CTkLabel(
        content,
        text=price_show,
        font=ctk.CTkFont(size=24, weight="bold"),
        text_color="#00ff88" if price_raw.upper() == "FREE" else "#ffb020"
    ).place(x=0, y=62)

    source = (game.get("source") or "").strip()
    score = game.get("ratingscore")
    info_parts = []
    if source:
        info_parts.append(source)
    if score:
        try:
            info_parts.append(f"Рейтинг {float(score):.1f}")
        except Exception:
            pass
    if info_parts:
        ctk.CTkLabel(
            content,
            text="    ".join(info_parts),
            font=ctk.CTkFont(size=12),
            text_color=THEMES["dark"]["text_secondary"]
        ).place(x=0, y=98)

    BTN_H = 34
    R = 10

    link = (game.get("link") or "").strip()

    open_btn = ctk.CTkButton(
        content,
        text="Открыть",
        font=ctk.CTkFont(size=12, weight="bold"),
        width=110,
        height=BTN_H,
        corner_radius=R,
        fg_color="#1a2235",
        hover_color="#2a3a5a",
        border_width=2,
        border_color="#2e334e",
        text_color="#d6d9e6",
        command=(lambda: __import__("webbrowser").open(link)) if link else None,
        state="normal" if link else "disabled",
    )
    open_btn.place(relx=1.0, rely=1.0, anchor="se", x=-156, y=-12)

    details_btn = ctk.CTkButton(
        content,
        text="Подробнее",
        font=ctk.CTkFont(size=13, weight="bold"),
        width=130,
        height=BTN_H,
        corner_radius=R,
        fg_color=THEMES["dark"]["primary"],
        hover_color="#2bffe3",
        border_width=2,
        border_color="#0a6b62",
        text_color="#06131a",
        command=lambda: details_callback(game),
    )
    details_btn.place(relx=1.0, rely=1.0, anchor="se", x=-12, y=-12)
    card_on_enter, _ = _bind_card_hover(card, extra_widgets=[content, img_frame])

    # Когда курсор на кнопке  карточку тоже держим подсвеченной,
    # но hover_color кнопок работает штатно.
    try:
        open_btn.bind("<Enter>", lambda e: card_on_enter())
        details_btn.bind("<Enter>", lambda e: card_on_enter())
    except Exception:
        pass

    return card



