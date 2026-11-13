import customtkinter as ctk
from ui.tema import FN, TEXT, MUTED, ACC, CARD, LINE, INPUT, sayfa_baslik, card

class YardimTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        
        sayfa_baslik(self, "Yardım ve Bilgilendirme", "Uygulama kullanımı, hesaplama kuralları ve sıkça sorulan sorular.")
        
        # Kaydırılabilir gövde
        body = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        body.pack(fill="both", expand=True)

        # 1. GENEL BİLGİ
        c1 = card(body, "📌 Genel Bilgiler")
        c1.pack(fill="x", pady=(0, 10))
        t1 = """
        Bu yazılım, 6245 sayılı Harcırah Kanunu'na uygun olarak Yurtiçi Geçici ve Sürekli Görev Yolluklarını hesaplamak, arşivlemek ve resmi PDF bildirimlerini oluşturmak için tasarlanmıştır.
        
        • Sol menüden ilgili sekmelere geçiş yapabilirsiniz.
        • Sol alttaki TEMA düğmesi ile Koyu ve Açık tema arasında geçiş yapabilirsiniz.
        • Verileriniz bilgisayarınızdaki yerel bir veritabanında (SQLite) güvenle saklanır.
        • PDF raporlarında görünen logoyu değiştirmek için programın kurulu olduğu klasördeki 'logo.png' dosyasını kendi kurum logonuzla değiştirebilirsiniz.
        """
        ctk.CTkLabel(c1.body, text=t1, font=FN["body"], text_color=TEXT, justify="left", anchor="w").pack(fill="x", padx=10)

        # 2. ADIM ADIM KULLANIM
        c2 = card(body, "🛠️ Adım Adım Kullanım")
        c2.pack(fill="x", pady=(0, 10))
        
        t2 = """
        1. KURUM & PERSONEL: Öncelikle güncel H Cetveli gündeliklerini ve kurum bilgilerinizi girip kaydedin. Ardından personellerinizi (TC, unvan, derece vb.) ekleyin.
        
        2. GEÇİCİ GÖREV: 'Geçici Görev Yolluğu' sekmesinden personel seçip süreci başlatın.
           • Görev, yolculuk ve konaklama bilgilerini adım adım doldurun.
           • Sistem, günübirlik görevlerde 13:00 ve 19:00 yemek saatlerini otomatik kontrol eder (1/3 veya 2/3 gündelik).
           • Son aşamada önizlemeyi görüp PDF oluşturabilir veya taslak kaydedebilirsiniz.
        
        3. SÜREKLİ GÖREV: 'Sürekli Görev Yolluğu' sekmesinden personel seçin.
           • Aile fertlerini (Kendisi, Eşi, Çocukları) tek tek ekleyin.
           • Tabloda bir hata yaparsanız, o satıra ÇİFT TIKLAYARAK düzenleyebilirsiniz.
           • Eş durumu veya çocuk yardımı seçeneklerini işaretleyip raporu oluşturabilirsiniz.
        """
        ctk.CTkLabel(c2.body, text=t2, font=FN["body"], text_color=TEXT, justify="left", anchor="w", wraplength=900).pack(fill="x", padx=10)

        # 3. SIKÇA SORULAN SORUNLAR (SSS)
        c3 = card(body, "❓ Sıkça Sorulan Sorular ve Sorun Giderme")
        c3.pack(fill="x", pady=(0, 10))
        
        sss = [
            ("PDF oluşturamıyorum, hata veriyor.", "Sisteminizde 'reportlab' kütüphanesi kurulu olmayabilir. Terminale 'pip install reportlab' yazarak kurulum yapın."),
            ("Gündelikler yanlış hesaplanıyor.", "Personelin Ek Göstergesi veya Kadro Derecesi yanlış girilmiş olabilir. 'Kurum & Personel' sekmesinden personelin bilgilerini kontrol edin ve güncelleyin."),
            ("Sürekli görevde değişken unsur neden 0 çıkıyor?", "Değişken unsur (yol gideri) sadece personelin 'Kendisi' için ödenir. Eş veya çocuklar için mesafe girseniz dahi hesaplanmaz (Kanun gereği)."),
            ("Neden 4'ten fazla çocuğa sabit unsur ödenmiyor?", "6245 sayılı kanuna göre sabit unsur (gündelik * 10) en fazla 4 aile ferdine ödenir. 5. ve sonraki fertler için sadece yevmiye ve taşıt ücreti ödenir."),
            ("Sürekli görevdeki geçmiş kayıtlarımı bulamıyorum.", "Geçmiş kayıtlar sadece ilgili personel seçildiğinde listelenir. Önce '1. Personel Seçimi' bölümünden kişiyi seçin."),
            ("Yanlış kaydettim, nasıl silerim?", "Geçmiş Kayıtlar tablosundan ilgili kaydı seçip 'Sil' butonuna basabilirsiniz. Eğer form üzerindeyseniz, satırı seçip 'Seçili Satırı Sil' butonunu kullanın."),
            ("Program güncellenmiyor.", "İnternet bağlantınızı kontrol edin. GitHub üzerinden güncelleme sunucusuna erişilemiyor olabilir.")
        ]
        
        for soru, cevap in sss:
            f = ctk.CTkFrame(c3.body, fg_color="transparent")
            f.pack(fill="x", pady=5, padx=10)
            ctk.CTkLabel(f, text=f"🔹 {soru}", font=FN["btn"], text_color=ACC, anchor="w").pack(fill="x")
            ctk.CTkLabel(f, text=cevap, font=FN["body"], text_color=MUTED, justify="left", anchor="w", wraplength=850).pack(fill="x", padx=15, pady=(2, 0))

        # 4. YASAL UYARI
        c4 = card(body, "⚖️ Yasal Uyarı")
        c4.pack(fill="x", pady=(0, 10))
        t4 = "Bu yazılım bilgilendirme amaçlı geliştirilmiştir. Hesaplamalar 6245 sayılı kanun ve H Cetveli baz alınarak yapılmakla birlikte, nihai resmi işlemler için kurumunuzun muhasebe/mali işler biriminin onayı esastır. Oluşabilecek maddi hatalardan geliştiriciler sorumlu tutulamaz."
        ctk.CTkLabel(c4.body, text=t4, font=FN["small"], text_color=MUTED, justify="left", anchor="w", wraplength=900).pack(fill="x", padx=10)