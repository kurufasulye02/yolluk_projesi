import tkinter as tk
from tkinter import filedialog
from datetime import date, datetime
from decimal import Decimal
import customtkinter as ctk
from config import VASITALAR
from utils import parse_money, fmt, tl, dstr, tr_lower, gundelik_bul, veri_coz, veri_serilestir, kayit_ozet, open_file, q, D0, yemek_sayisi
from core.hesaplama import hesapla, ozet_metin
from core.pdf_rapor import pdf_olustur
from ui.tema import btn, ent, cmb, radio, enabled, fld, card, banner, sayfa_baslik, make_tree, bilgi, uyari, hata, sor, TEXT, MUTED, ACC, ACC_H, OK_BG, OK, BAD, INPUT, FN
from ui.bilesenler import DatePick, TimePick
import uuid

ASAMALAR = ["Personel Seçimi", "Görev Bilgileri", "Yolculuk Bilgileri", "Konaklama", "Hesaplama ve Raporlama"]
CHIP = ["Personel", "Görev", "Yolculuk", "Konaklama", "Rapor"]

class GeciciTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app, self.db = app, app.db
        self.step = 0
        self.kisi = None
        self.kayit_id = None
        self.gundelik_override = None
        self._gece_varsayilan = None
        sayfa_baslik(self, "Yurtiçi Geçici Görev Yolluğu", "Beş adımda personelin yolluk bildirimini hazırlayın.")
        
        st = ctk.CTkFrame(self, fg_color="transparent"); st.pack(fill="x", pady=(0, 12))
        self.chips = []
        for i, t in enumerate(CHIP):
            c = ctk.CTkLabel(st, text=f"{i + 1}  {t}", width=150, height=34, corner_radius=17, font=FN["label"])
            c.pack(side="left", padx=(0, 8)); self.chips.append(c)
        self.mod_lbl = ctk.CTkLabel(st, text="Yeni süreç", font=FN["btn"], text_color=ACC)
        self.mod_lbl.pack(side="right", padx=8)
        
        nav = ctk.CTkFrame(self, fg_color="transparent"); nav.pack(side="bottom", fill="x", pady=(12, 0))
        self.geri = btn(nav, "← Geri", lambda: self.git(self.step - 1), kind="ghost", width=120)
        self.geri.pack(side="left")
        self.ileri = btn(nav, "İleri →", self.ileri_git, width=240)
        self.ileri.pack(side="right")
        
        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.body.pack(fill="both", expand=True)
        self.frames = [self.b1(), self.b2(), self.b3(), self.b4(), self.b5()]
        self.git(0)

    def b1(self):
        f = ctk.CTkFrame(self.body, fg_color="transparent")
        c = card(f, "Personel Seçimi", "Listeden personeli seçin ve YOLLUK SÜRECİNİ BAŞLAT düğmesine basın.")
        c.pack(fill="x")
        cols = ("tc", "ad", "unvan", "ekg", "derece", "gundelik")
        wrap, self.ptree = make_tree(c.body, cols, ("TC", "Ad Soyad", "Unvan", "Ek Gösterge", "Derece", "Gündelik"), (120, 220, 150, 150, 90, 110), height=7)
        wrap.pack(fill="x", padx=6)
        self.ptree.bind("<Double-1>", lambda e: self.ileri_git())
        self.ptree.bind("<<TreeviewSelect>>", self.p_secildi)
        self.secili_lbl = ctk.CTkLabel(c.body, text="", font=FN["body"], text_color=MUTED, anchor="w")
        self.secili_lbl.pack(anchor="w", padx=10, pady=(10, 0))

        c2 = card(f, "Önceki Yolluk Süreçleri", "Seçili personelin arşivdeki yolluk süreçleri.")
        c2.pack(fill="x", pady=(14, 0))
        cols = ("ref", "guzergah", "tarih", "tutar", "durum", "islem")
        wrap, self.atree = make_tree(c2.body, cols, ("Referans No", "Güzergah", "Görev Tarihi", "Genel Tutar", "Durum", "Son İşlem"), (140, 230, 190, 120, 100, 140), height=5)
        wrap.pack(fill="x", padx=6)
        self.atree.bind("<Double-1>", lambda e: self.arsiv_ac("duzenle"))
        self.arsiv_bos = ctk.CTkLabel(c2.body, text="Önce bir personel seçin.", font=FN["label"], text_color=MUTED, anchor="w")
        self.arsiv_bos.pack(anchor="w", padx=10, pady=(8, 0))
        bf = ctk.CTkFrame(c2.body, fg_color="transparent"); bf.pack(fill="x", padx=6, pady=(10, 0))
        btn(bf, "Düzenle", lambda: self.arsiv_ac("duzenle"), width=120).pack(side="left", padx=(0, 8))
        btn(bf, "Kopyasını Oluştur", lambda: self.arsiv_ac("kopya"), kind="ghost", width=170).pack(side="left", padx=(0, 8))
        btn(bf, "PDF'i Yeniden Oluştur", lambda: self.arsiv_ac("pdf"), kind="ghost", width=190).pack(side="left", padx=(0, 8))
        btn(bf, "Sil", self.arsiv_sil, kind="danger", width=90).pack(side="left")
        return f

    def personel_yenile(self):
        self.ptree.delete(*self.ptree.get_children())
        try: r = self.app.kurum_tab.oranlar()
        except ValueError: r = None
        for p in self.db.personeller():
            gun = tl(gundelik_bul(p["ekg"], p["derece"], r)) if r else "-"
            self.ptree.insert("", "end", iid=str(p["id"]), values=(p["tc"], p["ad"], p["unvan"], p["ekg"], p["derece"], gun))
        self.secili_lbl.configure(text="")
        self.arsiv_yenile(None)

    def secili_personel(self):
        s = self.ptree.selection()
        if not s: return None
        return next((p for p in self.db.personeller() if str(p["id"]) == s[0]), None)

    def p_secildi(self, _e=None):
        p = self.secili_personel()
        if not p: return
        try: gun = tl(gundelik_bul(p["ekg"], p["derece"], self.app.kurum_tab.oranlar()))
        except ValueError: gun = "-"
        self.secili_lbl.configure(text=f"Seçilen: {p['ad']}   •   Gündelik: {gun}", text_color=TEXT)
        self.arsiv_yenile(p["tc"])

    def arsiv_yenile(self, tc=None):
        self.atree.delete(*self.atree.get_children())
        n = 0
        if tc:
            for r in self.db.kayitlar(tc):
                d, ek = veri_coz(r["veri"])
                if ek.get("tip") == "surekli" or d.get("tip") == "surekli":
                    continue

                oz = kayit_ozet(r)
                self.atree.insert("", "end", iid=str(r["id"]), values=(r["ref_no"], oz["guzergah"], oz["tarih"], tl(q(Decimal(str(r["genel"] or 0)))), "PDF Hazır" if r.get("durum") == "pdf" else "Taslak", oz["islem"]))
                n += 1
        self.arsiv_bos.configure(text="" if n else ("Bu personel için kayıtlı yolluk süreci yok." if tc else "Önce bir personel seçin."))

    def arsiv_sil(self):
        s = self.atree.selection()
        if not s: return uyari(self, "Listeden bir kayıt seçin.")
        r = self.db.kayit_getir(int(s[0]))
        if r and sor(self, f"{r['ref_no']} numaralı kayıt arşivden silinsin mi?", "Kaydı sil"):
            self.db.kayit_sil(r["id"])
            if self.kayit_id == r["id"]:
                self.kayit_id = None
                self.mod_guncelle()
            self.arsiv_yenile(r["personel_tc"])

    def arsiv_ac(self, mod):
        s = self.atree.selection()
        if not s: return uyari(self, "Listeden bir kayıt seçin.")
        r = self.db.kayit_getir(int(s[0]))
        kisi = next((p for p in self.db.personeller() if p["tc"] == r["personel_tc"]), None) if r else None
        if not kisi: return hata(self, "Bu kaydın personeli listede bulunamadı.")
        try: d, ek = veri_coz(r["veri"])
        except Exception: return hata(self, "Kayıt verisi okunamadı.")
        self.reset_form()
        self.kisi = kisi
        try:
            guncel = self.gundelik()
            eski = Decimal(str(d["gundelik"])) if d.get("gundelik") else None
        except (ValueError, ArithmeticError): eski = guncel = None
        
        if mod != "kopya" and eski is not None and guncel is not None and q(eski) != q(guncel):
            if sor(self, f"Kayıttaki gündelik ({tl(eski)}) güncel gündelikten ({tl(guncel)}) farklı.\n\nKayıttaki gündelikle devam edilsin mi?\n(Hayır: güncel gündelik kullanılır)", "Gündelik farkı"):
                self.gundelik_override = q(eski)
        self.forma_yukle(d, ek)
        if mod == "kopya":
            self.kayit_id = None
            self.v5["belge"].set("")
            self.d_bild.set(date.today())
            self.ref_doldur()
        else: self.kayit_id = r["id"]
        self.git(4 if mod == "pdf" else 1)

    def reset_form(self):
        for k in ("nereden", "nereye", "konu"): self.v[k].set("")
        self.v["nereden"].set(self.db.get("son_nereden", ""))
        self.v["ekgun"].set("hayir"); self.v["gece"].set("hayir")
        self.v["gunluk_gidis"].set("hayir")
        self.d_bas.set(date.today()); self.d_bit.set(date.today())
        self.t_cikis.h.set("08"); self.t_cikis.m.set("00")
        self.t_donus.h.set("18"); self.t_donus.m.set("00")
        for v in self.v3.values(): v.set("")
        self.v4["tur"].set("fatura")
        for k in ("yer", "gece", "ucret"): self.v4[k].set("")
        self.rayic.set(False)
        for v in self.v5.values(): v.set("")
        self.d_bild.set(date.today())
        self.kayit_id = None; self.gundelik_override = None; self._gece_varsayilan = None
        self.mod_guncelle()

    def forma_yukle(self, d, ek):
        def tarih(x):
            try: return datetime.strptime(x, "%d.%m.%Y").date()
            except (ValueError, TypeError): return None
        def para(x):
            try: v = Decimal(str(x))
            except (ArithmeticError, ValueError): return ""
            return fmt(v) if v > 0 else ""
        def bayrak(x): return str(x).lower() in ("true", "evet", "1")

        v = self.v
        for k in ("nereden", "nereye", "konu"): v[k].set(d.get(k, "") or "")
        for dp, key in ((self.d_bas, "bas"), (self.d_bit, "bit")):
            t = tarih(d.get(key))
            if t: dp.set(t)
        for tp, key in ((self.t_cikis, "cikis"), (self.t_donus, "donus")):
            try: h, m = str(d.get(key)).split(":"); tp.h.set(f"{int(h):02d}"); tp.m.set(f"{int(m):02d}")
            except ValueError: pass
        v["ekgun"].set(d.get("ekgun", "hayir") or "hayir")
        v["gece"].set("evet" if bayrak(d.get("gece")) else "hayir")
        v["gunluk_gidis"].set("evet" if bayrak(d.get("gunluk_gidis")) else "hayir")
        self.v3["vasita"].set(d.get("vasita", "") or "")
        for k, key in (("gidis", "gidis_bilet"), ("donus", "donus_bilet"), ("s_gidis", "sehir_gidis"), ("s_donus", "sehir_donus"), ("zorunlu", "zorunlu")):
            self.v3[k].set(para(d.get(key)))
        self.v3["z_tur"].set(d.get("zorunlu_tur", "") or "")
        self.v4["tur"].set(d.get("konak_tur", "fatura") or "fatura")
        self.v4["yer"].set(d.get("konak_yer", "") or "")
        n = str(d.get("gece_sayisi") or "")
        self.v4["gece"].set("" if n in ("0", "None") else n)
        self.v4["ucret"].set(para(d.get("gece_ucret")))
        self.rayic.set(bayrak(d.get("rayic")))
        self._gece_varsayilan = None
        self.v5["ref"].set(ek.get("ref", "") or "")
        self.v5["belge"].set(ek.get("belge", "") or "")
        self.v5["ettn"].set(ek.get("ettn", "") or "")
        self.v5["avans"].set(para(ek.get("avans")))
        t = tarih(ek.get("bildirim"))
        self.d_bild.set(t or date.today())

    def mod_guncelle(self):
        ref = self.v5["ref"].get().strip() if hasattr(self, "v5") else ""
        self.mod_lbl.configure(text=f"Düzenleniyor: {ref}" if self.kayit_id else "Yeni süreç")

    def kaydet_kayit(self, durum, g, hs):
        ref = self.v5["ref"].get().strip()
        if not ref: self.ref_doldur(); ref = self.v5["ref"].get().strip()
        if self.db.ref_var_mi(ref, self.kayit_id) and not sor(self, f"{ref} referans numarası başka bir kayıtta var. Yine de kaydedilsin mi?", "Referans no"): return False
        ek = {"ref": ref, "belge": self.v5["belge"].get().strip(), "ettn": self.v5["ettn"].get().strip(), "avans": self.v5["avans"].get().strip(), "bildirim": dstr(self.d_bild.get() or date.today()), "tip": "gecici"}
        yeni = self.kayit_id is None
        self.kayit_id = self.db.kayit_kaydet(self.kayit_id, ref, self.kisi["tc"], hs["tot"]["genel"], veri_serilestir(g, ek), durum)
        if yeni: self.db.set("ref_sayac", str(int(self.db.get("ref_sayac", "1")) + 1))
        self.db.set("son_nereden", g["nereden"])
        self.mod_guncelle(); return True

    def taslak_kaydet(self):
        try:
            g = self.topla(); parse_money(self.v5["avans"].get())
        except ValueError as e: return hata(self, str(e))
        if self.kaydet_kayit("taslak", g, hesapla(g, g.get("gecmis_gun", 0))):
            bilgi(self, f"Süreç arşive taslak olarak kaydedildi ({self.v5['ref'].get().strip()}).", "Kaydedildi")

    def b2(self):
        f = ctk.CTkFrame(self.body, fg_color="transparent")
        self.v = {k: tk.StringVar() for k in ("nereden", "nereye", "konu", "ekgun", "gece", "gunluk_gidis")}
        self.v["ekgun"].set("hayir"); self.v["gece"].set("hayir"); self.v["gunluk_gidis"].set("hayir")
        
        c = card(f, "Görev Bilgileri"); c.pack(fill="x"); b = c.body
        fld(b, "Nereden gittiniz? (Çalıştığınız / Oturduğunuz yer)", lambda w: ent(w, self.v["nereden"], 320), hint="Örnek: Bartın/Ulus", row=0, column=0)
        fld(b, "Nereye gittiniz? (Görevin yapıldığı il/ilçe)", lambda w: ent(w, self.v["nereye"], 320), hint="Örnek: Tekirdağ/Ergene", row=0, column=1)
        fld(b, "Görevin konusu", lambda w: ent(w, self.v["konu"], 320), hint="Örnek: Seminer, kurs, toplantı", row=1, column=0, columnspan=2)
        self.d_bas = fld(b, "Görev hangi gün başladı?", lambda w: DatePick(w, on_change=self.tarih_degisti), row=2, column=0)
        self.d_bit = fld(b, "Görev hangi gün bitti? (Tek günlükse aynı tarih)", lambda w: DatePick(w, on_change=self.tarih_degisti), row=2, column=1)
        self.t_cikis = fld(b, "Yola çıkış saatiniz", lambda w: TimePick(w, 8, 0, on_change=self.saat_notu), row=3, column=0)
        self.t_donus = fld(b, "Dönüş saatiniz", lambda w: TimePick(w, 18, 0, on_change=self.saat_notu), row=3, column=1)
        
        info = banner(f, "Günübirlik veya günlük gidiş-geliş görevlerde yevmiye, öğle (13.00) ve akşam (19.00) yemek saatlerini görevde geçirip geçirmediğinize göre ödenir. Bunu saatlerden program hesaplar."); info.pack(fill="x", pady=(12, 0))
        self.saat_ban = banner(f, "", "ok"); self.saat_lbl = self.saat_ban.lbl; self.saat_ban.pack(fill="x", pady=(8, 0))
        
        c2 = card(f, "Konaklama ve Yol Günleri"); c2.pack(fill="x", pady=(14, 0)); b = c2.body
        
        self.v["gunluk_gidis"].trace_add("write", lambda *a: self.gunluk_gidis_degisti())
        
        self.chk_gunluk_gidis = ctk.CTkCheckBox(
            b, 
            text="Göreve Günlük Olarak Gidiş Geliş Yapıldı (Konaklama yoktur)", 
            variable=self.v["gunluk_gidis"], 
            onvalue="evet", offvalue="hayir",
            font=FN["body"], text_color=TEXT, fg_color=ACC, hover_color=ACC_H, border_color=MUTED
        )
        self.chk_gunluk_gidis.pack(anchor="w", padx=8, pady=(4, 8))
        
        ctk.CTkLabel(b, text="Görev yerinde geceyi geçirdiniz mi?", font=FN["body"], text_color=TEXT).pack(anchor="w", padx=8, pady=(4, 4))
        gf = ctk.CTkFrame(b, fg_color="transparent"); gf.pack(anchor="w", padx=8)
        self.r_gece = [radio(gf, "Evet", self.v["gece"], "evet"), radio(gf, "Hayır", self.v["gece"], "hayir")]
        for r in self.r_gece: r.pack(side="left", padx=(0, 20))
        
        self.lbl_ekgun = ctk.CTkLabel(b, text="Yolculuk için görev günleri dışında ayrıca gün harcadınız mı?", font=FN["body"], text_color=TEXT)
        self.lbl_ekgun.pack(anchor="w", padx=8, pady=(16, 4))
        
        self.ekgun_frame = ctk.CTkFrame(b, fg_color="transparent")
        self.ekgun_frame.pack(anchor="w", fill="x", padx=8)
        for t, val in (("Hayır", "hayir"), ("Gitmek için 1 gün önce yola çıktım", "once"), ("Dönüşte 1 gün sonra eve vardım", "sonra"), ("Hem 1 gün önce çıktım hem 1 gün sonra vardım", "ikisi")):
            radio(self.ekgun_frame, t, self.v["ekgun"], val).pack(anchor="w", pady=3)
            
        return f

    def gunluk_gidis_degisti(self):
        gunluk = self.v["gunluk_gidis"].get() == "evet"
        if gunluk:
            self.v["gece"].set("hayir")
            self.v["ekgun"].set("hayir")
        for r in self.r_gece:
            r.configure(state="disabled" if gunluk else "normal")
        
        for child in self.ekgun_frame.winfo_children():
            child.configure(state="disabled" if gunluk else "normal")

    def tarih_degisti(self):
        b, e = self.d_bas.get(), self.d_bit.get()
        tek = bool(b and e and b == e)
        if tek: self.v["gece"].set("hayir")
        for r in self.r_gece: r.configure(state="disabled" if tek or self.v["gunluk_gidis"].get() == "evet" else "normal")
        self.saat_notu()

    def saat_notu(self):
        b, e, c, d = self.d_bas.get(), self.d_bit.get(), self.t_cikis.get(), self.t_donus.get()
        renk = OK
        if not (b and e and c and d): txt = ""
        elif b != e and self.v["gunluk_gidis"].get() != "evet": txt = "Çok günlü görev: her görev günü için tam gündelik hesaplanır."
        elif d <= c: txt, renk = "Dönüş saati çıkış saatinden sonra olmalı.", BAD
        else:
            txt = {0: "13:00 ve 19:00 yemek saatleri kapsanmıyor: görev gündeliği ödenmez.", 1: "Bir yemek saati kapsanıyor: gündeliğin 1/3'ü ödenir.", 2: "13:00 ve 19:00 kapsanıyor: gündeliğin 2/3'ü ödenir."}[yemek_sayisi(c, d)]
        self.saat_lbl.configure(text=txt, text_color=renk)

    def b3(self):
        f = ctk.CTkFrame(self.body, fg_color="transparent")
        self.v3 = {k: tk.StringVar() for k in ("vasita", "gidis", "donus", "s_gidis", "s_donus", "zorunlu", "z_tur")}
        c = card(f, "Yolculuk Ücreti", "Taşıtı listeden seçebilir ya da kendiniz yazabilirsiniz. Kurum aracı ise bilet alanları kapanır."); c.pack(fill="x"); b = c.body
        self.cb_vasita = fld(b, "Neyle gittiniz?", lambda w: cmb(w, self.v3["vasita"], VASITALAR, 260, state="normal"), row=0, column=0, columnspan=2)
        self.v3["vasita"].trace_add("write", lambda *a: self.vasita_degisti())
        self.e_gidis = fld(b, "Gidiş Bileti", lambda w: ent(w, self.v3["gidis"], 200), hint="Örnek: 150,00 TL", row=1, column=0)
        self.e_donus = fld(b, "Dönüş Bileti", lambda w: ent(w, self.v3["donus"], 200), hint="Örnek: 150,00 TL", row=1, column=1)
        c2 = card(f, "Şehir içinde başka masrafınız oldu mu?", "Evden otogara, otogardan görev yerine giderken ödediğiniz taksi, dolmuş, otobüs ücretleri. Gidiş ve dönüş toplamını yazın. Yoksa boş bırakın."); c2.pack(fill="x", pady=(14, 0)); b = c2.body
        fld(b, "Gidiş Masrafı", lambda w: ent(w, self.v3["s_gidis"], 200), hint="Örnek: 100,00 TL", row=0, column=0)
        fld(b, "Dönüş Masrafı", lambda w: ent(w, self.v3["s_donus"], 200), hint="Örnek: 100,00 TL", row=0, column=1)
        c3 = card(f, "Başka zorunlu masrafınız oldu mu?", "Yoksa boş bırakın."); c3.pack(fill="x", pady=(14, 0)); b = c3.body
        fld(b, "Zorunlu masraflar toplamı", lambda w: ent(w, self.v3["zorunlu"], 200), hint="Örnek: 300,00 TL", row=0, column=0)
        fld(b, "Zorunlu masraflar türü", lambda w: ent(w, self.v3["z_tur"], 320), hint="Örnek: Köprü geçişi, otoyol ücreti vs.", row=0, column=1)
        return f

    def vasita_degisti(self):
        kurum = "kurum" in tr_lower(self.v3["vasita"].get())
        for e in (self.e_gidis, self.e_donus): enabled(e, not kurum)
        if kurum: self.v3["gidis"].set(""); self.v3["donus"].set("")

    def b4(self):
        f = ctk.CTkFrame(self.body, fg_color="transparent")
        self.v4 = {k: tk.StringVar() for k in ("tur", "yer", "gece", "ucret")}; self.v4["tur"].set("fatura"); self.rayic = tk.BooleanVar(value=False)
        self.uyari4 = banner(f, "", "warn")
        self.form4 = card(f, "Nerede kaldınız?"); b = self.form4.body
        for t, val in (("Otel/pansiyon/misafirhanede kaldım, faturam var (Her gece için yevmiyenin %50 fazlasına kadar ödenir)", "fatura"), ("Kendim ayarladım ama faturam yok (Her gece için yevmiyenin yarısı ödenir)", "faturasiz"), ("Ücretsiz yer verildi (Misafirhane, yurt, eğitim enstitüsü vb. konaklama ücreti için ödeme yapılmaz)", "ucretsiz")):
            radio(b, t, self.v4["tur"], val, command=self.konak_durum).grid(sticky="w", padx=8, pady=4, column=0, columnspan=2)
        fld(b, "Konaklanan yer (otel/misafirhane adı)", lambda w: ent(w, self.v4["yer"], 320), row=3, column=0, columnspan=2)
        fld(b, "Kaç gece kaldınız?", lambda w: ent(w, self.v4["gece"], 120), row=4, column=0)
        self.e_ucret = fld(b, "Bir gece için ne kadar ödediniz?", lambda w: ent(w, self.v4["ucret"], 200), row=4, column=1)
        self.tavan_lbl = ctk.CTkLabel(b, text="", font=FN["label"], text_color=MUTED, anchor="w", wraplength=700, justify="left"); self.tavan_lbl.grid(row=5, column=0, columnspan=2, sticky="w", padx=10, pady=(4, 0))
        ctk.CTkCheckBox(b, text="Rayiç bedel belgesi var (gecelik tavan aşılabilir)", variable=self.rayic, font=FN["body"], text_color=TEXT, fg_color=ACC, hover_color=ACC_H, border_color=MUTED).grid(row=6, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 0))
        return f

    def konak_durum(self):
        t = self.v4["tur"].get(); enabled(self.e_ucret, t == "fatura")
        if not self.kisi: return
        gun = self.gundelik()
        self.tavan_lbl.configure(text={"fatura": f"Bir gecelik ücret için en fazla {tl(gun * Decimal('1.5'))} (Gündelik x 1,50) ödenir.", "faturasiz": f"Gece başına {tl(gun / 2)} ödenir (gündeliğin yarısı).", "ucretsiz": "Ücretsiz konaklamada ödeme yapılmaz."}[t])

    def konak_hazirla(self):
        b, e = self.d_bas.get(), self.d_bit.get()
        self.uyari4.pack_forget(); self.form4.pack_forget()
        if b == e:
            self.uyari4.lbl.configure(text="Aynı gün gidilip dönülen görevlendirmelerde konaklama ücreti olmaz. Sonraki aşamaya geçebilirsiniz.")
            self.uyari4.pack(fill="x", pady=6)
        elif self.v["gunluk_gidis"].get() == "evet":
            self.uyari4.lbl.configure(text="Göreve günlük gidiş geliş yapıldığı için konaklama ücreti olmaz. Sonraki aşamaya geçebilirsiniz.")
            self.uyari4.pack(fill="x", pady=6)
        elif self.v["gece"].get() == "hayir":
            self.uyari4.lbl.configure(text="Görev yerinde geceyi geçirmediğiniz için konaklama ücreti olmaz. Sonraki aşamaya geçebilirsiniz.")
            self.uyari4.pack(fill="x", pady=6)
        else:
            varsayilan = str((e - b).days)
            if not self.v4["gece"].get() or self.v4["gece"].get() == self._gece_varsayilan: self.v4["gece"].set(varsayilan)
            self._gece_varsayilan = varsayilan
            self.form4.pack(fill="x"); self.konak_durum()

    def b5(self):
        f = ctk.CTkFrame(self.body, fg_color="transparent")
        sf = ctk.CTkFrame(f, fg_color="transparent"); sf.pack(fill="x"); sf.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="s")
        self.stat = {}
        for i, (k, t) in enumerate((("gundelik", "Gündelik"), ("yol", "Yol Masrafı"), ("konak", "Konaklama"), ("diger", "Diğer Masraf"))):
            s = ctk.CTkFrame(sf, fg_color=INPUT, corner_radius=14, border_width=1, border_color=ACC)
            s.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 6, 6 if i < 3 else 0))
            ctk.CTkLabel(s, text=t, font=FN["small"], text_color=MUTED).pack(anchor="w", padx=16, pady=(12, 0))
            self.stat[k] = ctk.CTkLabel(s, text="0,00 TL", font=FN["h2"], text_color=TEXT); self.stat[k].pack(anchor="w", padx=16, pady=(0, 12))
        gs = ctk.CTkFrame(f, fg_color=ACC, corner_radius=16); gs.pack(fill="x", pady=(10, 0))
        ctk.CTkLabel(gs, text="GENEL BİLDİRİM TUTARI", font=FN["small"], text_color="#E0E7FF").pack(anchor="w", padx=22, pady=(14, 0))
        self.stat["genel"] = ctk.CTkLabel(gs, text="0,00 TL", font=FN["h0"], text_color="#FFFFFF"); self.stat["genel"].pack(anchor="w", padx=22, pady=(0, 14))
        
        c = card(f, "Bildirim Bilgileri"); c.pack(fill="x", pady=(14, 0)); self.v5 = {k: tk.StringVar() for k in ("ref", "belge", "ettn", "avans")}; b = c.body
        fld(b, "Yolluk Referans No", lambda w: ent(w, self.v5["ref"], 200), row=0, column=0)
        fld(b, "Belge Numarası", lambda w: ent(w, self.v5["belge"], 200), row=0, column=1)
        self.d_bild = fld(b, "Bildirim Tarihi", lambda w: DatePick(w), row=0, column=2)
        fld(b, "ETTN", lambda w: ent(w, self.v5["ettn"], 410), row=1, column=0, columnspan=2)
        fld(b, "Avans Tutarı (varsa)", lambda w: ent(w, self.v5["avans"], 200), row=1, column=2)

        c2 = card(f, "Ön İzleme"); c2.pack(fill="x", pady=(14, 0))
        self.onizleme = ctk.CTkTextbox(c2.body, height=380, font=FN["mono"], wrap="none", fg_color=INPUT, text_color=TEXT, corner_radius=12)
        self.onizleme.pack(fill="x", padx=6)
        bf = ctk.CTkFrame(c2.body, fg_color="transparent"); bf.pack(fill="x", padx=6, pady=(12, 0))
        btn(bf, "Yenile", self.onizle, kind="ghost", width=110).pack(side="left")
        btn(bf, "Arşive Kaydet (Taslak)", self.taslak_kaydet, kind="ghost", width=210).pack(side="left", padx=8)
        btn(bf, "RAPORLA (PDF)", self.raporla, width=220).pack(side="right")
        return f

    def ref_doldur(self):
        self.v5["ref"].set(f"{self.app.kurum_tab.K['butce_yili'].get()}YLK{int(self.db.get('ref_sayac', '1')):05d}")
        self.v5["ettn"].set(str(uuid.uuid4()))

    def onizle(self):
        try: g = self.topla()
        except ValueError as e: return hata(self, str(e))
        hs = hesapla(g, g.get("gecmis_gun", 0))
        for k in ("gundelik", "yol", "konak", "diger", "genel"): self.stat[k].configure(text=tl(hs["tot"][k]))
        self.onizleme.configure(state="normal"); self.onizleme.delete("1.0", "end")
        self.onizleme.insert("1.0", ozet_metin(self.kisi, g, hs)); self.onizleme.configure(state="disabled")

    def gundelik(self):
        if self.gundelik_override is not None: return self.gundelik_override
        return gundelik_bul(self.kisi["ekg"], self.kisi["derece"], self.app.kurum_tab.oranlar())

    def topla(self):
        if not self.kisi: raise ValueError("Önce personel seçin.")
        v = self.v; b, e, c, d = self.d_bas.get(), self.d_bit.get(), self.t_cikis.get(), self.t_donus.get()
        if not v["nereden"].get().strip() or not v["nereye"].get().strip(): raise ValueError("Nereden / Nereye alanlarını doldurun.")
        if not (b and e): raise ValueError("Tarihler geçersiz (gg.aa.yyyy).")
        if e < b: raise ValueError("Bitiş tarihi başlangıçtan önce olamaz.")
        if not (c and d): raise ValueError("Saatler geçersiz.")
        if b == e and d <= c: raise ValueError("Günübirlik görevde dönüş saati çıkış saatinden sonra olmalı.")
        vasita = self.v3["vasita"].get().strip()
        if not vasita: raise ValueError("Taşıt bilgisini girin (Neyle gittiniz?).")
        
        gunluk_gidis = v["gunluk_gidis"].get() == "evet"
        gece_sayisi, gece_ucret = 0, D0
        
        if not gunluk_gidis and b != e and v["gece"].get() == "evet":
            try: gece_sayisi = int(self.v4["gece"].get() or 0)
            except ValueError: raise ValueError("Gece sayısı sayı olmalı.")
            gece_ucret = parse_money(self.v4["ucret"].get())
            if self.v4["tur"].get() == "fatura" and gece_sayisi > 0 and gece_ucret <= 0: raise ValueError("Faturalı konaklama için gecelik ücreti girin.")
            
        gecmis = self.db.gecici_gecmis_gun(self.kisi["tc"], v["nereye"].get().strip())
            
        P3 = self.v3
        return {
            "gundelik": self.gundelik(), "nereden": v["nereden"].get().strip(), "nereye": v["nereye"].get().strip(), "konu": v["konu"].get().strip(),
            "bas": b, "bit": e, "cikis": c, "donus": d, "gece": v["gece"].get() == "evet", "gunluk_gidis": gunluk_gidis, 
            "ekgun": v["ekgun"].get(), "vasita": vasita,
            "gidis_bilet": parse_money(P3["gidis"].get()), "donus_bilet": parse_money(P3["donus"].get()),
            "sehir_gidis": parse_money(P3["s_gidis"].get()), "sehir_donus": parse_money(P3["s_donus"].get()),
            "zorunlu": parse_money(P3["zorunlu"].get()), "zorunlu_tur": P3["z_tur"].get().strip(),
            "konak_tur": self.v4["tur"].get(), "konak_yer": self.v4["yer"].get().strip(), "gece_sayisi": gece_sayisi, "gece_ucret": gece_ucret, "rayic": self.rayic.get(),
            "gecmis_gun": gecmis
        }

    def stepper(self):
        for i, c in enumerate(self.chips):
            if i == self.step: c.configure(fg_color=ACC, text_color="#FFFFFF", text=f"{i + 1}  {CHIP[i]}")
            elif i < self.step: c.configure(fg_color=OK_BG, text_color=OK, text=f"✓  {CHIP[i]}")
            else: c.configure(fg_color=INPUT, text_color=MUTED, text=f"{i + 1}  {CHIP[i]}")

    def git(self, n):
        if n < 0 or n > 4: return
        for f in self.frames: f.pack_forget()
        self.step = n; self.frames[n].pack(fill="both", expand=True)
        try: self.body._parent_canvas.yview_moveto(0)
        except Exception: pass
        self.stepper(); self.mod_guncelle()
        self.geri.configure(state="disabled" if n == 0 else "normal")
        self.ileri.configure(text="YOLLUK SÜRECİNİ BAŞLAT" if n == 0 else "İleri →")
        if n == 4: self.ileri.pack_forget()
        else: self.ileri.pack(side="right")
        if n == 0: self.personel_yenile()
        elif n == 1: self.tarih_degisti()
        elif n == 3: self.konak_hazirla()
        elif n == 4:
            if not self.v5["ref"].get(): self.ref_doldur()
            self.onizle()

    def ileri_git(self):
        s = self.step
        if s == 0:
            sel = self.ptree.selection()
            if not sel: return uyari(self, "Listeden bir personel seçin.", "Personel")
            yeni = self.secili_personel()
            if self.kisi is None or self.kisi["tc"] != yeni["tc"]: self.reset_form()
            elif self.kayit_id is not None:
                if sor(self, f"{self.v5['ref'].get().strip()} kaydı üzerinde çalışıyordunuz.\n\nYeni bir yolluk süreci başlatılsın mı?\n(Hayır: bu kayda devam)", "Yeni süreç"): self.reset_form()
            self.kisi = yeni
            try: self.gundelik()
            except ValueError as e: return hata(self, str(e))
        elif s == 1:
            b, e, c, d = self.d_bas.get(), self.d_bit.get(), self.t_cikis.get(), self.t_donus.get()
            if not (self.v["nereden"].get().strip() and self.v["nereye"].get().strip()): return uyari(self, "Nereden / Nereye alanlarını doldurun.", "Eksik bilgi")
            if not (b and e and c and d): return uyari(self, "Tarih (gg.aa.yyyy) veya saat geçersiz.")
            if e < b: return uyari(self, "Bitiş tarihi başlangıçtan önce olamaz.")
            if b == e and d <= c: return uyari(self, "Dönüş saati çıkış saatinden sonra olmalı.")
        elif s == 2:
            if not self.v3["vasita"].get().strip(): return uyari(self, "Neyle gittiniz? alanını doldurun.", "Eksik bilgi")
            try:
                for k in ("gidis", "donus", "s_gidis", "s_donus", "zorunlu"): parse_money(self.v3[k].get())
            except ValueError as e: return uyari(self, str(e))
        elif s == 3:
            try: self.topla()
            except ValueError as e: return uyari(self, str(e))
        self.git(s + 1)

    def raporla(self):
        try:
            g = self.topla(); avans = parse_money(self.v5["avans"].get())
        except ValueError as e: return hata(self, str(e))
        hs = hesapla(g, g.get("gecmis_gun", 0))
        ref = self.v5["ref"].get().strip()
        ad = "".join(ch for ch in self.kisi["ad"] if ch.isalnum() or ch in " _-").strip().replace(" ", "_")
        yol = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], initialfile=f"Yolluk_{ref}_{ad}.pdf", title="Bildirimi kaydet")
        if not yol: return
        bt = self.d_bild.get() or date.today()
        try: pdf_olustur(yol, self.app.kurum_tab.kurum(), self.kisi, g, hs, ref, bt, self.v5["belge"].get().strip(), self.v5["ettn"].get().strip(), avans)
        except ImportError: return hata(self, "PDF için reportlab gerekli:\n\npip install reportlab", "Eksik paket")
        except Exception as ex: return hata(self, str(ex), "PDF hatası")
        self.kaydet_kayit("pdf", g, hs)
        open_file(yol)
        bilgi(self, f"Bildirim oluşturuldu ve arşive kaydedildi:\n{yol}\n\nGenel tutar: {tl(hs['tot']['genel'])}", "Hazır")