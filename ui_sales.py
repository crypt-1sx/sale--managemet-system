import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import database as db
import keybinds
from theme import FONTS, PRIMARY_FONT, MONO_FONT, get_icon
from languages import get_text
from arabic_fixer import ar
from ui_components import CustomDialog, CustomTextInputDialog, CustomSelectionDialog
from datetime import datetime

class SalesTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=app.T["bg2"])
        self.app = app
        self.cart = []
        self.selected_product = None
        self.selected_sale_group = None
        self.highlighted_index = -1
        self.search_results = []
        self.last_role = app.role
        self.credit_customer = None # New: track selected customer for credit sale

        # UI Elements
        self.info_panel = None
        self.results_list = None
        self.cart_list_frame = None
        self.recent_tree = None

        self._build()
        self._setup_keybinds()

    def _setup_keybinds(self):
        self.app.bind("<Key>", self._handle_keypress, add="+")

    def _handle_keypress(self, event):
        if self.app.active_page != "sales": return
        key = event.keysym
        char = event.char

        # Focus Search (F)
        if key in keybinds.SALES_KEYS["focus_search"]:
            focused = self.app.focus_get()
            if not isinstance(focused, (ctk.CTkEntry, tk.Entry)) or focused == self.barcode_entry:
                self.barcode_entry.focus_set()
                return "break"

        # Omni-Search: If user types alphanumeric and not in an entry, focus search bar
        if char and char.isalnum():
            focused = self.app.focus_get()
            if not isinstance(focused, (ctk.CTkEntry, tk.Entry)):
                self.barcode_entry.focus_set()
                # The character will be typed automatically because we just focused it
                # but in some cases we might need to manually insert it if focus happens after event
                return

        # Confirm Bulk Sale (Global Control key if nothing else focused)
        if key in keybinds.SALES_KEYS["confirm_sale"] and self.cart:
            if not self.selected_product and not self.barcode_var.get():
                self._confirm_bulk_sale()
                return "break"

    def _build(self):
        t = self.app.T
        lang = self.app.lang

        # --- MAIN LAYOUT ---
        self.side_panel = ctk.CTkFrame(self, fg_color=t["bg3"], width=380, corner_radius=20)
        self.side_panel.pack(side="right", fill="y", padx=(10, 0))
        self.side_panel.pack_propagate(False)

        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.pack(side="left", fill="both", expand=True)

        # --- MAIN AREA ---
        actions_header = ctk.CTkFrame(self.main_area, fg_color="transparent")
        actions_header.pack(fill="x", pady=(20, 10))

        self.confirm_btn = ctk.CTkButton(actions_header, text=ar(get_text("confirm", lang)),
                                         image=get_icon("confirm", color="#ffffff"),
                                         font=ctk.CTkFont(family=PRIMARY_FONT, size=16, weight="bold"),
                                         fg_color=t["success"], hover_color="#15803d",
                                         height=45, width=150, corner_radius=12,
                                         state="disabled",
                                         command=self._confirm_bulk_sale)
        self.confirm_btn.pack(side="right")

        self.clear_cart_btn = ctk.CTkButton(actions_header, text=ar(get_text("clear", lang)),
                                            image=get_icon("clear", color="#ffffff"),
                                            font=ctk.CTkFont(family=PRIMARY_FONT, size=16, weight="bold"),
                                            fg_color=t["danger"], hover_color="#991b1b",
                                            height=45, width=120, corner_radius=12,
                                            command=self._clear_cart_instantly)
        self.clear_cart_btn.pack(side="right", padx=10)

        if self.app.role == "admin":
            self.credit_btn = ctk.CTkButton(actions_header, text="",
                                             image=get_icon("credit", color="#ffffff"),
                                             fg_color=t["accent2"], hover_color="#2563eb",
                                             height=45, width=60, corner_radius=12,
                                             state="disabled",
                                             command=self._confirm_credit_sale_dialog)
            self.credit_btn.pack(side="right", padx=(0, 10))

        self.tables_container = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.tables_container.pack(fill="both", expand=True)

        self.cart_box = ctk.CTkFrame(self.tables_container, fg_color="transparent",
                                     border_width=2, border_color=t["accent"],
                                     corner_radius=15)
        self.cart_box.pack(fill="both", expand=True, pady=(0, 10))

        cart_header = ctk.CTkFrame(self.cart_box, fg_color="transparent")
        cart_header.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(cart_header, text=ar(get_text("cart_title", lang)),
                     font=FONTS["subhead"], text_color=t["accent"]).pack(side="right")

        # Customer indicator for credit sale
        self.customer_lbl = ctk.CTkLabel(cart_header, text="", font=ctk.CTkFont(family=PRIMARY_FONT, size=14, weight="bold"), text_color=t["accent2"])
        self.customer_lbl.pack(side="right", padx=20)

        self.total_desc_lbl = ctk.CTkLabel(cart_header, text=ar(get_text("total", lang)) + " : ",
                                           font=ctk.CTkFont(family=PRIMARY_FONT, size=18, weight="bold"),
                                           text_color="#ffffff")
        self.total_desc_lbl.pack(side="left")

        self.cart_total_lbl = ctk.CTkLabel(cart_header, text="0.00 DZD",
                                           font=ctk.CTkFont(family=PRIMARY_FONT, size=18, weight="bold"),
                                           text_color=t["success"])
        self.cart_total_lbl.pack(side="left")

        self.cart_list_frame = ctk.CTkScrollableFrame(self.cart_box, fg_color="transparent",
                                                   scrollbar_button_color=t["accent"],
                                                   scrollbar_button_hover_color=t["accent_hover"])
        self.cart_list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.history_box = ctk.CTkFrame(self.tables_container, fg_color=t["bg3"], corner_radius=15)
        self.history_box.pack(fill="both", expand=True)

        history_header = ctk.CTkFrame(self.history_box, fg_color="transparent")
        history_header.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(history_header, text=ar(get_text("recent_sales", lang)),
                     font=FONTS["subhead"], text_color=t["text2"]).pack(side="right")

        cols = ["timestamp", "time", "products", "total"]
        if self.app.role == "admin": cols.append("profit")

        self.recent_tree = ttk.Treeview(self.history_box, columns=tuple(cols), show="headings", style="Treeview")

        heads = {"timestamp": "", "time": get_text("time", lang), "products": get_text("product", lang), "total": get_text("total", lang), "profit": get_text("profit", lang)}
        for col in cols:
            self.recent_tree.heading(col, text=ar(heads[col]))
            if col == "products": self.recent_tree.column(col, width=300, anchor="e")
            elif col == "timestamp": self.recent_tree.column(col, width=0, stretch=False)
            else: self.recent_tree.column(col, width=100, anchor="center")

        tree_scroll = ctk.CTkScrollbar(self.history_box, orientation="vertical",
                                       command=self.recent_tree.yview,
                                       fg_color="transparent",
                                       button_color=t["accent"],
                                       button_hover_color=t["accent_hover"])
        self.recent_tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side="right", fill="y", padx=2, pady=5)
        self.recent_tree.pack(fill="both", expand=True, padx=10, pady=(0, 15))
        self.recent_tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # --- SIDE PANEL ---
        search_section = ctk.CTkFrame(self.side_panel, fg_color="transparent")
        search_section.pack(fill="x", padx=15, pady=20)

        ctk.CTkLabel(search_section, text=ar(get_text("barcode_scan", lang)),
                     font=FONTS["subhead"], text_color=t["accent"]).pack(anchor="e", pady=(0, 5))

        self.barcode_var = tk.StringVar()
        # OneUI-Inspired Search Bar: Rounded, blending background
        self.barcode_entry = ctk.CTkEntry(search_section, textvariable=self.barcode_var,
                                          placeholder_text=ar(get_text("search_placeholder", lang)),
                                          height=50, font=(MONO_FONT, 16),
                                          fg_color=t["bg2"], border_color=t["search_border"],
                                          border_width=1, corner_radius=25)
        self.barcode_entry.pack(fill="x")
        self.barcode_entry.bind("<FocusIn>", lambda e: self.barcode_entry.configure(border_color=t["accent"]))
        self.barcode_entry.bind("<FocusOut>", lambda e: self.barcode_entry.configure(border_color=t["search_border"]))
        self.barcode_entry.bind("<Return>", self._on_scan)
        self.barcode_entry.bind("<KeyRelease>", self._on_key_release)
        self.barcode_entry.bind("<Down>", self._on_search_down)
        self.barcode_entry.bind("<Up>", self._on_search_up)

        self.results_list = ctk.CTkScrollableFrame(self.side_panel, fg_color=t["bg"], height=200,
                                                   border_width=1, border_color=t["border"],
                                                   scrollbar_button_color=t["accent"],
                                                   scrollbar_button_hover_color=t["accent_hover"])

        self.info_panel = ctk.CTkFrame(self.side_panel, fg_color="transparent",
                                       border_width=2, border_color=t["border"],
                                       corner_radius=15)
        self.info_panel.pack(fill="both", expand=True, padx=15, pady=(0, 20))

        self._show_empty_info()
        self._update_cart_ui()
        self._load_recent()

    def _show_empty_info(self):
        for w in self.info_panel.winfo_children(): w.destroy()
        self.info_panel.configure(border_color=self.app.T["border"])
        ctk.CTkLabel(self.info_panel, text=ar(get_text("select_item_hint", self.app.lang)),
                     font=FONTS["body"], text_color=self.app.T["text2"]).pack(expand=True)

    def _show_product_details(self, product_data, initial_qty=None):
        # Refresh product from DB to ensure real-time stock
        product = db.get_product_by_id(product_data["id"])
        if not product: return

        t = self.app.T
        lang = self.app.lang
        self.selected_product = product
        self.selected_sale_group = None
        self.recent_tree.selection_remove(self.recent_tree.selection())
        self._update_cart_ui()

        # DYNAMIC STOCK DEDUCTION: Calculate stock minus items already in cart (excluding CURRENT if editing)
        in_cart_qty = sum(item["qty"] for item in self.cart if item["id"] == product["id"])

        # We want the display_qty to show total DB stock minus what's in cart for OTHER items.
        other_items_qty = in_cart_qty - (initial_qty if initial_qty is not None else 0)
        display_qty = max(0, product["quantity"] - other_items_qty)

        for w in self.info_panel.winfo_children(): w.destroy()
        self.info_panel.configure(border_color=t["accent"])

        # Use a scrollable frame to prevent any clipping if text is long or window is small
        scroll_container = ctk.CTkScrollableFrame(self.info_panel, fg_color="transparent",
                                                  scrollbar_button_color=t["accent"],
                                                  scrollbar_button_hover_color=t["accent_hover"])
        scroll_container.pack(fill="both", expand=True, padx=5, pady=5)

        details = ctk.CTkFrame(scroll_container, fg_color="transparent")
        details.pack(fill="both", expand=True, padx=10, pady=10)

        # Subtle reveal animation
        details.pack_forget()
        def reveal():
            details.pack(fill="both", expand=True, padx=10, pady=(30, 10))
            def slide(curr):
                if curr <= 10:
                    details.pack_configure(pady=(10, 10))
                    return
                new_y = curr - 2
                details.pack_configure(pady=(new_y, 10))
                self.after(5, lambda: slide(new_y))
            slide(30)
        self.after(10, reveal)

        # Header: Product Name
        ctk.CTkLabel(details, text=ar(product["name"]),
                     font=ctk.CTkFont(family=PRIMARY_FONT, size=24, weight="bold"),
                     text_color=t["text"], wraplength=300, justify="right").pack(anchor="e", pady=(0, 10))

        # Stats Area: Stock and Price Cards
        stats = ctk.CTkFrame(details, fg_color="transparent")
        stats.pack(fill="x", pady=10)

        # Remaining shelf stock (not including what's in the cart currently)
        remaining_on_shelf = max(0, product["quantity"] - in_cart_qty)
        qty_color = t["danger"] if remaining_on_shelf == 0 else (t["warning"] if remaining_on_shelf <= product["min_stock"] else t["success"])

        # Stock Card
        stock_f = ctk.CTkFrame(stats, fg_color=t["bg3"], corner_radius=12)
        stock_f.pack(side="right", expand=True, fill="both", padx=5)
        ctk.CTkLabel(stock_f, text=ar(get_text("stock", lang)), font=FONTS["small"], text_color=t["text2"]).pack(pady=(10, 0))
        ctk.CTkLabel(stock_f, text=str(remaining_on_shelf), font=ctk.CTkFont(family=PRIMARY_FONT, size=24, weight="bold"), text_color=qty_color).pack(pady=(0, 10))

        # Price Card
        currency = db.get_setting("currency", "DZD")
        price_f = ctk.CTkFrame(stats, fg_color=t["bg3"], corner_radius=12)
        price_f.pack(side="right", expand=True, fill="both", padx=5)
        ctk.CTkLabel(price_f, text=ar(get_text("price", lang)), font=FONTS["small"], text_color=t["text2"]).pack(pady=(10, 0))
        ctk.CTkLabel(price_f, text=f"{product['sell_price']:.2f}", font=ctk.CTkFont(family=PRIMARY_FONT, size=22, weight="bold"), text_color=t["accent"]).pack(pady=(0, 10))

        # Quantity Selector Area
        adj_section = ctk.CTkFrame(details, fg_color="transparent")
        adj_section.pack(pady=25, fill="x")

        start_val = str(initial_qty) if initial_qty is not None else "1"
        self.qty_var = tk.StringVar(value=start_val)

        def adj(d):
            try:
                current_v = int(self.qty_var.get() or 0)
                new_v = max(1, current_v + d)
                limit = product["quantity"] - other_items_qty
                if new_v <= limit: self.qty_var.set(str(new_v))
            except: self.qty_var.set("1")

        # Container for horizontal alignment of - [qty] +
        adj_controls = ctk.CTkFrame(adj_section, fg_color="transparent")
        adj_controls.pack(anchor="center")

        # + Button (Packed Right for RTL feel)
        ctk.CTkButton(adj_controls, text="+", width=50, height=50, corner_radius=12,
                      font=ctk.CTkFont(size=24, weight="bold"),
                      fg_color=t["bg3"], text_color=t["text"],
                      command=lambda: adj(1)).pack(side="right", padx=10)

        # Quantity Entry
        def validate_qty(P):
            if P == "" or P.isdigit(): return True
            return False
        vcmd = (self.register(validate_qty), '%P')

        from theme import MONO_FONT
        self.qty_entry = ctk.CTkEntry(adj_controls, textvariable=self.qty_var, width=90, height=55,
                                     font=(MONO_FONT, 22, "bold"), justify="center",
                                     fg_color=t["bg2"], border_color=t["search_border"],
                                     validate='key', validatecommand=vcmd)
        self.qty_entry.pack(side="right")
        self.qty_entry.bind("<Return>", lambda e: [self._add_selected_to_cart(is_update=(initial_qty is not None)), "break"][1])
        self.qty_entry.bind("<Right>", lambda e: [adj(1), "break"][1])
        self.qty_entry.bind("<Left>", lambda e: [adj(-1), "break"][1])

        # - Button (Packed Right for RTL feel)
        ctk.CTkButton(adj_controls, text="-", width=50, height=50, corner_radius=12,
                      font=ctk.CTkFont(size=24, weight="bold"),
                      fg_color=t["bg3"], text_color=t["text"],
                      command=lambda: adj(-1)).pack(side="right", padx=10)

        # Add to Cart Button
        btn_text = get_text("confirm", lang) if initial_qty is not None else get_text("add_to_cart", lang)

        if display_qty > 0 or initial_qty is not None:
            from theme import get_icon
            self.add_to_cart_btn = ctk.CTkButton(details, text=ar(btn_text),
                          image=get_icon("confirm" if initial_qty is not None else "add", color="#ffffff"),
                          fg_color=t["success"] if initial_qty is not None else t["accent"],
                          hover_color="#15803d" if initial_qty is not None else t["accent_hover"],
                          height=60, corner_radius=15,
                          font=ctk.CTkFont(family=PRIMARY_FONT, size=18, weight="bold"),
                          command=lambda: self._add_selected_to_cart(is_update=(initial_qty is not None)))
            self.add_to_cart_btn.pack(fill="x", pady=20)
        else:
            ctk.CTkLabel(details, text=ar(get_text("empty_stock", lang)),
                         text_color=t["danger"], font=FONTS["subhead"]).pack(pady=20)

        # Final adjustments
        if hasattr(self, "qty_entry"):
            self.qty_entry.focus_set()
            self.qty_entry.select_range(0, 'end')
            self.qty_entry.icursor('end')

    def _show_sale_details(self, timestamp):
        t = self.app.T
        lang = self.app.lang
        self.selected_sale_group = timestamp
        self.selected_product = None
        self._update_cart_ui()
        for w in self.info_panel.winfo_children(): w.destroy()
        self.info_panel.configure(border_color=t["accent2"])
        container = ctk.CTkScrollableFrame(self.info_panel, fg_color="transparent",
                                           scrollbar_button_color=t["accent"],
                                           scrollbar_button_hover_color=t["accent_hover"])
        container.pack(fill="both", expand=True, padx=15, pady=15)
        ctk.CTkLabel(container, text=ar(get_text("recent_sales", lang)), font=ctk.CTkFont(size=20, weight="bold"), text_color=t["accent2"]).pack(anchor="e", pady=(0, 10))
        ctk.CTkLabel(container, text=timestamp, font=FONTS["small"], text_color=t["text2"]).pack(anchor="e", pady=(0, 15))
        sales = db.get_connection().execute("SELECT * FROM sales WHERE sale_date=?", (timestamp,)).fetchall()
        total_group = 0
        currency = db.get_setting("currency", "DZD")
        for s in sales:
            item_f = ctk.CTkFrame(container, fg_color=t["bg3"], corner_radius=10)
            item_f.pack(fill="x", pady=4)
            ctk.CTkLabel(item_f, text=ar(s["product_name"]), font=FONTS["subhead"], anchor="e").pack(fill="x", padx=10, pady=(8, 0))
            bottom = ctk.CTkFrame(item_f, fg_color="transparent")
            bottom.pack(fill="x", padx=10, pady=(0, 8))
            ctk.CTkLabel(bottom, text=f"x{s['quantity']}", font=FONTS["body"]).pack(side="right")
            # FIX: Show single item price instead of row total
            ctk.CTkLabel(bottom, text=f"{s['sell_price']:.2f} {currency}", font=ctk.CTkFont(weight="bold"), text_color=t["text"]).pack(side="left")
            total_group += s["total"]
        ctk.CTkFrame(container, fg_color=t["border"], height=2).pack(fill="x", pady=15)
        total_f = ctk.CTkFrame(container, fg_color="transparent")
        total_f.pack(fill="x")
        ctk.CTkLabel(total_f, text=ar(get_text("total", lang)), font=FONTS["heading"]).pack(side="right")
        ctk.CTkLabel(total_f, text=f"{total_group:.2f} {currency}", font=ctk.CTkFont(size=18, weight="bold"), text_color=t["success"]).pack(side="left")
        if self.app.role == "admin":
            btn_box = ctk.CTkFrame(self.info_panel, fg_color="transparent")
            btn_box.pack(fill="x", side="bottom", padx=20, pady=20)
            ctk.CTkButton(btn_box, text=ar(f"↺ {get_text('undo', lang)}"), fg_color=t["accent2"], hover_color="#2563eb", height=45, corner_radius=10, command=lambda: self._confirm_undo(timestamp)).pack(fill="x", pady=5)
            ctk.CTkButton(btn_box, text=ar(f"✕ {get_text('delete', lang)}"), fg_color=t["danger"], hover_color="#991b1b", height=45, corner_radius=10, command=lambda: self._confirm_delete(timestamp)).pack(fill="x", pady=5)

    def _on_tree_select(self, event):
        sel = self.recent_tree.selection()
        if sel:
            # Clear search selection and search results to avoid double-selection confusion
            self.selected_product = None
            self.highlighted_index = -1
            self.search_results = [] # Clear results list
            self.barcode_var.set("") # Clear search text
            self._update_results_ui()
            self._update_cart_ui()

            ts = self.recent_tree.item(sel[0], "values")[0]
            self._show_sale_details(ts)

    def _on_scan(self, event=None):
        if self.highlighted_index >= 0 and self.highlighted_index < len(self.search_results):
            self._show_product_details(self.search_results[self.highlighted_index])
            self.barcode_var.set("")
            self.results_list.pack_forget()
        else:
            query = self.barcode_var.get().strip()
            if not query: return
            product = db.get_product_by_barcode(query)
            if product: self._show_product_details(product); self.barcode_var.set(""); self.results_list.pack_forget()
            elif self.search_results: self._show_product_details(self.search_results[0]); self.barcode_var.set(""); self.results_list.pack_forget()

    def _on_key_release(self, event):
        if event and event.keysym in ("Up", "Down", "Return"): return
        query = self.barcode_var.get().strip()
        if not query:
            self.results_list.pack_forget()
            self.search_results = []
            self.highlighted_index = -1
            # Also clear the info panel if search is empty
            self._show_empty_info()
            return
        results = db.search_products(query)
        if not results:
            self.results_list.pack_forget()
            self.search_results = []
            self.highlighted_index = -1
            return
        self.search_results = results[:8]
        self.highlighted_index = 0
        self._update_results_ui()

    def _update_results_ui(self):
        # Only show the frame if there are results AND the search bar has text
        if not self.search_results or not self.barcode_var.get().strip():
            self.results_list.pack_forget()
            return

        if not self.results_list.winfo_ismapped():
            self.results_list.pack(fill="x", padx=15, pady=(0, 10), after=self.barcode_entry)
            # Subtle slide down
            self.results_list.configure(height=1)
            def expand(h):
                if h >= 200:
                    self.results_list.configure(height=200)
                    return
                new_h = h + 20
                self.results_list.configure(height=new_h)
                self.after(5, lambda: expand(new_h))
            expand(1)
        else:
            self.results_list.pack(fill="x", padx=15, pady=(0, 10), after=self.barcode_entry)

        for w in self.results_list.winfo_children(): w.destroy()
        for i, p in enumerate(self.search_results):
            is_high = (i == self.highlighted_index)
            btn = ctk.CTkButton(self.results_list, text=f"{ar(p['name'])}",
                                font=ctk.CTkFont(family="DejaVu Sans", size=13, weight="bold"),
                                fg_color=self.app.T["accent"] if is_high else "transparent",
                                text_color="#ffffff" if is_high else self.app.T["text"],
                                hover_color=self.app.T["accent"],
                                anchor="e", height=35,
                                command=lambda pr=p, idx=i: self._select_by_mouse(pr, idx))
            btn.pack(fill="x", pady=1)

    def _select_by_mouse(self, product, index):
        self.highlighted_index = index
        self.search_results = [] # Clear results list
        self.barcode_var.set("") # Clear search text
        self._update_results_ui() # Sync and hide
        self._show_product_details(product)

    def _on_search_down(self, event):
        if self.search_results:
            self.highlighted_index = (self.highlighted_index + 1) % len(self.search_results)
            self._update_results_ui()
            return "break"

    def _on_search_up(self, event):
        if self.search_results:
            self.highlighted_index = (self.highlighted_index - 1) % len(self.search_results)
            self._update_results_ui()
            return "break"

    def _add_selected_to_cart(self, is_update=False):
        if not self.selected_product: return
        try:
            # Re-verify availability including what's already in the cart
            product = db.get_product_by_id(self.selected_product["id"])
            if not product: return

            in_cart_qty = sum(item["qty"] for item in self.cart if item["id"] == product["id"])

            # If update, we need to know the old quantity of THIS specific line (if we had lines)
            # Since our cart currently merges by ID, we find the existing entry
            existing_item = next((item for item in self.cart if item["id"] == product["id"]), None)
            old_qty = existing_item["qty"] if existing_item else 0

            available = product["quantity"] - (in_cart_qty - old_qty)

            q = int(self.qty_var.get())
            if q <= 0 or q > available:
                raise ValueError

            if is_update and existing_item:
                existing_item["qty"] = q
            else:
                self.add_item_to_cart(product, q)

            self._show_empty_info()
            self.barcode_var.set(""); self.results_list.pack_forget(); self.selected_product = None
            self.barcode_entry.focus_set()
            self._update_cart_ui()
        except ValueError:
            CustomDialog(self, get_text("error", self.app.lang), get_text("invalid_qty", self.app.lang))

    def add_item_to_cart(self, product, qty):
        for item in self.cart:
            if item["id"] == product["id"]:
                item["qty"] += qty
                self._update_cart_ui(); return
        self.cart.append({"id": product["id"], "name": product["name"], "price": product["sell_price"], "qty": qty})
        self._update_cart_ui()

    def _select_cart_item(self, index):
        if index < len(self.cart):
            item = self.cart[index]
            self._show_product_details(item, initial_qty=item["qty"])

    def _confirm_credit_sale_dialog(self):
        if not self.cart: return
        customers = db.get_all_customers()
        if not customers:
            CustomDialog(self, get_text("error", self.app.lang), "لا يوجد زبائن مضافين. يرجى إضافة زبون من تبويب الديون أولاً.")
            return

        names = [c["name"] for c in customers]
        CustomSelectionDialog(self, get_text("sell_on_credit", self.app.lang),
                               get_text("customer", self.app.lang),
                               names,
                               self._finish_credit_selection)

    def _finish_credit_selection(self, customer_name):
        if not customer_name:
            self.credit_customer = None
        else:
            self.credit_customer = customer_name.strip()
        self._update_cart_ui()

    def _update_cart_ui(self):
        # OPTIMIZATION: Only rebuild the cart if the contents have actually changed
        # or if the selected item has changed. This prevents "blinking".
        current_cart_state = ([(item["id"], item["qty"]) for item in self.cart],
                              self.selected_product["id"] if self.selected_product else None,
                              self.credit_customer)

        if hasattr(self, "_last_cart_state") and self._last_cart_state == current_cart_state:
            return
        self._last_cart_state = current_cart_state

        for w in self.cart_list_frame.winfo_children(): w.destroy()
        t = self.app.T

        # Update customer label
        if hasattr(self, "customer_lbl"):
            if self.credit_customer:
                self.customer_lbl.configure(text=ar(f"({get_text('customer', self.app.lang)}: {self.credit_customer})"))
            else:
                self.customer_lbl.configure(text="")

        if not self.cart:
            if hasattr(self, "cart_total_lbl"):
                currency = db.get_setting("currency", "DZD")
                self.cart_total_lbl.configure(text=f"0.00 {currency}")
            ctk.CTkLabel(self.cart_list_frame, text=ar(get_text("empty_cart", self.app.lang)), font=FONTS["body"], text_color=t["text2"]).pack(pady=40)
            self.confirm_btn.configure(state="disabled")
            if hasattr(self, "credit_btn"): self.credit_btn.configure(state="disabled")
            return
        self.confirm_btn.configure(state="normal")
        if hasattr(self, "credit_btn"): self.credit_btn.configure(state="normal")
        currency = db.get_setting("currency", "DZD")

        total_cart_value = 0
        for i, item in enumerate(self.cart):
            total_cart_value += (item["price"] * item["qty"])
            is_sel = self.selected_product and self.selected_product["id"] == item["id"]
            row_bg = t["accent"] if is_sel else t["bg3"]
            txt_color = "white" if is_sel else t["text"]

            row = ctk.CTkFrame(self.cart_list_frame, fg_color=row_bg, corner_radius=12, cursor="hand2")
            row.pack(fill="x", pady=5, padx=10)

            # Hover animation
            def on_enter(e, r=row, sel=is_sel):
                if not sel: r.configure(fg_color=t["bg3"], border_width=2, border_color=t["accent"])
            def on_leave(e, r=row, sel=is_sel):
                if not sel: r.configure(fg_color=t["bg3"], border_width=0)

            row.bind("<Enter>", on_enter)
            row.bind("<Leave>", on_leave)
            row.bind("<Button-1>", lambda e, idx=i: self._select_cart_item(idx))

            # Delete button on the absolute far left
            del_btn = ctk.CTkButton(row, text="✕", width=40, height=40, fg_color="transparent",
                          text_color=t["danger"],
                          hover_color="#fee2e2" if self.app.mode == "light" else "#450a0a",
                          command=lambda idx=i: self._remove_from_cart(idx))
            del_btn.pack(side="left", padx=(10, 5))

            # Order total next to it
            row_total = item["price"] * item["qty"]
            price_lbl = ctk.CTkLabel(row, text=f"{row_total:,.2f} {currency}",
                                     font=ctk.CTkFont(family=PRIMARY_FONT, size=16, weight="bold"),
                                     text_color=t["success"] if not is_sel else "white")
            price_lbl.pack(side="left", padx=10)
            price_lbl.bind("<Button-1>", lambda e, idx=i: self._select_cart_item(idx))

            # Product Name (Fixed width on the Right)
            name_lbl = ctk.CTkLabel(row, text=ar(item["name"]), font=FONTS["heading"], anchor="e", text_color=txt_color, width=250)
            name_lbl.pack(side="right", padx=(10, 20))
            name_lbl.bind("<Button-1>", lambda e, idx=i: self._select_cart_item(idx))

            # Center Container for Quantity and Unit Price (Table-like grid)
            center_info = ctk.CTkFrame(row, fg_color="transparent")
            center_info.pack(side="right", expand=True, fill="x")
            center_info.bind("<Button-1>", lambda e, idx=i: self._select_cart_item(idx))

            # Column 1: Unit Price (Fixed width and position)
            unit_price_lbl = ctk.CTkLabel(center_info, text=f"{item['price']:,.2f} {currency}",
                                          font=ctk.CTkFont(family=PRIMARY_FONT, size=16, weight="bold"),
                                          text_color=txt_color, width=150, anchor="center")
            unit_price_lbl.pack(side="right", expand=True)
            unit_price_lbl.bind("<Button-1>", lambda e, idx=i: self._select_cart_item(idx))

            # Column 2: Quantity (Fixed width and position)
            qty_lbl = ctk.CTkLabel(center_info, text=f"x{item['qty']}",
                                   font=FONTS["heading"], text_color=txt_color, width=100, anchor="center")
            qty_lbl.pack(side="right", expand=True)
            qty_lbl.bind("<Button-1>", lambda e, idx=i: self._select_cart_item(idx))

        # Update the live total label
        self.cart_total_lbl.configure(text=f"{total_cart_value:,.2f} {currency}")

    def _remove_from_cart(self, index):
        self.cart.pop(index)
        if not self.cart: self.credit_customer = None
        self._update_cart_ui()
        # Refresh current product details if it's the one being removed
        if self.selected_product:
            self._show_product_details(self.selected_product)

    def _clear_cart_instantly(self):
        self.cart = []
        self.credit_customer = None
        self._update_cart_ui()
        # Refresh current product details to show full stock
        if self.selected_product:
            self._show_product_details(self.selected_product)

    def _confirm_bulk_sale(self):
        if not self.cart: return
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        total_amount = 0

        is_paid = 1
        customer_id = None

        if self.credit_customer:
            is_paid = 0
            cust = db.get_customer_by_name(self.credit_customer)
            if cust: customer_id = cust["id"]

        for item in self.cart:
            ok, msg = db.confirm_sale(item["id"], item["qty"], timestamp=ts, is_paid=is_paid, customer_id=customer_id)
            if ok: total_amount += (item["price"] * item["qty"])

        self.cart = []
        self.credit_customer = None
        self._update_cart_ui(); self._load_recent(); self.app.refresh_alerts()
        for p in ["products", "analytics", "credit"]:
            if p in self.app.pages: self.app.pages[p].refresh()

        currency = db.get_setting("currency", "DZD")
        msg = f"{get_text('selled', self.app.lang)} - {total_amount:,.2f} {currency}"
        if is_paid == 0:
            msg = f"{get_text('sell_on_credit', self.app.lang)} - {total_amount:,.2f} {currency}"

        self._show_sale_toast(msg)

    def _show_sale_toast(self, message):
        """Shows a modern animated notification banner as an OVERLAY above the cart."""
        if hasattr(self, "active_toast") and self.active_toast:
            try: self.active_toast.destroy()
            except: pass

        t = self.app.T

        # Create toast as an overlay frame (relative to main_area)
        # bg_color="transparent" ensures no weird border backgrounds on rounded corners
        toast = ctk.CTkFrame(self.main_area, fg_color=t["success"], bg_color="transparent", corner_radius=15, height=50)
        # Initial hidden position (above the frame)
        toast.place(relx=0.5, y=-60, relwidth=0.6, anchor="n")
        self.active_toast = toast

        ctk.CTkLabel(toast, text=ar(message), font=ctk.CTkFont(size=15, weight="bold"), text_color="white").pack(expand=True)

        # Animation parameters
        target_y = 20
        step = 2 # Slower animation step

        def slide_down(curr_y):
            if not toast.winfo_exists(): return
            if curr_y < target_y:
                new_y = curr_y + step
                toast.place(y=new_y)
                self.after(10, lambda: slide_down(new_y))
            else:
                toast.place(y=target_y)
                # Auto-hide after 1.5 seconds
                self.after(1500, slide_up)

        def slide_up():
            if not toast.winfo_exists(): return
            def animate_up(curr_y):
                if not toast.winfo_exists(): return
                if curr_y > -60:
                    new_y = curr_y - step
                    toast.place(y=new_y)
                    self.after(10, lambda: animate_up(new_y))
                else:
                    try: toast.destroy()
                    except: pass
                    if hasattr(self, "active_toast") and self.active_toast == toast:
                        self.active_toast = None
            animate_up(target_y)

        slide_down(-60)

    def _load_recent(self):
        for item in self.recent_tree.get_children(): self.recent_tree.delete(item)
        now = datetime.now()
        sales = db.get_sales_by_month(now.year, now.month)
        today = now.strftime("%Y-%m-%d")
        today_sales = [s for s in sales if s["sale_date"].startswith(today)]
        groups = {}
        credit_txt = get_text('credit', self.app.lang)
        for s in today_sales:
            ts = s["sale_date"]
            if ts not in groups:
                groups[ts] = {"time": ts[11:16], "prods": [], "total": 0, "profit": 0, "is_paid": 1}
            groups[ts]["prods"].append(s["product_name"])
            if s.get("is_paid", 1) == 1:
                groups[ts]["total"] += s["total"]
                groups[ts]["profit"] += s["profit"]
            else:
                groups[ts]["is_paid"] = 0

        sorted_keys = sorted(groups.keys(), reverse=True)
        role_is_admin = (self.app.role == "admin")
        for ts in sorted_keys:
            g = groups[ts]
            prod_str = " + ".join(g["prods"])
            if g["is_paid"] == 0:
                prod_str = f"({credit_txt}) {prod_str}"

            vals = [ts, g["time"], ar(prod_str), f"{g['total']:.2f}"]
            if role_is_admin:
                vals.append(f"{g['profit']:.2f}")
            self.recent_tree.insert("", "end", values=tuple(vals))

    def _confirm_undo(self, timestamp):
        def cb(c):
            if c and db.delete_sale_group(timestamp):
                self._load_recent(); self._show_empty_info(); self.app.refresh_alerts()
                for p in ["products", "analytics"]:
                    if p in self.app.pages: self.app.pages[p].refresh()
        CustomDialog(self, get_text("undo", self.app.lang), get_text("confirm_delete_sale", self.app.lang), True, cb)

    def _confirm_delete(self, timestamp):
        def cb(c):
            if c and db.delete_sale_group_record(timestamp):
                self._load_recent(); self._show_empty_info()
                if "analytics" in self.app.pages: self.app.pages["analytics"].refresh()
        CustomDialog(self, get_text("confirm_delete", self.app.lang), get_text("delete_sale_confirm", self.app.lang), True, cb)

    def refresh(self):
        if self.last_role != self.app.role: self.refresh_ui()
        self.last_role = self.app.role
        self._load_recent()

    def refresh_ui(self):
        for w in self.winfo_children(): w.destroy()
        self._build()
