---
name: document-image-text-replacer
description: >-
  Seamlessly replaces dates, numbers, or text in document and table images while preserving typography, font, size, baseline, spacing, and scanned texture. Generates previews for user confirmation before overwriting. Use whenever asked to modify or replace dates, names, locations, numbers, or text in document scans, forms, or table images.
---

# Document Image Text Replacer

## Overview
This skill provides a high-speed, typography-grounded workflow to seamlessly replace dates, numbers, headers, or cell contents in scanned/photographed document images, forms, and tables. 

It automatically detects target text locations using local **RapidOCR**, fits the closest standard font family and size, seamlessly in-paints the background with **OpenCV Telea**, and simulates authentic print/scanner ink spread.

> [!IMPORTANT]
> **Always generate and present a cropped preview comparison (`preview_comparison.png`) to the user before overwriting the original file.** Never overwrite the original image without explicit user confirmation or review.

---

## Dependencies
- Python 3.10+
- `Pillow`
- `numpy`
- `rapidocr-onnxruntime` (for high-speed local OCR localization)
- `opencv-python` (for seamless background inpainting)
- Standard system fonts in `C:\Windows\Fonts` (STSong, SimSun, Times New Roman, SimHei, Arial, etc.)

---

## Quick Start (Recommended: High-Speed Auto Pipeline)

When the user asks to change text in an image (e.g. *"帮我将表格图片中的地点 '44506' 改为 '43411'，文字大小和规格保持现状"*):

### 1. Generate Preview in 1 Step (`auto`)
Run the all-in-one automated replacement command. It automatically locates the text, fits font family and point size, in-paints the background texture, and generates comparison previews in ~5-7 seconds:

```bash
python "C:\Users\Zax\.gemini\config\skills\document-image-text-replacer\scripts\replacer.py" auto \
  --image "<image_path>" \
  --search "<old_text>" \
  --replace "<new_text>" \
  --output-dir "<preview_dir>"
```

*(Optional)* If a coarse location hint is known (e.g. table header or top half), pass `--roi <x1> <y1> <x2> <y2>` to restrict search area and accelerate OCR.

### 2. Present Preview to User
View and display the generated `preview_comparison.png` to the user and request confirmation:
```
preview_dir/
├── preview_comparison.png   # Side-by-side comparison of original vs modified
├── preview_zoomed.png       # 4x zoomed detail comparison
├── modified_patch.png       # Rendered patch ready for application
└── preview_meta.json        # Auto-saved metadata, coordinates, and timings
```

### 3. Apply Replacement Upon Confirmation (`apply`)
Upon user confirmation, safely overwrite the target image:
```bash
python "C:\Users\Zax\.gemini\config\skills\document-image-text-replacer\scripts\replacer.py" apply \
  --meta-file "<preview_dir>\preview_meta.json"
```
- Automatically creates `<filename>_backup.<ext>` before modifying.
- Preserves original DPI resolution, ICC color profile, and EXIF orientation metadata.

---

## Utility Script Reference

CLI script path:
`C:\Users\Zax\.gemini\config\skills\document-image-text-replacer\scripts\replacer.py`

### Subcommands

#### 1. `auto` (High-Speed Automated Pipeline)
```bash
python replacer.py auto \
  --image "<image_path>" \
  --search "<old_text>" \
  --replace "<new_text>" \
  [--roi <x1> <y1> <x2> <y2>] \
  [--font-family <family>] \
  [--font-size <pt>] \
  [--ink-bleed <0.0-1.0>] \
  [--output-dir "<dir>"]
```
- `--search`: Text to search and replace.
- `--replace`: Replacement string.
- `--roi`: Optional coarse region `[x1, y1, x2, y2]` to restrict OCR search for faster execution.
- `--font-family`: Optional override if specific font is desired.
- `--font-size`: Optional override for font size.
- `--ink-bleed`: Morphological edge softening ratio (default: `0.28`).

#### 2. `preview` (Manual Coordinates Mode)
Use when target text cannot be detected by OCR (e.g. faint handwritten text or severely distorted image):
```bash
python replacer.py preview \
  --image "<path>" \
  --search-text "<text>" \
  --replace-text "<text>" \
  --box <x1> <y1> <x2> <y2> \
  --font-family <stsong|simsun|times_bold|simhei|arial> \
  --font-size <pt> \
  --output-dir "<dir>"
```

#### 3. `apply` (Safe Overwrite with Backup)
```bash
python replacer.py apply \
  --meta-file "<preview_dir>\preview_meta.json" \
  [--backup-suffix "_backup"] \
  [--quality 95]
```

---

## Best Practices

1. **Prefer `auto` for 99% of tasks**:
   The `auto` pipeline handles character location, typography matching, and texture inpainting automatically in a single command, eliminating multi-turn manual trial-and-error scripts.
2. **Always Show Preview**:
   Never skip preview presentation. Confirm visual quality with the user before executing `apply`.
3. **Preserve Metadata**:
   The tool automatically retains DPI (e.g. 120 or 300 DPI) and EXIF metadata so the modified document does not become blurry or loose print scale.
