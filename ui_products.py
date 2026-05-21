import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import database as db
from theme import FONTS, PRIMARY_FONT, MONO_FONT, get_icon
from languages import get_text
from arabic_fixer import ar
from ui_components import CustomDialog

class ProductFormDialog(ctk.CTkToplevel):
    """Modal dialog for adding or editing products with zero-lag centering."""
    def __init__(self, parent_tab, title, product_data=None):
        super().__init__(parent_tab.app)
        self.parent_tab = parent_tab
        self.app = parent_tab.app
        self.product_data = product_data # Dict if editing, None if adding

        # 1. Hide window during setup to prevent flickering
        self.withdraw()
        self.title(ar(title))
        t = self.app.T
        self.configure(fg_color=t["bg"])

        # 2. Define geometry and center instantly
        self.width = 460
        self.height = 720
        self.resizable(False, False)

        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw // 2) - (self.width // 2)
        y = (sh // 2) - (self.height // 2)
        self.geometry(f"{self.width}x{self.height}+{x}+{y}")

        # 3. Build UI and Reveal
        self._build()
        self.deiconify() # Reveal instantly in the center

        # 4. Modal behavior (Must be after deiconify)
        self.transient(self.app)
        self.grab_set()
        self.focus_force()

    def _build(self):
        t = self.app.T
        lang = self.app.lang

        # Validation Commands
        def validate_int(P):
            return P == "" or P.isdigit()

        def validate_float(P):
            if P == "": return True
            if P == ".": return True
            try:
                float(P)
                return True
            except ValueError: return False

        v_int = (self.register(validate_int), '%P')
        v_float = (self.register(validate_float), '%P')

        # Main Scrollable Container
        container = ctk.CTkScrollableFrame(self, fg_color=t["bg2"], corner_radius=20,
                                           scrollbar_button_color=t["accent"],
                                           scrollbar_button_hover_color=t["accent_hover"])
        container.pack(fill="both", expand=True, padx=20, pady=(20, 10))

        ctk.CTkLabel(container, text=ar(self.product_data['name'] if self.product_data else get_text("add_product", lang)),
                     font=ctk.CTkFont(family=PRIMARY_FONT, size=22, weight="bold"),
                     text_color=t["accent"]).pack(pady=(10, 25))

        fields = [
            ("name", ar(get_text("name_label", lang)), None),
            ("barcode", ar(get_text("barcode_label", lang)), v_int),
            ("category", ar(get_text("category_label", lang)), None),
            ("buy_price", ar(get_text("buy_price_label", lang)), v_float),
            ("sell_price", ar(get_text("sell_price_label", lang)), v_float),
            ("quantity", ar(get_text("quantity_label", lang)), v_int),
            ("min_stock", ar(get_text("min_stock_label", lang)), v_int),
        ]

        self.vars = {}
        for key, label, val_cmd in fields:
            f = ctk.CTkFrame(container, fg_color="transparent")
            f.pack(fill="x", pady=8, padx=15)
            ctk.CTkLabel(f, text=label, font=FONTS["small"], text_color=t["text2"]).pack(anchor="e")

            var = tk.StringVar()
            if self.product_data:
                val = str(self.product_data.get(key, "")) if self.product_data.get(key) is not None else ""
                var.set(val)
            elif key == "min_stock":
                var.set("5")

            self.vars[key] = var
            entry = ctk.CTkEntry(f, textvariable=var, height=45, corner_radius=15,
                                 fg_color=t["entry_bg"], border_color=t["search_border"],
                                 border_width=1, font=FONTS["body"])
            if val_cmd:
                entry.configure(validate='key', validatecommand=val_cmd)
            entry.pack(fill="x", pady=(4, 0))

            # Modern focus effects
            entry.bind("<FocusIn>", lambda e, w=entry: w.configure(border_color=t["accent"]))
            entry.bind("<FocusOut>", lambda e, w=entry: w.configure(border_color=t["search_border"]))

        # Action Buttons Area
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom", pady=25, padx=25)

        if not self.product_data:
            # Add Mode: Enregistrer, Quitter
            ctk.CTkButton(btn_frame, text=ar(get_text("save", lang)), fg_color=t["success"],
                          hover_color="#15803d", height=50, corner_radius=12, font=FONTS["subhead"],
                          command=self._on_save).pack(side="right", expand=True, padx=5)
            ctk.CTkButton(btn_frame, text=ar(get_text("back", lang)), fg_color=t["danger"],
                          hover_color="#991b1b", height=50, corner_radius=12, font=FONTS["subhead"],
                          command=self.destroy).pack(side="right", expand=True, padx=5)
        else:
            # Edit Mode: Confirmer, Vider, Quitter
            ctk.CTkButton(btn_frame, text=ar(get_text("confirm", lang)), fg_color=t["accent2"],
                          hover_color="#2563eb", height=50, corner_radius=12, font=FONTS["subhead"],
                          command=self._on_save).pack(side="right", expand=True, padx=3)
            ctk.CTkButton(btn_frame, text=ar(get_text("clear", lang)), fg_color=t["bg3"], text_color=t["text"],
                          height=50, corner_radius=12, font=FONTS["subhead"],
                          command=self._on_clear).pack(side="right", expand=True, padx=3)
            ctk.CTkButton(btn_frame, text=ar(get_text("back", lang)), fg_color=t["danger"],
                          hover_color="#991b1b", height=50, corner_radius=12, font=FONTS["subhead"],
                          command=self.destroy).pack(side="right", expand=True, padx=3)

    def _on_clear(self):
        for var in self.vars.values(): var.set("")
        if "min_stock" in self.vars: self.vars["min_stock"].set("5")

    def _on_save(self):
        data = {k: v.get().strip() for k, v in self.vars.items()}
        if not data["name"]:
            return CustomDialog(self, get_text("error", self.app.lang), get_text("product_name_req", self.app.lang))

        try:
            if not self.product_data:
                ok, msg = db.add_product(data["name"], data["barcode"], data["category"],
                                         float(data["buy_price"] or 0), float(data["sell_price"] or 0),
                                         int(data["quantity"] or 0), int(data["min_stock"] or 5))
            else:
                ok, msg = db.update_product(self.product_data["id"], data["name"], data["barcode"], data["category"],
                                            float(data["buy_price"] or 0), float(data["sell_price"] or 0),
                                            int(data["quantity"] or 0), int(data["min_stock"] or 5))

            if ok:
                self.parent_tab.refresh()
                self.app.refresh_alerts()
                self.destroy()
            else:
                CustomDialog(self, get_text("error", self.app.lang), msg)
        except ValueError:
            CustomDialog(self, get_text("error", self.app.lang), get_text("data_error", self.app.lang))


class ProductsTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=app.T["bg2"])
        self.app = app
        self.selected_id = None
        self.edit_btn = None
        self.delete_btn = None
        self.last_role = app.role
        self._build()

    def _build(self):
        t = self.app.T
        lang = self.app.lang
        role = self.app.role

        # 1. Top Bar: Full-width Search and Action Buttons
        top_bar = ctk.CTkFrame(self, fg_color=t["bg3"], corner_radius=15)
        top_bar.pack(fill="x", pady=(0, 15))

        # Search Box (Right Side)
        search_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        search_frame.pack(side="right", fill="x", expand=True, padx=20, pady=20)

        entry_row = ctk.CTkFrame(search_frame, fg_color="transparent")
        entry_row.pack(fill="x")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._load_products())

        # OneUI-Inspired Search Bar for consistency
        self.search_entry = ctk.CTkEntry(entry_row, textvariable=self.search_var,
                                         placeholder_text=ar(get_text("search_placeholder", lang)),
                                         height=50, font=(MONO_FONT, 18),
                                         fg_color=t["bg2"], border_color=t["search_border"],
                                         border_width=1, corner_radius=25)
        self.search_entry.pack(side="right", fill="x", expand=True, padx=(0, 20))
        self.search_entry.bind("<FocusIn>", lambda e: self.search_entry.configure(border_color=t["accent"]))
        self.search_entry.bind("<FocusOut>", lambda e: self.search_entry.configure(border_color=t["search_border"]))
        self.search_entry.bind("<Return>", lambda e: self._load_products())

        ctk.CTkButton(entry_row, text="", image=get_icon("search", color="#ffffff"),
                      fg_color=t["accent2"], hover_color="#2563eb",
                      height=50, width=50, corner_radius=25,
                      command=self._load_products).pack(side="right", padx=(10, 0))

        # Admin Action Buttons (Left Side)
        if role == "admin":
            actions_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
            actions_frame.pack(side="left", padx=20)

            self.delete_btn = ctk.CTkButton(actions_frame, text=ar(get_text("delete", lang)),
                                           image=get_icon("delete", color="#ffffff"),
                                           fg_color=t["danger"], state="disabled",
                                           height=48, corner_radius=12,
                                           font=ctk.CTkFont(family=PRIMARY_FONT, weight="bold"),
                                           command=self._on_delete)
            self.delete_btn.pack(side="left", padx=6)

            self.edit_btn = ctk.CTkButton(actions_frame, text=ar(get_text("edit", lang)),
                                         image=get_icon("edit", color="#ffffff"),
                                         fg_color=t["accent2"], state="disabled",
                                         height=48, corner_radius=12,
                                         font=ctk.CTkFont(family=PRIMARY_FONT, weight="bold"),
                                         command=self._open_edit)
            self.edit_btn.pack(side="left", padx=6)

            ctk.CTkButton(actions_frame, text=ar(get_text("add", lang)),
                          image=get_icon("add", color="#ffffff"),
                          fg_color=t["success"], hover_color="#15803d",
                          height=48, corner_radius=12,
                          font=ctk.CTkFont(family=PRIMARY_FONT, weight="bold"),
                          command=self._open_add).pack(side="left", padx=6)

        # 2. Main Table Area (Expanded Full Width)
        table_frame = ctk.CTkFrame(self, fg_color=t["bg3"], corner_radius=15)
        table_frame.pack(fill="both", expand=True)

        cols = ["id", "name", "barcode", "category", "stock"]
        heads = [
            ("ID", 50), (ar(get_text("product", lang)), 280),
            (ar(get_text("barcode_label", lang)), 160), (ar(get_text("category_label", lang)), 160),
            (ar(get_text("stock", lang)), 100)
        ]

        if role == "admin":
            cols.append("buy")
            heads.append((ar(get_text("buy_price", lang)), 130))

        cols.append("sell")
        heads.append((ar(get_text("sell_price", lang)), 130))

        self.tree = ttk.Treeview(table_frame, columns=tuple(cols), show="headings", style="Treeview")

        for col, (h, w) in zip(cols, heads):
            self.tree.heading(col, text=h)
            self.tree.column(col, width=w, anchor="center")

        # Hide Technical ID Column
        self.tree.column("id", width=0, stretch=False)

        # Layout Treeview and Scrollbar
        self.scrollbar = ctk.CTkScrollbar(table_frame, orientation="vertical",
                                          command=self.tree.yview,
                                          fg_color="transparent",
                                          button_color=t["accent"],
                                          button_hover_color=t["accent_hover"])
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y", padx=2, pady=5)
        self.tree.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=15)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self._load_products()

    def _on_select(self, e):
        sel = self.tree.selection()
        if not sel:
            if self.edit_btn: self.edit_btn.configure(state="disabled")
            if self.delete_btn: self.delete_btn.configure(state="disabled")
            self.selected_id = None
            return

        self.selected_id = self.tree.item(sel[0])["values"][0]
        if self.edit_btn: self.edit_btn.configure(state="normal")
        if self.delete_btn: self.delete_btn.configure(state="normal")

    def _open_add(self):
        ProductFormDialog(self, get_text("add", self.app.lang))

    def _open_edit(self):
        if not self.selected_id: return
        p = db.get_product_by_id(self.selected_id)
        if p:
            ProductFormDialog(self, get_text("edit", self.app.lang), product_data=p)

    def _on_delete(self):
        if not self.selected_id: return

        def confirm_callback(confirmed):
            if confirmed:
                db.delete_product(self.selected_id)
                self.refresh()
                self.app.refresh_alerts()

        CustomDialog(self, get_text("confirm_delete", self.app.lang),
                     get_text("delete_product_confirm", self.app.lang),
                     is_question=True, callback=confirm_callback)

    def _load_products(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        query = self.search_var.get().strip()

        products = db.search_products(query) if query else db.get_all_products()
        role = self.app.role

        for p in products:
            vals = [p["id"], p["name"], p["barcode"] or "-", p["category"] or "-", p["quantity"]]
            if role == "admin":
                vals.append(f"{p['buy_price']:.2f}")
            vals.append(f"{p['sell_price']:.2f}")
            self.tree.insert("", "end", values=tuple(vals))

    def refresh(self):
        # Rebuild UI if role changed (e.g. from Seller to Admin)
        if self.last_role != self.app.role:
            self.refresh_ui()
        self.last_role = self.app.role

        self._load_products()
        if self.edit_btn: self.edit_btn.configure(state="disabled")
        if self.delete_btn: self.delete_btn.configure(state="disabled")

    def refresh_ui(self):
        for w in self.winfo_children(): w.destroy()
        self._build()
