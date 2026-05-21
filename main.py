import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import database as db
from theme import get_theme_config, FONTS, PRIMARY_FONT
from arabic_fixer import ar
from languages import get_text
import keybinds

import ui_sales
import ui_products
import ui_analytics
import ui_notifications
import ui_settings
import ui_credit
import platform
import ctypes
import os
import sys

# Configure CustomTkinter
ctk.set_appearance_mode("dark")  # Default, will be updated in __init__
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        db.init_db()

        # Modern Theme State
        self.mode = db.get_setting("theme", "dark")
        self.accent_name = db.get_setting("accent_color", "Orange")
        self.T = get_theme_config(self.mode, self.accent_name)

        shop_name = db.get_setting("shop_name", "المتجر")
        self.title(ar(shop_name))
        self.geometry("1200x800")
        self.minsize(1000, 700)

        # Set Icon
        try:
            base_dir = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
            icon_path = os.path.join(base_dir, "icon.ico")
            self.iconbitmap(icon_path)
        except Exception:
            pass

        # Apply Modern Look
        ctk.set_appearance_mode(self.mode)
        self.configure(fg_color=self.T["bg"])

        self.role = "user"
        self.lang = db.get_setting("language", "ar")
        self.active_page = None
        self.last_low_count = 0

        self.pages = {}
        self.nav_buttons = {}

        # Main container for floating effect with outer padding
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=15, pady=15)

        # Sidebar with rounded corners
        self.sidebar = ctk.CTkFrame(self.main_container, fg_color=self.T["bg2"], width=240, corner_radius=20)
        self.sidebar.pack(side="left", fill="y", padx=(0, 15))
        self.sidebar.pack_propagate(False)

        # Content area with rounded corners
        self.content = ctk.CTkFrame(self.main_container, fg_color=self.T["bg2"], corner_radius=20)
        self.content.pack(side="left", fill="both", expand=True)

        # Configure Grid for Content area to allow stacking frames
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.update_treeview_styles(self.mode)
        self._build_sidebar()
        self._setup_global_keybinds()
        self.bind("<Button-1>", self._on_global_click, add="+")

        # Pre-initialize all pages for instant switching on Windows
        self._initialize_pages()

        self.show_page("sales")
        self.refresh_alerts()

    def _initialize_pages(self):
        """Initializes all page frames once and stacks them using grid."""
        keys = ["sales", "products", "analytics", "credit", "notifications", "settings"]
        for key in keys:
            if key not in self.pages:
                page = self._create_page(key)
                if page:
                    self.pages[key] = page
                    # Place all pages in the same grid cell
                    # We start with pady=15 to match the container's inner padding
                    page.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

    def restart_app(self):
        """Restarts the current application process."""
        import sys
        import os

        # Determine the path to the current script/executable
        if getattr(sys, 'frozen', False):
            # If running as an executable (PyInstaller)
            executable = sys.executable
            args = sys.argv[1:]
        else:
            # If running as a script
            executable = sys.executable
            args = [os.path.abspath(__file__)] + sys.argv[1:]

        os.execv(executable, [executable] + args)

    def _on_global_click(self, event):
        """Deselect everything when clicking away from selection-based widgets."""
        try:
            widget = event.widget
            if not widget: return

            # Convert string name to widget object if necessary
            if isinstance(widget, str):
                try:
                    widget = self.nametowidget(widget)
                except Exception:
                    return

            # 1. Detect if we clicked a Treeview, its scrollbar, or an action button
            is_protected = False
            curr = widget
            while curr:
                # Is it a Treeview or its scrollbar?
                if isinstance(curr, (ttk.Treeview, tk.Scrollbar, ctk.CTkScrollbar, ttk.Scrollbar)):
                    is_protected = True
                    break
                # Is it a Button? (Action buttons like Delete/Edit need the selection)
                if isinstance(curr, (ctk.CTkButton, tk.Button)):
                    is_protected = True
                    break
                # Is it a TopLevel window? (Dialogs should not clear background selection)
                if isinstance(curr, (tk.Toplevel, ctk.CTkToplevel)):
                    is_protected = True
                    break

                # Move up the hierarchy
                parent = curr.winfo_parent()
                if not parent: break
                try:
                    curr = self.nametowidget(parent)
                except Exception:
                    break

            # 2. If we clicked "away" (on empty frame, label, etc.), clear all selections
            if not is_protected:
                for page in self.pages.values():
                    if not page: continue
                    for attr in ("tree", "recent_tree"):
                        tree = getattr(page, attr, None)
                        if tree and tree.winfo_exists():
                            sel = tree.selection()
                            if sel:
                                tree.selection_remove(sel)
        except Exception:
            pass

    def _setup_global_keybinds(self):
        # Navigation shortcuts
        self.bind(f"<KeyPress-{keybinds.GLOBAL_KEYS['switch_sales']}>", lambda e: self.show_page("sales"))
        self.bind(f"<KeyPress-{keybinds.GLOBAL_KEYS['switch_products']}>", lambda e: self.show_page("products"))
        self.bind(f"<KeyPress-{keybinds.GLOBAL_KEYS['switch_analytics']}>", lambda e: self.show_page("analytics"))
        self.bind(f"<KeyPress-{keybinds.GLOBAL_KEYS['switch_notifications']}>", lambda e: self.show_page("notifications"))
        self.bind(f"<KeyPress-{keybinds.GLOBAL_KEYS['switch_settings']}>", lambda e: self.show_page("settings"))

    def _create_page(self, key):
        if key == "sales": return ui_sales.SalesTab(self.content, self)
        if key == "products": return ui_products.ProductsTab(self.content, self)
        if key == "analytics": return ui_analytics.AnalyticsTab(self.content, self)
        if key == "notifications": return ui_notifications.NotificationsTab(self.content, self)
        if key == "settings": return ui_settings.SettingsTab(self.content, self)
        if key == "credit": return ui_credit.CreditTab(self.content, self)
        return None

    def _build_sidebar(self):
        from theme import get_sidebar_icon, get_icon, PRIMARY_FONT
        for w in self.sidebar.winfo_children():
            w.destroy()

        self.nav_buttons = {} # Clear stale references

        # Logo Section
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color=self.T["accent"], corner_radius=15)
        logo_frame.pack(fill="x", padx=15, pady=25)

        # Smooth Modern Management Logo
        app_logo = get_icon("logo", color="#ffffff", size=(48, 48))
        ctk.CTkLabel(logo_frame, text="", image=app_logo,
                     fg_color=self.T["accent"]).pack(pady=(15, 5))

        shop_name = db.get_setting("shop_name", "المتجر")
        ctk.CTkLabel(logo_frame, text=ar(shop_name), font=(PRIMARY_FONT, 16, "bold"),
                     fg_color=self.T["accent"], text_color="#ffffff", wraplength=160).pack(pady=(0, 15))

        self._build_role_indicator()

        # Navigation Buttons
        buttons_order = ["sales", "products", "analytics", "credit", "notifications", "settings"]
        for key in buttons_order:
            if self._should_show_page(key):
                label = get_text(key, self.lang)

                # Initialize with correct theme/active state colors
                is_active = (key == self.active_page)
                icon_img = get_sidebar_icon(key, is_active=is_active)

                accent_color = self.T["accent"]

                btn = ctk.CTkButton(self.sidebar, text=ar(label), image=icon_img,
                                     font=ctk.CTkFont(family=PRIMARY_FONT, size=15, weight="bold"),
                                     fg_color=accent_color if is_active else "transparent",
                                     text_color="#ffffff" if is_active else self.T["text"],
                                     hover_color=accent_color if is_active else self.T["bg3"],
                                     height=54, corner_radius=12,
                                     anchor="e", compound="right",
                                     command=lambda k=key: self.show_page(k))
                btn.pack(fill="x", padx=12, pady=4)
                self.nav_buttons[key] = btn

        # Theme indicator
        status = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        status.pack(side="bottom", fill="x", pady=20)
        theme_lbl = ar(get_text("dark" if self.mode=="dark" else "light", self.lang))
        ctk.CTkLabel(status, text=f"{theme_lbl} | {self.accent_name}",
                     font=ctk.CTkFont(size=11), text_color=self.T["text2"]).pack()

    def _should_show_page(self, key):
        if key in ("sales", "products", "notifications", "settings"): return True
        return self.role == "admin"

    def _build_role_indicator(self):
        from theme import PRIMARY_FONT
        role_frame = ctk.CTkFrame(self.sidebar, fg_color=self.T["bg3"], corner_radius=10)
        role_frame.pack(fill="x", padx=15, pady=(0, 20))

        role_text = get_text("admin" if self.role == "admin" else "user", self.lang)

        ctk.CTkLabel(role_frame, text=ar(role_text),
                     font=ctk.CTkFont(family=PRIMARY_FONT, size=13, weight="bold"),
                     text_color=self.T["accent"]).pack(pady=8)

    def switch_to_admin(self):
        self.role = "admin"
        self._build_sidebar()
        # Force redirection to a valid page to prevent empty screen
        target = self.active_page if self._should_show_page(self.active_page) else "sales"
        self.show_page(target)
        # Refresh settings UI if it exists in cache
        if "settings" in self.pages:
            self.pages["settings"].refresh_ui()

    def switch_to_user(self):
        self.role = "user"
        self._build_sidebar()
        # Force redirection to sales if current page is now restricted
        if self.active_page in ("products", "analytics") or not self._should_show_page(self.active_page):
            self.show_page("sales")
        else:
            self.show_page(self.active_page)
        # Refresh settings UI if it exists in cache
        if "settings" in self.pages:
            self.pages["settings"].refresh_ui()

    def show_page(self, key):
        from theme import get_sidebar_icon
        if not self._should_show_page(key): key = "sales"

        # Prevent redundant lifts
        if self.active_page == key and key in self.pages:
            # Still refresh if needed
            if hasattr(self.pages[key], "refresh"):
                self.pages[key].refresh()
            return

        self.active_page = key

        # Lazy load page if not already initialized
        if key not in self.pages:
            page = self._create_page(key)
            if page:
                self.pages[key] = page
                page.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        # Update button highlights and icons
        for k, btn in self.nav_buttons.items():
            if btn.winfo_exists():
                is_active = (k == key)
                new_icon = get_sidebar_icon(k, is_active=is_active)
                accent_color = self.T["accent"]
                btn.configure(
                    fg_color=accent_color if is_active else "transparent",
                    text_color="#ffffff" if is_active else self.T["text"],
                    hover_color=accent_color if is_active else self.T["bg3"],
                    image=new_icon
                )

        # Alerts and Toast Notifications
        self.refresh_alerts()

        # Bring selected page to front using lift() for zero flickering on Windows
        page = self.pages.get(key)
        if page:
            page.lift()
            if hasattr(page, "refresh"):
                page.refresh()


    def refresh_alerts(self):
        low = db.get_low_stock_products()
        current_count = len(low)
        if current_count > 0 and current_count != self.last_low_count:
            names = ", ".join(p["name"] for p in low[:2])
            msg = f"{get_text('alerts', self.lang)}: {names}..."
            self.show_toast(msg, self.T["danger"])
        self.last_low_count = current_count

    def show_toast(self, message, color):
        toast = ctk.CTkToplevel(self)
        toast.withdraw()
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.configure(fg_color=color)

        w, h = 380, 100
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        # Bottom-right corner
        x = sw - w - 40
        y = sh - h - 100

        toast.geometry(f"{w}x{h}+{x}+{y}")

        # Border frame for effect
        inner = ctk.CTkFrame(toast, fg_color=color, corner_radius=10, border_width=2, border_color="white")
        inner.pack(fill="both", expand=True)

        ctk.CTkLabel(inner, text=ar(message), font=FONTS["subhead"], text_color="white", wraplength=340).pack(expand=True, padx=20)

        toast.deiconify()
        toast.after(5000, toast.destroy)

    def refresh_ui(self):
        self.mode = db.get_setting("theme", "dark")
        self.accent_name = db.get_setting("accent_color", "Orange")
        self.T = get_theme_config(self.mode, self.accent_name)
        self.lang = db.get_setting("language", "ar")

        ctk.set_appearance_mode(self.mode)
        self.update_treeview_styles(self.mode)
        self.configure(fg_color=self.T["bg"])

        # Update floating containers colors
        self.sidebar.configure(fg_color=self.T["bg2"])
        self.content.configure(fg_color=self.T["bg2"])

        for p in self.pages.values():
            if p: p.destroy()
        self.pages = {}

        self._build_sidebar()
        self._initialize_pages() # Pre-initialize pages with new theme
        self.show_page(self.active_page if self._should_show_page(self.active_page) else "sales")

    def update_treeview_styles(self, mode: str):
        style = ttk.Style()
        style.theme_use("clam")

        if mode.lower() == "dark":
            fg_color = "#ffffff"
            field_bg = self.T["bg2"]
            select_bg = self.T["accent"]
        else:
            fg_color = "#000000"
            field_bg = "#ffffff"
            select_bg = self.T["accent"]

        style.configure("Treeview",
                        background=field_bg,
                        foreground=fg_color,
                        fieldbackground=field_bg,
                        rowheight=42,
                        borderwidth=0,
                        font=(PRIMARY_FONT, 11))
        style.map("Treeview", background=[("selected", select_bg)], foreground=[("selected", "#ffffff")])

        style.configure("Treeview.Heading",
                        background=self.T["bg3"],
                        foreground=fg_color,
                        font=(PRIMARY_FONT, 11, "bold"),
                        borderwidth=1,
                        relief="flat")

        # Lock heading colors to prevent "blinking" or color changes on hover
        style.map("Treeview.Heading",
                  background=[("active", self.T["bg3"]), ("pressed", self.T["bg3"])],
                  foreground=[("active", fg_color)],
                  relief=[("active", "flat"), ("pressed", "flat")])


if __name__ == "__main__":
    if platform.system() == "Windows":
        try:
            # Per-Monitor DPI aware (2), fallback to System DPI aware (1)
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass

    # Enforce exact scaling to fix Windows oversized UI issue
    ctk.set_window_scaling(1.0)
    ctk.set_widget_scaling(1.0)

    app = App()
    app.mainloop()
