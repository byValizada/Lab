# -*- coding: utf-8 -*-
"""
İT Tədris Laboratoriyası — vizual təqdimat vərəqinin generatoru.

İşə salmaq:  python teqdimat_qur.py
Girişlər:    teqdimat.src.html · lab_parametrleri.json · renderler/*.jpg · sened_qur.py
Nəticələr:   teqdimat.html          — brauzerdə açılan müstəqil fayl
             teqdimat.body.html     — Artifact üçün (html/head/body teqləri olmadan)

Şəkillər data: URI kimi içəri hopdurulur ki, fayl tək başına, internetsiz işləsin.
Cədvəllərin rəqəmləri sened_qur.py-dən import edilir — yəni PDF ilə eyni mənbədən.
"""
import base64
import io
import json
import os
import re
import sys

from PIL import Image

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "teqdimat.src.html")
RENDERS = os.path.join(BASE, "renderler")

with open(os.path.join(BASE, "lab_parametrleri.json"), encoding="utf-8") as fh:
    PRM = json.load(fh)

# sened_qur.py PDF-i də qurur; təqdimat üçün yalnız rəqəmlər lazımdır
sys.path.insert(0, BASE)
import sened_qur as S  # noqa: E402  — büdcə rəqəmləri PDF ilə eyni mənbədən gəlir

M = S.money
PDF_PAGES = S.pdf_page_count()          # mövcud PDF-dən oxunur, əl ilə yazılmır


def autocrop(im, tol=26, pad=0.015):
    """3D səhnənin düz fon rəngini kəsir.

    Xarici kadrlarda otaq çərçivənin yalnız bir hissəsini tutur; qalan sahə
    səhnənin bir rəngli fonudur. İnteryer kadrlarında isə fon yoxdur — həmin
    halda kəsmə demək olar ki, heç nə dəyişmir və tətbiq olunmur.
    """
    w, h = im.size
    bg = im.getpixel((2, 2))
    px = im.load()
    step = 2                      # hər 2 pikseldən bir yoxlamaq kifayətdir
    x0, y0, x1, y1 = w, h, 0, 0
    for y in range(0, h, step):
        for x in range(0, w, step):
            r, g, b = px[x, y]
            if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > tol:
                if x < x0: x0 = x
                if x > x1: x1 = x
                if y < y0: y0 = y
                if y > y1: y1 = y
    if x1 <= x0 or y1 <= y0:
        return im
    area = (x1 - x0) * (y1 - y0)
    if area > 0.92 * w * h or area < 0.20 * w * h:
        return im                 # ya kəsiləsi fon yoxdur, ya da nəticə şübhəlidir
    mx, my = int(w * pad), int(h * pad)
    return im.crop((max(0, x0 - mx), max(0, y0 - my),
                    min(w, x1 + mx), min(h, y1 + my)))


RENDER_EXT = (".jpg", ".jpeg", ".png")


def img(name, width):
    """Renderi kəsib, verilmiş enə kiçildib data: URI kimi qaytarır.

    Uzantı sabit deyil: 3D dizaynerin "4K render" düyməsi PNG yükləyir,
    mövcud kadrlar isə JPEG-dir. Hər ikisi qəbul olunur ki, kadrı əvəz etmək
    üçün formatı çevirmək lazım gəlməsin.
    """
    for ext in RENDER_EXT:
        path = os.path.join(RENDERS, name + ext)
        if os.path.exists(path):
            break
    else:
        raise SystemExit(
            f"Render tapılmadı: renderler/{name}.(jpg|jpeg|png)\n"
            f"Ad teqdimat.src.html içindəki {{{{IMG:{name}:…}}}} yer tutucusu ilə "
            f"hərfbəhərf üst-üstə düşməlidir.")
    im = autocrop(Image.open(path).convert("RGB"))
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=78, optimize=True, progressive=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return (f'<img src="data:image/jpeg;base64,{b64}" width="{im.width}" '
            f'height="{im.height}" alt="{name}" loading="lazy">')


def cell(v, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f"<td{c}>{v}</td>"


def table(head, rows, caption="", aligns=None):
    aligns = aligns or [""] * len(head)
    th = "".join(f'<th class="{a}">{h}</th>' for h, a in zip(head, aligns))
    body = []
    for r in rows:
        cls = ""
        if isinstance(r, tuple):
            r, cls = r
        tds = "".join(cell(v, a) for v, a in zip(r, aligns))
        body.append(f'<tr class="{cls}">{tds}</tr>' if cls else f"<tr>{tds}</tr>")
    cap = f"<caption>{caption}</caption>" if caption else ""
    return ('<div class="tblwrap"><table><thead><tr>' + th + "</tr></thead><tbody>"
            + "".join(body) + "</tbody>" + cap + "</table></div>")


# ─────────────────────── AVADANLIQ CƏDVƏLİ ───────────────────────
def equip_table():
    rows = []
    for key, _title, items in S.EQUIP:
        sub = sum(say * qiy for _rid, _ad, _sp, say, qiy in items)
        # kateqoriyadakı ən vacib 3 mövqe qısa xülasə kimi
        top = sorted(items, key=lambda r: -r[3] * r[4])[:3]
        detail = " · ".join(
            f"{re.sub('<[^>]+>', '', ad)}" + (f" ×{say}" if say > 1 else "")
            for _rid, ad, _sp, say, qiy in top
        )
        rows.append(((key, detail, M(sub)), ""))
    rows.append((("<b>Ara cəm</b>", "", f"<b>{M(S.grand)}</b>"), "sub"))
    rows.append((("Gözlənilməz xərclər üçün ehtiyat (8 %)", "", M(S.reserve)), ""))
    rows.append((("<b>SSENARİ B — TÖVSİYƏ OLUNAN</b>", "",
                  f"<b>{M(S.total_b)}</b>"), "total"))
    pages = f" ({PDF_PAGES} səhifəlik PDF)" if PDF_PAGES else ""
    return table(["Kateqoriya", "Əsas mövqelər", "AZN"], rows,
                 caption=f"Tam spesifikasiya — sənədin 9-cu bölməsi{pages}.",
                 aligns=["", "", "n"])


# ─────────────────────── SSENARİLƏR ───────────────────────
def scen_table():
    drop = ", ".join(re.sub("<[^>]+>", "", S.ITEMS[r][0]) for r in S.SCEN_A_DROP)
    add = ", ".join(n for n, _v in S.SCEN_C_ADD)
    rows = [
        (("<b>A — Minimal</b>", M(S.sA),
          f"Çıxarılır: {drop}. Şəbəkə və AI praktikası zəifləyir; CCNA hazırlığı mümkün olmur."), ""),
        (("<b>B — Tövsiyə olunan</b>", M(S.total_b),
          "Yeddi istiqamətin hamısı tam praktika ilə örtülür; əlçatanlıq daxildir."), "total"),
        (("<b>C — Genişləndirilmiş</b>", M(S.sC),
          f"Əlavə olunur: {add}. Tədqiqat və magistr proqramları planlaşdırılırsa."), ""),
        (("Büdcədən kənar — akustik tavan + səssiz rack", M(S.OUT_OF_SCOPE),
          f"Ayrıca qərar. Ssenari B ilə birlikdə {M(S.total_full)} AZN."), ""),
    ]
    return table(["Ssenari", "AZN", "Əhatə və nəticəyə təsiri"], rows,
                 aligns=["", "n", ""])


def tco_table():
    rows = [
        (("Kapital xərci (birdəfəlik)", M(S.total_b), "Ssenari B"), ""),
        (("Elektrik enerjisi", "9 000", "≈1 800 AZN/il"), ""),
        (("Texniki xidmət və təmir", "12 500", "≈2 500 AZN/il — zəmanətdən sonra"), ""),
        (("Proqram abunələri", "8 000", "≈1 600 AZN/il"), ""),
        (("İstehlak materialları", "6 000", "≈1 200 AZN/il"), ""),
        (("Avadanlığın yenilənməsi", "18 000", "İllik 3 600 AZN ehtiyat"), ""),
        ((f"<b>5 İLLİK TCO</b>", f"<b>{M(S.tco)}</b>",
          f"<b>≈ {M(S.tco_seat)} AZN / iş yeri · {M(S.tco_seat_y)} AZN / iş yeri / il</b>"), "total"),
    ]
    return table(["5 illik sahiblik dəyəri", "AZN", "Qeyd"], rows, aligns=["", "n", ""])


def audit_table():
    sev = {"kritik": "MƏRHƏLƏ 1 — MÜTLƏQ", "vacib": "MƏRHƏLƏ 2 — TÖVSİYƏ OLUNAN"}
    rows = []
    for g, title, s, items in S.AUDIT:
        rows.append(((f'<b>{g}. {title}</b> <span style="color:var(--slate);'
                      f'font-size:11px;letter-spacing:.08em">{sev[s]}</span>',
                      f"<b>{M(S.AUDIT_GROUP_TOTAL[g])}</b>"), "sub"))
        for nm, desc, c in items:
            short = re.sub("<[^>]+>", "", desc).split(".")[0]
            if len(short) > 150:
                short = short[:147].rsplit(" ", 1)[0] + "…"
            rows.append(((f"{nm}<br><span style='color:var(--slate);font-size:12.5px'>"
                          f"{short}.</span>", M(c) if c else "—"), ""))
    rows.append((("<b>Kritik əlavələr (A–D)</b>", f"<b>{M(S.AUDIT_CRIT)}</b>"), "total"))
    return table(["Nə çatışmır", "AZN"], rows, aligns=["", "n"])


def ready_table():
    rows = [
        (("Ssenari B — avadanlıq spesifikasiyası", M(S.total_b), "Bölmə 05"), ""),
        (("Akustik tavan + səssiz rack", M(S.OUT_OF_SCOPE), "Bölmə 06"), ""),
        (("Auditin kritik əlavələri (A–D)", M(S.AUDIT_CRIT), "Bölmə 07"), ""),
        (("<b>İŞƏ DÜŞƏN LABORATORİYA</b>", f"<b>{M(S.total_ready)}</b>",
          "<b>Tövsiyə olunan qərar</b>"), "total"),
        (("Auditin tövsiyə olunan genişləndirməsi (E)", M(S.AUDIT_OPT),
          "İkinci mərhələyə salına bilər"), ""),
        (("Tam əhatə", M(S.total_max), ""), ""),
    ]
    return table(["Nəyə başa gəlir", "AZN", "Mənbə"], rows, aligns=["", "n", ""])


def plan_table():
    steps = [
        ("0", "Hazırlıq", "Məsul şəxsin təyini · akademik proqramlara qeydiyyat · otağın enerji hesabatı", "2 həftə"),
        ("1", "Otağın hazırlanması", f"Təmir · {PRM['elektrik']['kw_xett']} kVt elektrik montajı · struktur kabel · kondisionerlər · jalüzlər", "3–4 həftə"),
        ("2", "Satınalma", "Kommersiya təklifləri · müqavilələr · çatdırılma", "4–6 həftə"),
        ("3", "Quraşdırma", "Mebel · rack · şəbəkə konfiqurasiyası · iş yerləri", "1–2 həftə"),
        ("4", "Proqram təminatı", "Sistem imici · virtuallaşdırma · VLAN · AD/LDAP · davamlılıq modeli · test", "2–3 həftə"),
        ("5", "Pilot və təlim", "Müəllim təlimi · sınaq dərsləri · işıqlanma və akustika ölçülməsi · qəbul aktı", "1–2 həftə"),
    ]
    rows = [((n, ad, mz, md), "") for n, ad, mz, md in steps]
    return table(["№", "Mərhələ", "Məzmun", "Müddət"], rows, aligns=["n", "", "", "n"])


# ─────────────────────── MÜHƏNDİS YOXLAMASI ───────────────────────
def checks():
    lx, ac, el, cool, eg = (PRM["isiqlanma"], PRM["akustika"], PRM["elektrik"],
                            PRM["soyutma"], PRM["tahliye"])
    cap, a11 = PRM["tutum"], PRM["elcatanliq"]
    n = S.num

    items = [
        ("Sıxlıq", n(cap["sixliq"], 2), "m²/iş yeri", "norma ≥ 2,2", "ok"),
        ("Orta işıqlanma", str(lx["orta"]), "lx", f"norma ≥ {lx['norma']} lx", "ok"),
        ("Bərabərlik U₀", n(lx["u0"], 2), "", f"hədəf ≥ {n(lx['u0_norma'], 2)} — sərhəddə", "warn"),
        ("Əks-səda RT60", n(ac["rt_bare"], 2), "s", f"norma ≤ {n(ac['limit'], 2)} s", "bad"),
        ("Ayrılmış xətt", str(el["kw_xett"]), "kVt", f"hesabi yük {n(el['kw_hesabi'])} kVt", "ok"),
        ("Soyutma yükü", M(cool["btu"]), "BTU/s", f"{cool['kondisioner']} × 24000 BTU inverter", "ok"),
        ("Əlçatan iş yeri", f"{a11['say']} / {a11['teleb']}", "", "manevr dairəsi sərbəst", "ok"),
        ("Tahliyə", f"{eg['nefer']} / {eg['cixis']}", "nəfər / çıxış",
         f"ən uzaq yol {n(eg['en_uzaq_m'])} m (norma ≤ {eg['limit_m']} m)", "ok"),
    ]
    label = {"ok": "ödənir", "warn": "sərhəddə", "bad": "ödənmir"}
    out = ['<div class="checks">']
    for lbl, val, unit, norm, st in items:
        u = f'<span class="u">{unit}</span>' if unit else ""
        out.append(
            f'<div class="check"><div class="lbl">{lbl}</div>'
            f'<div class="val">{val}{u}</div>'
            f'<div class="norm">{norm}</div>'
            f'<span class="pill {st}">{label[st]}</span></div>')
    out.append("</div>")
    return "".join(out)


# ─────────────────────── QURULUŞ ───────────────────────
def build():
    html = open(SRC, encoding="utf-8").read()

    def sub_img(m):
        return img(m.group(1), int(m.group(2)))

    html = re.sub(r"\{\{IMG:([A-Za-z0-9_]+):(\d+)\}\}", sub_img, html)
    html = html.replace("{{TABLE:EQUIP}}", equip_table())
    html = html.replace("{{TABLE:SCEN}}", scen_table())
    html = html.replace("{{TABLE:TCO}}", tco_table())
    html = html.replace("{{TABLE:AUDIT}}", audit_table())
    html = html.replace("{{TABLE:READY}}", ready_table())
    html = html.replace("{{TABLE:PLAN}}", plan_table())
    html = html.replace("{{CHECKS}}", checks())
    html = html.replace("{{DATE}}", "Avqust 2026")

    left = re.findall(r"\{\{[^}]+\}\}", html)
    if left:
        raise SystemExit("Doldurulmamış yer tutucu qaldı: " + ", ".join(sorted(set(left))))

    body_path = os.path.join(BASE, "teqdimat.body.html")
    with open(body_path, "w", encoding="utf-8") as fh:
        fh.write(html)

    full = ('<!doctype html>\n<html lang="az">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            + html.split("</style>")[0] + "</style>\n</head>\n<body>\n"
            + html.split("</style>", 1)[1] + "\n</body>\n</html>\n")
    full_path = os.path.join(BASE, "teqdimat.html")
    with open(full_path, "w", encoding="utf-8") as fh:
        fh.write(full)

    for p in (full_path, body_path):
        print(f"  ✓ {os.path.basename(p)}  {os.path.getsize(p)/1024/1024:.2f} MB")


if __name__ == "__main__":
    print("Təqdimat vərəqi qurulur…")
    build()
