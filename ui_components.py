import customtkinter as ctk
import tkinter as tk
from arabic_fixer import ar
from theme import FONTS, PRIMARY_FONT
from languages import get_text

class CustomDialog(ctk.CTkToplevel):
    """Modern styled popup for Alerts and Confirmations with high visibility."""
    def __init__(self, parent, title, message, is_question=False, callback=None):
        master = parent.winfo_toplevel() if hasattr(parent, 'winfo_toplevel') else parent
        super().__init__(master)

        self.callback = callback
        app = getattr(parent, 'app', master)
        t = app.T

        self.withdraw()
        self.title(ar(title))
        self.configure(fg_color=t["bg"])

        width = 400
        height = 280
        self.resizable(False, False)

        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw // 2) - (width // 2)
        y = (sh // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.deiconify()

        self.transient(master)
        self.grab_set()

        container = ctk.CTkFrame(self, fg_color=t["bg2"], corner_radius=20, border_width=1, border_color=t["border"])
        container.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(container, text=ar(title),
                     font=ctk.CTkFont(family=PRIMARY_FONT, size=18, weight="bold"),
                     text_color=t["accent"]).pack(pady=(20, 5))

        ctk.CTkLabel(container, text=ar(message),
                     font=ctk.CTkFont(size=13),
                     wraplength=340, justify="center").pack(pady=15, padx=20)

        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=(0, 15), fill="x")

        if is_question:
            ctk.CTkButton(btn_frame, text=ar(get_text("confirm", app.lang)), fg_color=t["success"], hover_color="#15803d",
                          width=120, height=40, corner_radius=10, font=FONTS["subhead"],
                          command=self._on_yes).pack(side="right", padx=10)
            ctk.CTkButton(btn_frame, text=ar(get_text("cancel", app.lang)), fg_color=t["danger"], hover_color="#991b1b",
                          width=120, height=40, corner_radius=10, font=FONTS["subhead"],
                          command=self._on_no).pack(side="right", padx=10)
        else:
            ctk.CTkButton(btn_frame, text=ar(get_text("ok", app.lang)), fg_color=t["accent"], hover_color=t["accent_hover"],
                          width=140, height=40, corner_radius=10, font=FONTS["subhead"],
                          command=self.destroy).pack()

        self.lift()
        self.focus_force()

    def _on_yes(self):
        if self.callback: self.callback(True)
        self.destroy()

    def _on_no(self):
        if self.callback: self.callback(False)
        self.destroy()

class CustomInputDialog(ctk.CTkToplevel):
    """Modern styled popup for Password/Text input with high visibility."""
    def __init__(self, parent, title, message, callback):
        master = parent.winfo_toplevel() if hasattr(parent, 'winfo_toplevel') else parent
        super().__init__(master)
        self.callback = callback
        app = getattr(parent, 'app', master)
        t = app.T

        self.withdraw()
        self.title(ar(title))
        self.configure(fg_color=t["bg"])

        width = 380
        height = 300
        self.resizable(False, False)

        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw // 2) - (width // 2)
        y = (sh // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.deiconify()

        self.transient(master)
        self.grab_set()

        container = ctk.CTkFrame(self, fg_color=t["bg2"], corner_radius=20, border_width=1, border_color=t["border"])
        container.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(container, text=ar(message), font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(25, 5))
        self.entry = ctk.CTkEntry(container, show="*", width=280, height=45, corner_radius=15)
        self.entry.pack(pady=15)

        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=(0, 15), fill="x")

        ctk.CTkButton(btn_frame, text=ar(get_text("ok", app.lang)), fg_color=t["success"], width=120, height=40, command=self._submit).pack(side="right", padx=10)
        ctk.CTkButton(btn_frame, text=ar(get_text("cancel", app.lang)), fg_color=t["danger"], width=120, height=40, command=self._cancel).pack(side="right", padx=10)

        self.bind("<Return>", lambda e: self._submit())
        self.entry.focus_set()

    def _submit(self):
        self.callback(self.entry.get())
        self.destroy()

    def _cancel(self):
        self.callback(None)
        self.destroy()

class CustomTextInputDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, message, callback, placeholder=""):
        master = parent.winfo_toplevel() if hasattr(parent, 'winfo_toplevel') else parent
        super().__init__(master)
        self.callback = callback
        app = getattr(parent, 'app', master)
        t = app.T

        self.withdraw()
        self.title(ar(title))
        self.configure(fg_color=t["bg"])

        width = 400
        height = 300
        self.resizable(False, False)

        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw // 2) - (width // 2)
        y = (sh // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.deiconify()

        self.transient(master)
        self.grab_set()

        container = ctk.CTkFrame(self, fg_color=t["bg2"], corner_radius=20, border_width=1, border_color=t["border"])
        container.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(container, text=ar(message), font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(25, 5))
        self.entry = ctk.CTkEntry(container, width=300, height=45, placeholder_text=ar(placeholder))
        self.entry.pack(pady=15)

        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=(0, 15), fill="x")
        ctk.CTkButton(btn_frame, text=ar(get_text("ok", app.lang)), fg_color=t["success"], width=120, height=40, command=self._submit).pack(side="right", padx=10)
        ctk.CTkButton(btn_frame, text=ar(get_text("cancel", app.lang)), fg_color=t["danger"], width=120, height=40, command=self._cancel).pack(side="right", padx=10)

        self.bind("<Return>", lambda e: self._submit())
        self.entry.focus_set()

    def _submit(self):
        self.callback(self.entry.get())
        self.destroy()

    def _cancel(self):
        self.callback(None)
        self.destroy()

class CustomSelectionDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, message, options, callback):
        master = parent.winfo_toplevel() if hasattr(parent, 'winfo_toplevel') else parent
        super().__init__(master)
        self.callback = callback
        app = getattr(parent, 'app', master)
        t = app.T

        self.withdraw()
        self.title(ar(title))
        self.configure(fg_color=t["bg"])

        width = 400
        height = 450
        self.resizable(False, False)

        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw // 2) - (width // 2)
        y = (sh // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.deiconify()

        self.transient(master)
        self.grab_set()

        container = ctk.CTkFrame(self, fg_color=t["bg2"], corner_radius=20, border_width=1, border_color=t["border"])
        container.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(container, text=ar(message), font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 10))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._filter_options(t, app.lang))
        search_entry = ctk.CTkEntry(container, textvariable=self.search_var, placeholder_text=ar(get_text("search_placeholder", app.lang)), height=40)
        search_entry.pack(fill="x", padx=20, pady=(0, 10))

        self.options_frame = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.options_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.all_options = options
        self._filter_options(t, app.lang)

        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=(0, 15), fill="x")
        ctk.CTkButton(btn_frame, text=ar(get_text("cancel", app.lang)), fg_color=t["danger"], width=120, height=40, command=self.destroy).pack()

    def _filter_options(self, t, lang):
        for w in self.options_frame.winfo_children(): w.destroy()
        query = self.search_var.get().lower()
        filtered = [opt for opt in self.all_options if query in opt.lower()]
        for opt in filtered:
            btn = ctk.CTkButton(self.options_frame, text=ar(opt), fg_color=t["bg3"], text_color=t["text"], hover_color=t["accent"], height=45, anchor="e", command=lambda o=opt: self._select(o))
            btn.pack(fill="x", pady=2, padx=5)

    def _select(self, option):
        self.callback(option)
        self.destroy()
