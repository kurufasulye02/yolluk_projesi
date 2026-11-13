import os
from datetime import date, timedelta
from decimal import Decimal
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from config import APP_DIR
from utils import dstr, fmt, tl, kisa_yer, tstr, D0

FONT, FONTB = "Helvetica", "Helvetica-Bold"

def _fontlari_yukle():
    global FONT, FONTB
    adaylar = [
        ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
        ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        (os.path.join(APP_DIR, "DejaVuSans.ttf"), os.path.join(APP_DIR, "DejaVuSans-Bold.ttf")),
    ]
    for r, b in adaylar:
        if os.path.exists(r) and os.path.exists(b):
            pdfmetrics.registerFont(TTFont("YF", r))
            pdfmetrics.registerFont(TTFont("YFB", b))
            FONT, FONTB = "YF", "YFB"
            return True
    return False

def pdf_olustur(path, kurum, kisi, g, hs, ref_no, bildirim_tarihi, belge_no, ettn, avans=D0):
    _fontlari_yukle()
    MAVI = colors.HexColor("#7FA6D8")
    ACIK = colors.HexColor("#BFD3EE")
    TOPLAM = colors.HexColor("#A9C1E3")

    def P(txt, bold=False, size=7, align=0):
        st = ParagraphStyle("x", fontName=FONTB if bold else FONT, fontSize=size, leading=size + 2, alignment=align)
        txt = str(txt).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
        return Paragraph(txt, st)

    def kv(rows, widths):
        t = Table([[P(k), P(":"), P(v)] for k, v in rows], colWidths=widths)
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 1), ("RIGHTPADDING", (0, 0), (-1, -1), 1), ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
        return t

    story = []
    
    # DÜZELTME: Sütun genişlikleri 60-60-60 olarak eşitlendi ve iç tablolar buna göre daraltıldı.
    sol = kv([("Kamu İdaresi Adı", kurum["kamu"]), ("Birim Adı", kurum["birim"]), ("Birim VKN", kurum["vkn"]), ("Kurumsal Kod", kurum["kurumsal_kod"]), ("Bütçe Yılı", kurum["butce_yili"]), ("Yolluk Referans Numarası", "")], [25 * mm, 3 * mm, 32 * mm])
    
    sag = kv([("Versiyon Numarası", "1.0"), ("Senaryo Kodu", "TEMELYOLLUK"), ("Bildirim Tarihi", dstr(bildirim_tarihi)), ("Belge Numarası", belge_no), ("ETTN", ""), ("İşlem Türü", "Yolluk"), ("İşlem Alt Türü", "Yurtiçi Geçici Görev Yolluğu")], [22 * mm, 3 * mm, 35 * mm])
    
    orta = [P("Yurtiçi/Yurtdışı Geçici Görev Yolluğu Bildirimi", True, 10, 1)]
    logo = os.path.join(APP_DIR, "logo.png")
    if os.path.exists(logo):
        orta.insert(0, Image(logo, width=22 * mm, height=22 * mm, kind="proportional"))
    
    # Orta sütunu ortalamak için Table kullanıyoruz
    orta_tbl = Table([[orta]], colWidths=[60 * mm])
    orta_tbl.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))

    ust = Table([[sol, orta_tbl, sag]], colWidths=[60 * mm, 60 * mm, 60 * mm])
    ust.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story += [ust, Spacer(1, 6)]

    a, b = kisa_yer(g["nereden"]), kisa_yer(g["nereye"])
    dk = kisi["derece"].split(".")[0] + (("/" + kisi["kademe"].split(".")[0]) if kisi["kademe"] else "")
    pers = [
        [P("Adı ve Soyadı"), P(": " + kisi["ad"]), P("Derece ve Kademe"), P(": " + dk)],
        [P("TCKN/Pasaport No"), P(": " + kisi["tc"]), P("Ek Gösterge"), P(": " + (kisi.get("ekg_no") or kisi["ekg"]))],
        [P("Unvan"), P(": " + kisi["unvan"]), P("Atama Tarihi"), P(":")],
        [P("Nereden Nereye Gidildiği"), P(f": {a} - {b} - {a}"), P("Gündelik"), P(": " + tl(g["gundelik"]))],
        [P(""), P(""), P("Avans Tutarı"), P(": " + (tl(avans) if avans > 0 else ""))],
    ]
    t = Table([[P("Personel Bilgileri", True, 9, 1), "", "", ""]] + pers, colWidths=[38 * mm, 52 * mm, 38 * mm, 52 * mm])
    t.setStyle(TableStyle([("SPAN", (0, 0), (-1, 0)), ("BACKGROUND", (0, 0), (-1, 0), MAVI), ("GRID", (0, 0), (-1, -1), 0.5, colors.black), ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]))
    story.append(t)
    d = Table([[P("Detay Bilgileri", True, 9, 1)]], colWidths=[180 * mm])
    d.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), MAVI), ("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
    story.append(d)

    def bolum(baslik, kolonlar, satirlar, widths, birlestir_son_sutun=False):
        n = len(kolonlar)
        data = [[P(baslik, True, 8, 1)] + [""] * (n - 1), [P(k, True, 6.5, 1) for k in kolonlar]]
        
        toplam_deger = ""
        if birlestir_son_sutun and len(satirlar) > 1:
            toplam = Decimal("0.00")
            for r in satirlar:
                val_str = str(r[-1]).replace(" TL", "").replace(".", "").replace(",", ".")
                try:
                    toplam += Decimal(val_str)
                except Exception:
                    pass
            toplam_deger = tl(toplam)

        for idx, r in enumerate(satirlar):
            row_data = [P(c, False, 6.5, 1) for c in r]
            if birlestir_son_sutun and len(satirlar) > 1:
                if idx == 0:
                    row_data[-1] = P(toplam_deger, True, 6.5, 1)
                else:
                    row_data[-1] = P("", False, 6.5, 1)
            data.append(row_data)

        tb = Table(data, colWidths=[w * mm for w in widths])
        styles = [("SPAN", (0, 0), (-1, 0)), ("BACKGROUND", (0, 0), (-1, 0), ACIK), ("GRID", (0, 0), (-1, -1), 0.5, colors.black), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]
        if birlestir_son_sutun and len(satirlar) > 1:
            son_kolon = n - 1
            styles.append(("SPAN", (son_kolon, 2), (son_kolon, len(satirlar) + 1)))
        tb.setStyle(TableStyle(styles))
        story.append(tb)

    gundelik_data = [[i + 1, r[0], dstr(r[1]), dstr(r[2]), r[3], fmt(r[4]), fmt(r[5]), "TRY", "1.0", tl(r[5])] for i, r in enumerate(hs["gundelik"])]
    bolum("Gündelik", ["No", "Gündelik Türü", "Başlangıç Tarihi", "Bitiş Tarihi", "Gün Sayısı", "Gündelik", "Gündelik Tutarı", "Döviz Cinsi", "Döviz Kuru", "Toplam Tutar"], gundelik_data, [8, 32, 20, 20, 12, 18, 24, 14, 12, 20], birlestir_son_sutun=True)
    
    yol_data = [[i + 1, dstr(r[0]), r[1], tstr(r[2]), tstr(r[3]), r[4], fmt(r[5]), "TRY", "1.0", tl(r[5])] for i, r in enumerate(hs["yol"])]
    bolum("Yol Masrafı", ["No", "Yolculuk Tarihi", "Nereden Nereye", "Gidiş", "Dönüş", "Taşıt Çeşidi", "Taşıt Tutarı", "Döviz Cinsi", "Döviz Kuru", "Toplam Tutar"], yol_data, [8, 22, 34, 14, 14, 20, 22, 12, 12, 22], birlestir_son_sutun=True)
    
    konak_data = [[i + 1, r[0], dstr(r[1]), dstr(r[2]), r[3], fmt(r[4]), fmt(r[5]), "TRY", "1.0", tl(r[5])] for i, r in enumerate(hs["konak"])]
    bolum("Konaklama", ["No", "Konaklama Yeri", "Başlangıç Tarihi", "Bitiş Tarihi", "Gün Sayısı", "Gündelik", "Konaklama Tutarı", "Döviz Cinsi", "Döviz Kuru", "Toplam Tutar"], konak_data, [8, 34, 20, 20, 12, 18, 22, 12, 12, 22], birlestir_son_sutun=True)
    
    diger_data = [[i + 1, r[0], dstr(r[1]), r[2], fmt(r[3]), "TRY", "1.0", tl(r[3])] for i, r in enumerate(hs["diger"])]
    bolum("Diğer Masraf", ["No", "Masraf Türü", "Masraf Tarihi", "Masraf Adedi", "Masraf Tutarı", "Döviz Cinsi", "Döviz Kuru", "Toplam Tutar"], diger_data, [8, 50, 24, 20, 26, 14, 14, 24], birlestir_son_sutun=True)

    T = hs["tot"]
    gt = Table([[P("Genel Toplam", True, 8, 1), "", "", ""], [P("Gündelik Toplamı", True, 7, 1), P("Yol Masrafı Toplamı", True, 7, 1), P("Konaklama Toplamı", True, 7, 1), P("Diğer Masraf Toplamı", True, 7, 1)], [P(tl(T["gundelik"]), False, 8, 1), P(tl(T["yol"]), False, 8, 1), P(tl(T["konak"]), False, 8, 1), P(tl(T["diger"]), False, 8, 1)]], colWidths=[45 * mm] * 4)
    gt.setStyle(TableStyle([("SPAN", (0, 0), (-1, 0)), ("BACKGROUND", (0, 0), (-1, 0), ACIK), ("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
    story.append(gt)
    
    gb = Table([[P("Genel Bildirim Tutarı", True, 8, 1), P(tl(T["genel"]), True, 11, 1)]], colWidths=[135 * mm, 45 * mm])
    gb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), TOPLAM), ("GRID", (0, 0), (-1, -1), 0.5, colors.black), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story.append(gb)
    story.append(Spacer(1, 14))

    if avans > 0:
        son_mahsup = bildirim_tarihi + timedelta(days=30)
        story.append(P(f"Avans Mahsup Son Tarihi: {dstr(son_mahsup)}", True, 8))
        story.append(Spacer(1, 4))

    imza = Table([[P("Düzenleyen", True, 8), P(": " + kisi["ad"], True, 8), P("Onaylayan", True, 8), P(": " + kurum["onay_ad"], True, 8)], [P("Unvan", True, 8), P(": " + kisi["unvan"], True, 8), P("Unvan", True, 8), P(": " + kurum["onay_unvan"], True, 8)], [P("Düzenleme Tarihi", True, 8), P(": " + dstr(bildirim_tarihi), True, 8), P("Onay Tarihi", True, 8), P(":", True, 8)], [P("İmza", True, 8), P(":", True, 8), P("İmza", True, 8), P(":", True, 8)]], colWidths=[28 * mm, 62 * mm, 28 * mm, 62 * mm], rowHeights=[None, None, None, 28])
    imza.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(imza)

    SimpleDocTemplate(path, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=12 * mm, bottomMargin=12 * mm, title=f"Yolluk Bildirimi {ref_no}").build(story)

def surekli_pdf_olustur(path, kurum, kisi, atama_tarihi, avans_str, hs, bildirim_tarihi, es_durumu=False):
    _fontlari_yukle()
    MAVI = colors.HexColor("#7FA6D8")
    ACIK = colors.HexColor("#BFD3EE")
    
    def P(txt, bold=False, size=7, align=0):
        st = ParagraphStyle("x", fontName=FONTB if bold else FONT, fontSize=size, leading=size + 2, alignment=align)
        txt = str(txt).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
        return Paragraph(txt, st)

    story = []
    
    # DÜZELTME: Sürekli görev başlığı da ortalandı.
    baslik = Table([[P("YURTİÇİ / YURTDIŞI SÜREKLİ GÖREV YOLLUĞU BİLDİRİMİ", True, 12, 1)]], colWidths=[260*mm])
    baslik.setStyle(TableStyle([("ALIGN", (0,0), (-1,-1), "CENTER")]))
    story.append(baslik)
    story.append(Spacer(1, 5))

    pers = [
        [P("Adı Soyadı"), P(": " + kisi["ad"]), P("Dairesi"), P(": " + kurum["birim"])],
        [P("Unvanı"), P(": " + kisi["unvan"]), P("Bütçe Yılı"), P(": " + kurum["butce_yili"])],
        [P("Derece / Kademe"), P(f": {kisi['derece']} / {kisi['kademe']}"), P("Önceden Avans Almışsa Aldığı"), P(": " + (avans_str or "Almadı"))],
        [P("Ek Göstergesi"), P(": " + (kisi.get("ekg_no") or kisi["ekg"])), P("Atama Tarihi"), P(": " + (dstr(atama_tarihi) if atama_tarihi else ""))],
        [P("Gündeliği"), P(": " + tl(hs["satirlar"][0]["yevmiye"] if hs["satirlar"] else 0)), P(""), P("")]
    ]
    pt = Table(pers, colWidths=[30*mm, 80*mm, 50*mm, 100*mm])
    pt.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 0.5, colors.black), ("FONTSIZE", (0,0), (-1,-1), 8)]))
    story.append(pt)
    story.append(Spacer(1, 10))

    headers = [
        [
            P("NEREDEN", True, 7), P("NEREYE", True, 7), P("Adı Soyadı", True, 7), P("Akrabalık\nDerecesi", True, 7),
            P("GÜNDELİKLER", True, 7), "", "",
            P("TAŞITIN", True, 7), "",
            P("YER DEĞİŞTİRME\nGİDERİ", True, 7), "", "",
            P("Dövizin", True, 7), "",
            P("Toplam\nTutar", True, 7)
        ],
        [
            "", "", "", "",
            P("Gün\nSayısı", True, 6), P("Yevmiye", True, 6), P("Tutarı", True, 6),
            P("Çeşidi /\nMevki", True, 6), P("Ücreti", True, 6),
            P("Sabit Unsur", True, 6), P("Değişken Unsur", True, 6), "",
            P("Cinsi", True, 6), P("Kuru", True, 6),
            ""
        ],
        [
            "", "", "", "",
            "", "", "",
            "", "",
            "", P("Mesafe\nKm/Mil", True, 6), P("Tutarı", True, 6),
            "", "",
            ""
        ]
    ]
    
    data = headers.copy()
    
    for i, r in enumerate(hs["satirlar"]):
        data.append([
            P(r["nereden"], False, 6), P(r["nereye"], False, 6), P(r["ad"], False, 6), P(r["akraba"], False, 6),
            P(r["gun"], False, 6), P(fmt(r["yevmiye"]), False, 6), P(fmt(r["g_tutar"]), False, 6),
            P(r["tasit"], False, 6), P(fmt(r["tasit_ucret"]), False, 6),
            P(fmt(r["sabit"]), False, 6), P(r["mesafe"], False, 6), P(fmt(r["degisken"]), False, 6),
            P("TRY", False, 6), P("1.0", False, 6),
            P(tl(r["toplam"]), False, 6)
        ])

    T = hs["tot"]
    data.append([
        P("G E N E L   T O P L A M", True, 8), "", "", "", "", "",
        P(tl(T["yevmiye"]), True, 7),
        "", P(tl(T["tasit"]), True, 7),
        P(tl(T["sabit"]), True, 7), "", P(tl(T["degisken"]), True, 7),
        "", "",
        P(tl(T["genel"]), True, 8)
    ])

    col_widths = [21*mm, 21*mm, 26*mm, 15*mm, 12*mm, 16*mm, 16*mm, 15*mm, 15*mm, 18*mm, 14*mm, 16*mm, 12*mm, 12*mm, 21*mm]
    
    t = Table(data, colWidths=col_widths, repeatRows=3)
    
    style = [
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("BACKGROUND", (0,0), (-1,2), ACIK),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        
        ("SPAN", (0,0), (0,2)),
        ("SPAN", (1,0), (1,2)),
        ("SPAN", (2,0), (2,2)),
        ("SPAN", (3,0), (3,2)),
        ("SPAN", (14,0), (14,2)),
        
        ("SPAN", (4,0), (6,0)),
        ("SPAN", (7,0), (8,0)),
        ("SPAN", (9,0), (11,0)),
        ("SPAN", (12,0), (13,0)),
        
        ("SPAN", (4,1), (4,2)),
        ("SPAN", (5,1), (5,2)),
        ("SPAN", (6,1), (6,2)),
        ("SPAN", (7,1), (7,2)),
        ("SPAN", (8,1), (8,2)),
        ("SPAN", (9,1), (9,2)),
        ("SPAN", (10,1), (11,1)),
        ("SPAN", (12,1), (12,2)),
        ("SPAN", (13,1), (13,2)),
        
        ("SPAN", (0, len(data)-1), (5, len(data)-1)),
        ("BACKGROUND", (0, len(data)-1), (-1, len(data)-1), ACIK),
    ]
    t.setStyle(TableStyle(style))
    story.append(t)
    
    story.append(Spacer(1, 5))
    if hs["satirlar"]:
        r0 = hs["satirlar"][0]
        aciklama = f"{r0['nereden']} 'den/dan {r0['nereye']} 'a/e atanan {kisi['ad']} 'a/e ait sürekli görev yolluğu olarak tahakkuk eden {tl(T['genel'])} tutarı gösterir bildirimdir."
        at = Table([[P(aciklama, False, 8)]], colWidths=[260*mm])
        story.append(at)

    story.append(Spacer(1, 20))
    imza = Table([
        [P("Birim Yetkilisi (*)", True, 8), P("", True, 8), P("Bildirim Sahibi", True, 8)],
        [P("Adı Soyadı : " + kurum.get("onay_ad", ""), False, 8), P("", True, 8), P("Adı Soyadı : " + kisi["ad"], False, 8)],
        [P("Unvanı     : " + kurum.get("onay_unvan", ""), False, 8), P("", True, 8), P("", False, 8)],
        [P("İmzası     :", False, 8), P("", True, 8), P("İmzası     :", False, 8)],
        [P("Tarih      : " + dstr(bildirim_tarihi), False, 8), P("", True, 8), P("Tarih      : " + dstr(bildirim_tarihi), False, 8)],
    ], colWidths=[70*mm, 100*mm, 70*mm])
    imza.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
    story.append(imza)
    
    story.append(Spacer(1, 10))
    if es_durumu:
        story.append(P("Not: Eş nedeniyle tayin durumu seçilmiştir. Değişken unsur %2,5 üzerinden hesaplanmıştır.", True, 8))
    
    story.append(P("(*) Bu kısım bildirim sahibinin atama işleminden bilgisi olan amir tarafından imzalanacaktır.", False, 7))
    story.append(P("M.Y.H.B.Y. Örnek No: 28", False, 7))

    SimpleDocTemplate(path, pagesize=landscape(A4), leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm).build(story)