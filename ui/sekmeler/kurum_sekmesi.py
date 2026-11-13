import tkinter as tk
import sqlite3
from datetime import datetime, date
import customtkinter as ctk
from config import VARSAYILAN_KURUM, VARSAYILAN_GUNDELIK, EK_GOSTERGE, DERECELER, KADEMELER
from utils import parse_money, tl, dstr, gundelik_bul, tc_gecerli
from ui.tema import btn, ent, cmb, fld, card, sayfa_baslik, make_tree, bilgi, uyari, hata, sor, TEXT, MUTED, FN
from ui.bilesenler import DatePick

class KurumTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app, self.db = app, app.db
        self.sel_id = None
        sayfa_baslik(self, "Kurum, Gündelik ve Personel", "Kurum bilgilerini ve H Cetveli gündeliklerini girin, ardından okulun personelini ekleyin.")
        
        alt = ctk.CTkFrame(self, fg_color="transparent")
        alt.pack(side="bottom", fill="x", pady=(12, 0))
        btn(alt, "Yurtiçi Geçici Görev Yolluğu Hazırla", lambda: app.show("gecici"), width=320).pack(side="left", padx=(0, 10))
        btn(alt, "Yurtiçi Sürekli Görev Yolluğu Hazırla", lambda: app.show("surekli"), kind="ghost", width=320).pack(side="left")
        
        body = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure((0, 1), weight=1, uniform="c")

        # --- Kurum Bilgileri ---
        kc = card(body, "Kurum Bilgileri")
        kc.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 14))
        self.K = {k: tk.StringVar(value=self.db.get("kurum_" + k, VARSAYILAN_KURUM[k])) for k in VARSAYILAN_KURUM}
        b = kc.body
        fld(b, "Kamu İdaresi Adı", lambda f: ent(f, self.K["kamu"], 420), row=0, column=0, columnspan=2)
        fld(b, "Birim Adı", lambda f: ent(f, self.K["birim"], 420), row=1, column=0, columnspan=2)
        fld(b, "Birim VKN", lambda f: ent(f, self.K["vkn"], 200), row=2, column=0)
        fld(b, "Kurumsal Kod", lambda f: ent(f, self.K["kurumsal_kod"], 200), row=2, column=1)
        fld(b, "Bütçe Yılı", lambda f: ent(f, self.K["butce_yili"], 200), row=3, column=0)
        fld(b, "Onaylayan Ad Soyad", lambda f: ent(f, self.K["onay_ad"], 200), row=4, column=0)
        fld(b, "Onaylayan Unvan", lambda f: ent(f, self.K["onay_unvan"], 200), row=4, column=1)
        
        btn(b, "Kurum Bilgilerini Kaydet", self.kurum_kaydet, width=200).grid(row=5, column=1, sticky="e", padx=8, pady=(15, 0))

        # --- Gündelikler ---
        gc = card(body, "GÜNDELİKLER", "Her yıl T.C. Cumhurbaşkanlığı Strateji ve Bütçe Başkanlığı tarafından yayımlanan H Cetveline göre katsayıları güncelleyiniz.")
        gc.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 14))
        
        g = gc.body; g.grid_columnconfigure(0, weight=1)
        
        # Sabit Tarih Etiketi (Dinamik değil, DB'den çekilir)
        ctk.CTkLabel(g, text="Son Güncelleme Tarihi", font=FN["body"], text_color=TEXT).grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.lbl_guncelleme = ctk.CTkLabel(g, text=self.db.get("gundelik_tarih", "Henüz kaydedilmedi"), font=FN["btn"], text_color=MUTED, anchor="e")
        self.lbl_guncelleme.grid(row=0, column=1, sticky="e", padx=8)
        
        self.R = {}
        satirlar = [("r8000", "Ek göstergesi 8000+ olanlar"), ("r6400", "Ek göstergesi 6400 (dahil) - 8000 (hariç) olanlar"), ("r3600", "Ek göstergesi 3600 (dahil) - 6400 (hariç) olanlar"), ("r1_4", "Aylık/kadro derecesi 1-4 olanlar"), ("r5_15", "Aylık/kadro derecesi 5-15 olanlar")]
        for i, (k, t) in enumerate(satirlar, start=1):
            self.R[k] = tk.StringVar(value=self.db.get("gundelik_" + k, VARSAYILAN_GUNDELIK[k]))
            ctk.CTkLabel(g, text=t, font=FN["body"], text_color=TEXT, anchor="w", wraplength=280, justify="left").grid(row=i, column=0, sticky="w", padx=8, pady=5)
            f = ctk.CTkFrame(g, fg_color="transparent"); f.grid(row=i, column=1, sticky="e", padx=8)
            ent(f, self.R[k], 110).pack(side="left")
            ctk.CTkLabel(f, text="TL", font=FN["label"], text_color=MUTED).pack(side="left", padx=(6, 0))
        
        btn(g, "Gündelikleri Kaydet", self.gundelik_kaydet, width=150).grid(row=7, column=1, sticky="e", padx=8, pady=(12, 0))

        # --- Personel ---
        pc = card(body, "Personel", "Okulun tüm personelini ekleyin. Gündelik, ek gösterge ve kadro derecesine göre otomatik belirlenir.")
        pc.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.P = {k: tk.StringVar() for k in ("tc", "ad", "unvan", "ekg", "derece", "kademe", "iban", "ekg_no")}
        self.P["ekg"].set(EK_GOSTERGE[0]); self.P["derece"].set(DERECELER[0])
        b = pc.body
        for i in range(4): b.grid_columnconfigure(i, weight=1, uniform="p")
        fld(b, "TC Kimlik No *", lambda f: ent(f, self.P["tc"], 190), row=0, column=0)
        fld(b, "Ad Soyad *", lambda f: ent(f, self.P["ad"], 190), row=0, column=1)
        fld(b, "Unvan", lambda f: ent(f, self.P["unvan"], 190), row=0, column=2)
        fld(b, "İBAN (zorunlu değil)", lambda f: ent(f, self.P["iban"], 190), row=0, column=3)
        fld(b, "Ek Gösterge *", lambda f: cmb(f, self.P["ekg"], EK_GOSTERGE, 190), row=1, column=0)
        fld(b, "Kadro Derecesi *", lambda f: cmb(f, self.P["derece"], DERECELER, 190), row=1, column=1)
        fld(b, "Kademe (zorunlu değil)", lambda f: cmb(f, self.P["kademe"], KADEMELER, 190), row=1, column=2)
        fld(b, "Ek Gösterge Rakamı (isteğe bağlı)", lambda f: ent(f, self.P["ekg_no"], 190), hint="Bildirimde görünür, örn. 3000", row=1, column=3)
        bf = ctk.CTkFrame(b, fg_color="transparent"); bf.grid(row=2, column=0, columnspan=4, sticky="w", padx=6, pady=(6, 10))
        btn(bf, "Ekle", lambda: self.p_kaydet(False), width=110).pack(side="left", padx=(0, 8))
        btn(bf, "Güncelle", lambda: self.p_kaydet(True), kind="ghost", width=110).pack(side="left", padx=(0, 8))
        btn(bf, "Sil", self.p_sil, kind="danger", width=90).pack(side="left", padx=(0, 8))
        btn(bf, "Temizle", self.p_temizle, kind="ghost", width=100).pack(side="left")
        cols = ("tc", "ad", "unvan", "ekg", "derece", "kademe", "gundelik", "iban")
        wrap, self.tree = make_tree(b, cols, ("TC", "Ad Soyad", "Unvan", "Ek Gösterge", "Derece", "Kademe", "Gündelik", "İBAN"), (110, 170, 120, 130, 80, 80, 100, 200), height=9)
        wrap.grid(row=3, column=0, columnspan=4, sticky="nsew", padx=6)
        self.tree.bind("<<TreeviewSelect>>", self.p_sec)
        self.yenile()

    def kurum(self): return {k: v.get().strip() for k, v in self.K.items()}
    
    def oranlar(self):
        r = {}
        for k, v in self.R.items():
            try: r[k] = parse_money(v.get())
            except ValueError: raise ValueError("Gündelik tutarlarından biri hatalı.")
        return r

    def kurum_kaydet(self):
        for k, v in self.K.items(): 
            self.db.set("kurum_" + k, v.get().strip())
        bilgi(self, "Kurum bilgileri başarıyla kaydedildi.", "Kaydedildi")
        
    def gundelik_kaydet(self):
        try: 
            self.oranlar()
        except ValueError as e: 
            return hata(self, str(e))
            
        for k, v in self.R.items(): 
            self.db.set("gundelik_" + k, v.get().strip())
            
        # Tarihi sadece bu butona basıldığında güncelle ve kaydet
        bugun = dstr(date.today())
        self.db.set("gundelik_tarih", bugun)
        self.lbl_guncelleme.configure(text=bugun)
        
        self.yenile(); self.app.gecici.personel_yenile()
        bilgi(self, f"Gündelikler kaydedildi. Güncelleme Tarihi: {bugun}", "Kaydedildi")
        
    def yenile(self):
        self.tree.delete(*self.tree.get_children())
        try: r = self.oranlar()
        except ValueError: r = None
        for p in self.db.personeller():
            gun = tl(gundelik_bul(p["ekg"], p["derece"], r)) if r else "-"
            self.tree.insert("", "end", iid=str(p["id"]), values=(p["tc"], p["ad"], p["unvan"], p["ekg"], p["derece"], p["kademe"], gun, p["iban"]))
            
    def p_sec(self, _e=None):
        s = self.tree.selection()
        if not s: return
        self.sel_id = int(s[0])
        p = next((x for x in self.db.personeller() if x["id"] == self.sel_id), None)
        if p:
            for k, v in self.P.items(): v.set(p.get(k) or "")
            
    def p_temizle(self):
        self.sel_id = None
        for v in self.P.values(): v.set("")
        self.P["ekg"].set(EK_GOSTERGE[0]); self.P["derece"].set(DERECELER[0])
        sel = self.tree.selection()
        if sel: self.tree.selection_remove(*sel)
        
    def p_kaydet(self, guncelle):
        p = {k: v.get().strip() for k, v in self.P.items()}
        p["iban"] = p["iban"].replace(" ", "").upper()
        if not p["ad"] or not p["tc"]: return uyari(self, "TC Kimlik No ve Ad Soyad zorunludur.", "Eksik bilgi")
        if not tc_gecerli(p["tc"]) and not sor(self, "TC Kimlik No algoritma kontrolünden geçmedi. Yine de kaydedilsin mi?", "TC doğrulanamadı"): return
        if p["iban"] and not (p["iban"].startswith("TR") and len(p["iban"]) == 26) and not sor(self, "İBAN 'TR' ile başlayan 26 karakter görünmüyor. Yine de kaydedilsin mi?", "İBAN"): return
        try:
            if guncelle:
                if not self.sel_id: return bilgi(self, "Önce listeden bir personel seçin.")
                self.db.personel_kaydet(p, self.sel_id)
            else: self.db.personel_kaydet(p)
        except sqlite3.IntegrityError: return hata(self, "Bu TC ile kayıtlı personel zaten var.")
        self.yenile(); self.p_temizle(); self.app.gecici.personel_yenile()
        self.app.surekli_tab.personel_yukle()
        
    def p_sil(self):
        if self.sel_id and sor(self, "Seçili personel silinsin mi?", "Sil"):
            self.db.personel_sil(self.sel_id); self.p_temizle(); self.yenile(); self.app.gecici.personel_yenile()
            self.app.surekli_tab.personel_yukle()