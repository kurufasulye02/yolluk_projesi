import customtkinter as ctk
import threading
import urllib.request
import json
import webbrowser
from database import DB
from config import APP_VERSION, UPDATE_URL
from ui.tema import init_fonts, restyle, BG, SIDE, TEXT, MUTED, INPUT, ACC, ACC_H, FN, btn, _grab
from ui.sekmeler.kurum_sekmesi import KurumTab
from ui.sekmeler.gecici_sekme import GeciciTab
from ui.sekmeler.surekli_sekme import SurekliTab
from ui.sekmeler.yardim_sekme import YardimTab # <-- YENİ EKLENDİ

class UpdateDialog(ctk.CTkToplevel):
    def __init__(self, parent, yeni_versiyon, indirme_linki, aciklama):
        super().__init__(parent)
        self.title("Güncelleme Mevcut")
        self.geometry("450x260")
        self.resizable(False, False)
        self.configure(fg_color=("#F2F4FA", "#0B0E14"))
        self.transient(parent)
        
        x = parent.winfo_rootx() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 260) // 2
        self.geometry(f"+{x}+{y}")

        ctk.CTkLabel(self, text="🚀 Yeni Sürüm Yayınlandı!", font=FN["h1"], text_color=TEXT).pack(pady=(20, 5))
        ctk.CTkLabel(self, text=f"Mevcut Sürüm: v{APP_VERSION}  ➔  Yeni Sürüm: v{yeni_versiyon}", font=FN["btn"], text_color=ACC).pack(pady=5)
        
        txt = ctk.CTkTextbox(self, height=80, font=FN["body"], fg_color=INPUT, text_color=TEXT)
        txt.pack(fill="x", padx=20, pady=10)
        txt.insert("1.0", aciklama)
        txt.configure(state="disabled")

        def git():
            webbrowser.open(indirme_linki)
            self.destroy()

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        btn(btn_frame, "İndirme Sayfasına Git", git, width=180).pack(side="left")
        btn(btn_frame, "Daha Sonra", self.destroy, kind="ghost", width=100).pack(side="right")
        
        self.after(150, lambda: _grab(self))

class App(ctk.CTk):
    def __init__(self):
        self.db = DB()
        self.tema_adi = self.db.get("tema", "Koyu")
        ctk.set_appearance_mode("dark" if self.tema_adi == "Koyu" else "light")
        ctk.set_default_color_theme("blue")
        super().__init__(fg_color=BG)
        init_fonts()
        restyle()
        
        try:
            # Projenin ana dizinindeki logo.ico dosyasını arar
            self.iconbitmap("logo.ico")
        except Exception:
            pass        
        
        self.title(f"Yolluk Programı - v{APP_VERSION}")
        self.geometry("1320x820")
        self.minsize(1120, 700)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        yan = ctk.CTkFrame(self, fg_color=SIDE, corner_radius=0, width=250)
        yan.grid(row=0, column=0, sticky="nsw"); yan.grid_propagate(False)
        ctk.CTkLabel(yan, text="◈ Yolluk", font=FN["h0"], text_color=TEXT).pack(anchor="w", padx=24, pady=(28, 0))
        ctk.CTkLabel(yan, text="Harcırah bildirim sistemi", font=FN["small"], text_color=MUTED).pack(anchor="w", padx=26, pady=(0, 26))
        
        self.nav = {}
        # YENİ MENÜ ELEMANI EKLENDİ
        for key, text in (("kurum", "Kurum & Personel"), ("gecici", "Geçici Görev Yolluğu"), ("surekli", "Sürekli Görev Yolluğu"), ("yardim", "❓ Yardım & Bilgi")):
            b = ctk.CTkButton(yan, text=text, anchor="w", height=42, corner_radius=12, font=FN["body"], fg_color="transparent", hover_color=INPUT, text_color=TEXT, command=lambda k=key: self.show(k))
            b.pack(fill="x", padx=14, pady=3)
            self.nav[key] = b
            
        ctk.CTkLabel(yan, text="TEMA", font=FN["small"], text_color=MUTED).pack(side="bottom", anchor="w", padx=26, pady=(0, 18))
        sg = ctk.CTkSegmentedButton(yan, values=["Koyu", "Açık"], command=self.tema, font=FN["label"], selected_color=ACC, selected_hover_color=ACC_H, unselected_color=INPUT, unselected_hover_color=INPUT, text_color=TEXT)
        sg.set(self.tema_adi); sg.pack(side="bottom", fill="x", padx=20, pady=(0, 6))
        
        ctk.CTkLabel(yan, text=f"v{APP_VERSION}", font=FN["small"], text_color=MUTED).pack(side="bottom", anchor="w", padx=26, pady=(10, 0))

        icerik = ctk.CTkFrame(self, fg_color="transparent")
        icerik.grid(row=0, column=1, sticky="nsew", padx=26, pady=22)
        
        self.kurum_tab = KurumTab(icerik, self)
        self.gecici = GeciciTab(icerik, self)
        self.surekli_tab = SurekliTab(icerik, self)
        self.yardim_tab = YardimTab(icerik, self) # YENİ SEKME EKLENDİ
        
        self.pages = {"kurum": self.kurum_tab, "gecici": self.gecici, "surekli": self.surekli_tab, "yardim": self.yardim_tab}
        self.show("kurum")

        self.after(2000, self.check_for_updates)

    def show(self, key):
        for k, p in self.pages.items():
            p.pack_forget()
            self.nav[k].configure(fg_color=ACC if k == key else "transparent", text_color="#FFFFFF" if k == key else TEXT, hover_color=ACC_H if k == key else INPUT)
        
        self.pages[key].pack(fill="both", expand=True)
        
        if key == "surekli":
            self.surekli_tab.personel_yukle()

    def tema(self, v):
        self.db.set("tema", v)
        ctk.set_appearance_mode("dark" if v == "Koyu" else "light")
        restyle()

    def check_for_updates(self):
        threading.Thread(target=self._fetch_update_info, daemon=True).start()

    def _fetch_update_info(self):
        try:
            req = urllib.request.Request(UPDATE_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            yeni_versiyon = data.get("version", "1.0.0")
            indirme_linki = data.get("url", "https://github.com")
            aciklama = data.get("aciklama", "Yeni özellikler ve hata düzeltmeleri.")
            
            def parse_ver(v):
                return tuple(map(int, str(v).split('.')))
            
            if parse_ver(yeni_versiyon) > parse_ver(APP_VERSION):
                self.after(0, lambda: UpdateDialog(self, yeni_versiyon, indirme_linki, aciklama))
                
        except Exception as e:
            print(f"Güncelleme kontrolü başarısız: {e}")