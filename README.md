# İT Tədris Laboratoriyası — layihə paketi

Universitetdə tələbələrin **praktiki** İT təcrübəsi qazandığı bir otağın tam
layihəsi: 3D model, mühəndis hesablamaları, avadanlıq spesifikasiyası, büdcə və
qərarverici üçün vizual təqdimat.

**Otaq:** 12,5 × 7,5 × 2,8 m · 93,8 m² · 38 iş yeri · eyni anda 33 nəfər
**İşə düşən paket:** 199 040 AZN · **5 illik TCO:** 198 460 AZN · **İcra:** 11–16 həftə

> Sürətli baxış: [`teqdimat.html`](teqdimat.html) faylını brauzerdə açın —
> renderlər, zonalar, bir dərsin gedişi, audit və büdcə tək səhifədədir.
> Tam sənəd: [`IT_Laboratoriya_Plani.pdf`](IT_Laboratoriya_Plani.pdf) (21 səhifə).

| Məhsul | Nə edir |
|---|---|
| **3D Dizayner** (`3d/`) | Brauzerdə işləyən interaktiv otaq planlayıcısı. Mebeli sürükləyirsən — işıqlanma, akustika, soyutma, elektrik, əlçatanlıq və tahliyə göstəriciləri dərhal yenidən hesablanır. |
| **Sənəd generatoru** (`sened_qur.py`) | 21 səhifəlik texniki-iqtisadi əsaslandırma və avadanlıq spesifikasiyası → `IT_Laboratoriya_Plani.pdf` |
| **Sxem generatoru** (`sxem_qur.py`) | Sənədə daxil edilən üç sxem: otaq planı, texniki arxitektura, iş mühitinin davamlılığı |
| **Vizual təqdimat** (`teqdimat_qur.py`) | Qərarverici üçün tək səhifə: 3D renderlər, zonalar, bir dərsin gedişi, audit, büdcə → `teqdimat.html` |
| **Renderlər** (`renderler/`) | 3D səhnədən çəkilmiş 11 görüntü — ümumi görünüş, zonalar, plan, texniki qatlar |

---

## Vahid həqiqət mənbəyi

Bütün mühəndis rəqəmləri **bir yerdə** — 3D dizaynerin hesablama qatında yaşayır.
Oradan `lab_parametrleri.json` faylına ixrac olunur, PDF və sxem generatorları isə
həmin faylı oxuyur.

```
3d/app.js  ──"Parametrlər" düyməsi──►  lab_parametrleri.json
                                              │
                                     ┌────────┴────────┐
                                     ▼                 ▼
                              sened_qur.py       sxem_qur.py
                                     │                 │
                                     ▼                 ▼
                        IT_Laboratoriya_Plani.pdf   *.png
```

Nəticə: **PDF-dəki rəqəm 3D modeldəki rəqəmdən fərqlənə bilməz.** Əvvəllər hər ikisi
ayrı-ayrı yazıldığı üçün elektrik xətti (14 vs 16 kVt) və akustik tavan sahəsi
(49 vs 65 m²) kimi uyğunsuzluqlar yaranmışdı.

---

## İşə salmaq

### 1. 3D Dizayner

```bash
3d/BASLAT.bat
```

Python varsa lokal server qaldırır (port 8123) və brauzeri açır; yoxdursa faylı
birbaşa açır. Quraşdırma tələb olunmur — Three.js və bütün teksturalar `3d/vendor/`
və `3d/assets/` içindədir, xarici şəbəkə sorğusu yoxdur.

**İdarəetmə:** sol düymə seç · sürüklə yerini dəyiş · sağ düymə fırlat · çarx yaxınlaşdır ·
`Q`/`E` döndər · `Del` sil · `Ctrl`+`D` kopyala · `Ctrl`+`Z` geri · `Esc` seçimi ləğv et.
Gəzinti rejimində `W`/`A`/`S`/`D` + siçan.

**Düymələr:** `JSON ixrac` — düzülüş · `İdxal` — düzülüşü geri yüklə ·
`Parametrlər` — bütün mühəndis göstəriciləri (aşağıya bax) · `PNG` / `4K render` — şəkil.

### 2. Sənədin və təqdimatın yenidən qurulması

```bash
python3 -m pip install -r requirements.txt
python3 sxem_qur.py       # üç sxemi çəkir
python3 sened_qur.py      # 21 səhifəlik PDF-i qurur
python3 teqdimat_qur.py   # teqdimat.html-i qurur
```

> **Windows-da** `python3` əvəzinə `python` yazın. Python ≥ 3.9 tələb olunur.
> macOS və bir çox Linux distributivində `python` adlı əmr yoxdur — ona görə
> yuxarıda `python3` istifadə olunur.

Ardıcıllıq vacibdir: `teqdimat_qur.py` büdcə rəqəmlərini `sened_qur.py`-dən,
səhifə sayını isə qurulmuş PDF-dən oxuyur — ona görə PDF-dən sonra işlədilməlidir.
Beləliklə PDF ilə təqdimat heç vaxt fərqli rəqəm göstərə bilmir.

Renderləri yeniləmək üçün 3D dizaynerdə səhnəni istədiyiniz bucaqdan qurub
`4K render` düyməsini basın və faylı `renderler/` qovluğuna qoyun.

### 3. Otaq ölçüsü və ya düzülüş dəyişəndə

1. 3D dizaynerdə otağı/mebeli dəyiş
2. **Parametrlər** düyməsini bas → `lab_parametrleri.json` yüklənir
3. Faylı layihə qovluğuna (bu qovluğa) kopyala
4. `python3 sxem_qur.py && python3 sened_qur.py && python3 teqdimat_qur.py`

Sxemlər, PDF və təqdimat — hamısı yeni ölçüyə uyğun yenidən qurulur.

---

## Fayllar

```
lab_parametrleri.json        vahid həqiqət mənbəyi (3D-dən ixrac olunur)
sened_qur.py                 PDF generatoru
sxem_qur.py                  sxem generatoru
IT_Laboratoriya_Plani.pdf    nəticə sənəd
otaq_plani.png               ┐
texniki_arxitektura.png      ├ sxemlər (sxem_qur.py yaradır)
is_muhiti_davamliligi.png    ┘
3d/index.html                3D dizaynerin interfeysi
3d/app.js                    səhnə, mebel modelləri, mühəndis analizi
3d/vendor/                   Three.js r128 + post-emal keçidləri (lokal)
3d/assets/                   PBR teksturalar + HDRI (CC0, Poly Haven)
3d/BASLAT.bat                lokal serveri qaldırır və brauzeri açır
```

---

## Mühəndis modeli

| Analiz | Metod | Yeri |
|---|---|---|
| İşıqlanma | Lambert paylanmalı panel: `E = (Φ/π)·cos⁴θ/h²` + lümen metodu ilə əks komponent | `app.js` → `analyseLux` |
| Akustika | Sabine: `RT60 = 0,161·V/A`, 500 Hz udma əmsalları | `analyseAcoustics` |
| Soyutma | Avadanlıq + insan (75 Vt) + işıq (40 Vt/panel) + xarici qazanc (13 Vt/m²) | `analyseCooling` |
| Elektrik | `(kVt_İT + kVt_AC) × 1,25`, sonra standart nominala ≥15 % ehtiyatla yuvarlaqlaşdırma | `analyseElectric` |
| Əlçatanlıq | Ø1,5 m manevr dairəsinin digər mebellə kəsişməsi | `analyseA11y` |
| Toqquşma | Plan üzrə AABB **və** şaquli əhatə — divara asılan panel masanın üstündən keçir, amma 2 m-lik rack ilə toqquşur | `pairCheck` |
| Sahə norması | Sabit yer 2,30 m² + çevik 1,60 m² + hər əlçatan yerə +1,20 m² | `recommendedArea` |

Bütün hesablar **parametrikdir** — otaq ölçüsü dəyişəndə nəticələr dərhal yenilənir.
Təxmini hesablardır; icra layihəsində işıqlanma DIALux, akustika isə ölçmə ilə
dəqiqləşdirilməlidir.

---

## Asılılıqlar

`requirements.txt` — `reportlab`, `pillow`, `matplotlib`.
Şrift: Arial (Windows) və ya DejaVu Sans (Linux/macOS) avtomatik tapılır —
Azərbaycan əlifbasının ə/ğ/ş/ı hərfləri üçün TTF şrift mütləqdir.

3D dizayner heç bir quraşdırma tələb etmir və internetə çıxmır — Three.js və
bütün teksturalar repozitoriyanın içindədir.

---

## Lisenziya

Layihənin öz materialları — generatorlar, 3D dizayner, hesablama modeli, sənəd
mətni, sxemlər və renderlər — **MIT** lisenziyası altındadır: [`LICENSE`](LICENSE).
Yəni sərbəst istifadə, dəyişdirmə və paylaşma mümkündür; şərt yalnız müəllif
hüququ bildirişinin saxlanmasıdır.

Repozitoriyaya daxil edilmiş üçüncü tərəf komponentlər öz lisenziyaları altında
qalır — [`UCUNCU_TEREF.md`](UCUNCU_TEREF.md):
Three.js r128 — MIT · PBR teksturalar və HDRI — CC0 1.0 (Poly Haven).
