# -*- coding: utf-8 -*-
"""
İT Tədris Laboratoriyası — sənədə daxil edilən üç sxemin generatoru.

İşə salmaq:  python sxem_qur.py
Nəticə:      otaq_plani.png · texniki_arxitektura.png · is_muhiti_davamliligi.png

Otaq planı 3D dizaynerin ixrac etdiyi düzülüşdən (lab_parametrleri.json)
birbaşa çəkilir — yəni 2D plan ilə 3D model heç vaxt fərqlənə bilməz.
Digər iki sxemin rəqəmləri də eyni fayldan alınır.
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Ellipse, FancyArrowPatch

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
DPI = 200

# ─────────────────────────── ŞRİFT ───────────────────────────
_installed = {f.name for f in font_manager.fontManager.ttflist}
FONT = "Arial" if "Arial" in _installed else "DejaVu Sans"
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = [FONT, "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ─────────────────────────── PARAMETRLƏR ───────────────────────────
PARAM_FILE = os.path.join(BASE, "lab_parametrleri.json")
try:
    with open(PARAM_FILE, encoding="utf-8") as fh:
        PRM = json.load(fh)
except FileNotFoundError:
    raise SystemExit(
        f"'{os.path.basename(PARAM_FILE)}' tapılmadı.\n"
        "3D dizayneri açın (3d/BASLAT.bat), 'Parametrlər' düyməsini basın və "
        "yüklənən faylı layihə qovluğuna qoyun.")

ROOM = PRM["otaq"]
LAY = PRM["duzulus"]["obyektler"]
CAP = PRM["tutum"]
CNT = PRM["say"]
W, D = ROOM["en"], ROOM["uzunluq"]

# ─────────────────────────── PALİTRA ───────────────────────────
NAVY = "#243447"
INK = "#2c3e50"
GREY = "#7f8c8d"
LGREY = "#aab7b8"
PAPER = "#fbfcfd"
BLUE = "#3498db"
DBLUE = "#2874a6"
RED = "#c0392b"
GREEN = "#16a085"
PURPLE = "#8e44ad"
ORANGE = "#e67e22"
SKY = "#85c1e9"
CHAIR = "#c8d0d8"


def num(v, d=1):
    return f"{v:.{d}f}".replace(".", ",")


def save(fig, name, tight=True):
    path = os.path.join(BASE, name)
    kw = dict(bbox_inches="tight", pad_inches=0.30) if tight else {}
    fig.savefig(path, dpi=DPI, facecolor="white", **kw)
    plt.close(fig)
    print(f"  ✓ {name}")
    return path


def rbox(ax, x, y, w, h, fc, ec=None, lw=1.2, r=0.10, z=2, alpha=1.0):
    """Yumşaq künclü qutu — bütün sxemlərdə eyni üslub."""
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0,rounding_size={r}",
                       facecolor=fc, edgecolor=ec or fc, linewidth=lw,
                       zorder=z, alpha=alpha)
    ax.add_patch(p)
    return p


def txt(ax, x, y, s, size=11, color="white", weight="normal", ha="center", va="center",
        z=5, style="normal", rot=0):
    ax.text(x, y, s, fontsize=size, color=color, fontweight=weight,
            ha=ha, va=va, zorder=z, style=style, rotation=rot,
            linespacing=1.45)


def arrow(ax, p0, p1, color=LGREY, lw=1.6, z=1, style="-|>", ms=11):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=ms,
                                 color=color, linewidth=lw, zorder=z,
                                 shrinkA=2, shrinkB=4))


# ═══════════════════════════════════════════════════════════════════
#  1. OTAQ PLANI — düzülüş faylından çəkilir
# ═══════════════════════════════════════════════════════════════════
def rot_size(o):
    """90°/270° dönmüş obyektin plan üzrə ölçüsü yerini dəyişir."""
    if abs(o["bucaq"]) % 180 == 90:
        return o["uzunluq"], o["en"]
    return o["en"], o["uzunluq"]


def draw_chairs(ax, o, n, side_offset, along):
    """Masanın uzun tərəfi boyunca stul dairələri."""
    w, d = rot_size(o)
    for sgn in (-1, 1):
        for i in range(n):
            t = (i + 0.5) / n - 0.5
            if along == "x":
                cx = o["x"] + t * w * 0.82
                cz = o["z"] + sgn * (d / 2 + side_offset)
            else:
                cx = o["x"] + sgn * (w / 2 + side_offset)
                cz = o["z"] + t * d * 0.82
            ax.add_patch(Circle((cx, cz), 0.21, facecolor=CHAIR,
                                edgecolor="#9fadb9", linewidth=0.8, zorder=4))


def plan():
    fig = plt.figure(figsize=(14.4, 11.6))
    ax = fig.add_axes([0.035, 0.275, 0.93, 0.645])   # plan yuxarıda, izahat aşağıda
    ax.set_aspect("equal")
    ax.axis("off")

    # ── divar və döşəmə ──
    ax.add_patch(Rectangle((0, 0), W, D, facecolor=PAPER, edgecolor=NAVY,
                           linewidth=3.2, zorder=1))

    # ── pəncərə lentləri (sol divar) — monitorlara perpendikulyar işıq ──
    for zc in (D * 0.28, D * 0.68):
        ax.add_patch(Rectangle((-0.09, zc - 0.95), 0.18, 1.90, facecolor="#d6ecfb",
                               edgecolor="#7fb3d5", linewidth=1.4, zorder=3))
    txt(ax, -0.62, D * 0.48, "PƏNCƏRƏLƏR", size=8.5, color="#5499c7",
        weight="bold", rot=90)

    # ── server və şəbəkə zonası (kəsik xətli əhatə) ──
    srv = [o for o in LAY if o["tip"] in ("rack", "ups", "nas")]
    if srv:
        sx0 = min(o["x"] - rot_size(o)[0] / 2 for o in srv) - 0.22
        sx1 = max(o["x"] + rot_size(o)[0] / 2 for o in srv) + 0.22
        sz0 = min(o["z"] - rot_size(o)[1] / 2 for o in srv) - 0.22
        sz1 = max(o["z"] + rot_size(o)[1] / 2 for o in srv) + 0.22
        ax.add_patch(Rectangle((sx0, sz0), sx1 - sx0, sz1 - sz0, facecolor="none",
                               edgecolor=PURPLE, linewidth=1.5,
                               linestyle=(0, (6, 4)), zorder=2))
        txt(ax, (sx0 + sx1) / 2, sz1 + 0.22, "Server və şəbəkə zonası",
            size=9, weight="bold", color=PURPLE)

    # ── obyektlər ──
    seat_no = 1
    for o in LAY:
        w, d = rot_size(o)
        x0, z0 = o["x"] - w / 2, o["z"] - d / 2
        t = o["tip"]

        if t == "pod":
            # 4 iş yeri: 2 × 2 xana + hər tərəfdə 2 stul
            rbox(ax, x0, z0, w, d, BLUE, ec="white", lw=1.6, r=0.04, z=3)
            ax.plot([x0, x0 + w], [o["z"], o["z"]], color="white", lw=1.6, zorder=4)
            ax.plot([o["x"], o["x"]], [z0, z0 + d], color="white", lw=1.6, zorder=4)
            for dz in (0.5, -0.5):
                for dx in (-0.5, 0.5):
                    txt(ax, o["x"] + dx * w / 2, o["z"] + dz * d / 2,
                        str(seat_no), size=10, weight="bold", z=5)
                    seat_no += 1
            draw_chairs(ax, o, 2, 0.30, "x")

        elif t == "a11y":
            rbox(ax, x0, z0, w, d, DBLUE, ec="white", lw=1.4, r=0.05, z=3)
            txt(ax, o["x"], o["z"], "ƏLÇATAN", size=9, weight="bold")
            # Ø1,5 m manevr dairəsi istifadəçi tərəfindədir (−z)
            ax.add_patch(Circle((o["x"], o["z"] - 0.85), 0.75, facecolor="none",
                                edgecolor=DBLUE, linewidth=1.5, linestyle=(0, (5, 4)),
                                zorder=2))
            txt(ax, o["x"], o["z"] - 0.85, "Ø1,5 m", size=8.5, color=DBLUE)

        elif t == "byod":
            ax.add_patch(Ellipse((o["x"], o["z"]), w, d, facecolor=RED,
                                 edgecolor="white", linewidth=1.6, zorder=3))
            txt(ax, o["x"], o["z"] + 0.12, "BYOD", size=10.5, weight="bold")
            txt(ax, o["x"], o["z"] - 0.18, f"{o['is_yeri']} yer", size=9)
            import math
            for i in range(o["is_yeri"]):
                a = (i / o["is_yeri"]) * 2 * math.pi + math.pi / 6
                ax.add_patch(Circle((o["x"] + math.cos(a) * (w / 2 + 0.42),
                                     o["z"] + math.sin(a) * (d / 2 + 0.42)),
                                    0.21, facecolor=CHAIR, edgecolor="#9fadb9",
                                    linewidth=0.8, zorder=4))

        elif t == "iot":
            ax.add_patch(Rectangle((x0 - 0.30, z0 - 0.22), w + 0.60, d + 1.15,
                                   facecolor="none", edgecolor=GREEN, linewidth=1.5,
                                   linestyle=(0, (6, 4)), zorder=2))
            rbox(ax, x0, z0, w, d, GREEN, ec="white", lw=1.5, r=0.05, z=3)
            txt(ax, o["x"], o["z"], f"IoT / robototexnika — {o['is_yeri']} yer",
                size=9.5, weight="bold")
            for i in range(o["is_yeri"]):
                cx = x0 + (i + 0.5) * w / o["is_yeri"]
                ax.add_patch(Circle((cx, z0 + d + 0.42), 0.19, facecolor=CHAIR,
                                    edgecolor="#9fadb9", linewidth=0.8, zorder=4))

        elif t == "teacher":
            rbox(ax, x0, z0, w, d, ORANGE, ec="white", lw=1.5, r=0.05, z=3)
            txt(ax, o["x"], o["z"], "Müəllim", size=10.5, weight="bold")
            ax.add_patch(Circle((o["x"], o["z"] - 0.75), 0.21, facecolor=CHAIR,
                                edgecolor="#9fadb9", linewidth=0.8, zorder=4))

        elif t in ("rack", "ups", "nas"):
            rbox(ax, x0, z0, w, d, o["reng"], ec="white", lw=1.3, r=0.03, z=3)
            txt(ax, o["x"], o["z"], {"rack": "Rack", "ups": "UPS", "nas": "NAS"}[t],
                size=8.5, weight="bold")

        elif t == "gpu":
            rbox(ax, x0, z0, w, d, o["reng"], ec="white", lw=1.4, r=0.04, z=3)
            txt(ax, o["x"], o["z"], "AI /\nGPU", size=9, weight="bold",
                rot=90 if w < d else 0)
            ax.add_patch(Circle((o["x"] - 0.75, o["z"]), 0.21, facecolor=CHAIR,
                                edgecolor="#9fadb9", linewidth=0.8, zorder=4))

        elif t == "printer":
            rbox(ax, x0, z0, w, d, GREY, ec="white", lw=1.3, r=0.04, z=3)
            txt(ax, o["x"], o["z"] + d / 2 + 0.28, "3D printer + MFP",
                size=9, weight="bold", color=INK)

        elif t == "cabinet":
            rbox(ax, x0, z0, w, d, "#95a5a6", ec="white", lw=1.2, r=0.03, z=3)
            txt(ax, o["x"] - w / 2 - 0.28, o["z"], "Şkaf", size=9, weight="bold",
                color=INK, rot=90)

        elif t in ("panel", "screen55"):
            rbox(ax, x0, z0, max(w, 0.16), max(d, 0.16), INK, ec=INK, lw=1.0, r=0.02, z=3)
            name = 'İnteraktiv panel 86"' if t == "panel" else 'Komanda ekranı 55"'
            if w >= d:
                txt(ax, o["x"], o["z"] - 0.34, name, size=9, weight="bold", color=INK)
            else:
                txt(ax, o["x"] - 0.34, o["z"], name, size=9, weight="bold",
                    color=INK, rot=90)

        elif t == "ac":
            rbox(ax, x0, z0, max(w, 0.14), max(d, 0.14), SKY, ec=SKY, lw=1.0, r=0.02, z=3)

    # ── giriş qapısı (tahliyə istiqaməti) ──
    door_w = PRM["tahliye"]["qapi_eni"]
    dx = W * 0.62
    ax.plot([dx, dx + door_w], [0, 0], color="white", lw=5, zorder=4)
    ax.add_patch(FancyArrowPatch((dx + door_w, 0), (dx + door_w, -0.72),
                                 arrowstyle="-|>", mutation_scale=13,
                                 color=NAVY, linewidth=1.6, zorder=4))
    txt(ax, dx + door_w / 2, -1.02, f"GİRİŞ / TAHLİYƏ  {num(door_w, 2)} m",
        size=9.5, weight="bold", color=NAVY)

    # ── keçid yolu ──
    ax.annotate("", xy=(0.55, 4.05), xytext=(8.0, 4.05),
                arrowprops=dict(arrowstyle="<->", color=GREY, lw=1.2,
                                linestyle=(0, (4, 3))), zorder=4)
    txt(ax, 4.3, 4.28, "keçid yolu 1,40 m", size=9, color=GREY)

    # ── ölçü xətləri ──
    ax.annotate("", xy=(0, -1.55), xytext=(W, -1.55),
                arrowprops=dict(arrowstyle="<->", color=GREY, lw=1.4))
    txt(ax, W / 2, -1.85, f"{num(W)} m", size=12, color=INK, weight="bold")
    ax.annotate("", xy=(-0.75, 0), xytext=(-0.75, D),
                arrowprops=dict(arrowstyle="<->", color=GREY, lw=1.4))
    txt(ax, -1.12, D / 2, f"{num(D)} m", size=12, color=INK, weight="bold", rot=90)

    ax.set_xlim(-2.1, W + 0.6)
    ax.set_ylim(-2.4, D + 0.9)

    fig.text(0.5, 0.955, "İNFORMASİYA TEXNOLOGİYALARI LABORATORİYASI — OTAQ PLANI",
             fontsize=17, fontweight="bold", color=NAVY, ha="center")

    # ── şərti işarələr ──
    legend = [
        (BLUE, f"Sabit iş yeri — {CNT['pod']} pod × 4 = {CNT['pod']*4} yer"),
        (DBLUE, f"Əlçatan iş yeri — {CAP['elcatan']} yer"),
        (RED, f"BYOD / komanda zonası — {CNT['byod']*6} yer"),
        (GREEN, f"IoT / robototexnika — {CNT['iot']*6} yer"),
        (ORANGE, "Müəllim stansiyası"),
        (PURPLE, "Server və şəbəkə zonası"),
        (INK, "İnteraktiv panel / ekran"),
        (SKY, "Kondisioner"),
    ]
    lx, ltop = 0.045, 0.248
    fig.text(lx, ltop, "ŞƏRTİ İŞARƏLƏR", fontsize=11.5, fontweight="bold", color=NAVY)
    for i, (c, s) in enumerate(legend):
        col, row = divmod(i, 4)
        px = lx + col * 0.255
        py = ltop - 0.045 - row * 0.033
        fig.patches.append(plt.Rectangle((px, py - 0.009), 0.019, 0.019, facecolor=c,
                                         edgecolor="none", transform=fig.transFigure,
                                         figure=fig))
        fig.text(px + 0.027, py, s, fontsize=9.8, color=INK, va="center")

    # ── göstəricilər qutusu ──
    info = "\n".join([
        f"Otaq sahəsi:  {num(ROOM['sahe'])} m²   ({num(W)} × {num(D)} × {num(ROOM['hundurluk'])} m)",
        f"Ümumi tutum:  {CAP['is_yeri']} yer / eyni anda {CAP['eyni_anda']} nəfər",
        f"Sıxlıq:  {num(CAP['sixliq'], 2)} m² / iş yeri — norma daxilində",
        f"Əlçatanlıq:  {CAP['elcatan']} tənzimlənən masa + Ø1,5 m manevr",
        "Keçid yolları:  1,40 m (sıralar arası)",
        f"İşıqlanma:  {PRM['isiqlanma']['orta']} lx orta, "
        f"{PRM['isiqlanma']['panel_sayi']} panel × {PRM['isiqlanma']['panel_lm']} lm",
        f"Elektrik:  {PRM['elektrik']['kw_xett']} kVt xətt · "
        f"{PRM['elektrik']['rozetka']} rozetka · {PRM['elektrik']['rj45']} RJ-45",
    ])
    fig.text(0.605, ltop + 0.012, info, fontsize=9.8, color=INK, va="top",
             linespacing=1.85,
             bbox=dict(boxstyle="round,pad=0.85", facecolor="#eaf2f8",
                       edgecolor="#cfe0ec", linewidth=1.1))

    fig.text(lx, 0.028,
             f"Otaq ölçüsü sabit deyil — {CAP['is_yeri']} iş yeri üçün tələb olunan "
             f"minimum sahə {num(CAP['min_sahe'])} m²-dir. Layihədə {num(ROOM['sahe'])} m² "
             f"götürülüb ki,\nəlçatan iş yerləri və 1,40 m keçid yolları təmin olunsun.  "
             f"Plan 3D dizaynerin düzülüş faylından avtomatik çəkilir.",
             fontsize=9.5, color=GREY, style="italic", linespacing=1.7, va="bottom")

    return save(fig, "otaq_plani.png", tight=False)   # yerləşdirmə əl ilə qurulub


# ═══════════════════════════════════════════════════════════════════
#  2. TEXNİKİ ARXİTEKTURA
# ═══════════════════════════════════════════════════════════════════
def architecture():
    fig, ax = plt.subplots(figsize=(14.9, 10.4))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 74)
    ax.axis("off")

    def node(x, y, w, h, title, sub, fc, ts=12.5, ss=9.8):
        rbox(ax, x, y, w, h, fc, r=0.9, lw=0)
        txt(ax, x + w / 2, y + h * (0.66 if sub else 0.5), title,
            size=ts, weight="bold")
        if sub:
            txt(ax, x + w / 2, y + h * 0.30, sub, size=ss)
        return (x + w / 2, y, x + w / 2, y + h)

    rows = [(66.5, "XARİCİ"), (52.5, "SƏRHƏD"), (37.5, "SEQMENTASİYA"),
            (20.0, "SON NÖQTƏLƏR"), (4.5, "XİDMƏT QATI")]
    for y, name in rows:
        txt(ax, -1.5, y + 3.6, name, size=9.5, color=GREY, weight="bold",
            rot=90, ha="center")

    inet = node(6, 66.5, 26, 7.0, "İnternet", "≥ 250 Mbit/s ayrılmış kanal", NAVY)
    cloud = node(68, 66.5, 30, 7.0, "Bulud platformaları",
                 "AWS Academy • Azure for Students • GitHub Education", "#5d6d7e", ss=9.0)
    fw = node(6, 52.5, 26, 7.0, "Firewall / Router", "NGFW • VPN • məzmun filtri", RED)
    sw = node(38, 52.5, 30, 7.0, "Nüvə switch (L2+/L3)",
              "48 port Gigabit • PoE+ • VLAN", PURPLE)

    arrow(ax, (19, 66.5), (19, 59.5), NAVY, 2.0)
    arrow(ax, (32, 56.0), (38, 56.0), NAVY, 2.0)
    arrow(ax, (83, 59.5), (83, 66.5), NAVY, 2.0, style="<|-|>")

    vlans = [("VLAN 10", "Tələbə", BLUE), ("VLAN 20", "Server", PURPLE),
             ("VLAN 30", "IoT", GREEN), ("VLAN 40", "İdarəetmə", ORANGE),
             ("VLAN 50", "Qonaq Wi-Fi", "#95a5a6")]
    vw, gap = 16.5, 2.4
    x0 = (100 - (len(vlans) * vw + (len(vlans) - 1) * gap)) / 2
    for i, (a, b, c) in enumerate(vlans):
        vx = x0 + i * (vw + gap)
        node(vx, 37.5, vw, 6.6, a, b, c, ts=11.5, ss=10)
        arrow(ax, (53, 52.5), (vx + vw / 2, 44.1), LGREY, 1.4)

    ends = [
        (f"{CNT['pod']*4} sabit iş yeri",
         "Fiziki PC • lokal GPU yox\nGələcəkdə VDI-yə keçid mümkün", BLUE),
        ("Virtuallaşdırma serveri",
         "Proxmox VE • hər tələbəyə VM\nLinux • Windows Server • Docker", PURPLE),
        ("İxtisaslaşmış qovşaqlar",
         f"AI/GPU stansiyası • Cisco lab dəsti\nIoT skamyası • BYOD zonası", GREEN),
    ]
    ew, egap = 28.5, 5.5
    ex0 = (100 - (3 * ew + 2 * egap)) / 2
    svc = [("Laboratoriya idarəetməsi",
            "Deep Freeze / imic bərpası\nVeyon — sinif idarəetməsi"),
           ("Kimlik və çıxış",
            "Active Directory / LDAP\nKartla giriş • 24/7 rejim"),
           ("Monitorinq və analitika",
            "İstifadə statistikası • lisenziya izləmə\nEnerji və nasazlıq hesabatları")]
    for i, (t, s, c) in enumerate(ends):
        ex = ex0 + i * (ew + egap)
        node(ex, 20.0, ew, 9.6, t, s, c, ts=12, ss=9.4)
        arrow(ax, (x0 + [0, 1, 2][i] * (vw + gap) + vw / 2, 37.5),
              (ex + ew / 2, 29.6), LGREY, 1.3)
        node(ex, 4.5, ew, 9.4, svc[i][0], svc[i][1], NAVY, ts=11.5, ss=9.2)
        arrow(ax, (ex + ew / 2, 20.0), (ex + ew / 2, 13.9), LGREY, 1.3)

    fig.suptitle("LABORATORİYANIN TEXNİKİ ARXİTEKTURASI",
                 fontsize=17, fontweight="bold", color=NAVY, y=0.965)
    fig.text(0.065, 0.045,
             "Hibrid çatdırılma modeli:  sabit iş yerləri ağır proqramlar üçün, "
             "virtual maşınlar Linux/server praktikası üçün,\n"
             "bulud platformaları DevOps və AI dərsləri üçün, BYOD zonası isə öz "
             "noutbukunu gətirən tələbələr üçün nəzərdə tutulub.\n"
             "Bu model bir tip avadanlığa bağlılığı aradan qaldırır və gələcək "
             "yeniləmələri mərhələli etməyə imkan verir.",
             fontsize=10, color=GREY, style="italic", linespacing=1.8)
    fig.subplots_adjust(bottom=0.16)
    return save(fig, "texniki_arxitektura.png")


# ═══════════════════════════════════════════════════════════════════
#  3. İŞ MÜHİTİNİN DAVAMLILIĞI
# ═══════════════════════════════════════════════════════════════════
def continuity():
    fig, ax = plt.subplots(figsize=(14.9, 10.9))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 78)
    ax.axis("off")

    def node(x, y, w, h, title, sub, fc, ts=12.5, ss=9.8):
        rbox(ax, x, y, w, h, fc, r=0.9, lw=0)
        txt(ax, x + w / 2, y + h * (0.70 if sub else 0.5), title, size=ts, weight="bold")
        if sub:
            txt(ax, x + w / 2, y + h * 0.34, sub, size=ss)

    txt(ax, 3, 75.5, "TƏLƏBƏ HARADAN GİRSƏ — NƏTİCƏ EYNİDİR",
        size=12, color=NAVY, weight="bold", ha="left")

    srcs = [("İstənilən pod", f"{CNT['pod']*4} sabit iş yeri"),
            ("BYOD masası", "öz noutbuku"),
            ("Evdən", "VPN / veb portal")]
    sw_, sgap = 28.5, 5.5
    sx0 = (100 - (3 * sw_ + 2 * sgap)) / 2
    for i, (t, s) in enumerate(srcs):
        sx = sx0 + i * (sw_ + sgap)
        node(sx, 66.0, sw_, 7.2, t, s, NAVY, ts=12, ss=9.6)
        arrow(ax, (sx + sw_ / 2, 66.0), (50, 60.4), LGREY, 1.4)

    node(28, 52.0, 44, 8.4, "VAHİD HESAB  (Active Directory / LDAP)",
         "bir istifadəçi adı — bütün laboratoriya resursları", RED, ts=13, ss=10)
    txt(ax, 74.5, 56.2, "← Bünövrə:\nbu olmadan\nheç nə işləmir",
        size=10, color=RED, style="italic", ha="left")

    tiers = [
        ("PİLLƏ 1 — Şəxsi disk",
         "Şəbəkə qovluğu (H:)\nSənədlər və Masaüstü avtomatik\nbura yönləndirilir",
         "15 GB / tələbə  •  hər gecə yedəklənir\nBÜTÜN tələbələr üçün", BLUE),
        ("PİLLƏ 2 — Konteyner",
         "JupyterHub / code-server\nBrauzerdən açılır: kod, kitabxana,\nfayl, tarixçə — hamısı yerində",
         "2 GB RAM  •  semestr boyu qalır\nKURS üzrə açılır", GREEN),
        ("PİLLƏ 3 — Şəxsi VM",
         "Proxmox-da tam virtual maşın\nSnapshot: tələbə sistemi sındırsa\nbir kliklə geri qaytarır",
         "4 GB RAM  •  40 GB disk\nMƏHDUD SAYDA (≈40 yer)", PURPLE),
    ]
    tw, tgap = 28.5, 5.5
    tx0 = (100 - (3 * tw + 2 * tgap)) / 2
    for i, (t, s, foot, c) in enumerate(tiers):
        tx = tx0 + i * (tw + tgap)
        rbox(ax, tx, 30.5, tw, 15.4, c, r=0.9, lw=0)
        txt(ax, tx + tw / 2, 43.4, t, size=12.5, weight="bold")
        txt(ax, tx + tw / 2, 39.0, s, size=9.6)
        txt(ax, tx + tw / 2, 33.2, foot, size=9.4)
        arrow(ax, (50, 52.0), (tx + tw / 2, 45.9), LGREY, 1.4)
        arrow(ax, (tx + tw / 2, 30.5), (tx + tw / 2, 24.6), LGREY, 1.3)

    node(tx0, 15.6, tw, 9.0, "NAS — 24 TB faydalı",
         "4× 8 TB RAID5\nşəxsi qovluqlar • konteyner məlumatları\ngecə yedəkləməsi",
         NAVY, ts=12, ss=9.2)
    node(tx0 + (tw + tgap), 15.6, tw * 2 + tgap, 9.0,
         "Virtuallaşdırma serveri — 4 TB NVMe",
         "virtual maşınlar • snapshot-lar • linked clone", NAVY, ts=12, ss=9.2)

    node(20, 3.6, 60, 8.2, "PİLLƏ 4 — GitHub Education (universitetdən kənar davamlılıq)",
         "Hər tələbənin kodu öz repozitoriyasında • evdə davam edir • "
         "məzun olandan sonra da qalır — portfel rolunu oynayır",
         ORANGE, ts=12.5, ss=9.4)
    arrow(ax, (tx0 + tw / 2, 15.6), (42, 11.8), LGREY, 1.3)
    arrow(ax, (tx0 + 2.2 * tw, 15.6), (60, 11.8), LGREY, 1.3)

    for y, name in [(70, "1–4-cü\nkurs"), (20, "SAXLAMA"), (6, "XARİCİ")]:
        txt(ax, -1.5, y, name, size=9.5, color=GREY, weight="bold", rot=90)

    fig.suptitle("TƏLƏBƏNİN İŞ MÜHİTİNİN DAVAMLILIĞI — PİLLƏLİ MODEL",
                 fontsize=17, fontweight="bold", color=NAVY, y=0.965)
    fig.text(0.065, 0.042,
             'Əsas prinsip:  iş yeri "tək istifadəlik"dir — hər yenidən başlatmada '
             'təmizlənir.  Tələbənin bütün işi serverdə yaşayır.\n'
             'Buna görə tələbə növbəti dəfə hansı stula oturmasının fərqi yoxdur: '
             'hesabına girən kimi hər şey yerindədir.',
             fontsize=10, color=GREY, style="italic", linespacing=1.8)
    fig.subplots_adjust(bottom=0.13)
    return save(fig, "is_muhiti_davamliligi.png")


if __name__ == "__main__":
    print(f"Sxemlər çəkilir  (şrift: {FONT}, {DPI} dpi)")
    plan()
    architecture()
    continuity()
    print("Hazırdır — indi `python sened_qur.py` işlədin.")
