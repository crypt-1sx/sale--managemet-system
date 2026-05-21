import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import database as db
from languages import get_text
from arabic_fixer import ar

class NotificationsTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=app.T["bg2"])
        self.app = app
        self._build()

    def _build(self):
        t = self.app.T
        lang = self.app.lang

        # Header
        header = ctk.CTkFrame(self, fg_color=t["bg3"], corner_radius=15)
        header.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(header, text=ar(get_text("notifications", lang)),
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=t["accent"]).pack(side="right", padx=20, pady=15)

        self.clear_btn = ctk.CTkButton(header, text=ar(get_text("clear_logs", lang)), width=140, height=35,
                                      fg_color=t["danger"], corner_radius=8,
                                      command=self._clear_all)

        if self.app.role == "admin":
            self.clear_btn.pack(side="left", padx=20)

        # Table Container
        table_frame = ctk.CTkFrame(self, fg_color=t["bg3"], corner_radius=15)
        table_frame.pack(fill="both", expand=True)

        cols = ("time", "product", "status", "stock", "min")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", style="Treeview")

        heads = [
            (ar(get_text("time", lang)), 150),
            (ar(get_text("product", lang)), 300),
            (ar(get_text("status", lang)), 150),
            (ar(get_text("stock", lang)), 120),
            (ar(get_text("min_stock_label", lang)), 120)
        ]

        for col, (h, w) in zip(cols, heads):
            self.tree.heading(col, text=h)
            self.tree.column(col, width=w, anchor="center")

        self.scrollbar = ctk.CTkScrollbar(table_frame, orientation="vertical",
                                          command=self.tree.yview,
                                          fg_color="transparent",
                                          button_color=t["accent"],
                                          button_hover_color=t["accent_hover"])
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y", padx=2, pady=5)
        self.tree.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=15)

        self.refresh()

    def _clear_all(self):
        db.clear_notifications()
        self.refresh()

    def refresh(self):
        # Update button visibility if role changed
        if self.app.role == "admin":
            self.clear_btn.pack(side="left", padx=20)
        else:
            self.clear_btn.pack_forget()

        for item in self.tree.get_children(): self.tree.delete(item)
        notes = db.get_notifications()
        lang = self.app.lang
        for n in notes:
            time_display = n["time"]
            # Fallback to 'low_stock' if status is missing or unknown
            status_val = n.get("status")
            status_key = "refilled" if status_val == "refilled" else "low_stock"
            status_text = get_text(status_key, lang)

            self.tree.insert("", "end", values=(
                time_display, ar(n["product_name"]), ar(status_text), n["quantity"], n["min_stock"]
            ))
