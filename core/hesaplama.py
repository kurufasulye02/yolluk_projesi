from datetime import timedelta, datetime
from decimal import Decimal
from utils import q, dstr, tstr, tl, kisa_yer, tr_lower, yemek_sayisi, D0

def hesapla(g, gecmis_gun=0):
    gun = g["gundelik"]
    bas, bit = g["bas"], g["bit"]
    
    # 24 Saat Kuralı: Takvim günü farklı olsa bile 24 saatten az süren görevler günübirliktir.
    dt_bas = datetime.combine(bas, g["cikis"])
    dt_bit = datetime.combine(bit, g["donus"])
    sure_saat = (dt_bit - dt_bas).total_seconds() / 3600
    gunubirlik = (bas == bit) or (sure_saat < 24)
    
    once = g["ekgun"] in ("once", "ikisi")
    sonra = g["ekgun"] in ("sonra", "ikisi")
    d1 = timedelta(days=1)
    hs = {"gundelik": [], "yol": [], "konak": [], "diger": [], "uyari": [],
          "gunubirlik": gunubirlik, "yemek_notu": ""}

    if once and not g.get("gunluk_gidis", False):
        hs["gundelik"].append(("Gidiş Yol Gündeliği", bas - d1, bas - d1, 1, gun, q(gun)))
    
    if g.get("gunluk_gidis", False):
        delta = bit - bas
        for i in range(delta.days + 1):
            o_gun = bas + timedelta(days=i)
            k = yemek_sayisi(g["cikis"], g["donus"])
            tutar = q(gun * k / 3)
            txt = {0: "13:00 ve 19:00 yemek saatlerini kapsamıyor -> görev gündeliği ödenmez",
                   1: "Bir yemek saatini kapsıyor -> gündeliğin 1/3'ü",
                   2: "13:00 ve 19:00'u kapsıyor -> gündeliğin 2/3'ü"}[k]
            hs["yemek_notu"] = txt
            if tutar > 0:
                hs["gundelik"].append(("Görev Gündeliği", o_gun, o_gun, 1, gun, tutar))
            
            a, b = kisa_yer(g["nereden"]), kisa_yer(g["nereye"])
            if "kurum" not in tr_lower(g["vasita"]):
                if g["gidis_bilet"] > 0:
                    hs["yol"].append((o_gun, f"{a} {b}", g["cikis"], None, g["vasita"], g["gidis_bilet"]))
                if g["donus_bilet"] > 0:
                    hs["yol"].append((o_gun, f"{b} {a}", None, g["donus"], g["vasita"], g["donus_bilet"]))
                    
    elif gunubirlik:
        k = yemek_sayisi(g["cikis"], g["donus"])
        tutar = q(gun * k / 3)
        txt = {0: "13:00 ve 19:00 yemek saatlerini kapsamıyor -> görev gündeliği ödenmez",
               1: "Bir yemek saatini kapsıyor -> gündeliğin 1/3'ü",
               2: "13:00 ve 19:00'u kapsıyor -> gündeliğin 2/3'ü"}[k]
        hs["yemek_notu"] = txt
        if tutar > 0:
            hs["gundelik"].append(("Görev Gündeliği", bas, bit, 1, gun, tutar))
            
        a, b = kisa_yer(g["nereden"]), kisa_yer(g["nereye"])
        if "kurum" not in tr_lower(g["vasita"]):
            if g["gidis_bilet"] > 0:
                hs["yol"].append((bas, f"{a} {b}", g["cikis"], None, g["vasita"], g["gidis_bilet"]))
            if g["donus_bilet"] > 0:
                hs["yol"].append((bit, f"{b} {a}", None, g["donus"], g["vasita"], g["donus_bilet"]))
    else:
        # Çok günlü konaklamalı görev (90/180 Gün Kuralı)
        n = (bit - bas).days + 1
        toplam_gun = gecmis_gun + n
        
        normal_gun = 0
        kismi_gun = 0
        
        if toplam_gun <= 90:
            normal_gun = n
        elif toplam_gun <= 180:
            kalan_90 = max(0, 90 - gecmis_gun)
            normal_gun = min(n, kalan_90)
            kismi_gun = n - normal_gun
        else:
            kalan_180 = max(0, 180 - gecmis_gun)
            kismi_gun = min(n, kalan_180)
            # 180'i aşan kısım 0 (hesaplanmaz)
            
        if normal_gun > 0:
            hs["gundelik"].append(("Görev Gündeliği (Tam)", bas, bit, normal_gun, gun, q(gun * normal_gun)))
        if kismi_gun > 0:
            hs["gundelik"].append(("Görev Gündeliği (2/3)", bas, bit, kismi_gun, gun, q(gun * kismi_gun * Decimal("2") / Decimal("3"))))
            if gecmis_gun > 90:
                hs["uyari"].append(f"Aynı yere yapılan görevlerde 90 gün dolduğu için kalan {kismi_gun} gün 2/3 oranında hesaplandı.")
            if toplam_gun > 180:
                hs["uyari"].append("Aynı yere yapılan görevlerde 180 gün sınırı aşıldığı için 180 günü aşan kısma gündelik ödenmedi.")
        
        a, b = kisa_yer(g["nereden"]), kisa_yer(g["nereye"])
        if "kurum" not in tr_lower(g["vasita"]):
            t_gidis = bas - d1 if once else bas
            t_donus = bit + d1 if sonra else bit
            if g["gidis_bilet"] > 0:
                hs["yol"].append((t_gidis, f"{a} {b}", g["cikis"], None, g["vasita"], g["gidis_bilet"]))
            if g["donus_bilet"] > 0:
                hs["yol"].append((t_donus, f"{b} {a}", None, g["donus"], g["vasita"], g["donus_bilet"]))

    if sonra and not g.get("gunluk_gidis", False):
        hs["gundelik"].append(("Dönüş Yol Gündeliği", bit + d1, bit + d1, 1, gun, q(gun)))

    # Diğer masraflar
    t_gidis = bas - d1 if once and not g.get("gunluk_gidis", False) else bas
    t_donus = bit + d1 if sonra and not g.get("gunluk_gidis", False) else bit
    if g["sehir_gidis"] > 0:
        hs["diger"].append(("Şehir içi ulaşım (gidiş)", t_gidis, 1, g["sehir_gidis"]))
    if g["sehir_donus"] > 0:
        hs["diger"].append(("Şehir içi ulaşım (dönüş)", t_donus, 1, g["sehir_donus"]))
    if g["zorunlu"] > 0:
        hs["diger"].append((g["zorunlu_tur"] or "Zorunlu masraf", bas, 1, g["zorunlu"]))

    # Konaklama (Kademeli Oranlar)
    if not gunubirlik and not g.get("gunluk_gidis", False) and g["gece"] and g["konak_tur"] != "ucretsiz" and g["gece_sayisi"] > 0:
        if g["konak_tur"] == "fatura":
            toplam_konak = D0
            for i in range(1, g["gece_sayisi"] + 1):
                if i <= 10: tavan = q(gun * Decimal("1.5"))
                elif i <= 90: tavan = q(gun * Decimal("1.0"))
                else: tavan = q(gun * Decimal("0.8"))
                
                gece = g["gece_ucret"]
                if gece > tavan and not g["rayic"]:
                    gece = tavan
                toplam_konak += gece
                
            ort_gece = q(toplam_konak / g["gece_sayisi"]) if g["gece_sayisi"] > 0 else D0
            hs["konak"].append((g["konak_yer"] or "-", bas, bit, g["gece_sayisi"], ort_gece, toplam_konak))
        else:
            gece = q(gun / 2)
            hs["konak"].append((g["konak_yer"] or "-", bas, bit, g["gece_sayisi"], gece, q(gece * g["gece_sayisi"])))
            
        if g["gece_sayisi"] > (bit - bas).days:
            hs["uyari"].append("Gece sayısı görev gün sayısından fazla görünüyor, kontrol edin.")

    gt = sum((r[5] for r in hs["gundelik"]), D0)
    yt = sum((r[5] for r in hs["yol"]), D0)
    kt = sum((r[5] for r in hs["konak"]), D0)
    dt = sum((r[3] for r in hs["diger"]), D0)
    hs["tot"] = {"gundelik": q(gt), "yol": q(yt), "konak": q(kt), "diger": q(dt), "genel": q(gt + yt + kt + dt)}
    return hs

def surekli_hesapla(satirlar, es_durumu=False, cocuk_sahibi="Kendisi"):
    # Öncelik Sıralaması: Kendisi -> Eşi -> Çocuğu
    def sort_key(s):
        ak = s.get("akraba", "")
        if ak == "Kendisi": return 0
        if ak == "Eşi": return 1
        return 2
        
    sorted_satirlar = sorted(satirlar, key=sort_key)
    hs = {"satirlar": [], "tot": {"yevmiye": D0, "tasit": D0, "sabit": D0, "degisken": D0, "genel": D0}}
    sabit_unsur_alan_aile_sayisi = 0
    
    for s in sorted_satirlar:
        gun = s["gun"]
        yevmiye = s["yevmiye"]
        tasit_ucret = s["tasit_ucret"]
        mesafe = s["mesafe"]
        akraba = s["akraba"]
        
        if akraba == "Çocuğu" and cocuk_sahibi == "Eşi":
            g_tutar = D0
            sabit = D0
            degisken = D0
            toplam = D0
        else:
            g_tutar = q(gun * yevmiye)
            
            if akraba == "Kendisi":
                sabit = q(yevmiye * 20)
            else:
                if sabit_unsur_alan_aile_sayisi < 4:
                    sabit = q(yevmiye * 10)
                    sabit_unsur_alan_aile_sayisi += 1
                else:
                    sabit = D0
            
            # DEĞİŞKEN UNSUR (Senin Excel formülüne göre: %5 normal, %2.5 eş durumu)
            if akraba == "Kendisi":
                oran = Decimal("0.025") if es_durumu else Decimal("0.05")
                degisken = q(yevmiye * oran * mesafe)
            else:
                degisken = D0
                
            toplam = g_tutar + tasit_ucret + sabit + degisken
        
        hs["satirlar"].append({
            **s, "g_tutar": g_tutar, "sabit": sabit, "degisken": degisken, "toplam": toplam
        })
        hs["tot"]["yevmiye"] += g_tutar
        hs["tot"]["tasit"] += tasit_ucret
        hs["tot"]["sabit"] += sabit
        hs["tot"]["degisken"] += degisken
        hs["tot"]["genel"] += toplam
        
    return hs

def ozet_metin(kisi, g, hs):
    L = []
    L.append(f"PERSONEL : {kisi['ad']}   (TC: {kisi['tc']})")
    L.append(f"GÜZERGAH : {g['nereden']}  ->  {g['nereye']}   [{g['konu']}]")
    L.append(f"TARİH    : {dstr(g['bas'])} - {dstr(g['bit'])}   Çıkış {tstr(g['cikis'])} / Dönüş {tstr(g['donus'])}")
    L.append(f"GÜNDELİK : {tl(g['gundelik'])}")
    if hs["gunubirlik"] or g.get("gunluk_gidis"): 
        L.append(f"           ({hs['yemek_notu']})")
    L.append("\n-- GÜNDELİK --")
    for tur, b, e, n, birim, t in hs["gundelik"]:
        L.append(f"  {tur:<22} {dstr(b)}-{dstr(e)}  {n} gün  {tl(t):>16}")
    L.append("-- YOL MASRAFI --")
    for tar, yer, gs, ds, vas, t in hs["yol"]:
        L.append(f"  {dstr(tar)}  {yer:<22} {vas:<10} {tl(t):>16}")
    L.append("-- KONAKLAMA --")
    for yer, b, e, n, gece, t in hs["konak"]:
        L.append(f"  {yer:<22} {n} gece x {tl(gece)} = {tl(t):>16}")
    L.append("-- DİĞER MASRAF --")
    for tur, tar, adet, t in hs["diger"]:
        L.append(f"  {tur:<30} {tl(t):>16}")
    T = hs["tot"]
    L.append("")
    L.append(f"Gündelik Toplamı     : {tl(T['gundelik']):>16}")
    L.append(f"Yol Masrafı Toplamı  : {tl(T['yol']):>16}")
    L.append(f"Konaklama Toplamı    : {tl(T['konak']):>16}")
    L.append(f"Diğer Masraf Toplamı : {tl(T['diger']):>16}")
    L.append(f"GENEL BİLDİRİM TUTARI: {tl(T['genel']):>16}")
    for u in hs["uyari"]:
        L.append(f"\n! {u}")
    return "\n".join(L)