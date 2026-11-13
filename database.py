import sqlite3
import json
from datetime import datetime
from config import DB_PATH

class DB:
    def __init__(self, path=DB_PATH):
        self.c = sqlite3.connect(path)
        self.c.row_factory = sqlite3.Row
        self.c.executescript("""
        CREATE TABLE IF NOT EXISTS ayar (k TEXT PRIMARY KEY, v TEXT);
        CREATE TABLE IF NOT EXISTS personel (
            id INTEGER PRIMARY KEY AUTOINCREMENT, tc TEXT UNIQUE, ad TEXT, unvan TEXT,
            ekg TEXT, derece TEXT, kademe TEXT, iban TEXT);
        CREATE TABLE IF NOT EXISTS kayit (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ref_no TEXT, personel_tc TEXT,
            tarih TEXT, genel REAL, veri TEXT);
        """)
        for alter in ("ALTER TABLE personel ADD COLUMN ekg_no TEXT DEFAULT ''",
                      "ALTER TABLE kayit ADD COLUMN durum TEXT DEFAULT 'pdf'",
                      "ALTER TABLE kayit ADD COLUMN guncelleme TEXT"):
            try: self.c.execute(alter)
            except sqlite3.OperationalError: pass
        self.c.commit()

    def get(self, k, default=""):
        r = self.c.execute("SELECT v FROM ayar WHERE k=?", (k,)).fetchone()
        return r["v"] if r else default

    def set(self, k, v):
        self.c.execute("INSERT INTO ayar(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (k, v))
        self.c.commit()

    def personeller(self):
        return [dict(r) for r in self.c.execute("SELECT * FROM personel ORDER BY ad COLLATE NOCASE")]

    def personel_kaydet(self, p, pid=None):
        if pid:
            self.c.execute("UPDATE personel SET tc=?,ad=?,unvan=?,ekg=?,derece=?,kademe=?,iban=?,ekg_no=? WHERE id=?",
                           (p["tc"], p["ad"], p["unvan"], p["ekg"], p["derece"], p["kademe"], p["iban"], p.get("ekg_no", ""), pid))
        else:
            self.c.execute("INSERT INTO personel(tc,ad,unvan,ekg,derece,kademe,iban,ekg_no) VALUES(?,?,?,?,?,?,?,?)",
                           (p["tc"], p["ad"], p["unvan"], p["ekg"], p["derece"], p["kademe"], p["iban"], p.get("ekg_no", "")))
        self.c.commit()

    def personel_sil(self, pid):
        self.c.execute("DELETE FROM personel WHERE id=?", (pid,))
        self.c.commit()

    def kayitlar(self, tc):
        return [dict(r) for r in self.c.execute(
            "SELECT * FROM kayit WHERE personel_tc=? ORDER BY COALESCE(guncelleme,tarih) DESC, id DESC", (tc,))]

    def kayit_getir(self, kid):
        r = self.c.execute("SELECT * FROM kayit WHERE id=?", (kid,)).fetchone()
        return dict(r) if r else None

    def kayit_kaydet(self, kid, ref_no, tc, genel, veri, durum):
        now = datetime.now().isoformat(timespec="seconds")
        if kid:
            self.c.execute("UPDATE kayit SET ref_no=?,personel_tc=?,genel=?,veri=?,durum=?,guncelleme=? WHERE id=?",
                           (ref_no, tc, float(genel), veri, durum, now, kid))
        else:
            cur = self.c.execute(
                "INSERT INTO kayit(ref_no,personel_tc,tarih,genel,veri,durum,guncelleme) VALUES(?,?,?,?,?,?,?)",
                (ref_no, tc, now, float(genel), veri, durum, now))
            kid = cur.lastrowid
        self.c.commit()
        return kid

    def kayit_sil(self, kid):
        self.c.execute("DELETE FROM kayit WHERE id=?", (kid,))
        self.c.commit()

    def ref_var_mi(self, ref, haric=None):
        r = self.c.execute("SELECT id FROM kayit WHERE ref_no=? AND id IS NOT ?", (ref, haric)).fetchone()
        return r is not None

    def gecici_gecmis_gun(self, tc, nereye):
        """Son 1 yıl içinde aynı yere yapılan geçici görevlerin toplam gün sayısını döndürür."""
        kayitlar = self.kayitlar(tc)
        toplam = 0
        simdi = datetime.now()
        bir_yil_once = simdi.replace(year=simdi.year - 1)
        
        for k in kayitlar:
            try:
                d = json.loads(k["veri"])
                tip = d.get("_ekstra", {}).get("tip")
                if tip == "gecici" or k["ref_no"].startswith(str(simdi.year)):
                    if d.get("nereye") == nereye:
                        bas = datetime.strptime(d["bas"], "%d.%m.%Y")
                        bit = datetime.strptime(d["bit"], "%d.%m.%Y")
                        if bas >= bir_yil_once:
                            toplam += (bit - bas).days + 1
            except Exception:
                pass
        return toplam