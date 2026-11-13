import tkinter as tk
from tkinter import filedialog
import json
from datetime import date
from decimal import Decimal
import customtkinter as ctk
from config import VASITALAR
from utils import parse_money, fmt, tl, dstr, surekli_gundelik_bul, open_file, q, D0, veri_coz, kayit_ozet
from core.hesaplama import surekli_hesapla
from core.pdf_rapor import surekli_pdf_olustur
from ui.tema import btn, ent, cmb, radio, enabled, fld, card, sayfa_baslik, make_tree, bilgi, uyari, hata, sor, TEXT, MUTED, ACC, ACC_H, OK, BAD, INPUT, FN, LINE, CARD
from ui.bilesenler import DatePick

class SurekliTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app, self.db = app, app.db
        self.kisi = None
        self.satirlar = []
        self.kayit_id = None 
        self.duzenlenen_index = None
        
        sayfa_baslik(self, "Yurtiçi Sürekli Görev Yolluğu", "Atama işlemleri için sürekli görev yolluğu hazırlayın.")
        
        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.body.pack(fill="both", expand=True)
        
        self.setup_ui()
        self.personel_yukle()
        
    def setup_ui(self):
        # 1. PERSONEL SEÇİMİ
        c1 = card(self.body, "1. Personel Seçimi")
        c1.pack(fill="x", pady=(0, 10))
        cols = ("tc", "ad", "unvan", "derece", "kademe")
        wrap, self.ptree = make_tree(c1.body, cols, ("TC", "Ad Soyad", "Unvan", "Derece", "Kademe"), (120, 200, 150, 80, 80), height=4)
        wrap.pack(fill="x", padx=6)
        self.ptree.bind("<<TreeviewSelect>>", self.p_secildi)
        self.lbl_secili = ctk.CTkLabel(c1.body, text="Lütfen yukarıdan bir personel seçin.", font=FN["body"], text_color=MUTED)
        self.lbl_secili.pack(anchor="w", padx=10, pady=(5, 0))
        
        # 1.5 GEÇMİŞ KAYITLAR
        self.c_gecmis = card(self.body, "Geçmiş Kayıtlar", "Daha önce kaydettiğiniz taslak veya raporları buradan geri yükleyebilirsiniz.")
        cols_h = ("ref", "tarih", "tutar", "durum")
        wrap_h, self.htree = make_tree(self.c_gecmis.body, cols_h, ("Referans No", "İşlem Tarihi", "Genel Tutar", "Durum"), (150, 150, 150, 100), height=3)
        wrap_h.pack(fill="x", padx=6)
        self.htree.bind("<Double-1>", lambda e: self.gecmis_yukle())
        btn(self.c_gecmis.body, "Seçili Kaydı Yükle", self.gecmis_yukle, width=150).pack(anchor="e", padx=6, pady=(5,0))
        self.c_gecmis.pack_forget()

        # 2. GENEL BİLGİLER VE DURUM SEÇİMİ
        self.c2 = card(self.body, "2. Atama, Avans ve Durum Bilgileri")
        self.c2.pack(fill="x", pady=(0, 10))
        b2 = self.c2.body
        
        self.d_atama = fld(b2, "Atama Tarihi", lambda w: DatePick(w), row=0, column=0)
        self.v_avans = tk.StringVar(value="Almadı")
        fld(b2, "Önceden Avans Almışsa Aldığı", lambda w: ent(w, self.v_avans, 200), row=0, column=1)
        
        self.v_es_durumu = tk.BooleanVar(value=False)
        self.v_es_durumu.trace_add("write", lambda *a: self.tabloyu_yenile())
        
        chk_frame = ctk.CTkFrame(b2, fg_color="transparent")
        chk_frame.grid(row=1, column=0, columnspan=4, sticky="w", padx=8, pady=(15, 5))
        
        ctk.CTkCheckBox(
            chk_frame, 
            text="Eş Nedeniyle Tayin", 
            variable=self.v_es_durumu,
            onvalue=True, offvalue=False,
            font=FN["body"], text_color=TEXT, fg_color=ACC, hover_color=ACC_H, border_color=MUTED
        ).pack(side="left", anchor="n")
        
        ctk.CTkLabel(
            chk_frame, 
            text="(İkisi de memur olan eşler aynı görev mahallinden aynı görev mahalline atanırsa eşlerden birisi tam diğeri yarım yolluk yapılır ve çocuk varsa çocuk yardımını kim alıyorsa yollukta çocuk onun hesabına eklenir.)",
            font=FN["small"], text_color=MUTED, wraplength=800, justify="left"
        ).pack(side="left", padx=(10, 0), anchor="w")
        
        self.v_cocuk_sahibi = tk.StringVar(value="Kendisi")
        self.v_cocuk_sahibi.trace_add("write", lambda *a: self.tabloyu_yenile())
        
        ctk.CTkLabel(b2, text="Çocuk Yardımı Kimin Üzerinden Hesaplanacak?", font=FN["label"], text_color=MUTED).grid(row=2, column=0, sticky="w", padx=8, pady=(10, 0))
        cf = ctk.CTkFrame(b2, fg_color="transparent")
        cf.grid(row=3, column=0, columnspan=4, sticky="w", padx=8)
        radio(cf, "Bu Personel (Kendisi)", self.v_cocuk_sahibi, "Kendisi").pack(side="left", padx=(0, 15))
        radio(cf, "Diğer Eş (Eşi)", self.v_cocuk_sahibi, "Eşi").pack(side="left")

        # 3. AİLE FERTLERİ VE MASRAFLAR (TABLO)
        self.c3 = card(self.body, "3. Aile Fertleri ve Masraf Bilgileri", "Satır ekleyerek hesaplama yapabilirsiniz. Düzenlemek için tablodaki satıra çift tıklayın.")
        self.c3.pack(fill="x", pady=(0, 10))
        
        b3 = self.c3.body
        self.v_nereden = tk.StringVar()
        self.v_nereye = tk.StringVar()
        self.v_ad = tk.StringVar()
        self.v_akraba = tk.StringVar(value="Kendisi")
        self.v_akraba.trace_add("write", lambda *a: self.akraba_degisti()) 
        self.v_gun = tk.StringVar(value="1")
        self.v_tasit = tk.StringVar(value="Otobüs")
        self.v_tasit_ucret = tk.StringVar(value="0,00")
        self.v_mesafe = tk.StringVar(value="0")
        
        frame_inputs = ctk.CTkFrame(b3, fg_color="transparent")
        frame_inputs.pack(fill="x", pady=5)
        
        fld(frame_inputs, "Nereden", lambda w: ent(w, self.v_nereden, 150), row=0, column=0)
        fld(frame_inputs, "Nereye", lambda w: ent(w, self.v_nereye, 150), row=0, column=1)
        fld(frame_inputs, "Adı Soyadı", lambda w: ent(w, self.v_ad, 150), row=0, column=2)
        fld(frame_inputs, "Yakınlık", lambda w: cmb(w, self.v_akraba, ["Kendisi", "Eşi", "Çocuğu"], 100, state="readonly"), row=0, column=3)
        fld(frame_inputs, "Gün", lambda w: ent(w, self.v_gun, 60), row=0, column=4)
        fld(frame_inputs, "Taşıt", lambda w: cmb(w, self.v_tasit, VASITALAR, 100, state="readonly"), row=0, column=5)
        fld(frame_inputs, "Taşıt Ücreti", lambda w: ent(w, self.v_tasit_ucret, 100), row=0, column=6)
        self.e_mesafe = fld(frame_inputs, "Mesafe (Km)", lambda w: ent(w, self.v_mesafe, 80), row=0, column=7)
        
        # DÜZELTİLEN BUTONLAR (Grid Hizalaması ve İptal Rengi)
        btn_frame = ctk.CTkFrame(frame_inputs, fg_color="transparent")
        btn_frame.grid(row=0, column=8, padx=(10, 0), pady=(15,0), sticky="ew")
        
        self.btn_ekle = btn(btn_frame, "Satır Ekle", self.satir_kaydet, width=120)
        self.btn_ekle.pack(side="left")
        
        self.btn_iptal = btn(btn_frame, "İptal", self.formu_temizle, kind="danger", width=70)
        self.btn_iptal.pack(side="left", padx=(5, 0))
        self.btn_iptal.pack_forget() # Başlangıçta gizli
        
        cols = ("nereden", "nereye", "ad", "akraba", "gun", "yevmiye", "g_tutar", "tasit", "tasit_ucret", "sabit", "degisken", "toplam")
        heads = ("Nereden", "Nereye", "Adı Soyadı", "Yakınlık", "Gün", "Yevmiye", "Gündelik", "Taşıt", "Ücret", "Sabit", "Değişken", "Toplam")
        widths = (100, 100, 120, 70, 40, 70, 70, 70, 70, 70, 70, 90)
        
        wrap, self.tree = make_tree(b3, cols, heads, widths, height=5)
        wrap.pack(fill="x", pady=10, padx=6)
        self.tree.bind("<Double-1>", self.satir_secildi)
        
        btn(b3, "Seçili Satırı Sil", self.satir_sil, kind="danger", width=120).pack(anchor="e", padx=6)

        # 4. ÖZET VE RAPOR
        self.c4 = card(self.body, "4. Genel Toplam ve Raporlama")
        self.c4.pack(fill="x", pady=10)
        b4 = self.c4.body
        
        self.lbl_genel = ctk.CTkLabel(b4, text="GENEL TOPLAM: 0,00 TL", font=FN["h1"], text_color=ACC)
        self.lbl_genel.pack(pady=10)
        
        btn_frame2 = ctk.CTkFrame(b4, fg_color="transparent")
        btn_frame2.pack(pady=10)
        
        btn(btn_frame2, "Taslak Olarak Kaydet", self.taslak_kaydet, kind="ghost", width=160).pack(side="left", padx=10)
        btn(btn_frame2, "Raporu Oluştur (PDF)", self.raporla, width=200).pack(side="left", padx=10)
        
        self.c_gecmis.pack_forget()
        self.c2.pack_forget()
        self.c3.pack_forget()
        self.c4.pack_forget()

    def akraba_degisti(self):
        if self.v_akraba.get() == "Kendisi":
            enabled(self.e_mesafe, True)
        else:
            enabled(self.e_mesafe, False)
            self.v_mesafe.set("0")

    def personel_yukle(self):
        self.ptree.delete(*self.ptree.get_children())
        for p in self.db.personeller():
            self.ptree.insert("", "end", iid=str(p["id"]), values=(p["tc"], p["ad"], p["unvan"], p["derece"], p["kademe"]))

    def p_secildi(self, _e=None):
        s = self.ptree.selection()
        if not s: return
        pid = int(s[0])
        
        if self.kisi and self.kisi["id"] != pid:
            self.satirlar.clear()
            self.kayit_id = None
            
        self.kisi = next((p for p in self.db.personeller() if p["id"] == pid), None)
        if not self.kisi: return
        
        self.lbl_secili.configure(text=f"Seçilen Personel: {self.kisi['ad']} ({self.kisi['unvan']})", text_color=TEXT)
        
        self.v_nereden.set(self.app.kurum_tab.K["birim"].get())
        self.v_nereye.set("")
        self.v_ad.set(self.kisi["ad"])
        
        self.c_gecmis.pack_forget()
        self.c2.pack_forget()
        self.c3.pack_forget()
        self.c4.pack_forget()
        
        self.c_gecmis.pack(fill="x", pady=(0, 10))
        self.c2.pack(fill="x", pady=(10, 0)) 
        self.c3.pack(fill="x", pady=(10, 0))
        self.c4.pack(fill="x", pady=(10, 0))
        
        self.gecmis_yenile()
        self.tabloyu_yenile()
        self.formu_temizle()

    def gecmis_yenile(self):
        self.htree.delete(*self.htree.get_children())
        if not self.kisi: return
        for r in self.db.kayitlar(self.kisi["tc"]):
            try:
                d = json.loads(r["veri"])
                if d.get("tip") == "surekli":
                    oz = kayit_ozet(r)
                    self.htree.insert("", "end", iid=str(r["id"]), values=(
                        r["ref_no"], oz["islem"], tl(q(Decimal(str(r["genel"] or 0)))), "PDF" if r.get("durum") == "pdf" else "Taslak"
                    ))
            except Exception:
                pass

    def gecmis_yukle(self):
        s = self.htree.selection()
        if not s: return uyari(self, "Lütfen listeden bir kayıt seçin.")
        
        r = self.db.kayit_getir(int(s[0]))
        if not r: return
        
        try:
            d = json.loads(r["veri"])
            if d.get("tip") != "surekli": return
            
            self.kayit_id = r["id"]
            self.v_avans.set(d.get("avans", "Almadı"))
            self.v_es_durumu.set(d.get("es_durumu", False))
            self.v_cocuk_sahibi.set(d.get("cocuk_sahibi", "Kendisi"))
            
            atama_str = d.get("atama_tarihi")
            if atama_str:
                from datetime import datetime
                try:
                    self.d_atama.set(datetime.strptime(atama_str, "%d.%m.%Y").date())
                except:
                    pass
            
            self.satirlar = []
            for s_data in d.get("satirlar", []):
                self.satirlar.append({
                    "nereden": s_data["nereden"],
                    "nereye": s_data["nereye"],
                    "ad": s_data["ad"],
                    "akraba": s_data["akraba"],
                    "gun": int(s_data["gun"]),
                    "yevmiye": Decimal(s_data["yevmiye"]),
                    "tasit": s_data["tasit"],
                    "tasit_ucret": Decimal(s_data["tasit_ucret"]),
                    "mesafe": int(s_data["mesafe"])
                })
                
            self.tabloyu_yenile()
            self.formu_temizle()
            bilgi(self, f"{r['ref_no']} numaralı kayıt geri yüklendi.")
            
        except Exception as e:
            hata(self, f"Kayıt yüklenirken hata oluştu: {e}")

    def satir_secildi(self, _e=None):
        s = self.tree.selection()
        if not s: return
        idx = int(s[0])
        if idx >= len(self.satirlar): return
        
        r = self.satirlar[idx]
        self.v_nereden.set(r["nereden"])
        self.v_nereye.set(r["nereye"])
        self.v_ad.set(r["ad"])
        self.v_akraba.set(r["akraba"])
        self.v_gun.set(str(r["gun"]))
        self.v_tasit.set(r["tasit"])
        self.v_tasit_ucret.set(fmt(r["tasit_ucret"]))
        self.v_mesafe.set(str(r["mesafe"]))
        
        self.duzenlenen_index = idx
        
        self.btn_ekle.configure(text="Satırı Güncelle", fg_color=OK)
        self.btn_iptal.pack(side="left", padx=(5, 0))

    def formu_temizle(self):
        self.v_ad.set("")
        self.v_akraba.set("Kendisi")
        self.v_gun.set("1")
        self.v_tasit_ucret.set("0,00")
        self.v_mesafe.set("0")
        
        self.duzenlenen_index = None
        self.btn_ekle.configure(text="Satır Ekle", fg_color=ACC)
        self.btn_iptal.pack_forget()
        
        sel = self.tree.selection()
        if sel: self.tree.selection_remove(*sel)

    def satir_kaydet(self):
        if not self.kisi: return uyari(self, "Lütfen önce personel seçin.")
        try:
            nereden = self.v_nereden.get().strip()
            nereye = self.v_nereye.get().strip()
            ad = self.v_ad.get().strip()
            akraba = self.v_akraba.get()
            gun = int(self.v_gun.get())
            tasit = self.v_tasit.get()
            tasit_ucret = parse_money(self.v_tasit_ucret.get())
            mesafe = int(self.v_mesafe.get()) if akraba == "Kendisi" else 0
            
            if not nereden or not nereye or not ad: raise ValueError("Nereden, Nereye ve Ad Soyad zorunludur.")
            
            r_surekli = {
                "r8000": self.app.kurum_tab.R["r8000"].get(),
                "r6400": self.app.kurum_tab.R["r6400"].get(),
                "r3600": self.app.kurum_tab.R["r3600"].get(),
                "r1_4": self.app.kurum_tab.R["r1_4"].get(),
                "r5_15": self.app.kurum_tab.R["r5_15"].get()
            }
            yevmiye = surekli_gundelik_bul(self.kisi["ekg"], self.kisi["derece"], r_surekli)
            
            yeni_veri = {
                "nereden": nereden, "nereye": nereye, "ad": ad, "akraba": akraba,
                "gun": gun, "yevmiye": yevmiye, "tasit": tasit, 
                "tasit_ucret": tasit_ucret, "mesafe": mesafe
            }
            
            if self.duzenlenen_index is not None:
                self.satirlar[self.duzenlenen_index] = yeni_veri
            else:
                self.satirlar.append(yeni_veri)
                if akraba == "Kendisi":
                    self.v_akraba.set("Eşi")
            
            self.tabloyu_yenile()
            self.formu_temizle()
                
        except ValueError as e:
            uyari(self, str(e))

    def tabloyu_yenile(self):
        self.tree.delete(*self.tree.get_children())
        es_durumu = self.v_es_durumu.get()
        cocuk_sahibi = self.v_cocuk_sahibi.get()
        
        hs = surekli_hesapla(self.satirlar, es_durumu, cocuk_sahibi)
        
        for i, r in enumerate(hs["satirlar"]):
            self.tree.insert("", "end", iid=str(i), values=(
                r["nereden"], r["nereye"], r["ad"], r["akraba"], r["gun"],
                fmt(r["yevmiye"]), fmt(r["g_tutar"]), r["tasit"], fmt(r["tasit_ucret"]),
                fmt(r["sabit"]), fmt(r["degisken"]), fmt(r["toplam"])
            ))
            
        T = hs["tot"]
        self.lbl_genel.configure(text=f"GENEL TOPLAM: {tl(T['genel'])}")

    def satir_sil(self):
        s = self.tree.selection()
        if not s: return
        idx = int(s[0])
        del self.satirlar[idx]
        self.tabloyu_yenile()
        self.formu_temizle()

    def taslak_kaydet(self):
        if not self.satirlar: return uyari(self, "Kaydedilecek veri yok.")
        
        es_durumu = self.v_es_durumu.get()
        cocuk_sahibi = self.v_cocuk_sahibi.get()
        hs = surekli_hesapla(self.satirlar, es_durumu, cocuk_sahibi)
        
        ek = {
            "es_durumu": es_durumu,
            "cocuk_sahibi": cocuk_sahibi,
            "avans": self.v_avans.get().strip(),
            "atama_tarihi": dstr(self.d_atama.get() or date.today()),
            "bildirim_tarihi": dstr(date.today()),
            "tip": "surekli",
            "satirlar": []
        }
        
        for s in self.satirlar:
            ek["satirlar"].append({
                "nereden": s["nereden"], "nereye": s["nereye"], "ad": s["ad"], "akraba": s["akraba"],
                "gun": s["gun"], "yevmiye": str(s["yevmiye"]), "tasit": s["tasit"], 
                "tasit_ucret": str(s["tasit_ucret"]), "mesafe": s["mesafe"]
            })
            
        ref = f"{date.today().year}SRK{int(self.db.get('ref_sayac_surekli', '1')):04d}"
        veri_str = json.dumps(ek, ensure_ascii=False)
        
        if self.kayit_id:
            ref = self.db.kayit_getir(self.kayit_id)["ref_no"]
        
        self.kayit_id = self.db.kayit_kaydet(self.kayit_id, ref, self.kisi["tc"], hs["tot"]["genel"], veri_str, "taslak")
        if not self.kayit_id:
            self.db.set("ref_sayac_surekli", str(int(self.db.get("ref_sayac_surekli", "1")) + 1))
        
        self.gecmis_yenile()
        bilgi(self, f"Sürekli görev yolluğu taslağı arşive kaydedildi.\nReferans: {ref}")

    def raporla(self):
        if not self.satirlar: return uyari(self, "Lütfen en az bir satır ekleyin.")
        
        es_durumu = self.v_es_durumu.get()
        cocuk_sahibi = self.v_cocuk_sahibi.get()
        hs = surekli_hesapla(self.satirlar, es_durumu, cocuk_sahibi)
        
        yol = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
            initialfile=f"Surekli_Yolluk_{self.kisi['ad'].replace(' ', '_')}.pdf", title="Raporu Kaydet"
        )
        if not yol: return
        
        atama = self.d_atama.get() or date.today()
        avans = self.v_avans.get().strip()
        
        try:
            surekli_pdf_olustur(yol, self.app.kurum_tab.kurum(), self.kisi, atama, avans, hs, date.today(), es_durumu=es_durumu)
        except Exception as ex:
            return hata(self, str(ex), "PDF Hatası")
            
        ek = {
            "es_durumu": es_durumu, "cocuk_sahibi": cocuk_sahibi, "avans": avans,
            "atama_tarihi": dstr(atama), "bildirim_tarihi": dstr(date.today()), "tip": "surekli",
            "satirlar": [{"nereden": s["nereden"], "nereye": s["nereye"], "ad": s["ad"], "akraba": s["akraba"],
                          "gun": s["gun"], "yevmiye": str(s["yevmiye"]), "tasit": s["tasit"], 
                          "tasit_ucret": str(s["tasit_ucret"]), "mesafe": s["mesafe"]} for s in self.satirlar]
        }
        ref = f"{date.today().year}SRK{int(self.db.get('ref_sayac_surekli', '1')):04d}"
        if self.kayit_id:
            ref = self.db.kayit_getir(self.kayit_id)["ref_no"]
            
        self.kayit_id = self.db.kayit_kaydet(self.kayit_id, ref, self.kisi["tc"], hs["tot"]["genel"], json.dumps(ek, ensure_ascii=False), "pdf")
        if not self.kayit_id:
            self.db.set("ref_sayac_surekli", str(int(self.db.get("ref_sayac_surekli", "1")) + 1))
            
        self.gecmis_yenile()
        open_file(yol)
        bilgi(self, f"Rapor oluşturuldu ve arşive kaydedildi.\n{yol}")