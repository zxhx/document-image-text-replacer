# Typography Guidelines for Document & Table Image Replacement

This reference guides the agent on font matching, baseline alignment, and ink bleed modeling for scanned and photographed Chinese and bilingual documents.

---

## 1. Common Font Families in Chinese Office Documents

| Document Style / Usage | Chinese Font | English / Numeric Font | Windows Font File | Key Visual Signatures |
| :--- | :--- | :--- | :--- | :--- |
| **Standard Official Tables / Forms** | 华文宋体 (STSong) / 宋体 (SimSun) | STSong / Times New Roman | `STSONG.TTF`, `simsun.ttc`, `times.ttf` | Delicate horizontal strokes, thicker verticals; digits have ball terminals on 2, 3, 6, 8. |
| **Government Formal Heading (公文红头/标题)** | 小标宋 (FZXiaoBiaoSong) / 仿宋 | Times New Roman / SimSun | `simfang.ttf`, `STSONG.TTF` | Formal triangular serifs, elongated verticals. |
| **Modern Tables / Header Labels** | 微软雅黑 (Microsoft YaHei) / 黑体 | Arial / Segoe UI | `msyh.ttc`, `simhei.ttf`, `arial.ttf` | Clean sans-serif, uniform stroke width, no serifs or ball terminals. |
| **Notice / Notes / Calligraphic (批注/强调)** | 楷体 (KaiTi) | Times New Roman | `simkai.ttf`, `times.ttf` | Brush calligraphy stroke endings, visible tilt and variation. |

---

## 2. Standard Word / WPS Font Sizes to Pixel Heights

In standard office software, fonts are measured in Chinese point sizes or standard points (pt).
Formula: `Pixels = Points * (DPI / 72)`

| Chinese Name (字号) | Points (pt) | Height @ 96 DPI | Height @ 120 DPI (Standard Scan) | Height @ 150 DPI | Height @ 300 DPI (High Scan) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **初号** | 42 pt | ~56 px | ~70 px | ~88 px | ~175 px |
| **小初** | 36 pt | ~48 px | ~60 px | ~75 px | ~150 px |
| **一号** | 26 pt | ~35 px | ~43 px | ~54 px | ~108 px |
| **二号** | 22 pt | ~29 px | ~37 px | ~46 px | ~92 px |
| **小二** | 18 pt | ~24 px | ~30 px | ~38 px | ~75 px |
| **三号** | 16 pt | ~21 px | ~27 px | ~33 px | ~67 px |
| **小三** | 15 pt | ~20 px | ~25 px | ~31 px | ~63 px |
| **四号 (Table Title)** | 14 pt | ~19 px | ~23-24 px | ~29 px | ~58 px |
| **小四 (Table Body)** | 12 pt | ~16 px | ~20 px | ~25 px | ~50 px |
| **五号 (Normal Text)**| 10.5 pt | ~14 px | ~17-18 px | ~22 px | ~44 px |
| **小五 (Footer/Notes)** | 9 pt | ~12 px | ~15 px | ~19 px | ~38 px |

---

## 3. Punctuation & Spacing Conventions

1. **Date Spacing**:
   - In Word / WPS tables, dates typed as `2026. 8. 21` frequently have half-width space or full-width period spacing after each dot.
   - Always check the distance between `.` and the following digit in the original text (e.g. 12-14 px vs standard 4-5 px digit gap).
2. **Baseline Alignment**:
   - Chinese characters and Western digits in the same line share the bottom baseline.
   - Letters with descenders (`p`, `q`, `y`, `g`, `j`) extend below the baseline.
3. **Ink Bleed Simulation**:
   - Scanned physical prints exhibit ~0.3-0.5 px ink spread and slight grayscale anti-aliasing.
   - Blend pure digital text with a subtle `MinFilter(3)` morphological dilation at 25%-35% weight to seamlessly eliminate the "too-sharp digital paste" look.
