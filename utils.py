import json
import os
import subprocess
import sys
from datetime import date, time as dtime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

D0 = Decimal("0.00")

def q(x):
    return Decimal(x).quantize(Decimal("0.01"), ROUND_HALF_UP)

def parse_money(s):
    s = str(s).upper().replace("TL", "").replace("₺", "").replace(" ", "").strip()
    if not s:
        return D0
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif s.count(".") > 1 or (s.count(".") == 1 and len(s.split(".")[1]) == 3):
        s = s.replace(".", "")
    try:
        v = q(Decimal(s))
    except InvalidOperation:
        raise ValueError(f"Geçersiz tutar: {s}")
    if v < 0:
        raise ValueError("Tutar negatif olamaz")
    return v

def fmt(x):
    s = f"{q(x):,.2f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")

def tl(x):
    return fmt(x) + " TL"

def dstr(d):
    return d.strftime("%d.%m.%Y") if d else ""

def tstr(t):
    return t.strftime("%H:%M") if t else ""

def tr_lower(s):
    return s.replace("İ", "i").replace("I", "ı").lower()

def kisa_yer(s):
    s = (s or "").strip()
    return s.split("/")[-1].strip() if "/" in s else s

def tc_gecerli(tc):
    if not (tc.isdigit() and len(tc) == 11 and tc[0] != "0"):
        return False
    d = [int(c) for c in tc]
    if (sum(d[0:9:2]) * 7 - sum(d[1:8:2])) % 10 != d[9]:
        return False
    return sum(d[:10]) % 10 == d[10]

def gundelik_bul(ek_gosterge, derece, r):
    if ek_gosterge == "8000 ve Üzeri": return r["r8000"]
    if ek_gosterge == "6400 - 7999 Arası": return r["r6400"]
    if ek_gosterge == "3600 - 6399 Arası": return r["r3600"]
    n = int(str(derece).split(".")[0])
    return r["r1_4"] if n <= 4 else r["r5_15"]

def yemek_sayisi(cikis, donus):
    k = 0
    if cikis <= dtime(13, 0) <= donus: k += 1
    if cikis <= dtime(19, 0) <= donus: k += 1
    return k

def veri_serilestir(g, ekstra):
    d = {}
    for k, x in g.items():
        if isinstance(x, date): d[k] = dstr(x)
        elif isinstance(x, dtime): d[k] = tstr(x)
        elif isinstance(x, Decimal): d[k] = str(x)
        else: d[k] = x
    d["_ekstra"] = ekstra
    return json.dumps(d, ensure_ascii=False)

def veri_coz(s):
    d = json.loads(s)
    ek = d.pop("_ekstra", {}) or {}
    return d, ek

def kayit_ozet(r):
    from datetime import datetime
    try: d = json.loads(r["veri"])
    except Exception: d = {}
    a, b = d.get("nereden", ""), d.get("nereye", "")
    guzergah = f"{kisa_yer(a)} → {kisa_yer(b)}" if (a or b) else "-"
    bas, bit = d.get("bas", ""), d.get("bit", "")
    tarih = "-" if not bas else (bas if bas == bit else f"{bas} – {bit}")
    t = r.get("guncelleme") or r.get("tarih") or ""
    try: islem = datetime.fromisoformat(t).strftime("%d.%m.%Y %H:%M")
    except ValueError: islem = t
    return {"guzergah": guzergah, "tarih": tarih, "islem": islem}

def open_file(p):
    try:
        if sys.platform.startswith("win"): os.startfile(p)
        elif sys.platform == "darwin": subprocess.Popen(["open", p])
        else: subprocess.Popen(["xdg-open", p])
    except Exception: pass

# utils.py içine ekleyin

def surekli_gundelik_bul(ek_gosterge, derece, r_surekli):
    """Sürekli görev yevmiyesini Ek Gösterge (öncelikli) ve Dereceye göre hesaplar."""
    try:
        d = int(str(derece).split(".")[0])
    except:
        d = 15
        
    # 1. Öncelik: Ek Gösterge
    if ek_gosterge == "8000 ve Üzeri":
        return parse_money(r_surekli.get("r8000", "890,00"))
    elif ek_gosterge == "6400 - 7999 Arası":
        return parse_money(r_surekli.get("r6400", "880,00"))
    elif ek_gosterge == "3600 - 6399 Arası":
        return parse_money(r_surekli.get("r3600", "870,00"))
    
    # 2. Öncelik: Ek Gösterge "3600'den Az" ise (veya boşsa) Dereceye Bak
    else:
        if d <= 4:
            return parse_money(r_surekli.get("r1_4", "860,00"))
        else:
            return parse_money(r_surekli.get("r5_15", "850,00"))    