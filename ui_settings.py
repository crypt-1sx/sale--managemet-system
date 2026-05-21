import tkinter as tk
import customtkinter as ctk
import database as db
from theme import FONTS, ACCENTS
from arabic_fixer import ar
from languages import get_text, LANGUAGES
from ui_components import CustomDialog, CustomInputDialog

class RestartDialog(ctk.CTkToplevel):
    """Clean popup asking user to restart for theme changes."""
    def __init__(self, parent_app):
        super().__init__(parent_app)
        self.app = parent_app
        self.withdraw()
        self.title(ar(get_text("restart_required", self.app.lang)))

        t = self.app.T
        self.configure(fg_color=t["bg"])
        self.width = 400
        self.height = 250
        self.resizable(False, False)

        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{self.width}x{self.height}+{(sw-self.width)//2}+{(sh-self.height)//2}")

        container = ctk.CTkFrame(self, fg_color=t["bg3"], corner_radius=15)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text=ar(get_text("restart_required", self.app.lang)),
                     font=ctk.CTkFont(size=18, weight="bold"), text_color=t["accent"]).pack(pady=(20, 10))

        ctk.CTkLabel(container, text=ar(get_text("restart_msg", self.app.lang)),
                     font=FONTS["body"], wraplength=340).pack(pady=10)

        btn_f = ctk.CTkFrame(container, fg_color="transparent")
        btn_f.pack(side="bottom", pady=15)

        ctk.CTkButton(btn_f, text=ar(get_text("restart_now", self.app.lang)), fg_color=t["success"],
                      width=140, height=40, command=self.app.restart_app).pack(side="left", padx=10)

        ctk.CTkButton(btn_f, text=ar(get_text("later", self.app.lang)), fg_color=t["bg3"],
                      text_color=t["text"], width=100, height=40, command=self.destroy).pack(side="left", padx=10)

        self.deiconify()
        self.grab_set()

class SettingsTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=app.T["bg2"])
        self.app = app
        self.vars = {}
        self._build()

    def _build(self):
        t = self.app.T
        lang = self.app.lang

        # Main scrollable container
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                             scrollbar_button_color=t["accent"],
                                             scrollbar_button_hover_color=t["accent_hover"])
        self.scroll.pack(fill="both", expand=True)

        # Title
        ctk.CTkLabel(self.scroll, text=ar(get_text("settings_title", lang)),
                     font=ctk.CTkFont(family="DejaVu Sans", size=28, weight="bold"),
                     text_color=t["accent"]).pack(pady=(10, 20))

        # 1. Appearance Section
        self._add_section_header(ar(get_text("appearance", lang)))
        sec_box = self._create_section_box()

        # Theme Mode
        row_mode = ctk.CTkFrame(sec_box, fg_color="transparent")
        row_mode.pack(fill="x", pady=10, padx=15)
        ctk.CTkLabel(row_mode, text=ar(get_text("theme_mode", lang)), font=FONTS["body"]).pack(side="right", padx=10)

        self.theme_var = tk.StringVar(value=self.app.mode)
        ctk.CTkRadioButton(row_mode, text=ar(get_text("dark", lang)), variable=self.theme_var, value="dark",
                           command=self._save_theme_preference).pack(side="right", padx=10)
        ctk.CTkRadioButton(row_mode, text=ar(get_text("light", lang)), variable=self.theme_var, value="light",
                           command=self._save_theme_preference).pack(side="right", padx=10)

        # Accent Color
        row_accent = ctk.CTkFrame(sec_box, fg_color="transparent")
        row_accent.pack(fill="x", pady=10, padx=15)
        ctk.CTkLabel(row_accent, text=ar(get_text("accent_color_label", lang)), font=FONTS["body"]).pack(side="right", padx=10)

        palette = ctk.CTkFrame(row_accent, fg_color="transparent")
        palette.pack(side="right", padx=10)
        for name, info in ACCENTS.items():
            is_active = (self.app.accent_name == name)
            if is_active:
                btn = ctk.CTkButton(palette, text="", width=24, height=24, corner_radius=12,
                                    fg_color=info["main"], hover_color=info["hover"],
                                    border_width=2, border_color="white",
                                    command=lambda n=name: self._save_accent_preference(n))
            else:
                btn = ctk.CTkButton(palette, text="", width=24, height=24, corner_radius=12,
                                    fg_color=info["main"], hover_color=info["hover"],
                                    command=lambda n=name: self._save_accent_preference(n))
            btn.pack(side="left", padx=5)

        # 2. Account Type
        self._add_section_header(ar(get_text("account_type", lang)))
        sec_account = self._create_section_box()
        row_role = ctk.CTkFrame(sec_account, fg_color="transparent")
        row_role.pack(fill="x", pady=10, padx=15)

        self.role_var = tk.StringVar(value=self.app.role)
        ctk.CTkRadioButton(row_role, text=ar(get_text("user", lang)), variable=self.role_var, value="user",
                           command=self._on_role_change).pack(side="right", padx=10)
        ctk.CTkRadioButton(row_role, text=ar(get_text("admin", lang)), variable=self.role_var, value="admin",
                           command=self._on_role_change).pack(side="right", padx=10)

        # 3. Language
        self._add_section_header(ar(get_text("language", lang)))
        sec_lang = self._create_section_box()
        row_lang = ctk.CTkFrame(sec_lang, fg_color="transparent")
        row_lang.pack(fill="x", pady=10, padx=15)

        current_lang_name = LANGUAGES.get(self.app.lang, "العربية")
        self.lang_combo = ctk.CTkComboBox(row_lang, values=list(LANGUAGES.values()),
                                          height=45, corner_radius=15,
                                          fg_color=t["entry_bg"], border_color=t["search_border"],
                                          button_color=t["accent"], button_hover_color=t["accent_hover"],
                                          font=FONTS["body"], dropdown_font=FONTS["body"],
                                          command=self._apply_language)
        self.lang_combo.set(current_lang_name)
        self.lang_combo.pack(side="left", padx=10)
        ctk.CTkLabel(row_lang, text=ar(get_text("language", lang)), font=FONTS["body"]).pack(side="right", padx=10)

        # 4. Store Data
        self._add_section_header(ar(get_text("account_settings", lang)))
        sec_data = self._create_section_box()
        fields = [
            (get_text("shop_name_label", lang), "shop_name", "المتجر"),
            (get_text("currency_label", lang), "currency", "DZD"),
            (get_text("low_stock_label", lang), "low_stock_threshold", "5"),
        ]
        self.vars = {}
        for label, key, default in fields:
            r = ctk.CTkFrame(sec_data, fg_color="transparent")
            r.pack(fill="x", pady=8, padx=10)
            ctk.CTkLabel(r, text=ar(label), font=FONTS["body"]).pack(side="right", padx=12)
            var = tk.StringVar(value=db.get_setting(key, default))
            self.vars[key] = var
            entry = ctk.CTkEntry(r, textvariable=var, width=220, height=45,
                                 corner_radius=15, fg_color=t["entry_bg"],
                                 border_color=t["search_border"], border_width=1,
                                 font=FONTS["body"])
            entry.pack(side="left", padx=12)
            # Modern focus effects
            entry.bind("<FocusIn>", lambda e, w=entry: w.configure(border_color=t["accent"]))
            entry.bind("<FocusOut>", lambda e, w=entry: w.configure(border_color=t["search_border"]))

        # 5. Password Section (Admin only)
        if self.app.role == "admin":
            self._add_section_header(ar(get_text("change_password", lang)))
            sec_pwd = self._create_section_box()
            self.current_pwd_var = tk.StringVar()
            self.new_pwd_var = tk.StringVar()
            self.confirm_pwd_var = tk.StringVar()

            password_fields = [
                ("current_password_label", self.current_pwd_var),
                ("new_password_label", self.new_pwd_var),
                ("confirm_password_label", self.confirm_pwd_var)
            ]

            for lbl_key, var in password_fields:
                p = ctk.CTkFrame(sec_pwd, fg_color="transparent")
                p.pack(fill="x", pady=8, padx=10)
                ctk.CTkLabel(p, text=ar(get_text(lbl_key, lang)), font=FONTS["body"]).pack(side="right", padx=12)
                entry = ctk.CTkEntry(p, textvariable=var, show="•", width=220, height=45,
                                     corner_radius=15, fg_color=t["entry_bg"],
                                     border_color=t["search_border"], border_width=1,
                                     font=FONTS["body"])
                entry.pack(side="left", padx=12)
                # Modern focus effects
                entry.bind("<FocusIn>", lambda e, w=entry: w.configure(border_color=t["accent"]))
                entry.bind("<FocusOut>", lambda e, w=entry: w.configure(border_color=t["search_border"]))

        # Save Button
        ctk.CTkButton(self.scroll, text=ar(get_text("save_settings", lang)),
                      font=ctk.CTkFont(size=16, weight="bold"),
                      fg_color=t["accent"], hover_color=t["accent_hover"],
                      height=48, corner_radius=12,
                      command=self._save_all).pack(pady=40)

    def _add_section_header(self, title):
        ctk.CTkLabel(self.scroll, text=title, font=FONTS["subhead"],
                     text_color=self.app.T["text2"]).pack(anchor="e", padx=15, pady=(20, 5))

    def _create_section_box(self):
        box = ctk.CTkFrame(self.scroll, fg_color=self.app.T["bg3"], corner_radius=15)
        box.pack(fill="x", padx=10, pady=(0, 10))
        return box

    def _save_theme_preference(self):
        db.set_setting("theme", self.theme_var.get())
        RestartDialog(self.app)

    def _save_accent_preference(self, color_name):
        db.set_setting("accent_color", color_name)
        RestartDialog(self.app)

    def _apply_language(self, choice):
        lang_map = {v: k for k, v in LANGUAGES.items()}
        lang_code = lang_map.get(choice, "ar")
        db.set_setting("language", lang_code)
        self.app.refresh_ui()

    def _on_role_change(self):
        if self.role_var.get() == "admin":
            def check_pwd(pwd):
                if pwd == db.get_setting("admin_password", "admin123"):
                    self.app.switch_to_admin()
                else:
                    if pwd is not None:
                        CustomDialog(self, get_text("error", self.app.lang), get_text("wrong_password", self.app.lang))
                    self.role_var.set("user")

            CustomInputDialog(self, get_text("password_required", self.app.lang),
                              get_text("enter_password", self.app.lang), check_pwd)
        else:
            self.app.switch_to_user()

    def _save_all(self):
        # Handle password change if admin
        if hasattr(self, 'new_pwd_var'):
            curr_p = self.current_pwd_var.get().strip()
            np, cp = self.new_pwd_var.get().strip(), self.confirm_pwd_var.get().strip()

            if curr_p or np or cp:
                stored_p = db.get_setting("admin_password", "admin123")
                if curr_p != stored_p:
                    CustomDialog(self, get_text("error", self.app.lang), get_text("wrong_current_password", self.app.lang))
                    return

                if np:
                    if np == cp:
                        db.set_setting("admin_password", np)
                    else:
                        CustomDialog(self, get_text("error", self.app.lang), get_text("passwords_dont_match", self.app.lang))
                        return

        # Handle other settings
        for k, v in self.vars.items():
            db.set_setting(k, v.get().strip())

        CustomDialog(self, get_text("success", self.app.lang), get_text("settings_saved", self.app.lang))
        self.app.refresh_ui()

    def refresh_ui(self):
        for w in self.winfo_children(): w.destroy()
        self._build()
