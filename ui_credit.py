import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import database as db
from theme import FONTS, PRIMARY_FONT
from languages import get_text
from arabic_fixer import ar
from ui_components import CustomDialog

class CreditTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=app.T["bg2"])
        self.app = app
        self.selected_customer = None
        self._build()

    def _build(self):
        t = self.app.T
        lang = self.app.lang

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 20))

        ctk.CTkButton(header, text=ar(get_text("add_customer", lang)),
                      font=ctk.CTkFont(family=PRIMARY_FONT, size=15, weight="bold"),
                      fg_color=t["accent"], hover_color=t["accent_hover"],
                      height=45, corner_radius=12,
                      command=self._add_customer_dialog).pack(side="right")

        ctk.CTkLabel(header, text=ar(get_text("credit", lang)),
                     font=FONTS["title"], text_color=t["text"]).pack(side="left")

        # Main Layout
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        # Right Section: Clients Sidebar (RTL: Sidebar on the right)
        self.sidebar_frame = ctk.CTkFrame(self.container, fg_color="transparent", width=380)
        self.sidebar_frame.pack(side="right", fill="both", padx=(10, 0))
        self.sidebar_frame.pack_propagate(False)

        # "My clients" Label
        ctk.CTkLabel(self.sidebar_frame, text=ar(get_text("my_clients", lang)),
                     font=ctk.CTkFont(family=PRIMARY_FONT, size=18, weight="bold"),
                     text_color=t["text"]).pack(pady=(0, 10), anchor="e")

        # Customer List
        self.left_panel = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent")
        self.left_panel.pack(fill="both", expand=True)

        # Left Section: Debt Details (RTL: Details on the left)
        self.details_panel = ctk.CTkFrame(self.container, fg_color=t["bg2"], corner_radius=20)
        self.details_panel.pack(side="left", fill="both", expand=True)

        self._load_customers()
        self._show_empty_details()

    def _load_customers(self):
        for w in self.left_panel.winfo_children(): w.destroy()
        customers = db.get_all_customers_summary()
        t = self.app.T
        currency = db.get_setting("currency", "DZD")

        if not customers:
            ctk.CTkLabel(self.left_panel, text=ar(get_text("no_data", self.app.lang)),
                         font=FONTS["body"], text_color=t["text2"]).pack(pady=50)
            return

        for c in customers:
            card = ctk.CTkFrame(self.left_panel, fg_color=t["bg3"], corner_radius=15, cursor="hand2")
            card.pack(fill="x", pady=5, padx=5)

            # Hover effect
            def on_enter(e, r=card): r.configure(border_width=2, border_color=t["accent"])
            def on_leave(e, r=card): r.configure(border_width=0)
            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)

            card.bind("<Button-1>", lambda e, cust=c: self._show_details(cust))

            # Customer Name
            name_lbl = ctk.CTkLabel(card, text=ar(c["name"]), font=FONTS["subhead"], text_color=t["text"])
            name_lbl.pack(side="right", padx=15, pady=15)
            name_lbl.bind("<Button-1>", lambda e, cust=c: self._show_details(cust))

            # Total Debt
            debt_lbl = ctk.CTkLabel(card, text=f"{c['total_debt']:.2f} {currency}",
                         font=ctk.CTkFont(family=PRIMARY_FONT, size=15, weight="bold"),
                         text_color=t["danger"])
            debt_lbl.pack(side="left", padx=15)
            debt_lbl.bind("<Button-1>", lambda e, cust=c: self._show_details(cust))

    def _show_empty_details(self):
        for w in self.details_panel.winfo_children(): w.destroy()
        self.details_panel.configure(border_width=0)
        ctk.CTkLabel(self.details_panel, text=ar(get_text("select_item_hint", self.app.lang)),
                     font=FONTS["body"], text_color=self.app.T["text2"]).pack(expand=True)

    def _show_details(self, customer):
        self.selected_customer = customer
        for w in self.details_panel.winfo_children(): w.destroy()
        t = self.app.T
        lang = self.app.lang

        self.details_panel.configure(border_width=2, border_color=t["accent"])

        # Header for details
        header = ctk.CTkFrame(self.details_panel, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=25)

        # Name and Phone container (on the right for RTL)
        name_phone_f = ctk.CTkFrame(header, fg_color="transparent")
        name_phone_f.pack(side="right")

        ctk.CTkLabel(name_phone_f, text=ar(customer["name"]),
                     font=ctk.CTkFont(family=PRIMARY_FONT, size=24, weight="bold"),
                     text_color=t["accent"]).pack(anchor="e")

        if customer.get("phone"):
            ctk.CTkLabel(name_phone_f, text=ar(customer["phone"]),
                         font=FONTS["body"], text_color=t["text2"]).pack(anchor="e")

        # Delete Customer Button
        ctk.CTkButton(header, text=ar(get_text("delete", lang)), fg_color=t["danger"], width=100, height=35, corner_radius=10,
                      command=lambda: self._confirm_delete_customer(customer)).pack(side="left", padx=10)

        currency = db.get_setting("currency", "DZD")
        ctk.CTkLabel(header, text=f"{customer['total_debt']:.2f} {currency}",
                     font=ctk.CTkFont(family=PRIMARY_FONT, size=22, weight="bold"), text_color=t["danger"]).pack(side="left")

        # Scrollable area for history
        scroll = ctk.CTkScrollableFrame(self.details_panel, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        history = db.get_customer_history(customer["id"])
        # Group by sale_date
        groups = {}
        for d in history:
            ts = d["sale_date"]
            if ts not in groups: groups[ts] = {"items": [], "is_paid": d["is_paid"]}
            groups[ts]["items"].append(d)

        sorted_ts = sorted(groups.keys(), reverse=True)
        for ts in sorted_ts:
            g = groups[ts]
            is_paid = g["is_paid"]

            row_bg = t["bg3"]
            sale_f = ctk.CTkFrame(scroll, fg_color=row_bg, corner_radius=15)
            sale_f.pack(fill="x", pady=8, padx=5)

            top = ctk.CTkFrame(sale_f, fg_color="transparent")
            top.pack(fill="x", padx=15, pady=10)

            # Date on the right
            ctk.CTkLabel(top, text=ts, font=FONTS["small"], text_color=t["text2"]).pack(side="right")

            # Paid Status in header if already paid
            if is_paid:
                ctk.CTkLabel(top, text=ar(get_text("paid", lang)), font=ctk.CTkFont(weight="bold"), text_color=t["success"]).pack(side="left")

            ctk.CTkFrame(sale_f, fg_color=t["border"], height=1).pack(fill="x", padx=15)

            for item in g["items"]:
                item_row = ctk.CTkFrame(sale_f, fg_color="transparent")
                item_row.pack(fill="x", padx=20, pady=8)

                # Use Grid for perfect alignment: [Left: Btn+Price] [Center: Qty] [Right: Name]
                item_row.columnconfigure(0, weight=1)
                item_row.columnconfigure(1, weight=1)
                item_row.columnconfigure(2, weight=1)

                # 1. FAR LEFT: Payer Button and Total Price
                left_box = ctk.CTkFrame(item_row, fg_color="transparent")
                left_box.grid(row=0, column=0, sticky="w")

                if not is_paid:
                    ctk.CTkButton(left_box, text=ar(get_text("pay", lang)), width=80, height=32,
                                  fg_color=t["success"], hover_color="#15803d",
                                  font=ctk.CTkFont(family=PRIMARY_FONT, size=12, weight="bold"),
                                  command=lambda d=ts: self._pay_sale(customer["id"], d)).pack(side="left", padx=(0, 10))

                ctk.CTkLabel(left_box, text=f"{item['total']:.2f} {currency}",
                             font=ctk.CTkFont(family=PRIMARY_FONT, size=15, weight="bold"),
                             text_color=t["text"] if is_paid else t["danger"]).pack(side="left")

                # 2. CENTER: Quantity
                ctk.CTkLabel(item_row, text=f"x{item['quantity']}",
                             font=ctk.CTkFont(family=PRIMARY_FONT, size=15, weight="bold")).grid(row=0, column=1)

                # 3. FAR RIGHT: Product Name
                ctk.CTkLabel(item_row, text=ar(item["product_name"]), font=FONTS["body"],
                             anchor="e").grid(row=0, column=2, sticky="e")

    def _pay_sale(self, customer_id, sale_date):
        def cb(res):
            if res:
                if db.mark_sale_group_as_paid(customer_id, sale_date):
                    self.refresh()
                    if "analytics" in self.app.pages: self.app.pages["analytics"].refresh()
        CustomDialog(self, get_text("pay", self.app.lang), get_text("confirm", self.app.lang), True, cb)

    def _confirm_delete_customer(self, customer):
        def cb(res):
            if res:
                db.delete_customer(customer["id"])
                self.selected_customer = None
                self.refresh()
        CustomDialog(self, get_text("confirm_delete", self.app.lang), f"{get_text('delete', self.app.lang)} {customer['name']}?", True, cb)

    def _add_customer_dialog(self):
        AddCustomerDialog(self, self._add_customer)

    def _add_customer(self, data):
        if not data: return
        name, phone = data
        ok, msg = db.add_customer(name.strip(), phone.strip())
        if ok:
            self._load_customers()
        else:
            CustomDialog(self, get_text("error", self.app.lang), msg)

    def refresh(self):
        self._load_customers()
        if self.selected_customer:
            # Re-fetch customer data to get updated summary
            customers = db.get_all_customers_summary()
            found = next((c for c in customers if c["id"] == self.selected_customer["id"]), None)
            if found:
                self._show_details(found)
            else:
                self._show_empty_details()
        else:
            self._show_empty_details()

class AddCustomerDialog(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        master = parent.winfo_toplevel()
        super().__init__(master)
        self.callback = callback
        t = parent.app.T
        lang = parent.app.lang

        # 1. Hide during setup
        self.withdraw()
        self.title(ar(get_text("add_customer", lang)))
        self.configure(fg_color=t["bg"])

        # 2. Geometry
        self.width = 400
        self.height = 350
        self.resizable(False, False)

        # 3. Center Window
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw // 2) - (self.width // 2)
        y = (sh // 2) - (self.height // 2)
        self.geometry(f"{self.width}x{self.height}+{x}+{y}")

        # 4. Reveal
        self.deiconify()

        self.transient(master)
        self.grab_set()

        container = ctk.CTkFrame(self, fg_color=t["bg2"], corner_radius=20, border_width=1, border_color=t["border"])
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text=ar(get_text("add_customer", lang)),
                     font=ctk.CTkFont(size=20, weight="bold"), text_color=t["accent"]).pack(pady=20)

        self.name_entry = ctk.CTkEntry(container, placeholder_text=ar(get_text("customer_name", lang)),
                                      height=45, width=300, corner_radius=12)
        self.name_entry.pack(pady=10)

        self.phone_entry = ctk.CTkEntry(container, placeholder_text=ar(get_text("phone", lang)),
                                       height=45, width=300, corner_radius=12)
        self.phone_entry.pack(pady=10)

        btn_f = ctk.CTkFrame(container, fg_color="transparent")
        btn_f.pack(side="bottom", pady=20)

        ctk.CTkButton(btn_f, text=ar(get_text("confirm", lang)), fg_color=t["success"],
                      width=120, height=40, corner_radius=10, command=self._submit).pack(side="right", padx=10)
        ctk.CTkButton(btn_f, text=ar(get_text("cancel", lang)), fg_color=t["danger"],
                      width=120, height=40, corner_radius=10, command=self.destroy).pack(side="right", padx=10)

        # Focus name entry
        self.name_entry.focus_set()

    def _submit(self):
        name = self.name_entry.get()
        phone = self.phone_entry.get()
        if not name: return
        self.callback((name, phone))
        self.destroy()
