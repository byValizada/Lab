# Üçüncü tərəf komponentlər və atribusiya

## Lisenziyanın əhatəsi

**MIT** ([`LICENSE`](LICENSE)) layihənin **öz** materiallarına aiddir:

- generatorlar — `sened_qur.py`, `sxem_qur.py`, `teqdimat_qur.py`
- 3D dizayner — `3d/index.html`, `3d/app.js` (`3d/vendor/` istisna olmaqla)
- hesablama modeli və `lab_parametrleri.json`
- sənəd mətni, sxemlər (`*.png`) və renderlər (`renderler/`)

Repozitoriyaya daxil edilmiş **kənar** kod və aktivlər isə öz lisenziyaları
altında qalır. Aşağıda həmin lisenziyaların tələb etdiyi müəllif hüququ
bildirişləri saxlanılır.

---

## three.js — r128

**Yer:** `3d/vendor/`
**Lisenziya:** MIT
**Mənbə:** https://github.com/mrdoob/three.js/tree/r128

`3d/vendor/three.min.js` faylı kitabxananın özüdür. Qalan fayllar three.js-in
`examples/js/` qovluğundan götürülmüş və eyni MIT lisenziyası ilə əhatə olunan
əlavələrdir — həmin fayllarda ayrıca lisenziya başlığı olmadığı üçün burada
qeyd edilir:

```
BufferGeometryUtils.js   CopyShader.js            EffectComposer.js
GammaCorrectionShader.js LuminosityHighPassShader.js  OrbitControls.js
RGBELoader.js            RenderPass.js            SMAAPass.js
SMAAShader.js            SSAOPass.js              SSAOShader.js
ShaderPass.js            SimplexNoise.js          UnrealBloomPass.js
```

```
The MIT License

Copyright © 2010-2021 three.js authors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

---

## SMAA — v2.8 (three.js portu daxilində)

**Yer:** `3d/vendor/SMAAShader.js`, `3d/vendor/SMAAPass.js`
**Lisenziya:** MIT (three.js portu) + orijinal SMAA lisenziyası
**Mənbə:** https://github.com/iryoku/smaa/releases/tag/v2.8

`SMAAShader.js` orijinal SMAA v2.8 alqoritminin WebGL portudur; `SMAAPass.js`
isə orijinal paylanmadan gələn iki axtarış teksturasını (`area`, `search`)
base64 PNG kimi öz içində daşıyır. Yəni portla yanaşı orijinal əsərin bir hissəsi
də yenidən yayılır və müəllif hüququ bildirişi surətlərlə birlikdə saxlanmalıdır:

```
Copyright (C) 2013 Jorge Jimenez, Jose I. Echevarria,
                   Belen Masia, Fernando Navarro, Diego Gutierrez
```

Bu bildiriş faylların öz başlığında yoxdur, ona görə burada qeyd olunur.
`SimplexNoise.js` üçün atribusiya (Stefan Gustavson / Sean McCullough) faylın
öz başlığında qorunub.

---

## PBR teksturalar və HDRI

**Yer:** `3d/assets/`
**Lisenziya:** CC0 1.0 (ictimai mülkiyyət) — atribusiya tələb olunmur
**Mənbə:** Poly Haven — https://polyhaven.com

```
floor_diff.jpg  floor_nor.jpg  floor_arm.jpg
wall_diff.jpg   wall_nor.jpg   wall_arm.jpg
desk_diff.jpg   desk_nor.jpg   desk_arm.jpg
fabric_diff.jpg fabric_nor.jpg fabric_arm.jpg
sky_1k.hdr
```

Bu faylların mənşəyi `3d/app.js` içindəki şərhdən götürülüb. Aktivləri
əvəz edərkən mənbə və lisenziyanı bu siyahıda yeniləyin.

**Metadata təmizlənib.** Orijinal fayllar EXIF/XMP seqmentlərində istehsal
alətinin işlətdiyi tam yerli fayl yollarını daşıyırdı (üçüncü şəxsin istifadəçi
adı və daxili qovluq quruluşu). Bütün `APP1…APP15` və `COM` seqmentləri itkisiz
silinib — piksel datası (sıxılmış SOS bloku) toxunulmayıb, yəni normal xəritələr
artefakt almayıb. CC0 atribusiya tələb etmədiyi üçün bu, heç bir öhdəliyi pozmur;
mənbə isə yuxarıda göstərilib.

Yeni aktiv əlavə edərkən eyni təmizləməni aparın:

```bash
python -c "from PIL import Image; print(dict(Image.open('yeni.jpg').getexif()))"
```

---

## Python kitabxanaları

Repoya daxil edilmir, `pip install -r requirements.txt` ilə quraşdırılır:

| Kitabxana | Lisenziya |
|---|---|
| ReportLab | BSD-3-Clause |
| Pillow | MIT-CMU |
| matplotlib | matplotlib (BSD-uyğun) |

---

## Şriftlər

Repoya **heç bir şrift faylı daxil edilmir**. Generatorlar sistemdə mövcud olan
şriftdən istifadə edir:

- **Arial** — Windows-da sistem şrifti. Paylanmır, yalnız yerli fayl kimi oxunur.
- **DejaVu Sans** — matplotlib ilə birlikdə gəlir, ehtiyat variantdır
  (lisenziya: Bitstream Vera / Public Domain).

---

## Sənəddəki mənbələr

`IT_Laboratoriya_Plani.pdf` sənədinin "İstifadə olunmuş mənbələr" bölməsində
göstərilən nəşrlərə yalnız istinad verilir — həmin materialların mətni
təkrarlanmır və kopyalanmır.
