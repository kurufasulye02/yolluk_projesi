import calendar
import tkinter as tk
from datetime import date, datetime, time as dtime
import customtkinter as ctk
from ui.tema import ent, cmb, ACC, ACC_H, CARD, TEXT, MUTED, INPUT, FN, LINE, _grab
from utils import dstr

# Takvim için Türkçe ay ve gün isimleri
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
GUNLER = ["Pt", "Sa", "Ça", "Pe", "Cu", "Ct", "Pz"]

class DatePick(ctk.CTkFrame):
    def __init__(self, master, initial=None, on_change=None, width=170):
        super().__init__(master, fg_color="transparent")
        self.on_change = on_change
        self.var = tk.StringVar(value=dstr(initial or date.today()))
        ent(self, self.var, width - 46).pack(side="left")
        ctk.CTkButton(self, text="▦", width=38, height=36, corner_radius=10, fg_color=ACC, hover_color=ACC_H, text_color="#FFFFFF", command=self.ac).pack(side="left", padx=(6, 0))
        self.var.trace_add("write", lambda *a: self.on_change and self.on_change())

    def get(self):
        t = self.var.get().strip().replace("/", ".").replace("-", ".")
        try: return datetime.strptime(t, "%d.%m.%Y").date()
        except ValueError: return None
        
    def set(self, d): self.var.set(dstr(d))

    def ac(self):
        d = self.get() or date.today()
        bugun = date.today()
        st = {"y": d.year, "m": d.month}
        top = ctk.CTkToplevel(self)
        top.title("Tarih seç"); top.resizable(False, False); top.configure(fg_color=CARD)
        top.geometry(f"+{self.winfo_rootx()}+{self.winfo_rooty() + 44}")
        top.transient(self.winfo_toplevel())
        head = ctk.CTkFrame(top, fg_color="transparent"); head.pack(fill="x", padx=12, pady=(12, 4))
        baslik = ctk.CTkLabel(head, text="", font=FN["h2"], text_color=TEXT, width=150)
        grid = ctk.CTkFrame(top, fg_color="transparent")

        def ciz():
            for w in grid.winfo_children(): w.destroy()
            baslik.configure(text=f"{AYLAR[st['m'] - 1]} {st['y']}")
            for i, g in enumerate(GUNLER):
                ctk.CTkLabel(grid, text=g, width=38, font=FN["small"], text_color=MUTED).grid(row=0, column=i)
            for r, hafta in enumerate(calendar.monthcalendar(st["y"], st["m"]), start=1):
                for c, gun in enumerate(hafta):
                    if gun == 0: continue
                    t = date(st["y"], st["m"], gun)
                    ctk.CTkButton(grid, text=str(gun), width=38, height=32, corner_radius=8, fg_color=ACC if t == d else "transparent", hover_color=INPUT, text_color="#FFFFFF" if t == d else TEXT, font=FN["label"], border_width=1 if t == bugun else 0, border_color=ACC, command=lambda g=gun: sec(g)).grid(row=r, column=c, padx=1, pady=1)

        def gez(k):
            m, y = st["m"] + k, st["y"]
            if m < 1: m, y = 12, y - 1
            elif m > 12: m, y = 1, y + 1
            st.update(y=y, m=m); ciz()
            
        def sec(g):
            self.var.set(dstr(date(st["y"], st["m"], g)))
            top.destroy()

        for t, k, side in (("‹", -1, "left"), ("›", 1, "right")):
            ctk.CTkButton(head, text=t, width=34, height=30, corner_radius=8, fg_color="transparent", hover_color=INPUT, text_color=TEXT, border_width=1, border_color=LINE, command=lambda k=k: gez(k)).pack(side=side)
        baslik.pack(side="left", expand=True)
        grid.pack(padx=12, pady=(0, 12))
        ciz(); top.after(150, lambda: _grab(top))

class TimePick(ctk.CTkFrame):
    def __init__(self, master, h=8, m=0, on_change=None):
        super().__init__(master, fg_color="transparent")
        self.h, self.m = tk.StringVar(value=f"{h:02d}"), tk.StringVar(value=f"{m:02d}")
        cmb(self, self.h, [f"{i:02d}" for i in range(24)], 80, state="normal").pack(side="left")
        ctk.CTkLabel(self, text=":", font=FN["h2"], text_color=TEXT).pack(side="left", padx=4)
        cmb(self, self.m, [f"{i:02d}" for i in range(0, 60, 5)], 80, state="normal").pack(side="left")
        if on_change:
            self.h.trace_add("write", lambda *a: on_change())
            self.m.trace_add("write", lambda *a: on_change())

    def get(self):
        try: return dtime(int(self.h.get()), int(self.m.get()))
        except ValueError: return None