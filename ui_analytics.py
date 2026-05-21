import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from datetime import datetime
import database as db
from theme import FONTS
from languages import get_text
from arabic_fixer import ar
from ui_components import CustomDialog, CustomInputDialog

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

class AnalyticsTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=app.T["bg2"])
        self.app = app
        self.current_year = datetime.now().year
        self.chart_type = "bar" # "bar" or "line"
        self._build()

    def _build(self):
        t = self.app.T
        lang = self.app.lang

        # Main Scrollable Container
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                             scrollbar_button_color=t["accent"],
                                             scrollbar_button_hover_color=t["accent_hover"])
        self.scroll.pack(fill="both", expand=True)

        # Header Card
        header = ctk.CTkFrame(self.scroll, fg_color=t["bg3"], corner_radius=15)
        header.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(header, text=ar(get_text("analytics_title", lang)),
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=t["accent"]).pack(side="right", padx=20, pady=15)

        ctrl = ctk.CTkFrame(header, fg_color="transparent")
        ctrl.pack(side="left", padx=20)

        # Modern Year Selection
        self.year_var = tk.StringVar(value=str(self.current_year))
        years = [str(y) for y in range(self.current_year, self.current_year - 5, -1)]

        self.year_menu = ctk.CTkOptionMenu(ctrl, values=years, variable=self.year_var,
                                           width=120, height=35, corner_radius=8,
                                           fg_color=t["bg3"], button_color=t["accent"],
                                           dropdown_fg_color=t["bg3"],
                                           command=lambda x: self._refresh_charts())
        self.year_menu.pack(side="right", padx=10)

        # Refresh Button
        ctk.CTkButton(ctrl, text=ar(get_text("refresh", lang)), width=100, height=35,
                      fg_color=t["accent2"], corner_radius=8,
                      command=self._refresh_charts).pack(side="right", padx=5)

        # Red Action Button: Delete Year Data
        ctk.CTkButton(ctrl, text=ar(get_text("delete_year", lang)), width=160, height=35,
                      fg_color="#d32f2f", hover_color="#b71c1c", corner_radius=8,
                      command=self._on_delete_year_click).pack(side="right", padx=5)

        # Stats Row
        cards_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        cards_row.pack(fill="x", pady=(0, 15))

        self.card_labels = {}
        cards_cfg = [
            ("today_revenue",  get_text("today_revenue", lang),   t["accent"]),
            ("today_profit",   get_text("today_profit", lang),    t["success"]),
            ("month_revenue",  get_text("month_revenue", lang),    t["accent2"]),
            ("month_profit",   get_text("month_profit", lang),     t["warning"]),
            ("total_products", get_text("total_products", lang),  t["text2"]),
        ]
        for key, label, color in cards_cfg:
            f = ctk.CTkFrame(cards_row, fg_color=t["bg3"], corner_radius=15)
            f.pack(side="left", expand=True, fill="both", padx=5)
            ctk.CTkLabel(f, text=ar(label), font=FONTS["small"], text_color=t["text2"]).pack(pady=(15, 0))
            lbl = ctk.CTkLabel(f, text="—", font=ctk.CTkFont(size=24, weight="bold"), text_color=color)
            lbl.pack(pady=(0, 15))
            self.card_labels[key] = lbl

        # Chart Area - Now with separate cards and toggle
        self.charts_container = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.charts_container.pack(fill="both", expand=True, pady=(0, 15))

        # Toggle Button Header
        chart_ctrl = ctk.CTkFrame(self.charts_container, fg_color="transparent")
        chart_ctrl.pack(fill="x", pady=(0, 10))

        self.toggle_btn = ctk.CTkButton(chart_ctrl, text=ar(get_text("line_chart", lang)),
                                        fg_color=t["accent"], hover_color=t["accent_hover"],
                                        height=35, corner_radius=8,
                                        command=self._toggle_chart_type)
        self.toggle_btn.pack(side="right")

        if HAS_MPL:
            # Revenue Box
            self.revenue_box = ctk.CTkFrame(self.charts_container, fg_color=t["bg3"], corner_radius=15)
            self.revenue_box.pack(fill="both", expand=True, pady=(0, 15))
            self.rev_inner = ctk.CTkFrame(self.revenue_box, fg_color="transparent")
            self.rev_inner.pack(fill="both", expand=True, padx=15, pady=15)

            # Profit Box
            self.profit_box = ctk.CTkFrame(self.charts_container, fg_color=t["bg3"], corner_radius=15)
            self.profit_box.pack(fill="both", expand=True)
            self.pro_inner = ctk.CTkFrame(self.profit_box, fg_color="transparent")
            self.pro_inner.pack(fill="both", expand=True, padx=15, pady=15)

            self._draw_charts()
        else:
            no_mpl = ctk.CTkFrame(self.charts_container, fg_color=t["bg3"], corner_radius=15)
            no_mpl.pack(fill="both", expand=True)
            ctk.CTkLabel(no_mpl, text=ar(get_text("matplotlib_missing", lang)),
                         text_color=t["warning"]).pack(pady=50)

        # Top Insights Area (New)
        insights_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        insights_row.pack(fill="x", pady=(0, 20))

        # Top Selling Products Box
        self.top_selling_box = ctk.CTkFrame(insights_row, fg_color=t["bg3"], corner_radius=15)
        self.top_selling_box.pack(side="left", expand=True, fill="both", padx=(0, 5))
        ctk.CTkLabel(self.top_selling_box, text=ar(get_text("top_selling_title", lang)), font=FONTS["subhead"], text_color=t["accent"]).pack(pady=10)
        self.top_selling_list = ctk.CTkFrame(self.top_selling_box, fg_color="transparent")
        self.top_selling_list.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Most Profitable Products Box
        self.top_profit_box = ctk.CTkFrame(insights_row, fg_color=t["bg3"], corner_radius=15)
        self.top_profit_box.pack(side="left", expand=True, fill="both", padx=(5, 0))
        ctk.CTkLabel(self.top_profit_box, text=ar(get_text("most_profitable_title", lang)), font=FONTS["subhead"], text_color=t["success"]).pack(pady=10)
        self.top_profit_list = ctk.CTkFrame(self.top_profit_box, fg_color="transparent")
        self.top_profit_list.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self._update_cards()
        self._update_insights()

    def _on_delete_year_click(self):
        year = self.year_var.get()

        def on_pwd_entry(pwd):
            if pwd is None: return # Cancelled
            stored = db.get_setting("admin_password", "admin123")
            if pwd == stored:
                def confirm_deletion(confirmed):
                    if confirmed:
                        if db.delete_sales_by_year(year):
                            CustomDialog(self, get_text("success", self.app.lang), f"{get_text('success', self.app.lang)}")
                            self._refresh_charts()
                            self.app.refresh_alerts()
                        else:
                            CustomDialog(self, get_text("error", self.app.lang), f"{get_text('error', self.app.lang)}")

                CustomDialog(self, get_text("confirm", self.app.lang), get_text("delete_year_confirm", self.app.lang),
                             is_question=True, callback=confirm_deletion)
            else:
                CustomDialog(self, get_text("error", self.app.lang), get_text("wrong_password", self.app.lang))

        CustomInputDialog(self, get_text("admin_required", self.app.lang), get_text("enter_password", self.app.lang), on_pwd_entry)

    def _update_cards(self):
        currency = db.get_setting("currency", "DZD")
        today = db.get_today_summary()
        year = int(self.year_var.get())
        month = datetime.now().month
        month_data = db.get_monthly_summary_total(year, month)

        month_rev = month_data["revenue"] or 0
        month_pro = month_data["profit"] or 0
        products_count = db.get_products_count()

        def fmt(v): return f"{v:,.0f} {currency}" if v else f"0 {currency}"

        self.card_labels["today_revenue"].configure(text=fmt(today["revenue"]))
        self.card_labels["today_profit"].configure(text=fmt(today["profit"]))
        self.card_labels["month_revenue"].configure(text=fmt(month_rev))
        self.card_labels["month_profit"].configure(text=fmt(month_pro))
        self.card_labels["total_products"].configure(text=str(products_count))

    def _toggle_chart_type(self):
        self.chart_type = "line" if self.chart_type == "bar" else "bar"
        btn_key = "bar_chart" if self.chart_type == "line" else "line_chart"
        self.toggle_btn.configure(text=ar(get_text(btn_key, self.app.lang)))
        self._draw_charts()

    def _draw_charts(self):
        if not HAS_MPL: return
        for w in self.rev_inner.winfo_children(): w.destroy()
        for w in self.pro_inner.winfo_children(): w.destroy()

        t = self.app.T
        year = int(self.year_var.get())
        data = db.get_monthly_summary(year)

        revenue = [0] * 12
        profit  = [0] * 12
        for row in data:
            idx = row["month"] - 1
            revenue[idx] = row["revenue"] or 0
            profit[idx]  = row["profit"] or 0

        from theme import get_months
        labels = get_months(self.app.lang)[1:]

        # Create Two Separate Figures
        def create_fig(data_list, title_key, color):
            fig, ax = plt.subplots(figsize=(10, 3))
            fig.patch.set_facecolor(t["bg3"])
            ax.set_facecolor(t["bg3"])
            ax.tick_params(colors=t["text"], labelsize=8)
            for spine in ax.spines.values(): spine.set_color(t["border"])

            ax.set_xticks(range(12))
            ax.set_xticklabels(labels, rotation=30, fontsize=8)

            title_text = f"{get_text(title_key, self.app.lang)} {year}"
            ax.set_title(ar(title_text), color=t["accent"], fontsize=12, fontweight="bold", pad=20)

            if self.chart_type == "bar":
                ax.bar(range(12), data_list, color=color, alpha=0.8, width=0.6)
            else:
                # Trading Chart Style (Line with Markers)
                ax.plot(range(12), data_list, color=color, marker='o', markersize=6,
                        linewidth=3, markerfacecolor=t["bg"], markeredgecolor=color)
                ax.fill_between(range(12), data_list, color=color, alpha=0.1)
                ax.grid(True, linestyle='--', alpha=0.3, color=t["text2"])

            fig.tight_layout()
            return fig

        # Draw Revenue Figure
        fig_rev = create_fig(revenue, "revenue_chart", t["accent"])
        canvas_rev = FigureCanvasTkAgg(fig_rev, master=self.rev_inner)
        canvas_rev.draw()
        canvas_rev.get_tk_widget().pack(fill="both", expand=True)

        # Draw Profit Figure
        fig_pro = create_fig(profit, "profit_chart", t["success"])
        canvas_pro = FigureCanvasTkAgg(fig_pro, master=self.pro_inner)
        canvas_pro.draw()
        canvas_pro.get_tk_widget().pack(fill="both", expand=True)

        plt.close('all')

    def _update_insights(self):
        t = self.app.T
        currency = db.get_setting("currency", "DZD")

        # Update Top Selling
        for w in self.top_selling_list.winfo_children(): w.destroy()
        top_selling = db.get_top_selling_products(5)
        if not top_selling:
            ctk.CTkLabel(self.top_selling_list, text=ar(get_text("no_data", self.app.lang)), font=FONTS["small"]).pack(pady=20)
        for i, p in enumerate(top_selling):
            row = ctk.CTkFrame(self.top_selling_list, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{i+1}.", font=FONTS["small"], width=30).pack(side="right")
            ctk.CTkLabel(row, text=ar(p["product_name"]), font=FONTS["small"], anchor="e").pack(side="right", expand=True, fill="x")
            ctk.CTkLabel(row, text=str(p["total_qty"]), font=ctk.CTkFont(weight="bold"), text_color=t["accent"]).pack(side="left")

        # Update Top Profit
        for w in self.top_profit_list.winfo_children(): w.destroy()
        top_profit = db.get_most_profitable_products(5)
        if not top_profit:
            ctk.CTkLabel(self.top_profit_list, text=ar(get_text("no_data", self.app.lang)), font=FONTS["small"]).pack(pady=20)
        for i, p in enumerate(top_profit):
            row = ctk.CTkFrame(self.top_profit_list, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{i+1}.", font=FONTS["small"], width=30).pack(side="right")
            ctk.CTkLabel(row, text=ar(p["product_name"]), font=FONTS["small"], anchor="e").pack(side="right", expand=True, fill="x")
            ctk.CTkLabel(row, text=f"{p['total_profit']:,.0f}", font=ctk.CTkFont(weight="bold"), text_color=t["success"]).pack(side="left")

    def _refresh_charts(self):
        if HAS_MPL: self._draw_charts()
        self._update_cards()
        self._update_insights()

    def refresh(self):
        self._refresh_charts()
