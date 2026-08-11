# -*- coding: utf-8 -*-
"""
İT Tədris Laboratoriyası — layihə və satınalma sənədinin generatoru.

İşə salmaq:  python sened_qur.py
Nəticə:      IT_Laboratoriya_Plani.pdf

Bütün mühəndis göstəriciləri lab_parametrleri.json faylından oxunur.
Həmin faylı 3D dizayner ("Parametrlər" düyməsi) yaradır — beləliklə sənəd,
sxemlər və 3D model eyni mənbədən qidalanır və bir-birindən ayrı düşə bilmir.
Faylı yeniləmək üçün: 3d/BASLAT.bat → "Parametrlər" → faylı layihə qovluğuna kopyala.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                Table, TableStyle, Image, HRFlowable)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from PIL import Image as PILImage
import json
import os
import re
import sys

# Windows konsolu standart olaraq cp1252-dir və ş/ə hərflərində çökür.
# stderr də lazımdır — xəta mesajları oradan çıxır.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

BASE = os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────── ŞRİFTLƏR ───────────────────────────
# Azərbaycan əlifbası ə/ğ/ş/ı/ö/ü tələb edir — ReportLab-ın daxili Type1
# şriftləri bu hərfləri daşımır, ona görə mütləq TTF qeydiyyatdan keçir.
# Sistemə görə ilk tapılan tam ailə (adi + qalın + maili) götürülür.
FONT_FAMILIES = [
    (r"C:\Windows\Fonts\arial.ttf",
     r"C:\Windows\Fonts\arialbd.ttf",
     r"C:\Windows\Fonts\ariali.ttf"),
    ("/usr/share/fonts/truetype/msttcorefonts/Arial.ttf",
     "/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf",
     "/usr/share/fonts/truetype/msttcorefonts/Arial_Italic.ttf"),
    ("/Library/Fonts/Arial.ttf",
     "/Library/Fonts/Arial Bold.ttf",
     "/Library/Fonts/Arial Italic.ttf"),
    ("/System/Library/Fonts/Supplemental/Arial.ttf",
     "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
     "/System/Library/Fonts/Supplemental/Arial Italic.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"),
]


def _dejavu_from_matplotlib():
    """matplotlib layihənin asılılığıdır və DejaVu şriftlərini özü ilə gətirir."""
    try:
        import matplotlib
    except ImportError:
        return None
    d = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
    trio = (os.path.join(d, "DejaVuSans.ttf"),
            os.path.join(d, "DejaVuSans-Bold.ttf"),
            os.path.join(d, "DejaVuSans-Oblique.ttf"))
    return trio if all(os.path.exists(p) for p in trio) else None


def register_fonts():
    for trio in FONT_FAMILIES + [_dejavu_from_matplotlib() or ()]:
        if len(trio) == 3 and all(os.path.exists(p) for p in trio):
            pdfmetrics.registerFont(TTFont("Arial", trio[0]))
            pdfmetrics.registerFont(TTFont("Arial-Bold", trio[1]))
            pdfmetrics.registerFont(TTFont("Arial-Italic", trio[2]))
            registerFontFamily("Arial", normal="Arial", bold="Arial-Bold",
                               italic="Arial-Italic", boldItalic="Arial-Bold")
            return os.path.basename(trio[0])
    raise SystemExit(
        "Uyğun TTF şrift tapılmadı. Arial və ya DejaVu Sans quraşdırın "
        "(Linux: sudo apt install fonts-dejavu), yaxud FONT_FAMILIES siyahısına "
        "öz şriftinizin yolunu əlavə edin.")


FONT_USED = register_fonts()

# ─────────────────────────── LAYİHƏ PARAMETRLƏRİ ───────────────────────────
# Vahid həqiqət mənbəyi: 3D dizaynerin ixrac etdiyi lab_parametrleri.json.
PARAM_FILE = os.path.join(BASE, "lab_parametrleri.json")
try:
    with open(PARAM_FILE, encoding="utf-8") as fh:
        PRM = json.load(fh)
except FileNotFoundError:
    raise SystemExit(
        f"'{os.path.basename(PARAM_FILE)}' tapılmadı.\n"
        "3D dizayneri açın (3d/BASLAT.bat), 'Parametrlər' düyməsini basın və "
        "yüklənən faylı layihə qovluğuna qoyun.")

_room = PRM["otaq"]; _cap = PRM["tutum"]; _n = PRM["say"]
_lux = PRM["isiqlanma"]; _ac = PRM["akustika"]
_cool = PRM["soyutma"]; _el = PRM["elektrik"]; _eg = PRM["tahliye"]

ROOM_W, ROOM_D, ROOM_H = _room["en"], _room["uzunluq"], _room["hundurluk"]
AREA      = _room["sahe"]
SEATS     = _cap["is_yeri"]
CONCUR    = _cap["eyni_anda"]
A11Y_N    = _cap["elcatan"]
MIN_AREA  = _cap["min_sahe"]
DENSITY   = _cap["sixliq"]

LUX_AVG, LUX_MIN  = _lux["orta"], _lux["min"]
LUX_U0, LUX_PANELS = _lux["u0"], _lux["panel_sayi"]
LUX_LM            = _lux["panel_lm"]

RT60_BARE, RT60_CEIL, RT60_FULL = _ac["rt_bare"], _ac["rt_ceiling"], _ac["rt_full"]
RT60_LIMIT   = _ac["limit"]
CEIL_AREA    = _ac["tavan_sahesi"]
WALL_PANEL_A = _ac["divar_paneli"]
VOLUME       = _ac["hecm"]

COOL_BTU, AC_UNITS = _cool["btu"], _cool["kondisioner"]
KW_IT, KW_CALC, KW_LINE = _el["kw_it"], _el["kw_hesabi"], _el["kw_xett"]
SOCKETS, RJ45 = _el["rozetka"], _el["rj45"]
EXITS, DOOR_W, TRAVEL = _eg["cixis"], _eg["qapi_eni"], _eg["en_uzaq_m"]

# Avadanlıq sayları düzülüşdən çıxarılır — əl ilə saymağa ehtiyac qalmır.
N_STUDENT_PC = _n["monitor_telebe"]                     # pod iş yerləri
N_MONITOR    = _n["monitor_telebe"] + _n["gpu"]         # + AI/GPU stansiyası
N_KEYBOARD   = N_MONITOR + _n["teacher"] + _n["a11y"]   # müəllimin 2 monitoru 1 dəstdir
N_FREEZE_LIC = _n["monitor_telebe"] + _n["teacher"] + _n["a11y"]   # yalnız Windows iş yerləri
N_CHAIR      = _n["stul"]                               # əlçatan yerdə stul yoxdur (əlil arabası)
N_STOOL      = _n["taburet"]                            # IoT skamyası


def num(v, d=1):
    """Azərbaycan yazı qaydasında onluq ayırıcı vergüldür: 93,8 — 93.8 deyil."""
    return f"{v:.{d}f}".replace(".", ",")


# Mətndə təkrar-təkrar işlənən ölçülərin hazır sətir formaları
S_W, S_D, S_H = num(ROOM_W), num(ROOM_D), num(ROOM_H)
S_AREA   = num(AREA)
S_MINA   = num(MIN_AREA)
S_DENS   = num(DENSITY, 2)
S_U0     = num(LUX_U0, 2)
S_U0_REQ = num(_lux["u0_norma"], 2)
S_RT_B   = num(RT60_BARE, 2)
S_RT_C   = num(RT60_CEIL, 2)
S_RT_F   = num(RT60_FULL, 2)
S_LIMIT  = num(RT60_LIMIT, 2)
S_RT_X   = num(RT60_BARE / RT60_LIMIT)          # normanı neçə dəfə aşır
S_KWIT   = num(KW_IT)
S_KWCALC = num(KW_CALC)
S_KFACT  = num(_el["emsal"], 2)
S_DOOR   = num(DOOR_W, 2)
S_CEIL   = num(CEIL_AREA, 0)
S_VOL    = num(VOLUME, 0)
S_TRAVEL = num(TRAVEL, 0)
S_WORK_H = num(_lux["is_sethi_h"], 2)
S_MAINT  = num(_lux["istismar_emsali"], 2)

NAVY  = colors.HexColor("#243447"); BLUE = colors.HexColor("#2874a6")
LBLUE = colors.HexColor("#eaf2f8"); GOLD = colors.HexColor("#f9e79f")
GREY  = colors.HexColor("#7f8c8d"); LINE = colors.HexColor("#aab7b8")
ROSE  = colors.HexColor("#fdedec")

s_title = ParagraphStyle("t", fontName="Arial-Bold", fontSize=23, leading=29, textColor=NAVY, alignment=TA_CENTER)
s_sub   = ParagraphStyle("s", fontName="Arial", fontSize=12.5, leading=18, textColor=GREY, alignment=TA_CENTER)
s_h1    = ParagraphStyle("h1", fontName="Arial-Bold", fontSize=14.5, leading=19, textColor=NAVY, spaceBefore=15, spaceAfter=7)
s_h2    = ParagraphStyle("h2", fontName="Arial-Bold", fontSize=11.5, leading=15, textColor=BLUE, spaceBefore=10, spaceAfter=4)
s_body  = ParagraphStyle("b", fontName="Arial", fontSize=10.2, leading=14.6, alignment=TA_JUSTIFY, spaceAfter=5)
s_bul   = ParagraphStyle("bl", parent=s_body, leftIndent=13, bulletIndent=3, spaceAfter=2.5)
s_cell  = ParagraphStyle("c", fontName="Arial", fontSize=9.2, leading=12)
s_cellb = ParagraphStyle("cb", parent=s_cell, fontName="Arial-Bold")
s_cells = ParagraphStyle("cs", fontName="Arial", fontSize=8.6, leading=11.2)
s_note  = ParagraphStyle("n", fontName="Arial-Italic", fontSize=8.8, leading=11.8, textColor=GREY, spaceBefore=3)
s_src   = ParagraphStyle("src", fontName="Arial", fontSize=8.6, leading=11.5, textColor=GREY, spaceAfter=2.5)

def P(t, st=s_body): return Paragraph(t, st)
def B(t): return Paragraph("•  " + t, s_bul)
def money(n): return f"{n:,}".replace(",", " ")
def WH(t): return Paragraph(f"<font color='white'><b>{t}</b></font>", s_cellb)

def fitimg(path, width_cm=17.2):
    w, h = PILImage.open(path).size
    dw = width_cm * cm
    return Image(path, width=dw, height=dw * h / w)

BASE_TS = [("BACKGROUND", (0,0), (-1,0), NAVY), ("GRID", (0,0), (-1,-1), 0.5, LINE),
           ("VALIGN", (0,0), (-1,-1), "TOP"),
           ("TOPPADDING", (0,0), (-1,-1), 4.5), ("BOTTOMPADDING", (0,0), (-1,-1), 4.5)]

def mktable(header, rows, widths, small=False):
    cs = s_cells if small else s_cell
    data = [[WH(h) for h in header]] + [[Paragraph(c, cs) for c in r] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle(BASE_TS + [("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LBLUE])]))
    return t

# ─────────────────────────── AVADANLIQ ───────────────────────────
# Sətir formatı: (id, ad, spesifikasiya, say, vahid qiymət).
# id ssenari hesablamalarında istifadə olunur — beləliklə ssenarinin izahı ilə
# rəqəmi bir-birindən ayrı düşə bilmir.
EQUIP = [
 ("Son nöqtələr (iş yerləri)", "9.1. Son nöqtələr — tələbə və müəllim iş yerləri", [
    ("student_pc", "Tələbə kompüteri", "Core i5-14400 / Ryzen 5 7600, 16 GB DDR5, 512 GB NVMe, 3 il zəmanət", N_STUDENT_PC, 1350),
    ("monitor", "Monitor 24\"", f"IPS, Full HD, hündürlüyü tənzimlənən ayaq — {N_STUDENT_PC} tələbə iş yeri + AI/GPU stansiyası", N_MONITOR, 300),
    ("kbmouse", "Klaviatura + siçan", "USB dəst — hər iş yerinə (müəllimin iki monitoru bir dəstdir)", N_KEYBOARD, 40),
    ("teacher_pc", "Müəllim stansiyası", "Core i7 / Ryzen 7, 32 GB RAM, 1 TB SSD, 2× monitor", 1, 2600),
    ("a11y_desk", "<b>Əlçatan iş yeri</b>", "Elektrik mühərriki ilə 70–120 sm tənzimlənən masa + PC + monitor. "
     "Əlil arabası üçün Ø1,5 m manevr sahəsi (bax: bölmə 13)", A11Y_N, 2640)]),
 ("Server və hesablama", "9.2. Server və hesablama infrastrukturu", [
    ("vm_server", "Virtuallaşdırma serveri", "2× CPU 16 nüvə, <b>256 GB ECC RAM</b>, 4 TB NVMe RAID (bax: 7.1)", 1, 11500),
    ("gpu_station", "AI / GPU stansiyası", "RTX 5070 Ti 16 GB, 64 GB RAM, Ubuntu LTS", 1, 6200),
    ("nas", "Yedəkləmə (NAS)", "4-bay, 4× 8 TB RAID5 (≈24 TB faydalı)", 1, 3400)]),
 ("Şəbəkə", "9.3. Şəbəkə avadanlığı", [
    ("switch", "Nüvə switch 48-port", "Managed L2+/L3, Gigabit, PoE+, VLAN", 1, 1400),
    ("firewall", "Firewall / Router", "NGFW, VPN, məzmun filtri", 1, 1100),
    ("wifi", "Wi-Fi 6 Access Point", "Tavan montajı", 2, 280),
    ("rack", "Rack şkaf 19\" 18U", "Patch panel, kabel təşkilatçıları ilə", 1, 800),
    ("cabling", "Struktur kabel sistemi", f"CAT6, {RJ45} şəbəkə portu + {SOCKETS} rozetka nöqtəsi, montaj daxil", 1, 3600),
    ("cisco_kit", "Cisco praktika dəsti", "2× ISR router + 2× Catalyst switch — CCNA praktikası", 1, 3200)]),
 ("Təqdimat və əməkdaşlıq", "9.4. Təqdimat və əməkdaşlıq", [
    ("panel86", "İnteraktiv panel 86\"", "4K, sensor, Android + OPS modul", 1, 5200),
    ("team_screen", "Komanda ekranı 55\"", "4K, BYOD zonası üçün", 1, 1100),
    ("vc_kit", "Videokonfrans dəsti", "4K kamera + mikrofon massivi + akustika", 1, 900)]),
 ("IoT və prototipləmə", "9.5. IoT, robototexnika və prototipləmə", [
    ("arduino", "Arduino dəsti", "Starter kit: sensor, motor, displey modulları", 10, 130),
    ("rpi", "Raspberry Pi 5", "8 GB, korpus, kamera modulu ilə", 6, 380),
    ("electronics_kit", "Elektronika iş dəsti", "Lehimləmə stansiyası, multimetr, ossiloskop", 1, 2200),
    ("printer3d", "3D printer", "FDM, 220×220 mm, qapalı korpus", 1, 1700)]),
 ("Mebel", "9.6. Mebel", [
    ("pod", "Pod modulu (4 yerlik)", "Kabel kanallı, hərəkət edən klaster masa", _n["pod"], 950),
    ("chair", "Ergonomik stul", f"Bel dayaqlı, tənzimlənən hündürlük, təkərli — {_n['pod']*4} pod + "
     f"{_n['byod']*6} BYOD + müəllim + AI/GPU. Əlçatan iş yerlərində stul yoxdur (əlil arabası girir)", N_CHAIR, 150),
    ("stool", "Laboratoriya taburetti", "Ayaq halqalı, hündür — IoT skamyası üçün", N_STOOL, 120),
    ("byod_table", "BYOD / komanda masası", "Oval, elektrik və USB-C çıxışları ilə", _n["byod"], 1400),
    ("iot_bench", "IoT skamyası", "Antistatik səth, alət saxlanma sistemi, 3 m", _n["iot"], 1600),
    ("cabinet", "Şkaf və rəf sistemi", "Kilidli", _n["cabinet"], 900)]),
 ("Elektrik və iqlim", "9.7. Elektrik, iqlim və təhlükəsizlik", [
    ("ups_server", "UPS — server", "6 kVA online, rack tipli, ≥15 dəq", 1, 2800),
    ("ups_desk", "UPS — iş yerləri", "Xətt filtrləri və qrup UPS-lər", 1, 1200),
    ("ac", "Kondisioner", f"24000 BTU inverter — soyutma yükü {money(COOL_BTU)} BTU/s", AC_UNITS, 1400),
    ("power", "Elektrik montajı", f"<b>{KW_LINE} kVt</b> ayrılmış xətt (hesabi yük {S_KWCALC} kVt), "
     "paylayıcı lövhə, torpaqlama, rozetka şəbəkəsi", 1, 2800),
    ("security", "Təhlükəsizlik sistemi", "2× IP kamera, kartla giriş nəzarəti, yanğın datçiki", 1, 1600)]),
 ("Proqram və idarəetmə", "9.8. Proqram təminatı və laboratoriya idarəetməsi", [
    ("freeze", "Sistem bərpa proqramı", f"Deep Freeze tipli ({N_FREEZE_LIC} lisenziya — Windows iş yerləri)", 1, 1900),
    ("analytics", "İstifadə analitikası", "3 illik abunə", 1, 1600),
    ("licenses", "Kommersiya lisenziyaları", "Ehtiyat büdcə", 1, 2500),
    ("identity", "Kimlik və davamlılıq sistemi", "AD/LDAP, şəbəkə profilləri, JupyterHub, Proxmox, VPN (bölmə 7.1)", 1, 3000)]),
 ("Ehtiyat hissələr", "9.9. Ehtiyat hissələr və istismar dəsti", [
    ("spares", "Ehtiyat komplekt", "1× ehtiyat PC, 1× monitor, SSD/RAM, kabellər", 1, 2400),
    ("consumables", "İstehlak materialları", "Filament, toner, kabel, komponentlər — 1 illik", 1, 1200)]),
]

RESERVE_RATE = 0.08          # gözlənilməz xərclər üçün ehtiyat

ITEMS = {rid: (ad, say, qiy) for _, _, rows in EQUIP for rid, ad, _spec, say, qiy in rows}


def cost(rid):
    _ad, say, qiy = ITEMS[rid]
    return say * qiy


def with_reserve(base):
    """Ehtiyat həmişə cari ara cəmdən hesablanır — ssenari dəyişəndə də düzgün qalır."""
    return base + int(round(base * RESERVE_RATE, -2))


totals = {k: sum(say*qiy for _rid, _ad, _sp, say, qiy in rows) for k, _t, rows in EQUIP}
grand   = sum(totals.values())
reserve = int(round(grand*RESERVE_RATE, -2))
total_b = grand + reserve

# Ssenarilər id ilə təsvir olunur; həm mətn, həm rəqəm eyni siyahıdan çıxarılır.
SCEN_A_DROP = ["gpu_station", "cisco_kit", "nas", "analytics", "team_screen", "electronics_kit"]
SCEN_C_ADD  = [("Əlavə AI / GPU stansiyası", 6200),
               ("VR / AR tədris dəsti", 4600),
               ("İkinci Cisco praktika dəsti", 3200)]

sA = with_reserve(grand - sum(cost(r) for r in SCEN_A_DROP))
sC = with_reserve(grand + sum(v for _n_, v in SCEN_C_ADD))

OPEX_5Y = 9000 + 12500 + 8000 + 6000 + 18000
tco       = total_b + OPEX_5Y
capex_seat = int(round(total_b/SEATS, -1))          # kapital xərci / iş yeri
tco_seat   = int(round(tco/SEATS, -1))              # 5 illik TCO / iş yeri
tco_seat_y = int(round(tco/SEATS/5, -1))            # 5 illik TCO / iş yeri / il

# ── Büdcədən KƏNAR işlər (ayrıca qərar tələb edir) ──
ACOUSTIC_COST = 3300     # akustik asma tavan
QUIET_RACK    = 1600     # səssiz (akustik) rack şkaf
OUT_OF_SCOPE  = ACOUSTIC_COST + QUIET_RACK
total_full    = total_b + OUT_OF_SCOPE

# ─────────────────────── MÜHƏNDİS AUDİTİ ───────────────────────
# Layihə paketi altı müstəqil lens üzrə (pedaqogika, avadanlıq, təhlükəsizlik,
# əlçatanlıq, istismar, təqdimat) yenidən nəzərdən keçirilib. Aşağıdakılar
# yoxlamadan keçmiş — yəni sənədin heç bir yerində olmayan — boşluqlardır.
# Qruplar: A–D mərhələ 1-də mütləq, E ikinci mərhələyə salına bilər.
AUDIT = [
 ("A", "Təhlükəsizlik və otaq mühiti", "kritik", [
   ("Mexaniki havalandırma, CO₂ nəzarəti və lokal tüstü sorucusu",
    "≥70 % rekuperatorlu balanslaşdırılmış təchizat–çıxarış qurğusu 800–900 m³/saat "
    f"({CONCUR} nəfər × 25 m³/saat), ePM1 filtr, 2× CO₂ datçiki (900 ppm) — 9 000; "
    "lehimləmə üçün çevik qollu HEPA + aktiv kömür sorucu — 1 500; 3D printerə "
    "HEPA13 filtrli korpus və ya bayıra kanal — 700.<br/>"
    "<b>Kondisioner havanı soyudur, təzələmir.</b> 262,5 m³ otaqda 33 nəfərlə CO₂ "
    "ikinci dərs saatında 3000 ppm-i keçir; 350 °C lehim ucu və FDM printer "
    "tələbənin tənəffüs zonasından 0,8 m aralıda işləyir.", 11200),
   ("30 mA differensial müdafiə (RCD/RCBO), ESD torpaqlama və qəza dayandırma",
    "Sənəddə yalnız avtomat açar (MCB) var — o, artıq cərəyandan qoruyur, "
    "<b>insanı elektrik zərbəsindən qorumur</b>. Bütün rozetka qruplarına 30 mA RCBO, "
    "lehimləmə xəttinə 10 mA (1 200); torpaqlanmış ESD dəsti — 2 nöqtə (1 MΩ), "
    "6 bilək bandı, illik müqavimət ölçməsi (450); skamya və printer qidasını kəsən "
    "kontaktor + qapı yanında qırmızı göbələk düyməsi (700); ossiloskop üçün "
    "ayırıcı transformator (250).", 2600),
   ("Yanğınsöndürmə, ilk yardım, kimyəvi saxlama və lavabo",
    "Yeganə yanğın vasitəsi CO₂-dir — bərk yanan materiala (filament, kağız, kabel) "
    "təsirsizdir. 6 kq ABC toz odsöndürən + yanğın örtüyü (240); LiPo yanmaz "
    "doldurma qutusu (150); izopropil/flus üçün ventilyasiyalı metal şkaf (450); "
    "ilk yardım çantası + 2× göz yuma (370); 3D printer üzərində istilik/tüstü "
    "datçiki (300). <b>Otaqda su nöqtəsi yoxdur</b> — lehim və flusdan sonra "
    "əl yumaq üçün lavabo (900).", 2410),
   ("Təcili işıqlandırma, ÇIXIŞ nişanı, fail-safe kilid və vizual xəbərdarlıq",
    "Otaqda avariya işıqlandırması yoxdur, üstəlik işıq keçirməyən jalüz tələb "
    "olunur — cərəyan kəsiləndə 33 nəfər tam qaranlıqda qalır. Tək qapıda kartla "
    "giriş var, yanğın siqnalı ilə açılma yazılmayıb. 3× avtonom armatur (≥1 lx, "
    "1 saat) + işıqlı ÇIXIŞ nişanı + tahliyə sxemi (750); fail-safe elektromaqnit "
    "kilid + daxildən avariya düyməsi (350); 2× işıqlı yanğın mayakı və vibro-çağırış "
    "— səsi eşitməyən tələbə üçün (500).", 1600),
 ]),
 ("B", "Praktikanın işləməsi üçün avadanlıq", "kritik", [
   ("Aparat və şəbəkə praktikası dəsti",
    "Sənəd 2-ci kursa CompTIA A+, 3-cü kursa CCNA hədəfləyir, lakin sökülüb-yığıla "
    "bilən bir dənə də cihaz və bir dənə də krimp aləti yoxdur; tələbə kompüterləri "
    "3 il zəmanətlidir — açmaq zəmanəti pozur.<br/>"
    "6× açıq korpuslu praktika PC-si (4 500 — <b>alternativ: universitetin silinmiş "
    "PC-lərindən 0 AZN</b>); 2× işlənmiş rack server, IPMI və RAID ilə (2 800); "
    "9–12U praktika rack-ı (700); şəbəkə terminasiya dəsti — 6× krimp, 2× punch-down, "
    "2× kabel testeri, 305 m CAT6, 500 RJ-45, 6U divar rack-ı (2 000); POST kartı, "
    "qidalandırıcı testeri, 6× alət dəsti, rollover kabelləri (800).", 10800),
   ("Kommutasiya (patch) kordları",
    f"{RJ45} port, 28 kompüter və 25 monitor quraşdırılır, amma <b>qoşulmur</b> — "
    "patch kord heç bir sətirdə yoxdur (mövcud “patch panel”dir). "
    f"{RJ45}× CAT6 0,25–0,5 m rack tərəfinə + 35× CAT6 2–3 m iş yeri tərəfinə.<br/>"
    "Kabel sertifikat testi üçün ayrıca vəsait lazım deyil — mövcud struktur kabel "
    "sətrinin spesifikasiyasına “Fluke DSX tipli sertifikat testi və protokolu daxil” "
    "yazılsın və qəbul aktının şərti edilsin.", 400),
   ("IoT skamyasının ölçüyə uyğun təchizatı",
    "6 nəfərlik skamyaya 1 lehimləmə dəsti düşür: +3 lehimləmə stansiyası (660), "
    "+5 multimetr (450), 4× USB-ossiloskop (900). Qurğuşunsuz lehim (Sn99,3Cu0,7) "
    "məcburi olsun.", 2010),
   ("Etiketləmə və inventar dəsti",
    "Sənaye etiket printeri və lentlər, kabel/port etiketləri, 38 iş yerinə QR "
    "nişanı, USB barkod oxuyucu. Etiketsiz laboratoriya bir ildə idarəolunmaz olur.", 1800),
   ("Şəbəkə lazerli MFP",
    "Otaq planında və 5-ci bölmədə var, 9-cu bölmədəki spesifikasiyada yox idi. "
    "A4, ikitərəfli çap, ADF skaner, AD hesabı ilə çap.", 800),
 ]),
 ("C", "Əlçatanlıq və erqonomika", "kritik", [
   ("Eşitmə məhdudiyyəti üçün həll",
    "Təqdimat zonasına rəqəmsal FM / induksiya döngəsi və mühazirələrdə avtomatik "
    "subtitr. Bura akustik asma tavanın əsas büdcəyə keçirilməsi arqumenti də "
    "daxildir — o, yalnız rahatlıq deyil, eşitmə əlçatanlığı tələbidir.", 2200),
   ("IoT skamyasının və bir pod yerinin əlil arabası üçün açılması",
    "Skamyanın 1,05 m-lik bölməsi konsol tipli və 0,70–1,05 m tənzimlənən olsun, "
    "alət relsi ≤1,20 m-ə ensin, ESD torpaqlama nöqtəsi aşağı gətirilsin; bir pod "
    "iş yerində diz boşluğu ≥68 sm təmin edilsin.", 3200),
   ("Rack, şkaf və açarların çatma hündürlüyü",
    "Cisco praktika dəsti və məşq patch paneli istismar rack-ından ayrılıb təkərli "
    "12U açıq rack-a köçürülsün, aktiv hissə 0,40–1,20 m zolağında qalsın, "
    "qarşısında 1,50 m boş döşəmə verilsin.", 1550),
   ("Tahliyə və naviqasiya",
    "Otaq yer səviyyəsindən yuxarıdadırsa — pilləkən qəfəsində sığınacaq zonası, "
    "tahliyə kreslosu və çağırış rabitəsi; relyefli və Brayl otaq nişanı, "
    "kontrastı ≥70 % olan zona işarələri.", 2050),
   ("Monitor qolları və işıq keyfiyyəti tələbləri",
    "24× monitor qolu — baxış məsafəsini 45–50 sm-dən 60 sm-ə çıxarır (2 160). "
    "İşıqlandırma spesifikasiyasına UGR ≤19, Ra ≥80, 4000 K və flikersizlik tələbi "
    "əlavə olunsun (xərcsiz, satınalma şərtidir).", 2160),
 ]),
 ("D", "Tədris məzmunu və istismar", "kritik", [
   ("Laboratoriya işləri üzrə metodik göstərişlər",
    "7 istiqamətin hər biri üçün ən azı 4–5 laboratoriya işi: məqsəd, istifadə "
    "olunan avadanlıq (inventar № ilə), addımlar, gözlənilən nəticə, qiymətləndirmə "
    "meyarı. Pilot mərhələsinin məcburi nəticəsi olmalıdır — avadanlıq gəlir, "
    "metodika gəlmirsə, otaq boş qalır.", 3000),
   ("İnventar reyestri və illik siyahıyaalma",
    "Nömrələmə sxemi (ITLAB-PC-01…), hər vahidə davamlı QR etiket, reyestrdə "
    "seriya №, alış tarixi, zəmanətin bitmə tarixi, yer və məsul şəxs.", 800),
   ("Nasazlıq bildirişi kanalı və dəstək SLA-sı",
    "Hər iş yerində QR etiket → sadə bildiriş forması (GLPI / osTicket, lisenziya "
    "xərci yoxdur); nasazlığın 24 saat ərzində aradan qaldırılması öhdəliyi.", 600),
   ("Təhvil-təslim paketi — “bir nəfər riski”nin aradan qaldırılması",
    "Ödənişin şərti kimi tələb olunsun: icra olunmuş şəbəkə sxemi, VLAN/IP planı, "
    "patch-panel port cədvəli, rack elevasiyası, kabel sertifikat protokolu, "
    "işıqlanma və akustika ölçmə protokolu, parolların təhlükəsiz saxlanması.", 0),
 ]),
 ("E", "Tövsiyə olunan genişləndirmə", "vacib", [
   ("Robototexnika və dron dəsti",
    "Zonanın adı var, avadanlığı yoxdur: 6× proqramlaşdırıla bilən mobil robot "
    "platforması, poliqon xalçası, 4× pərqoruyuculu daxili dron.", 4230),
   ("Görmə əlçatanlığı",
    "Şəbəkə praktikumunun ekran oxuyucusu ilə keçilən alternativ marşrutu (real "
    "avadanlıqda CLI — xərcsiz), tələb üzrə köməkçi texnologiya dəsti, "
    "rəng-kor uyğun tədris materialı qaydası.", 4950),
   ("Sakit guşə və işıq zonalaması",
    "Akustik arakəsmə ilə bir tək iş yeri; 15 panelin 3 ayrıca idarə olunan "
    "zonaya bölünməsi (DALI / 0-10 V) və fərdi masa lampaları.", 4250),
   ("Kibertəhlükəsizlik poliqonu",
    "Server yaddaşının 256 → 512 GB artırılması və internetə çıxışı olmayan "
    "6-cı “poliqon” VLAN-ı. Hazırkı tutumla bütün qrup eyni anda məşq edə bilmir.", 3000),
   ("BYOD və əməkdaşlıq zonasının qoşqusu",
    "Simsiz ekran ötürücü, 6× USB-C adapter və 2× dok, 26× mikrofonlu qulaqlıq, "
    "2× mobil ağ lövhə.", 2700),
   ("Sərf materialı və zəmanət izləmə fondu",
    "Minimum ehtiyat həddi və avtomatik sifariş qaydası (filament, toner, lehim, "
    "komponent), ehtiyat komplektin bərpası, zəmanət müddətlərinin izlənməsi — "
    "5 illik fond.", 6000),
   ("Layihə şkafçıqları və ağ lövhələr",
    "12× nömrələnmiş kilidli şkafça (davam edən işlər üçün), 2× açıq rəf, "
    "təkərli alət arabası, 4× hərəkət edən ikitərəfli ağ lövhə.", 3430),
   ("Rezervasiya və məsuliyyət qaydası",
    "GPU stansiyası, 3D printer, Cisco dəsti və elektronika dəsti üçün resurs "
    "təqvimi; avadanlığın verilməsi-qaytarılması jurnalı və zədə/itki qaydası.", 900),
 ]),
]

AUDIT_GROUP_TOTAL = {g: sum(c for _n, _d, c in rows) for g, _t, _s, rows in AUDIT}
AUDIT_CRIT = sum(v for g, v in AUDIT_GROUP_TOTAL.items() if g in "ABCD")
AUDIT_OPT  = AUDIT_GROUP_TOTAL["E"]
AUDIT_ALL  = AUDIT_CRIT + AUDIT_OPT
# İşə düşən laboratoriya = Ssenari B + büdcədən kənar işlər + kritik əlavələr
total_ready = total_b + OUT_OF_SCOPE + AUDIT_CRIT
total_max   = total_ready + AUDIT_OPT

story = []

# ═══════════════ ÜZ QABIĞI ═══════════════
story += [Spacer(1, 3.4*cm),
          P("İNFORMASİYA TEXNOLOGİYALARI<br/>TƏDRİS LABORATORİYASI", s_title),
          Spacer(1, 0.5*cm), HRFlowable(width="42%", thickness=2, color=BLUE, hAlign="CENTER"),
          Spacer(1, 0.5*cm),
          P("Mühəndis analizi, texniki layihə və satınalma sənədi", s_sub), Spacer(1, 0.3*cm),
          P(f"1–4-cü kurs tələbələri üçün  •  {SEATS} iş yeri  •  {S_AREA} m²", s_sub),
          Spacer(1, 1.4*cm)]
ZONE_TEXT = (f"{_n['pod']*4} pod + {_n['byod']*6} BYOD + {_n['iot']*6} IoT + "
             f"{A11Y_N} əlçatan")
cover = [["Sənədin növü", "Texniki-iqtisadi əsaslandırma və avadanlıq spesifikasiyası"],
         ["Otaq", f"{S_W} × {S_D} × {S_H} m = {S_AREA} m² (ölçü sabit deyil — bax: bölmə 5)"],
         ["Tutum", f"{ZONE_TEXT} = {SEATS} yer / eyni anda {CONCUR} nəfər"],
         ["Təxmini büdcə", f"{money(total_b)} AZN  (5 illik TCO: {money(tco)} AZN)"],
         ["Büdcədən kənar", f"Akustik işləmə və səssiz rack — {money(OUT_OF_SCOPE)} AZN (bölmə 12)"],
         ["İcra müddəti", "11–16 həftə"],
         ["Uyğunluq", "AR Süni İntellekt Strategiyası 2025–2028 (Sərəncam № 530)"],
         ["Tarix", "Avqust 2026"]]
ct = Table([[Paragraph(f"<b>{a}</b>", s_cell), Paragraph(b, s_cell)] for a,b in cover],
           colWidths=[4.2*cm, 11.8*cm], hAlign="CENTER")
ct.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.5,LINE),
    ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white,LBLUE]), ("VALIGN",(0,0),(-1,-1),"TOP"),
    ("TOPPADDING",(0,0),(-1,-1),5), ("BOTTOMPADDING",(0,0),(-1,-1),5)]))
story += [ct, PageBreak()]

# ═══════════════ 1. İCMAL ═══════════════
story.append(P("1. İCMAL", s_h1))
story.append(P(
    "Bu sənəd universitetin informasiya texnologiyaları tədris laboratoriyasının yaradılması "
    "üçün hazırlanıb. Avadanlıq siyahısından əlavə bazar analizi, mühəndis hesablamaları "
    "(işıqlanma, akustika, soyutma, elektrik, tahliyə, əlçatanlıq), üç büdcə ssenarisi, "
    "5 illik sahiblik dəyəri, idarəetmə modeli və uğur meyarlarını əhatə edir."))
story.append(P(
    f"<b>Əsas qərar:</b> laboratoriya eyni tipli stolüstü kompüterlərdən ibarət ənənəvi sinif "
    f"kimi deyil, <b>hibrid model</b> üzərində qurulur — {_n['pod']*4} sabit pod iş yeri, "
    f"{A11Y_N} əlçatan iş yeri, virtuallaşdırma serveri, bulud platformaları və BYOD zonasının "
    f"birləşməsi."))
story.append(P("Əsas göstəricilər", s_h2))
kpi = [["Ümumi tutum", f"{SEATS} yer ({ZONE_TEXT})", f"Eyni anda {CONCUR} nəfər"],
       ["Sahə və sıxlıq", f"{S_AREA} m² — {S_DENS} m²/iş yeri", "Norma daxilində (≥2,2)"],
       ["İşıqlanma", f"{LUX_AVG} lx orta, U<sub>0</sub> {S_U0}", "Norma ≥400 lx — ödənir"],
       ["Akustika (RT60)", f"{S_RT_B} s işlənməmiş",
        f"Norma ≤{S_LIMIT} s — <b>ödənmir</b>"],
       ["Elektrik", f"{KW_LINE} kVt xətt (hesabi {S_KWCALC} kVt)", "Standart nominal, ≥15 % ehtiyat"],
       ["Kapital xərci", f"{money(total_b)} AZN", f"Ssenari B — ≈ {money(capex_seat)} AZN / iş yeri"],
       ["5 illik TCO", f"{money(tco)} AZN", f"≈ {money(tco_seat)} AZN / iş yeri (5 il)"]]
story.append(mktable(["Göstərici", "Dəyər", "Qeyd"], kpi, [4.0*cm, 7.4*cm, 5.8*cm]))
story.append(P(
    f"<b>Diqqət:</b> akustik göstərici normanı ödəmir. Səbəb və həll yolu 12-ci bölmədə "
    f"verilib; müvafiq iş (akustik tavan + səssiz rack, cəmi {money(OUT_OF_SCOPE)} AZN) büdcəyə "
    f"<b>daxil edilməyib</b> və ayrıca qərar tələb edir. Hər ikisi görülərsə, tam kapital "
    f"xərci <b>{money(total_full)} AZN</b> olur.", s_note))

# ═══════════════ 2. STRATEJİ ═══════════════
story.append(P("2. STRATEJİ ƏSASLANDIRMA", s_h1))
story.append(P("Layihə qüvvədə olan strateji sənədlərə birbaşa uyğundur:"))
story.append(B("<b>AR-in 2025–2028-ci illər üçün Süni İntellekt Strategiyası</b> (Prezidentin "
               "19.03.2025 tarixli 530 nömrəli Sərəncamı) — infrastrukturun əlçatanlığı və "
               "<b>ixtisaslı kadr potensialının gücləndirilməsi</b> elan olunmuş məqsədlərdəndir."))
story.append(B("<b>Rəqəmsal İnkişaf Şurası</b> — Prezidentin 27.02.2026 tarixli sərəncamı ilə yaradılıb."))
story.append(B("<b>Sahə üzrə hərəkat:</b> ATU-da Data-analitika və Süni İntellekt Laboratoriyası "
               "açılıb; Mingəçevir, Naxçıvan və Sumqayıt universitetlərini əhatə edən regional "
               "proqramlar icra olunur. Müasir İT laboratoriyası artıq minimum tələbdir."))
story.append(PageBreak())

# ═══════════════ 3. BAZAR ANALİZİ ═══════════════
story.append(P("3. BAZAR ANALİZİ: UNİVERSİTET LABORATORİYALARI HANSI VƏZİYYƏTDƏDİR", s_h1))
story.append(P("Beynəlxalq təcrübə göstərir ki, universitet kompüter laboratoriyaları eyni dörd "
                "problemdən əziyyət çəkir. Layihə bu problemləri əvvəlcədən həll edir."))
probs = [
 ["<b>1. Boş qalan laboratoriyalar</b>",
  "Tələbələr öz noutbuklarına üstünlük verir; avadanlığa pul xərclənir, otaq boş qalır.",
  "BYOD zonası + 24/7 çıxış + istifadə statistikasının ölçülməsi"],
 ["<b>2. Avadanlığın köhnəlməsi</b>",
  "Dəstəklənməyən köhnə sistem təhlükəsizlik riskidir; yeniləmə çatdırılmır.",
  "Yüngül sistem imici, mərhələli yeniləmə, büdcədə illik ehtiyat"],
 ["<b>3. Sənaye ilə uyğunsuzluq</b>",
  "Məhdud praktika → məzunların bacarığı sənayenin gözləntisindən geri qalır.",
  "Sertifikat proqramlarına uyğunlaşdırılmış tədris (CCNA, CompTIA, AWS, Azure)"],
 ["<b>4. Sərt sıra düzülüşü</b>",
  "Yalnız fərdi işə imkan verir; komanda layihələri mümkün olmur.",
  "Pod (klaster) düzülüşü, hərəkət edən mebel — \"active learning\" modeli"]]
story.append(mktable(["Problem", "Nəyə görə yaranır", "Bu layihədə həlli"], probs,
                     [3.5*cm, 7.0*cm, 6.7*cm], small=True))
story.append(P("2026-cı ilin əsas meylləri", s_h2))
for x in ["<b>Hibrid çatdırılma:</b> uğurlu laboratoriyalar vahid modelə arxalanmır — VDI, "
          "nazik klient və stolüstü PC qatlar halında birləşdirilir",
          "<b>Çevik məkan:</b> modul mebel, tez yenidən qurulan düzülüş, bol elektrik çıxışı",
          "<b>Analitika ilə idarəetmə:</b> istifadə statistikası əsasında optimallaşdırma",
          "<b>BYOD standartdır:</b> laboratoriya öz cihazını gətirən tələbəni də dəstəkləməlidir",
          "<b>Əlçatanlıq:</b> universal dizayn artıq layihənin ayrılmaz hissəsidir"]:
    story.append(B(x))

# ═══════════════ 4. DİZAYN PRİNSİPLƏRİ ═══════════════
story.append(P("4. DİZAYN PRİNSİPLƏRİ", s_h1))
princ = [["1","Hibrid çatdırılma","Bir tip avadanlığa bağlanmamaq: fiziki PC + VM + bulud + BYOD"],
         ["2","Çeviklik","Pod düzülüşü və hərəkət edən mebel — otaq yenidən qurula bilir"],
         ["3","Ölçülə bilənlik","İstifadə, lisenziya, enerji göstəriciləri toplanır"],
         ["4","Sənaye uyğunluğu","Avadanlıq tanınmış sertifikatların tələblərinə uyğun seçilir"],
         ["5","Universal dizayn","Əlçatan iş yerləri və manevr sahəsi layihənin bir hissəsidir"],
         ["6","Mərhələli inkişaf","Arxitektura sonrakı büdcələrdə genişləndirilə bilir"],
         ["7","Aşağı istismar xərci","Açıq mənbəli lisenziyalar, imic bərpası ilə dəstək yükünün azaldılması"]]
story.append(mktable(["№","Prinsip","Praktiki mənası"], princ, [0.9*cm, 4.0*cm, 12.3*cm]))
story.append(PageBreak())

# ═══════════════ 5. KONSEPSİYA VƏ ZONALAR ═══════════════
story.append(P("5. KONSEPSİYA, ZONALAR VƏ OTAQ ÖLÇÜSÜ", s_h1))
zones = [
 ["<b>Tədris zonası</b>",f"{_n['pod']*4} yer",f"{_n['pod']} pod × 4 iş yeri. Pod düzülüşü müəllimə hər "
  "tələbənin ekranına fiziki çıxış verir. Hər iş yerində PC, 24\" monitor, 2× RJ-45, 4× rozetka, USB-C."],
 ["<b>Əlçatan iş yerləri</b>",f"{A11Y_N} yer","Hündürlüyü 70–120 sm tənzimlənən masa, Ø1,5 m manevr "
  "dairəsi, sərbəst yanaşma. Tədris zonası ilə eyni şəbəkə və proqram mühiti."],
 ["<b>BYOD / layihə zonası</b>",f"{_n['byod']*6} yer","Elektrik, şəbəkə və 55\" komanda ekranı ilə təchiz olunmuş masa."],
 ["<b>IoT / robototexnika</b>",f"{_n['iot']*6} yer","Antistatik skamya (taburetlərlə): Arduino, "
  "Raspberry Pi, sensorlar, lehimləmə stansiyası, ossiloskop."],
 ["<b>Təqdimat zonası</b>","1 yer","86\" interaktiv panel və müəllim stansiyası; Veyon ilə ekran ötürmə."],
 ["<b>Server və şəbəkə</b>","—","19\" rack: virtuallaşdırma serveri, switch, router, patch panel, UPS, NAS."],
 ["<b>Prototipləmə</b>","—","3D printer və lazerli MFP."]]
story.append(mktable(["Zona","Tutum","Təyinat"], zones, [4.1*cm, 1.7*cm, 11.4*cm], small=True))

story.append(P("Otaq ölçüsünün seçilməsi", s_h2))
story.append(P(
    f"<b>Otağın ölçüsü sabit deyil — tələbdən çıxarılır.</b> Sabit iş yerləri üçün 2,30 m²/yer, "
    f"növbə ilə istifadə olunan çevik yerlər üçün 1,60 m²/yer, hər əlçatan yerə əlavə 1,20 m² "
    f"manevr sahəsi götürülür. {SEATS} iş yeri üçün tələb olunan minimum sahə <b>{S_MINA} m²</b>-dir."))
sizes = [["24 (yalnız podlar)","55,2 m²","≈ 8,0 × 7,0"],
         ["30 (pod + BYOD)","74,4 m²","≈ 10,5 × 7,0"],
         [f"<b>{SEATS} (layihə variantı)</b>",f"<b>{S_MINA} m²</b>",f"<b>{S_W} × {S_D}</b>"],
         ["44 (genişləndirilmiş)","99,8 m²","≈ 13,5 × 7,5"]]
story.append(mktable(["İş yeri sayı","Tələb olunan minimum sahə","Tövsiyə olunan ölçü (m)"],
                     sizes, [5.0*cm, 6.0*cm, 6.2*cm]))
story.append(P(
    f"Layihədə <b>{S_W} × {S_D} m = {S_AREA} m²</b> götürülüb — tələb olunan minimumdan "
    f"{num(AREA-MIN_AREA)} m² çoxdur. Bu ehtiyat sıraların arasında 1,40 m keçid yolu və əlçatan "
    f"iş yerlərinin manevr dairəsini təmin edir. Sıxlıq <b>{S_DENS} m²/iş yeri</b>-dir. "
    f"Başqa ölçülü otaq ayrılarsa, 3D dizayner proqramı bütün göstəriciləri yenidən hesablayır."))
story.append(PageBreak())

# ═══════════════ 6. OTAQ PLANI ═══════════════
story.append(P("6. OTAQ PLANI", s_h1))
story.append(fitimg(os.path.join(BASE, "otaq_plani.png")))
story.append(P(
    "Düzülüşün məntiqi: server zonası və interaktiv panel ön divarda, tələbə podları mərkəzdə, "
    "əlçatan iş yerləri keçid yoluna birbaşa çıxışı olan sağ zolaqda, BYOD zonası girişə yaxın, "
    "IoT skamyası arxa divarda. Pəncərələr sol divardadır — monitorlara perpendikulyar düşən "
    "işıq ekranda parıltı yaratmır, bu şüurlu layihə qərarıdır."))

story.append(PageBreak())
# ═══════════════ 7. TEXNİKİ ARXİTEKTURA ═══════════════
story.append(P("7. TEXNİKİ ARXİTEKTURA", s_h1))
story.append(fitimg(os.path.join(BASE, "texniki_arxitektura.png"), 15.6))
story.append(P("Şəbəkə beş VLAN-a bölünür — bu, həm təhlükəsizlik tədbiri, həm tədris vasitəsidir. "
               "IoT cihazları ayrıca VLAN-da izolyasiya olunur."))

story.append(PageBreak())
# ═══════════════ 7.1 DAVAMLILIQ ═══════════════
story.append(P("7.1. TƏLƏBƏNİN İŞ MÜHİTİNİN DAVAMLILIĞI", s_h1))
story.append(P(
    "İş yerləri tələbələr arasında daim dəyişir, hər iş yerində isə sistem bərpa proqramı "
    "quraşdırılır — hər yenidən başlatmada lokal disk təmizlənir. "
    "<b>Buradan prinsip çıxır: iş yeri “tək istifadəlik”dir, tələbənin işi serverdə yaşayır.</b> "
    "Tələbə hesabına daxil olan kimi bütün faylları və mühiti olduğu yerdə açılır."))
story.append(fitimg(os.path.join(BASE, "is_muhiti_davamliligi.png"), 16.4))
tiers = [
 ["<b>Pillə 0</b><br/>Vahid hesab","Bütün tələbələr","AD / LDAP — bir hesab 4 il boyunca dəyişmir","Bünövrə"],
 ["<b>Pillə 1</b><br/>Şəxsi disk","Hamı — 15 GB","Şəbəkə qovluğu H:; Sənədlər və Masaüstü ora yönləndirilir","Bütün fənlər"],
 ["<b>Pillə 2</b><br/>Konteyner","Kurs üzrə — 2 GB","JupyterHub / code-server; semestr boyu saxlanılır","Proqramlaşdırma, AI, data"],
 ["<b>Pillə 3</b><br/>Şəxsi VM","≈40 yer — 4 GB","Proxmox VM, snapshot ilə geri qaytarma","Şəbəkə, Linux, təhlükəsizlik"],
 ["<b>Pillə 4</b><br/>GitHub","Hamı","Kod öz repozitoriyasında; məzun olandan sonra da qalır","Portfel"]]
story.append(mktable(["Pillə","Kimə / nə qədər","Nə verir","Hansı fənlər"], tiers,
                     [2.5*cm, 3.3*cm, 7.3*cm, 4.2*cm], small=True))
story.append(P("Serverin 256 GB RAM tələbi: 30 konteyner × 2 GB + 15 VM × 4 GB + hipervizor 12 GB "
               "≈ 132 GB. 128 GB bu yükü daşımır, sonradan artırmaq isə bahadır.", s_note))
story.append(P("<b>Kritik icra qeydi:</b> sistem bərpa proqramında C: qorunmalı, şəbəkə diski "
               "<b>qorunmamalı</b>, profil şəbəkə qovluğuna yönləndirilməlidir. Səhv konfiqurasiya "
               "tələbələrin işini itirməsi ilə nəticələnir — qəbul testinə ayrıca bənd kimi salınmalıdır."))

story.append(PageBreak())
# ═══════════════ 8. TƏDRİS PROQRAMI ═══════════════
story.append(P("8. TƏDRİS PROQRAMI İLƏ ƏLAQƏ", s_h1))
kurs = [
 ["<b>1-ci kurs</b>","Proqramlaşdırmanın əsasları (Python, C++) • Alqoritmlər • Kompüter arxitekturası • Linux/Windows","Sabit iş yerləri","—"],
 ["<b>2-ci kurs</b>","OOP (Java, C#) • Verilənlər bazası • Veb-proqramlaşdırma • Kompüter qrafikası","Sabit iş yerləri, VM-lər","CompTIA A+"],
 ["<b>3-cü kurs</b>","Kompüter şəbəkələri • Linux server • Mobil proqramlaşdırma • DevOps (Git, Docker, CI/CD)","Cisco dəsti, virtuallaşdırma serveri","CCNA, Network+"],
 ["<b>4-cü kurs</b>","Süni intellekt • Kibertəhlükəsizlik • Bulud • IoT layihələri • Diplom işi","AI/GPU, bulud, IoT, BYOD","AWS SAA, AZ-104, Security+"]]
story.append(mktable(["Kurs","Praktiki fənlər","İstifadə olunan resurs","Hədəflənən sertifikat"],
                     kurs, [1.9*cm, 7.2*cm, 4.2*cm, 3.9*cm], small=True))
story.append(P("<b>Sertifikat uyğunluğu</b> tədrisin nəticəsini ölçülə bilən edir — “neçə tələbə "
               "sertifikat aldı” sualına konkret cavab verilir. Bu, növbəti illərin büdcə "
               "əsaslandırması üçün ən güclü arqumentdir."))
story.append(P("Dərsdənkənar istifadə", s_h2))
story.append(P("Kartla giriş nəzarəti ilə laboratoriya dərsdənkənar vaxtlarda (18:00–22:00) "
               "sərbəst praktika, layihə işləri, dərnək və hakatonlar üçün açıq qalır."))

# ═══════════════ 9. AVADANLIQ ═══════════════
story.append(P("9. AVADANLIQ SPESİFİKASİYASI", s_h1))
story.append(P("Siyahı tövsiyə olunan (B) ssenariyə aiddir. Qiymətlər indikativdir — rəsmi "
               "satınalmada ən azı üç kommersiya təklifi alınmalıdır."))
W5 = [3.9*cm, 6.4*cm, 1.2*cm, 2.9*cm, 2.8*cm]
for _key, title, rows in EQUIP:
    story.append(P(title, s_h2))
    data = [[WH("Avadanlıq"), WH("Spesifikasiya"), WH("Say"), WH("Vahid (AZN)"), WH("Cəmi (AZN)")]]
    sub = 0
    for _rid, ad, spec, say, q in rows:
        c = say*q; sub += c
        data.append([Paragraph(f"<b>{ad}</b>", s_cells), Paragraph(spec, s_cells),
                     Paragraph(str(say), s_cells), Paragraph(money(q), s_cells), Paragraph(money(c), s_cells)])
    data.append(["", "", "", Paragraph("<b>Yekun:</b>", s_cellb), Paragraph(f"<b>{money(sub)}</b>", s_cellb)])
    t = Table(data, colWidths=W5, repeatRows=1)
    t.setStyle(TableStyle(BASE_TS + [("ROWBACKGROUNDS",(0,1),(-1,-2),[colors.white,LBLUE]),
                                     ("BACKGROUND",(0,-1),(-1,-1),colors.HexColor("#d6eaf8"))]))
    story.append(t)

# ═══════════════ 10. BÜDCƏ ═══════════════
story.append(P("10. BÜDCƏ: ÜÇ SSENARİ", s_h1))
bdata = [[WH("Kateqoriya"), WH("Məbləğ (AZN)"), WH("Payı")]]
for k, v in totals.items():
    bdata.append([Paragraph(k, s_cell), Paragraph(money(v), s_cell), Paragraph(f"{v/grand*100:.0f} %", s_cell)])
bdata += [[Paragraph("<b>Ara cəm</b>", s_cellb), Paragraph(f"<b>{money(grand)}</b>", s_cellb), ""],
          [Paragraph(f"Gözlənilməz xərclər üçün ehtiyat ({RESERVE_RATE*100:.0f} %)", s_cell),
           Paragraph(money(reserve), s_cell), ""],
          [Paragraph("<b>SSENARİ B — TÖVSİYƏ OLUNAN</b>", s_cellb), Paragraph(f"<b>{money(total_b)}</b>", s_cellb), ""]]
bt = Table(bdata, colWidths=[10.4*cm, 4.4*cm, 2.4*cm], repeatRows=1)
bt.setStyle(TableStyle(BASE_TS + [("ROWBACKGROUNDS",(0,1),(-1,-4),[colors.white,LBLUE]),
                                  ("BACKGROUND",(0,-1),(-1,-1),GOLD)]))
story.append(bt)

# Ssenarilərin mətni və rəqəmi eyni siyahıdan çıxarılır — uyğunsuzluq mümkün deyil.
drop_txt = ", ".join(ITEMS[r][0] for r in SCEN_A_DROP)
add_txt  = ", ".join(n for n, _v in SCEN_C_ADD)
scen = [["<b>A — Minimal</b>", money(sA),
         f"Çıxarılır: {drop_txt} (cəmi {money(sum(cost(r) for r in SCEN_A_DROP))} AZN + ehtiyat).",
         "Şəbəkə və AI praktikası zəifləyir; CCNA hazırlığı mümkün olmur"],
        ["<b>B — Tövsiyə olunan</b>", money(total_b),
         "Bütün 7 istiqamət tam praktika ilə örtülür; əlçatanlıq daxildir.",
         "Optimal xərc/nəticə nisbəti"],
        ["<b>C — Genişləndirilmiş</b>", money(sC),
         f"Əlavə olunur: {add_txt} (cəmi {money(sum(v for _n_, v in SCEN_C_ADD))} AZN + ehtiyat).",
         "Tədqiqat və magistr proqramları planlaşdırılırsa"]]
story.append(P("Ssenari müqayisəsi", s_h2))
story.append(mktable(["Ssenari","Büdcə (AZN)","Əhatə","Nəticəyə təsiri"], scen,
                     [2.7*cm, 2.3*cm, 6.6*cm, 5.6*cm], small=True))
story.append(P(
    f"Hər üç ssenaridə {RESERVE_RATE*100:.0f} %-lik ehtiyat həmin ssenarinin öz ara cəmindən "
    f"hesablanır. Akustik işləmə və səssiz rack heç bir ssenariyə daxil deyil (bölmə 12).", s_note))
story.append(P("5 illik sahiblik dəyəri (TCO)", s_h2))
opex = [["Kapital xərci (birdəfəlik)", money(int(total_b)), "Ssenari B"],
        ["Elektrik enerjisi","9 000","≈1 800 AZN/il"],
        ["Texniki xidmət və təmir","12 500","≈2 500 AZN/il — zəmanətdən sonra"],
        ["Proqram abunələri","8 000","≈1 600 AZN/il"],
        ["İstehlak materialları","6 000","≈1 200 AZN/il"],
        ["Avadanlığın yenilənməsi","18 000","İllik 3 600 AZN ehtiyat"]]
odata = [[WH("Xərc maddəsi"), WH("5 il (AZN)"), WH("Qeyd")]]
odata += [[Paragraph(a, s_cell), Paragraph(b, s_cell), Paragraph(c, s_cells)] for a,b,c in opex]
odata.append([Paragraph("<b>5 İLLİK TCO</b>", s_cellb), Paragraph(f"<b>{money(tco)}</b>", s_cellb),
              Paragraph(f"<b>≈ {money(tco_seat)} AZN / iş yeri (5 il) · "
                        f"{money(tco_seat_y)} AZN / iş yeri / il</b>", s_cellb)])
ot = Table(odata, colWidths=[5.4*cm, 3.0*cm, 8.8*cm], repeatRows=1)
ot.setStyle(TableStyle(BASE_TS + [("ROWBACKGROUNDS",(0,1),(-1,-2),[colors.white,LBLUE]),
                                  ("BACKGROUND",(0,-1),(-1,-1),GOLD)]))
story.append(ot)

story.append(P("Büdcədən kənar qalan işlər", s_h2))
oos = [["Akustik asma tavan", money(ACOUSTIC_COST),
        f"≈{S_CEIL} m², RT60-ı {S_RT_B} s → {S_RT_C} s endirir (bölmə 12)"],
       ["Səssiz (akustik) rack şkaf", money(QUIET_RACK),
        "Server səs-küyünü tədris otağı normasına salır"]]
odata2 = [[WH("İş"), WH("Təxmini xərc (AZN)"), WH("Nə verir")]]
odata2 += [[Paragraph(a, s_cell), Paragraph(b, s_cell), Paragraph(c, s_cells)] for a, b, c in oos]
odata2.append([Paragraph("<b>CƏMİ — ayrıca qərar tələb edir</b>", s_cellb),
               Paragraph(f"<b>{money(OUT_OF_SCOPE)}</b>", s_cellb),
               Paragraph(f"<b>Ssenari B ilə birlikdə {money(total_full)} AZN</b>", s_cellb)])
ot2 = Table(odata2, colWidths=[5.4*cm, 3.0*cm, 8.8*cm], repeatRows=1)
ot2.setStyle(TableStyle(BASE_TS + [("ROWBACKGROUNDS",(0,1),(-1,-2),[colors.white,LBLUE]),
                                   ("BACKGROUND",(0,-1),(-1,-1),ROSE)]))
story.append(ot2)
story.append(PageBreak())

# ═══════════════ 10.1 MÜHƏNDİS AUDİTİ ═══════════════
story.append(P("10.1. MÜHƏNDİS AUDİTİ — ƏLAVƏ TƏLƏB OLUNANLAR", s_h1))
story.append(P(
    "Layihə paketi altı müstəqil istiqamət üzrə yenidən nəzərdən keçirilib: pedaqogika və "
    "praktiki təcrübə, avadanlığın tamlığı, təhlükəsizlik və normalar, əlçatanlıq, gündəlik "
    "istismar, qərarvericiyə təqdimat. Aşağıdakılar yoxlamadan keçmiş — yəni sənədin heç bir "
    "yerində olmayan — boşluqlardır. <b>A–D qrupları laboratoriyanın işə düşməsi üçün "
    "mütləqdir</b>; E qrupu ikinci mərhələyə salına bilər."))
for g, title, sev, rows in AUDIT:
    story.append(P(f"{g}. {title} — {money(AUDIT_GROUP_TOTAL[g])} AZN", s_h2))
    data = [[WH("Nə lazımdır"), WH("Nə üçün və nə qədər"), WH("AZN")]]
    for nm, desc, c in rows:
        data.append([Paragraph(f"<b>{nm}</b>", s_cells), Paragraph(desc, s_cells),
                     Paragraph(money(c) if c else "—", s_cells)])
    t = Table(data, colWidths=[4.3*cm, 10.5*cm, 2.4*cm], repeatRows=1)
    t.setStyle(TableStyle(BASE_TS + [("ROWBACKGROUNDS", (0,1), (-1,-1),
                                      [colors.white, LBLUE])]))
    story.append(t)

story.append(P("Yekun mənzərə", s_h2))
sumtab = [["Ssenari B — avadanlıq spesifikasiyası (bölmə 9–10)", money(total_b), ""],
          ["Büdcədən kənar işlər — akustik tavan + səssiz rack", money(OUT_OF_SCOPE),
           "Bölmə 12"],
          ["<b>Audit: A–D — mütləq əlavələr</b>", f"<b>{money(AUDIT_CRIT)}</b>",
           "Təhlükəsizlik, praktika avadanlığı, əlçatanlıq, istismar"],
          ["<b>İŞƏ DÜŞƏN LABORATORİYA</b>", f"<b>{money(total_ready)}</b>",
           "<b>Tövsiyə olunan qərar</b>"],
          ["Audit: E — tövsiyə olunan genişləndirmə", money(AUDIT_OPT),
           "İkinci mərhələyə salına bilər"],
          ["Tam əhatə", money(total_max), ""]]
st = Table([[WH("Mərhələ"), WH("AZN"), WH("Qeyd")]] +
           [[Paragraph(a, s_cell), Paragraph(b, s_cell), Paragraph(c, s_cells)]
            for a, b, c in sumtab],
           colWidths=[8.0*cm, 3.2*cm, 6.0*cm], repeatRows=1)
st.setStyle(TableStyle(BASE_TS + [("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LBLUE]),
                                  ("BACKGROUND", (0,4), (-1,4), GOLD)]))
story.append(st)
story.append(P(
    f"<b>Nə üçün rəqəm {money(total_b)}-dən {money(total_ready)}-ə qalxır:</b> ilkin "
    "spesifikasiya iş yerlərini və şəbəkəni əhatə edirdi, lakin tələbənin <b>əli ilə</b> "
    "işləyəcəyi mühiti tam əhatə etmirdi — sökülə bilən avadanlıq, alət, təzə hava, tüstü "
    "sorucu, differensial müdafiə və əlçatanlığın fiziki hissəsi. Bunlar olmadan otaq "
    "açılır, amma praktiki dərs ya keçirilə bilmir, ya da təhlükəsiz keçirilmir.", s_note))
warn3 = Table([[Paragraph(
    "<b>Diqqət — havalandırma qərarı kondisioner sayını dəyişir.</b> Hazırkı soyutma "
    f"hesabı ({money(COOL_BTU)} BTU/saat, {AC_UNITS} × 24000 BTU) yalnız daxili "
    "istilik mənbələrini nəzərə alır. Rekuperatorsuz mexaniki havalandırma "
    "quraşdırılarsa, təzə havanın soyudulması yükə <b>təxminən 8–10 kVt</b> əlavə edir "
    "və iki kondisioner yetmir. Ona görə havalandırma qərarı iqlim avadanlığının "
    "satınalınmasından <b>əvvəl</b> verilməlidir; ≥70 % rekuperatorlu variant seçilərsə, "
    "mövcud hesab qüvvədə qalır.<br/><br/>"
    "<b>Düzülüş tövsiyəsi:</b> IoT skamyası və 3D printer — hər iki potensial alışma "
    "mənbəyi — hazırda tahliyə qapısı ilə eyni divardadır. Qapıya birbaşa maneə "
    "yaratmasalar da, icra layihəsində onların əks divara köçürülməsi nəzərdən "
    "keçirilməlidir.", s_cell)]], colWidths=[17.2*cm])
warn3.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),ROSE),
                           ("BOX",(0,0),(-1,-1),1.2,colors.HexColor("#c0392b")),
                           ("LEFTPADDING",(0,0),(-1,-1),10), ("RIGHTPADDING",(0,0),(-1,-1),10),
                           ("TOPPADDING",(0,0),(-1,-1),9), ("BOTTOMPADDING",(0,0),(-1,-1),9)]))
story.append(Spacer(1, 0.2*cm)); story.append(warn3)

# ═══════════════ 10.2 KEÇİD YOLU ═══════════════
story.append(P("10.2. KEÇİD YOLLARI — DƏQİQLƏŞDİRMƏ", s_h1))
story.append(P(
    "Sənədin əvvəlki variantında “sıralar arasında 1,40 m keçid yolu” yazılmışdı. Bu rəqəm "
    "<b>masa kənarından masa kənarına</b> olan ölçüdür və stulun çəkilməsi üçün kifayətdir "
    "(hər tərəfə ≈0,61 m). Lakin hər iki sıra dolu olduqda aradan qalan sərbəst en "
    "<b>≈0,18 m</b>-dir — yəni bu zolaq <b>iş sahəsidir, gediş-gəliş yolu deyil</b>."))
circ = [["Sıra addımı (masadan masaya)", "1,40 m", "Stulun çəkilməsi üçün — ödənir"],
        ["Oturmuş iki sıra arasında qalan en", "≈0,18 m", "<b>Keçid yolu kimi istifadə olunmur</b>"],
        ["Pod sütunları arasında (şimal–cənub)", "0,55 m", "Sıralar arası əsas hərəkət"],
        ["Sağ zolaq — əlçatan yerlərdən qapıya", "≥1,20 m", "Əlil arabası marşrutu — sərbəst"],
        ["Qapıdan ən uzaq iş yerinə", f"{S_TRAVEL} m", f"Norma ≤{_eg['limit_m']} m — ödənir"]]
story.append(mktable(["Ölçü", "Dəyər", "Şərh"], circ, [6.2*cm, 3.0*cm, 8.0*cm]))
story.append(P(
    "Bu, sıra düzülüşlü tədris otaqları üçün normal vəziyyətdir — tələbə keçmək üçün "
    "stulu içəri çəkir. Əlçatan marşrut isə bu zolaqdan keçmir: əlçatan iş yerləri sağ "
    "zolaqda, qapıya birbaşa çıxışı olan mövqedədir və bu marşrut 3D modeldə yoxlanılıb."))
warn2 = Table([[Paragraph(
    "<b>Qərar tələb olunur.</b> Əgər universitet oturmuş sıralar arasında da sərbəst keçid "
    "istəyirsə, iki yol var: <b>(a)</b> pod sıralarını 3+3-dən 3+2-yə salmaq — masa kənarları "
    "arasında ≥2,40 m alınır, tutum isə 38 → 34 yerə düşür; <b>(b)</b> otağın dərinliyini "
    "7,5 m-dən ≈8,3 m-ə artırmaq — tutum saxlanılır. Hazırkı layihə (a) və (b) olmadan da "
    "normalara uyğundur, çünki əlçatan marşrut ayrıca təmin olunub.", s_cell)]],
    colWidths=[17.2*cm])
warn2.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),LBLUE),
                           ("BOX",(0,0),(-1,-1),1.0,BLUE),
                           ("LEFTPADDING",(0,0),(-1,-1),10), ("RIGHTPADDING",(0,0),(-1,-1),10),
                           ("TOPPADDING",(0,0),(-1,-1),9), ("BOTTOMPADDING",(0,0),(-1,-1),9)]))
story.append(Spacer(1, 0.2*cm)); story.append(warn2)
story.append(PageBreak())

# ═══════════════ 11. PROQRAM ═══════════════
story.append(P("11. PROQRAM TƏMİNATI", s_h1))
sw = [["Əməliyyat sistemləri","Windows 11 Education • Ubuntu LTS","Akademik / pulsuz"],
      ["Proqramlaşdırma","VS Code, Visual Studio, Python (Anaconda), Node.js, JDK, .NET SDK","Pulsuz"],
      ["Verilənlər bazası","PostgreSQL, MySQL, MongoDB, SQLite, DBeaver","Pulsuz"],
      ["Veb və dizayn","Git + GitHub Education, Postman, Figma (Edu)","Akademik / pulsuz"],
      ["Şəbəkə","Cisco Packet Tracer, GNS3, Wireshark, PuTTY","Pulsuz (NetAcad)"],
      ["Virtuallaşdırma","Proxmox VE, VirtualBox, Docker, Kubernetes","Açıq mənbə"],
      ["Bulud","AWS Academy, Azure for Students","Akademik"],
      ["Süni intellekt","PyTorch, TensorFlow, Jupyter, scikit-learn, CUDA","Pulsuz"],
      ["Kibertəhlükəsizlik","Kali Linux (VM), Burp Suite, OWASP alətləri","Pulsuz"],
      ["IoT","Arduino IDE, Raspberry Pi OS, Thonny, MQTT","Pulsuz"],
      ["<b>Sinif idarəetməsi</b>","Veyon — ekran izləmə, idarəetmə, ötürmə","Açıq mənbə"],
      ["<b>Sistem bərpası</b>","Deep Freeze tipli","Kommersiya"],
      ["<b>İstifadə analitikası</b>","İş yerlərinin istifadəsi, lisenziya statistikası","Abunə"],
      ["<b>Əlçatanlıq</b>","NVDA ekran oxuyucusu, Windows Ease of Access, böyüdücü","Pulsuz"]]
story.append(mktable(["İstiqamət","Proqramlar","Lisenziya"], sw, [3.4*cm, 9.6*cm, 4.2*cm], small=True))
story.append(P("Proqram təminatının əksəriyyəti pulsuz və ya akademik lisenziyalıdır. "
               "GitHub Education, AWS Academy, Azure for Students və Cisco NetAcad qeydiyyatı "
               "layihənin ilk addımı olmalıdır — pulsuzdur, lakin 4–8 həftə çəkir."))

# ═══════════════ 12. AKUSTİKA ═══════════════
story.append(P("12. AKUSTİKA", s_h1))
story.append(P(
    "Akustika tədris otağının ən çox nəzərdən qaçırılan, lakin tədrisin keyfiyyətinə ən birbaşa "
    "təsir edən parametridir. Səs sərt səthlərdən (döşəmə, suvaqlı divar və tavan, şüşə) əks "
    "olunaraq uzun müddət sönmür; nəticədə müəllimin nitqi anlaşılmaz olur, tələbələr yorulur."))
story.append(P("Hesablama — Sabine düsturu", s_h2))
story.append(P(f"RT60 = 0,161 · V / A,  otağın həcmi V = {S_VOL} m³. "
               f"500 Hz-də udma əmsalları: vinil döşəmə 0,03 · suvaqlı tavan 0,05 · "
               f"boyalı divar 0,02 · şüşə 0,05 · oturmuş adam 0,40 sabin · mebel 0,10 sabin."))
ac = [["<b>Mövcud layihə</b> — bütün səthlər sərt", f"<b>{S_RT_B} s</b>", "<b>Normanı pozur</b>"],
      [f"Akustik asma tavan (≈{S_CEIL} m², {_ac['ortuk_payi']*100:.0f} % örtük)",
       f"{S_RT_C} s", "Norma ödənir"],
      [f"Akustik tavan + {WALL_PANEL_A:.0f} m² divar paneli", f"{S_RT_F} s", "Norma ödənir, ehtiyatla"]]
story.append(mktable(["Variant", "RT60 (500 Hz)", f"Tədris otağı norması ≤ {S_LIMIT} s"], ac,
                     [9.4*cm, 3.4*cm, 4.4*cm]))
warn = Table([[Paragraph(
    f"<b>Nəticə:</b> işlənməmiş otaqda RT60 = {S_RT_B} s — normadan "
    f"<b>{S_RT_X} dəfə çoxdur</b>. "
    f"Akustik asma tavan (≈{S_CEIL} m²) tək başına problemi həll edir ({S_RT_C} s). "
    f"Təxmini xərc <b>{money(ACOUSTIC_COST)} AZN</b> — kapital büdcəsinin "
    f"təxminən {ACOUSTIC_COST/total_b*100:.0f} %-i.<br/><br/>"
    "<b>Bu iş cari büdcəyə daxil edilməyib</b> və ayrıca qərar tələb edir. Qərar verilməzsə, "
    "laboratoriya işə salındıqdan sonra nitqin anlaşılması ilə bağlı şikayətlər gözlənilməlidir; "
    "sonradan tavan quraşdırmaq isə kabel və işıqlandırma sisteminin sökülməsini tələb edəcək.",
    s_cell)]], colWidths=[17.2*cm])
warn.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),ROSE),
                          ("BOX",(0,0),(-1,-1),1.2,colors.HexColor("#c0392b")),
                          ("LEFTPADDING",(0,0),(-1,-1),10), ("RIGHTPADDING",(0,0),(-1,-1),10),
                          ("TOPPADDING",(0,0),(-1,-1),9), ("BOTTOMPADDING",(0,0),(-1,-1),9)]))
story.append(Spacer(1, 0.25*cm)); story.append(warn)
story.append(P("Server rack-ın səs-küyü", s_h2))
story.append(P(
    "Rack serverinin səs gücü səviyyəsi ≈55 dB(A)-dir; işlənməmiş otaqda əks-səda sahəsində "
    "təxminən 47 dB(A) fon səs-küyü yaranır — tədris otağı norması 35–40 dB(A). "
    f"Akustik tavan bu göstəricini də azaldır. Tam həll üçün səssiz (akustik) rack şkaf "
    f"(≈+{money(QUIET_RACK)} AZN) və ya serverin ayrıca otağa köçürülməsi variantları var. "
    f"Bu iş də cari büdcəyə daxil edilməyib — akustik tavanla birlikdə "
    f"{money(OUT_OF_SCOPE)} AZN (bax: 10-cu bölmə, “Büdcədən kənar qalan işlər”)."))

# ═══════════════ 13. ƏLÇATANLIQ ═══════════════
story.append(P("13. ƏLÇATANLIQ (UNİVERSAL DİZAYN)", s_h1))
story.append(P(
    "Laboratoriya hərəkət məhdudiyyəti olan tələbələr üçün də istifadəyə yararlı olmalıdır. "
    "Bu, yalnız sosial öhdəlik deyil — universal dizayn beynəlxalq akkreditasiya "
    "tələblərinin ayrılmaz hissəsidir və layihəyə əvvəldən salınanda praktik olaraq "
    "əlavə xərc yaratmır."))
_pozuntu = PRM["elcatanliq"]["pozuntu"]
a11 = [["Əlçatan iş yeri sayı", f"{A11Y_N} ədəd",
        f"{SEATS} iş yerinə — hər 20 yerə 1 norması ödənir "
        f"(tələb {PRM['elcatanliq']['teleb']})"],
       ["Masa hündürlüyü", "70–120 sm", "Elektrik mühərriki ilə tənzimlənir"],
       ["Masa altı boşluq", "≥68 sm hündürlük, ≥80 sm en", "Əlil arabasının girməsi üçün"],
       ["Manevr dairəsi", "Ø1,50 m",
        "Hər əlçatan iş yerinin qarşısında sərbəst — 3D modeldə "
        + ("kəsişmə yoxdur" if _pozuntu == 0 else f"<b>{_pozuntu} pozuntu var</b>")],
       ["Yanaşma zolağı", "≥0,90 m", "Keçid yolundan iş yerinə"],
       ["Qapı eni", f"{S_DOOR} m", "Norma ≥0,85 m — ödənir"],
       ["Keçid yolları", "1,40 m", "Norma ≥1,20 m (iki tərəfli hərəkət) — ödənir"],
       ["Proqram dəstəyi", "NVDA, Windows Ease of Access", "Ekran oxuyucu və böyüdücü"]]
story.append(mktable(["Parametr","Layihə həlli","Qeyd"], a11, [4.6*cm, 4.6*cm, 8.0*cm]))
story.append(P(
    "Əlçatan iş yerləri otağın sağ zolağında, əsas keçid yoluna birbaşa çıxışı olan mövqedə "
    "yerləşdirilib — qapıdan iş yerinə qədər pilləkən və astana yoxdur. Ø1,5 m manevr dairələri "
    "otaq planında göstərilib və 3D dizayner proqramı bu dairələrin başqa mebellə kəsişmədiyini "
    "avtomatik yoxlayır."))
story.append(P("Sənədin bu bölməsi əvvəlki versiyada yox idi — mühəndis analizi zamanı aşkar "
               "edilmiş boşluq kimi əlavə olunub.", s_note))

# ═══════════════ 14. TEXNİKİ TƏLƏBLƏR ═══════════════
story.append(P("14. OTAĞA DAİR TEXNİKİ TƏLƏBLƏR", s_h1))
story.append(P("İşıqlanma", s_h2))
_ac_reserve = (AC_UNITS*24000 - COOL_BTU) / COOL_BTU * 100
story.append(P(f"Hesablama: {LUX_PANELS} ədəd 1200×300 LED panel ({money(LUX_LM)} lm), "
               f"iş səthi {S_WORK_H} m, istismar əmsalı {S_MAINT}. "
               f"Nəticə: orta <b>{LUX_AVG} lx</b> (norma ≥{_lux['norma']} lx — ödənir), "
               f"minimum {LUX_MIN} lx, bərabərlik U<sub>0</sub> = {S_U0} "
               f"(hədəf ≥{S_U0_REQ} — sərhəddə). "
               f"Bərabərliyi yaxşılaşdırmaq üçün kənar panelləri divarlara yaxınlaşdırmaq tövsiyə olunur. "
               f"İcra layihəsində DIALux ilə dəqiqləşdirilməlidir."))
for h, items in [
 ("Elektrik təchizatı", [
   f"Ayrılmış xətt: <b>{KW_LINE} kVt</b> — hesabi yük {S_KWCALC} kVt (k={S_KFACT}), "
   f"üzərinə ≥{(_el['ehtiyat']-1)*100:.0f} % ehtiyat qoyulub və standart nominala yuvarlaqlaşdırılıb",
   f"Hər iş yerində 4× rozetka + USB-C; BYOD masasında 6× rozetka; cəmi {SOCKETS} rozetka",
   "Server zonası online UPS ilə (≥15 dəq); iş yerləri qrup UPS/filtrlə",
   "Torpaqlama; IoT skamyası üçün ayrıca avtomat açar"]),
 ("İnternet və şəbəkə", [
   "Minimum <b>250 Mbit/s</b> ayrılmış kanal",
   f"Bütün sabit iş yerləri kabellə ({RJ45} RJ-45 portu); Wi-Fi 6 yalnız BYOD üçün",
   "5 VLAN: tələbə, server, IoT, idarəetmə, qonaq — IoT mütləq izolyasiya olunur",
   "Struktur kabel sistemi sertifikatlaşdırılmalı və sənədləşdirilməlidir"]),
 ("İqlim", [
   f"Soyutma yükü <b>{money(COOL_BTU)} BTU/saat</b> (avadanlıq {S_KWIT} kVt + {CONCUR} nəfər + işıq)",
   f"{AC_UNITS} × {money(_cool['kondisioner_btu'])} BTU inverter kondisioner — "
   f"{_ac_reserve:.0f} % ehtiyatla",
   "Temperatur 21–24°C, rütubət 40–60 %",
   "Pəncərələrdə işıq keçirməyən jalüzlər"]),
 ("Təhlükəsizlik və tahliyə", [
   f"Otaqda eyni anda {CONCUR} nəfər — 50 nəfərdən az olduğu üçün "
   f"<b>{EXITS} çıxış kifayətdir</b>",
   f"Qapı eni {S_DOOR} m (buraxma qabiliyyəti {_eg['qapi_tutumu']} nəfər); "
   f"<b>qapı çölə açılmalıdır</b>",
   f"Ən uzaq nöqtədən qapıya məsafə ≈{S_TRAVEL} m (norma ≤{_eg['limit_m']} m) — ödənir",
   "Kartla giriş nəzarəti, 2× IP kamera, CO<sub>2</sub> odsöndürən",
   "Server rack tahliyə yolunu tutmamalıdır"])]:
    story.append(P(h, s_h2))
    for x in items: story.append(B(x))
story.append(PageBreak())

# ═══════════════ 15. İDARƏETMƏ ═══════════════
story.append(P("15. İDARƏETMƏ VƏ İSTİSMAR MODELİ", s_h1))
gov = [["<b>Laboratoriya rəhbəri</b>","1 ştat (və ya 0,5)","Cədvəl, inventar, təhlükəsizlik, illik hesabat"],
       ["<b>Texniki dəstək</b>","İT şöbəsi ilə SLA","İmic yenilənməsi, nasazlığın 24 saat ərzində aradan qaldırılması"],
       ["<b>Tələbə köməkçiləri</b>","2–3 nəfər (yuxarı kurs)","Dərsdənkənar növbətçilik"],
       ["<b>Çıxış siyasəti</b>","Sənədləşdirilmiş qaydalar","Dərs saatları • sərbəst praktika 18:00–22:00"],
       ["<b>Yeniləmə siyasəti</b>","5 illik dövr","İllik büdcədə yeniləmə ehtiyatı"]]
story.append(mktable(["Element","Resurs","Məzmun"], gov, [3.6*cm, 4.4*cm, 9.2*cm], small=True))

story.append(P("16. UĞUR MEYARLARI (KPI)", s_h1))
kpis = [["İstifadə əmsalı (dərs saatları)","≥ 70 %","Analitika proqramı","Rüblük"],
        ["Dərsdənkənar istifadə","≥ 25 saat/həftə","Giriş nəzarəti","Aylıq"],
        ["Sertifikat alan tələbə","İlk il ≥ 20 nəfər","Sertifikat qeydiyyatı","İllik"],
        ["Komanda layihəsi","≥ 15 layihə/il","Kafedra hesabatı","İllik"],
        ["Avadanlığın işlək qalması","≥ 97 %","Nasazlıq jurnalı","Rüblük"],
        ["Tələbə məmnuniyyəti","≥ 4,2 / 5","Semestr sorğusu","Semestrlik"]]
story.append(mktable(["Göstərici","Hədəf","Ölçmə mənbəyi","Tezlik"], kpis,
                     [6.2*cm, 3.6*cm, 4.4*cm, 3.0*cm]))

story.append(P("17. RİSKLƏR VƏ AZALDILMA TƏDBİRLƏRİ", s_h1))
risks = [["Büdcənin tam ayrılmaması","Yüksək","Ssenari A-dan başlamaq; AI stansiyası və Cisco dəstini ikinci mərhələyə keçirmək"],
         ["<b>Akustikanın işlənməməsi</b>","<b>Yüksək</b>",
          f"<b>RT60 normanı {S_RT_X} dəfə aşır. Sonradan tavan quraşdırmaq kabel və "
          f"işıq sisteminin sökülməsini tələb edir — qərar layihə mərhələsində verilməlidir</b>"],
         ["Avadanlığın gec çatdırılması","Orta","Satınalmanı erkən başlatmaq; alternativ təchizatçı"],
         ["Az istifadə olunması","Yüksək","İlk semestrdən cədvələ salmaq; dərsdənkənar rejim; istifadəni ölçmək"],
         ["Texniki dəstəyin olmaması","Yüksək","Məsul şəxsi əvvəlcədən təyin etmək; sistem bərpası ilə dəstək yükünü azaltmaq"],
         ["Tələbələrin işinin itməsi","Yüksək","Bərpa proqramının konfiqurasiyasını qəbul testinə salmaq (7.1); gecə yedəkləməsi"],
         ["Müəllimlərin hazır olmaması","Orta","Pilot mərhələdə təlim; NetAcad və AWS Academy instruktor proqramları"]]
story.append(mktable(["Risk","Ehtimal","Azaldılma tədbiri"], risks, [4.6*cm, 2.0*cm, 10.6*cm], small=True))
story.append(PageBreak())

# ═══════════════ 18. İCRA ═══════════════
story.append(P("18. İCRA QRAFİKİ", s_h1))
steps = [["0","Hazırlıq","Məsul şəxsin təyini • akademik proqramlara qeydiyyat • otağın enerji hesabatı","2 həftə","Qeydiyyatlar paralel gedir"],
         ["1","Otağın hazırlanması",f"Təmir • {KW_LINE} kVt elektrik montajı • struktur kabel • kondisionerlər • jalüzlər","3–4 həftə","Ən uzun mərhələ"],
         ["2","Satınalma","Kommersiya təklifləri • müqavilələr • çatdırılma","4–6 həftə","1-ci mərhələ ilə paralel"],
         ["3","Quraşdırma","Mebel • rack • şəbəkə konfiqurasiyası • iş yerləri","1–2 həftə","—"],
         ["4","Proqram təminatı","Sistem imici • virtuallaşdırma • VLAN • AD/LDAP və davamlılıq (7.1) • test","2–3 həftə","İmic bir dəfə hazırlanır"],
         ["5","Pilot və təlim","Müəllim təlimi • sınaq dərsləri • ölçmələr • qəbul aktı","1–2 həftə","İşıqlanma və akustika ölçülür"]]
story.append(mktable(["№","Mərhələ","Məzmun","Müddət","Qeyd"], steps,
                     [0.8*cm, 3.0*cm, 7.4*cm, 2.2*cm, 3.8*cm], small=True))
story.append(P("<b>Ümumi müddət: 11–16 həftə.</b> Mərhələ 1 və 2 paralel aparılarsa, layihə bir "
               "semestr ərzində tamamlana bilər."))
story.append(P("Növbəti addımlar", s_h2))
for i, x in enumerate([
  "Bu sənədin razılaşdırılması və ssenarinin (A / B / C) seçilməsi",
  f"<b>Akustik işləmə və səssiz rack barədə qərar</b> (+{money(OUT_OF_SCOPE)} AZN) — bölmə 12",
  "Otağın təsdiqlənməsi: tələb olunan minimum sahə " + f"{S_MINA} m²",
  "Akademik proqramlara qeydiyyatın başladılması (pulsuzdur, uzun çəkir)",
  "Ən azı üç təchizatçıdan kommersiya təklifinin alınması",
  "Laboratoriya rəhbərinin təyin edilməsi və texniki tapşırığın hazırlanması"], 1):
    story.append(Paragraph(f"<b>{i}.</b>  {x}", s_bul))

# ═══════════════ MƏNBƏLƏR ═══════════════
story.append(P("İSTİFADƏ OLUNMUŞ MƏNBƏLƏR", s_h1))
for s in [
 "AR Prezidentinin 19.03.2025 tarixli 530 nömrəli Sərəncamı — “2025–2028-ci illər üçün süni intellekt Strategiyası” (president.az)",
 "AR Prezidentinin 27.02.2026 tarixli Sərəncamı — Rəqəmsal İnkişaf Şurasının yaradılması",
 "Times Higher Education Campus — “Modernising university computer labs”",
 "AppsAnywhere — “VDI Alternatives for Higher Education … 2026”",
 "EdTech Magazine — “Active Learning Classrooms Foster Collaboration Among Students” (2026)",
 "EdTech Magazine — “6 Benefits of Establishing a Higher Education Device Refresh Cycle”",
 "LabStats — laboratoriya istifadə analitikası materialları",
 "Faronics — “Deep Freeze in Education: Lab Management Simplified”",
 "Ascend Education — “Most Valuable IT Certifications in 2026”",
 "Report.az — ATU-da Data-analitika və Süni İntellekt Laboratoriyasının açılışı",
 "Akustik hesablama: Sabine düsturu (RT60 = 0,161·V/A), 500 Hz udma əmsalları",
 "İşıqlanma hesablaması: Lambert paylanmalı panel modeli + lümen metodu ilə əks olunan komponent",
 "Bütün mühəndis rəqəmləri layihənin 3D dizayner proqramından (lab_parametrleri.json) "
 "avtomatik alınır — sənəd, sxemlər və 3D model eyni mənbədən qidalanır"]:
    story.append(Paragraph("•  " + s, s_src))

def footer(canvas, doc):
    if doc.page == 1: return
    canvas.saveState()
    canvas.setFont("Arial", 8.2); canvas.setFillColor(GREY)
    canvas.drawString(1.85*cm, 1.0*cm, "İT Tədris Laboratoriyası — layihə və satınalma sənədi")
    canvas.drawRightString(A4[0]-1.85*cm, 1.0*cm, f"Səhifə {doc.page}")
    canvas.setStrokeColor(colors.HexColor("#d5d8dc"))
    canvas.line(1.85*cm, 1.28*cm, A4[0]-1.85*cm, 1.28*cm)
    canvas.restoreState()

PDF_PATH = os.path.join(BASE, "IT_Laboratoriya_Plani.pdf")


def build_pdf(path=PDF_PATH):
    """PDF-i qurur və qurulmuş səhifə sayını qaytarır.

    Bu iş qəsdən funksiyanın içindədir: teqdimat_qur.py bu moduldan yalnız
    RƏQƏMLƏRİ import edir. Modul gövdəsində qurulsaydı, hər idxal 1,2 MB-lıq
    PDF-i yenidən yazardı (reportlab hər dəfə yeni CreationDate yazır → git-də
    səbəbsiz binar dəyişiklik), sənəd baxıcıda açıq olsaydı isə PermissionError
    verərdi.
    """
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=1.85*cm, rightMargin=1.85*cm,
                            topMargin=1.7*cm, bottomMargin=1.7*cm,
                            title="İT Tədris Laboratoriyası — layihə və satınalma sənədi",
                            author="Laboratoriya layihə qrupu")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return doc.page


def pdf_page_count(path=PDF_PATH):
    """Mövcud PDF-in səhifə sayı; fayl yoxdursa None.

    Səhifə sayı sənəd böyüdükcə dəyişir, ona görə mətnə əl ilə yazılmır —
    təqdimat vərəqi bu funksiyadan oxuyur.
    """
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except FileNotFoundError:
        return None
    m = re.findall(rb"/Count\s+(\d+)", data)
    return max(int(x) for x in m) if m else None


if __name__ == "__main__":
    pages = build_pdf()
    print(f"OK  |  şrift: {FONT_USED}  |  parametrlər: {os.path.basename(PARAM_FILE)}")
    print(f"    Ssenari A: {money(sA)}  ·  B: {money(total_b)}  ·  C: {money(sC)} AZN")
    print(f"    5 illik TCO: {money(tco)} AZN  ({money(tco_seat)} AZN / iş yeri)")
    print(f"    Büdcədən kənar: {money(OUT_OF_SCOPE)} AZN  →  tam: {money(total_full)} AZN")
    print(f"    Audit: kritik +{money(AUDIT_CRIT)} · tövsiyə +{money(AUDIT_OPT)} AZN")
    print(f"    İŞƏ DÜŞƏN LABORATORİYA: {money(total_ready)} AZN  (tam əhatə {money(total_max)})")
    print(f"    {pages} səhifə  ·  {PDF_PATH}")
