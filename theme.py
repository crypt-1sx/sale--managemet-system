"""
Modernized Theme and color configuration for the app.
Supports dynamic accent colors and rounded UI components.
"""
from arabic_fixer import ar
from languages import get_text
import customtkinter as ctk
from PIL import Image, ImageDraw
import io
import base64

# Ultra-Modern Professional Font Stack
# 'Noto Sans Arabic' for perfect Arabic typography
PRIMARY_FONT = "Noto Sans Arabic"
MONO_FONT = "DejaVu Sans Mono"

FONTS = {
    "title":    (PRIMARY_FONT, 32, "bold"),
    "heading":  (PRIMARY_FONT, 20, "bold"),
    "subhead":  (PRIMARY_FONT, 16, "bold"),
    "body":     (PRIMARY_FONT, 13),
    "small":    (PRIMARY_FONT, 11),
    "mono":     (MONO_FONT, 12),
    "big_num":  (PRIMARY_FONT, 42, "bold"),
}

# Modern Color Palettes
ACCENTS = {
    "Orange":   {"main": "#f97316", "hover": "#ea580c", "light": "#ffedd5"},
    "Neon Blue": {"main": "#0ea5e9", "hover": "#0284c7", "light": "#e0f2fe"},
    "Emerald":  {"main": "#10b981", "hover": "#059669", "light": "#d1fae5"},
    "Crimson":  {"main": "#ef4444", "hover": "#dc2626", "light": "#fee2e2"},
    "Amethyst": {"main": "#8b5cf6", "hover": "#7c3aed", "light": "#ede9fe"},
}

THEMES = {
    "dark": {
        "bg":           "#0f172a", # Slate 950
        "bg2":          "#1e293b", # Slate 800
        "bg3":          "#334155", # Slate 700
        "card":         "#1e293b",
        "text":         "#f8fafc", # Slate 50
        "text2":        "#94a3b8", # Slate 400
        "border":       "#334155",
        "entry_bg":     "#0f172a",
        "btn_text":     "#ffffff",
        "table_row":    "#1e293b",
        "table_alt":    "#1e293b",
        "table_head":   "#0f172a",
        "search_border": "#3A3A3C",
        "success":      "#22c55e",
        "danger":       "#ef4444",
        "warning":      "#f59e0b",
    },
    "light": {
        "bg":           "#ffffff", # Pure White
        "bg2":          "#f2f2f7", # Premium Soft Grey (OneUI style)
        "bg3":          "#e5e5ea", # Muted Layer Grey
        "card":         "#f2f2f7",
        "text":         "#1c1c1e", # Deep Grey/Black
        "text2":        "#8e8e93", # iOS-style Muted Text
        "border":       "#d1d1d6", # Subtle contrast border
        "entry_bg":     "#ffffff",
        "btn_text":     "#ffffff",
        "table_row":    "#ffffff",
        "table_alt":    "#f2f2f7",
        "table_head":   "#e5e5ea",
        "search_border": "#DDE2E5",
        "success":      "#34c759",
        "danger":       "#ff3b30",
        "warning":      "#ff9500",
    }
}

def get_theme_config(mode="dark", accent_name="Orange"):
    """Returns a merged theme dictionary with the chosen accent."""
    base = THEMES.get(mode, THEMES["dark"]).copy()
    accent = ACCENTS.get(accent_name, ACCENTS["Orange"])

    base["accent"] = accent["main"]
    base["accent_hover"] = accent["hover"]
    base["accent_light"] = accent["light"]
    base["accent2"] = "#3b82f6" # Secondary blue for specific UI elements
    base["select"] = accent["main"]
    return base

def _draw_icon_raw(name, color, size_m, w):
    m = size_m
    canvas_size = (24 * m, 24 * m)
    img = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if name == "sales": # Shopping Cart
        draw.line([(4*m, 6*m), (10*m, 6*m), (14*m, 18*m), (22*m, 18*m)], fill=color, width=w)
        draw.line([(10*m, 6*m), (20*m, 6*m), (18*m, 14*m), (14*m, 14*m)], fill=color, width=w)
        draw.ellipse([12*m, 19*m, 14*m, 21*m], fill=color)
        draw.ellipse([19*m, 19*m, 21*m, 21*m], fill=color)
    elif name == "products": # Package/Box
        draw.rectangle([6*m, 6*m, 18*m, 18*m], outline=color, width=w)
        draw.line([6*m, 10*m, 18*m, 10*m], fill=color, width=w)
    elif name == "analytics": # Chart
        draw.line([6*m, 20*m, 20*m, 20*m], fill=color, width=w)
        draw.rectangle([8*m, 14*m, 10*m, 19*m], fill=color)
        draw.rectangle([12*m, 10*m, 14*m, 19*m], fill=color)
        draw.rectangle([16*m, 16*m, 18*m, 19*m], fill=color)
    elif name == "notifications": # Bell
        draw.ellipse([10*m, 8*m, 14*m, 12*m], outline=color, width=w)
        draw.line([8*m, 18*m, 16*m, 18*m], fill=color, width=w)
    elif name == "settings": # Gear
        draw.ellipse([8*m, 8*m, 16*m, 16*m], outline=color, width=w)
        draw.ellipse([11*m, 11*m, 13*m, 13*m], fill=color)
    elif name == "add": # Plus
        draw.line([12*m, 6*m, 12*m, 18*m], fill=color, width=w)
        draw.line([6*m, 12*m, 18*m, 12*m], fill=color, width=w)
    elif name == "edit": # Pencil
        draw.line([6*m, 18*m, 18*m, 6*m], fill=color, width=w)
    elif name == "delete": # Trash
        draw.rectangle([8*m, 8*m, 16*m, 18*m], outline=color, width=w)
        draw.line([6*m, 8*m, 18*m, 8*m], fill=color, width=w)
    elif name == "logo": # Modern Management/Dashboard Icon
        draw.rectangle([6*m, 6*m, 18*m, 18*m], outline=color, width=w)
        draw.line([10*m, 6*m, 10*m, 18*m], fill=color, width=w)
        draw.line([6*m, 12*m, 18*m, 12*m], fill=color, width=w)
    elif name == "confirm": # Check
        draw.line([6*m, 12*m, 10*m, 16*m], fill=color, width=w)
        draw.line([10*m, 16*m, 18*m, 8*m], fill=color, width=w)
    elif name == "clear": # Undo/Refresh
        draw.arc([8*m, 8*m, 16*m, 16*m], 0, 270, fill=color, width=w)
    elif name == "credit": # Wallet/Credit
        draw.rectangle([6*m, 8*m, 18*m, 16*m], outline=color, width=w)
        draw.line([14*m, 10*m, 18*m, 10*m], fill=color, width=w)
    elif name == "search": # Magnifying Glass
        draw.ellipse([7*m, 7*m, 15*m, 15*m], outline=color, width=w)
        draw.line([14*m, 14*m, 19*m, 19*m], fill=color, width=w)
    else:
        draw.ellipse([8*m, 8*m, 16*m, 16*m], outline=color, width=w)

    return img

def get_icon(name, color=None, size=(24, 24)):
    """Returns a CTkImage that automatically syncs with Light/Dark mode."""
    m = 4
    w = 2 * m

    # Version for Light Mode (typically dark text on light bg)
    l_color = color if color else THEMES["light"]["text"]
    # Version for Dark Mode (typically light text on dark bg)
    d_color = color if color else THEMES["dark"]["text"]

    # SPECIAL CASE: Sidebar Active Buttons.
    # If this is the active button, the background becomes 'accent' (e.g. Orange)
    # On many accents, white text looks better than theme text.
    # However, for pure theme sync, we use white for dark and dark for light.

    img_l = _draw_icon_raw(name, l_color, m, w).resize(size, Image.Resampling.LANCZOS)
    img_d = _draw_icon_raw(name, d_color, m, w).resize(size, Image.Resampling.LANCZOS)

    return ctk.CTkImage(light_image=img_l, dark_image=img_d, size=size)

def get_sidebar_icon(name, is_active=False, size=(24, 24)):
    """Returns an icon specifically optimized for the sidebar with active state color handling."""
    m = 4
    w = 2 * m

    # 1. Light Mode Logic
    # In Light mode, inactive text is black. Active text is WHITE (on accent bg).
    l_color = "#ffffff" if is_active else THEMES["light"]["text"]

    # 2. Dark Mode Logic
    # In Dark mode, inactive text is white. Active text is also WHITE (on accent bg).
    d_color = "#ffffff"

    img_l = _draw_icon_raw(name, l_color, m, w).resize(size, Image.Resampling.LANCZOS)
    img_d = _draw_icon_raw(name, d_color, m, w).resize(size, Image.Resampling.LANCZOS)

    return ctk.CTkImage(light_image=img_l, dark_image=img_d, size=size)

_MONTHS_RAW = [
    "", "جانفي", "فيفري", "مارس", "أفريل", "ماي", "جوان",
    "جويلية", "أوت", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
]
MONTHS_AR = [ar(m) for m in _MONTHS_RAW]

def get_months(lang="ar"):
    if lang == "ar":
        return MONTHS_AR
    elif lang == "fr":
        return ["", "Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
                "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]
    else:
        return ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
