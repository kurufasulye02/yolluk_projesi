# 📑 e-Yolluk Bildirim Sistemi (Yolluk Hazırlama)

6245 sayılı Harcırah Kanunu'na uygun olarak **Yurtiçi Geçici Görev Yolluğu** ve **Yurtiçi Sürekli Görev Yolluğu** hesaplamalarını yapabilen, hesaplanan tutarları resmi formata uygun şekilde PDF olarak raporlayan ve arşivleyen modern bir masaüstü uygulamasıdır.

## 🚀 Özellikler

* **Kurum ve Personel Yönetimi:** Kurum bilgileri, güncel H Cetveli gündelikleri ve okul/kurum personel listesinin yönetimi.
* **Yurtiçi Geçici Görev Yolluğu:** 
  * 5 aşamalı akıllı sihirbaz (Personel, Görev, Yolculuk, Konaklama, Rapor).
  * Günübirlik görevlerde 13:00 ve 19:00 yemek saati kuralına göre 1/3 ve 2/3 gündelik hesaplaması.
  * 24 saatten az süren görevlerin otomatik tespiti.
  * Aynı görev yerine yapılan görevlerde 90 ve 180 gün sınırı kontrolü.
  * Konaklamada gün sayısına göre kademeli tavan ücret uygulaması.
* **Yurtiçi Sürekli Görev Yolluğu:**
  * Aile fertleri (Eş, Çocuk) için yevmiye, taşıt ve sabit unsur hesaplamaları.
  * Değişken unsurda kanuni oran (%5 veya Eş Durumunda %2,5) ve mesafe (km) hesabı.
  * Çocuk yardımının hangi eş üzerinden alınacağını seçme imkanı.
  * Tabloda çift tıklayarak satır düzenleme ve güncelleme kolaylığı.
* **PDF Raporlama:** Resmi M.Y.H.B.Y. formatına uygun, çıktı alınmaya hazır PDF bildirimleri.
* **SQLite Veritabanı:** Tüm personel, ayarlar ve geçmiş yolluk kayıtlarının güvenli bir şekilde arşivlenmesi.
* **Otomatik Güncelleme Kontrolü:** Uygulama açılışında GitHub üzerinden yeni sürüm kontrolü.
* **Modern Arayüz:** CustomTkinter ile hazırlanmış Koyu/Açık tema destekli şık tasarım.

## 🛠️ Kurulum

Projeyi yerel bilgisayarınızda çalıştırmak için aşağıdaki adımları izleyin:

1. Bu depoyu bilgisayarınıza indirin veya klonlayın:
   ```bash
   git clone https://github.com/KULLANICI_ADIN/REPO_ADIN.git
   cd yolluk_projesi
2. Gerekli Python kütüphanelerini yükleyin:

pip install customtkinter reportlab

3. Uygulamayı başlatın:

python main.py


📂 Proje Yapısı
Proje, sürdürülebilirlik ve okunabilirlik açısından modüler bir mimariyle tasarlanmıştır:

text
yolluk_projesi/
│
├── main.py                  # Programı başlatan ana dosya
├── config.py                # Sabitler, varsayılan değerler ve versiyon bilgisi
├── utils.py                 # Yardımcı fonksiyonlar (para formatlama, tarih, TC kontrol vb.)
├── database.py              # SQLite veritabanı işlemleri
├── version.json             # GitHub otomatik güncelleme kontrol dosyası
│
├── core/                    # İş Mantığı (Logic) Katmanı
│   ├── hesaplama.py         # Yolluk hesaplama kuralları ve kanun maddeleri
│   └── pdf_rapor.py         # ReportLab ile PDF oluşturma
│
└── ui/                      # Arayüz (Görsel) Katmanı
    ├── tema.py              # Renkler, fontlar, buton/kutu fabrikaları
    ├── bilesenler.py        # Özel yapılar (DatePick, TimePick)
    ├── uygulama.py          # Ana Pencere ve Navigasyon
    └── sekmeler/            # Sekme Sayfaları
        ├── kurum_sekmesi.py 
        ├── gecici_sekme.py  
        └── surekli_sekme.py 
⚖️ Yasal Uyarı
Bu yazılım, 6245 sayılı Harcırah Kanunu ve ilgili tebliğler baz alınarak geliştirilmiştir. Hesaplamalar bilgilendirme amaçlıdır. Resmi işlemlerinizde kurumunuzun muhasebe biriminin onayını almanız gerekmektedir. Oluşabilecek maddi hatalardan geliştiriciler sorumlu tutulamaz.

🤝 Katkıda Bulunma
Her türlü öneri, hata bildirimi ve katkı için GitHub üzerinden Issue açabilir veya Pull Request gönderebilirsiniz.

📄 Lisans
Bu proje MIT Lisansı ile lisanslanmıştır. Detaylar için LICENSE dosyasına göz atabilirsiniz.