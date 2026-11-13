import sys
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

WIN = sys.platform.startswith("win")
UI_FONT = "Segoe UI" if WIN else ("SF Pro Text" if sys.platform == "darwin" else "Noto Sans")
MONO = "Consolas" if WIN else "DejaVu Sans Mono"

BG = ("#F2F4FA", "#0B0E14")
SIDE = ("#FFFFFF", "#10141D")
CARD = ("#FFFFFF", "#161B26")
LINE = ("#E2E7F1", "#262D3D")
TEXT = ("#0F172A", "#E8ECF4")
MUTED = ("#64748B", "#8A94A8")
INPUT = ("#F0F3F9", "#1D2332")
ACC = ("#4F46E5", "#6366F1")
ACC_H = ("#4338CA", "#7C83F7")
OK = ("#047857", "#34D399")
OK_BG = ("#D1FAE5", "#0B3B2E")
WARN = ("#B45309", "#FBBF24")
WARN_BG = ("#FEF3C7", "#3A2A0A")
BAD = ("#DC2626", "#F87171")

FN = {}
TREES = []

def init_fonts():
    f = ctk.CTkFont
    FN.update(h0=f(family=UI_FONT, size=26, weight="bold"), h1=f(family=UI_FONT, size=22, weight="bold"),
              h2=f(family=UI_FONT, size=15, weight="bold"), body=f(family=UI_FONT, size=13),
              label=f(family=UI_FONT, size=12), small=f(family=UI_FONT, size=11),
              btn=f(family=UI_FONT, size=13, weight="bold"), mono=f(family=MONO, size=12))

def rc(c):
    if isinstance(c, tuple):
        return c[1] if ctk.get_appearance_mode() == "Dark" else c[0]
    return c

def restyle():
    s = ttk.Style()
    try: s.theme_use("clam")
    except tk.TclError: pass
    bg, fg = rc(CARD), rc(TEXT)
    s.configure("M.Treeview", background=bg, fieldbackground=bg, foreground=fg, borderwidth=0, rowheight=34, font=(UI_FONT, 10))
    s.map("M.Treeview", background=[("selected", rc(ACC))], foreground=[("selected", "#FFFFFF")])
    s.configure("M.Treeview.Heading", background=rc(INPUT), foreground=rc(MUTED), relief="flat", borderwidth=0, font=(UI_FONT, 9, "bold"), padding=(8, 8))
    s.map("M.Treeview.Heading", background=[("active", rc(INPUT))])
    s.layout("M.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

def btn(parent, text, cmd, kind="primary", width=160):
    if kind == "primary": kw = dict(fg_color=ACC, hover_color=ACC_H, text_color="#FFFFFF")
    elif kind == "danger": kw = dict(fg_color="transparent", hover_color=INPUT, text_color=BAD, border_width=1, border_color=BAD)
    else: kw = dict(fg_color="transparent", hover_color=INPUT, text_color=TEXT, border_width=1, border_color=LINE)
    return ctk.CTkButton(parent, text=text, command=cmd, width=width, height=38, corner_radius=10, font=FN["btn"], **kw)

def ent(parent, var, width=220):
    return ctk.CTkEntry(parent, textvariable=var, width=width, height=36, corner_radius=10, border_width=1, border_color=LINE, fg_color=INPUT, text_color=TEXT, font=FN["body"])

def cmb(parent, var, values, width=220, state="readonly", command=None):
    return ctk.CTkComboBox(parent, variable=var, values=values, width=width, height=36, corner_radius=10, border_width=1, border_color=LINE, fg_color=INPUT, button_color=ACC, button_hover_color=ACC_H, dropdown_fg_color=CARD, dropdown_text_color=TEXT, dropdown_hover_color=INPUT, text_color=TEXT, state=state, command=command, font=FN["body"], dropdown_font=FN["body"])

def radio(parent, text, var, value, command=None, wrap=620):
    return ctk.CTkRadioButton(parent, text=text, variable=var, value=value, command=command, font=FN["body"], text_color=TEXT, fg_color=ACC, hover_color=ACC_H, border_color=MUTED)

def enabled(w, on):
    w.configure(state="normal" if on else "disabled")
    try: w.configure(text_color=TEXT if on else MUTED)
    except Exception: pass

def fld(parent, label, make, hint=None, **grid):
    f = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(f, text=label, font=FN["label"], text_color=MUTED, anchor="w").pack(anchor="w")
    w = make(f)
    w.pack(anchor="w", pady=(3, 0))
    if hint: ctk.CTkLabel(f, text=hint, font=FN["small"], text_color=MUTED, anchor="w").pack(anchor="w", pady=(2, 0))
    if grid: f.grid(sticky="w", padx=8, pady=6, **grid)
    return w

def card(parent, title=None, sub=None):
    c = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=16, border_width=1, border_color=LINE)
    if title: ctk.CTkLabel(c, text=title, font=FN["h2"], text_color=TEXT).pack(anchor="w", padx=22, pady=(18, 0))
    if sub: ctk.CTkLabel(c, text=sub, font=FN["small"], text_color=MUTED, wraplength=640, justify="left", anchor="w").pack(anchor="w", padx=22, pady=(2, 0))
    c.body = ctk.CTkFrame(c, fg_color="transparent")
    c.body.pack(fill="both", expand=True, padx=14, pady=(8, 16))
    return c

def banner(parent, text="", kind="info"):
    bg, fg = {"info": (INPUT, TEXT), "warn": (WARN_BG, WARN), "ok": (OK_BG, OK)}[kind]
    f = ctk.CTkFrame(parent, fg_color=bg, corner_radius=12)
    f.lbl = ctk.CTkLabel(f, text=text, font=FN["body"], text_color=fg, wraplength=760, justify="left", anchor="w")
    f.lbl.pack(anchor="w", padx=16, pady=12)
    return f

def sayfa_baslik(parent, baslik, alt):
    h = ctk.CTkFrame(parent, fg_color="transparent")
    h.pack(fill="x", pady=(0, 14))
    ctk.CTkLabel(h, text=baslik, font=FN["h1"], text_color=TEXT).pack(anchor="w")
    ctk.CTkLabel(h, text=alt, font=FN["body"], text_color=MUTED, wraplength=900, justify="left").pack(anchor="w")

def make_tree(parent, cols, heads, widths, height=8):
    wrap = ctk.CTkFrame(parent, fg_color="transparent")
    tree = ttk.Treeview(wrap, columns=cols, show="headings", height=height, selectmode="browse", style="M.Treeview")
    for c, h, w in zip(cols, heads, widths):
        tree.heading(c, text=h, anchor="w")
        tree.column(c, width=w, anchor="w")
    sb = ctk.CTkScrollbar(wrap, command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y", padx=(4, 0))
    TREES.append(tree)
    return wrap, tree

def _grab(top):
    try:
        top.lift(); top.focus_force(); top.grab_set()
    except tk.TclError: pass

def _dialog(parent, baslik, mesaj, ikon, sor=False):
    root = parent.winfo_toplevel()
    top = ctk.CTkToplevel(root)
    top.title(baslik); top.resizable(False, False); top.configure(fg_color=CARD)
    w = 480
    h = 160 + (mesaj.count("\n") + len(mesaj) // 46 + 1) * 20
    x = root.winfo_rootx() + (root.winfo_width() - w) // 2
    y = root.winfo_rooty() + (root.winfo_height() - h) // 3
    top.geometry(f"{w}x{h}+{max(x, 0)}+{max(y, 0)}")
    renk = {"info": ACC, "uyari": WARN, "hata": BAD, "soru": ACC}[ikon]
    simge = {"info": "i", "uyari": "!", "hata": "✕", "soru": "?"}[ikon]
    ust = ctk.CTkFrame(top, fg_color="transparent")
    ust.pack(fill="both", expand=True, padx=24, pady=(22, 6))
    ctk.CTkLabel(ust, text=simge, width=42, height=42, corner_radius=21, fg_color=renk, text_color="#FFFFFF", font=FN["h2"]).pack(side="left", anchor="n")
    ctk.CTkLabel(ust, text=mesaj, wraplength=350, justify="left", anchor="w", font=FN["body"], text_color=TEXT).pack(side="left", padx=14, anchor="n", fill="x", expand=True)
    alt = ctk.CTkFrame(top, fg_color="transparent")
    alt.pack(fill="x", padx=24, pady=(0, 18))
    sonuc = {"v": False}
    def kapat(v): sonuc["v"] = v; top.destroy()
    if sor:
        btn(alt, "Evet", lambda: kapat(True), width=100).pack(side="right")
        btn(alt, "Hayır", lambda: kapat(False), kind="ghost", width=100).pack(side="right", padx=8)
    else:
        btn(alt, "Tamam", lambda: kapat(True), width=100).pack(side="right")
    top.protocol("WM_DELETE_WINDOW", lambda: kapat(False))
    top.after(150, lambda: _grab(top))
    root.wait_window(top)
    return sonuc["v"]

def bilgi(w, msg, baslik="Bilgi"): return _dialog(w, baslik, msg, "info")
def uyari(w, msg, baslik="Uyarı"): return _dialog(w, baslik, msg, "uyari")
def hata(w, msg, baslik="Hata"): return _dialog(w, baslik, msg, "hata")
def sor(w, msg, baslik="Onay"): return _dialog(w, baslik, msg, "soru", sor=True)