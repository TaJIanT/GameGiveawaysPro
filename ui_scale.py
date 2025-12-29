# -*- coding: utf-8 -*-
import sys

def enable_windows_dpi_awareness():
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))  # Per-monitor v2
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

def maximize_window(root):
    """
    Максимизация окна:
    - Windows: root.state('zoomed')
    - Другие ОС: пытаемся сделать fullscreen
    """
    try:
        root.state("zoomed")  # Windows/Tk
        return True
    except Exception:
        try:
            root.attributes("-fullscreen", True)
            return True
        except Exception:
            return False

def compute_screen_geometry(root, min_w=1000, min_h=650):
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    w = max(sw, min_w)
    h = max(sh, min_h)
    return w, h
