import sys
import os
from datetime import date

# --- EXE UYUMLU DİZİN BULMA ---
if getattr(sys, 'frozen', False):
    # PyInstaller ile .exe yapıldıysa, .exe'nin bulunduğu dizini kullan
    APP_DIR = os.path.dirname(sys.executable)
else:
    # Normal python betiği olarak çalışıyorsa
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(APP_DIR, "yolluk.db")

# --- VERSİYON KONTROLÜ AYARLARI ---
APP_VERSION = "1.0.0"
UPDATE_URL = "https://raw.githubusercontent.com/KULLANICI_ADIN/REPO_ADIN/main/version.json"

EK_GOSTERGE = ["3600'den Az", "3600 - 6399 Arası", "6400 - 7999 Arası", "8000 ve Üzeri"]
DERECELER = [f"{i}. Derece" for i in range(1, 16)]
KADEMELER = [""] + [f"{i}. Kademe" for i in range(1, 10)]
VASITALAR = ["Otobüs", "Minibüs", "Dolmuş", "Taksi", "Uçak", "Vapur", "Tren", "Kurum Aracı"]

VARSAYILAN_GUNDELIK = {"r8000": "890,00", "r6400": "880,00", "r3600": "870,00", "r1_4": "860,00", "r5_15": "850,00"}
VARSAYILAN_KURUM = {
    "kamu": "MİLLİ EĞİTİM BAKANLIĞI",
    "birim": "BARTIN ULUS İLÇE MİLLİ EĞİTİM MÜDÜRLÜĞÜ",
    "vkn": "8890288324",
    "kurumsal_kod": "13.68",
    "butce_yili": str(date.today().year),
    "onay_ad": "",
    "onay_unvan": "Okul Müdürü",
}