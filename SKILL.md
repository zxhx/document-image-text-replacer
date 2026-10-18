---
name: document-image-text-replacer
description: >-
  Seamlessly replaces dates, numbers, or text in document and table images while preserving typography, font, size, baseline, spacing, and scanned texture. Generates previews for user confirmation before overwriting. Use whenever asked to modify or replace dates, names, locations, numbers, or text in document scans, forms, or table images.
---

# Document Image Text Replacer

## Overview
This skill provides a systematic, typography-grounded workflow to seamlessly replace dates, numbers, headers, or cell contents in scanned/photographed document images, forms, and tables. It ensures that the replaced text is visually indistinguishable from the original by matching font family, point size, baseline, kerning, and scanned ink texture.

> [!IMPORTANT]
> **Always generate and present a cropped preview comparison (`preview_comparison.png`) to the user before overwriting the original file.** Never overwrite the original image without explicit user confirmation or review.

---

## Dependencies
- Python 3.10+
- `Pillow` (PIL)
- `numpy`
- Standard system fonts in `C:\Windows\Fonts` (STSong, SimSun, Times New Roman, SimHei, Arial, etc.)

---

## Quick Start

When the user asks to change text in an image (e.g. *"帮我将表格图片中的日期 '2026.8.21' 改为 '2026.5.30'，文字大小和规格保持现状"*):

1. **Locate Target Region**:
   Crop a small region around the text using Python/PIL to determine exact pixel bounding box `(x1, y1, x2, y2)`.
2. **Generate Preview**:
   Run the CLI tool to render replacement text with matched typography and generate a comparison preview:
   ```bash
   python "C:\Users\Zax\.gemini\config\skills\document-image-text-replacer\scripts\replacer.py" preview \
     --image "<image_path>" \
     --search-text "<old_text>" \
     --replace-text "<new_text>" \
     --box <x1> <y1> <x2> <y2> \
     --output-dir "<preview_dir>"
   ```
3. **Show Preview to User**:
   View and display the generated `preview_comparison.png` to the user and request confirmation.
4. **Apply Replacement**:
   Upon confirmation, apply the modification (which creates an automatic `_backup` and preserves all EXIF, DPI, and ICC profile metadata):
   ```bash
   python "C:\Users\Zax\.gemini\config\skills\document-image-text-replacer\scripts\replacer.py" apply \
     --meta-file "<preview_dir>\preview_meta.json"
   ```

---

## Utility Scripts

The CLI script is located at:
`C:\Users\Zax\.gemini\config\skills\document-image-text-replacer\scripts\replacer.py`

### Subcommands

#### 1. `preview`
Generates a side-by-side comparison image and 4x zoomed detail image without modifying the source image.
```bash
python replacer.py preview \
  --image "<path>" \
  --search-text "<text>" \
  --replace-text "<text>" \
  --box <x1> <y1> <x2> <y2> \
  --erase-box <ex1> <ey1> <ex2> <ey2> \
  --font-family <stsong|simsun|times|simhei|arial> \
  --font-size <pt> \
  --ink-bleed <0.0-1.0> \
  --output-dir "<dir>"
```
- `--box`: Target region `[x1, y1, x2, y2]` in the original full image.
- `--erase-box`: Relative region inside the crop to erase with clean background.
- `--font-family`: Matched font name (`stsong`, `simsun`, `times`, `simhei`, `arial`) or direct `.ttf` path.
- `--font-size`: Font size matching original height (consult `references/typography_guidelines.md`).
- `--ink-bleed`: Amount of morphological edge softening (default: `0.35`).
- `--clone-box` & `--clone-dest`: (Optional) Clone identical glyphs (e.g. `0` or `.`) directly from the crop.

#### 2. `apply`
Safely overwrites the original image using parameters from `preview_meta.json`.
```bash
python replacer.py apply \
  --meta-file "<preview_dir>\preview_meta.json" \
  [--backup-suffix "_backup"] \
  [--quality 95]
```
- Automatically creates `<filename>_backup.<ext>` before touching the original file.
- Preserves original DPI resolution, ICC color profile, and EXIF orientation tags.

---

## Workflow

### Step 1: Image Inspection & Typography Matching
1. Open the image with `Pillow` (supporting Chinese paths) and crop the target cell/sentence.
2. Measure digit/character height in pixels and baseline position.
3. Check `references/typography_guidelines.md` to map measured height to standard font families and sizes (e.g., 23-24 px at 120 DPI = 14 pt 四号 华文宋体).
4. Identify reusable glyphs:
   - If characters already exist in untouched parts of the document (e.g. `0` in `2026`, or original dots/colons), reuse them to preserve authentic scan noise.

### Step 2: Generate Preview
Run `replacer.py preview` to generate:
- `preview_comparison.png`: Direct comparison between Original and Modified.
- `preview_zoomed.png`: 4x zoomed view to verify stroke weight and antialiasing.
- `preview_meta.json`: Saved coordinates and rendering parameters.

### Step 3: Present Preview to User
Use `view_file` to inspect the preview image, then present the result to the user for explicit confirmation.

### Step 4: Apply & Final Verification
1. Run `replacer.py apply` to execute the replacement.
2. Verify the saved file on disk.
3. Inform the user of the updated file and the location of the `_backup` copy.

---

## Common Mistakes

1. **Skipping Preview Confirmation**:
   - *Never* directly overwrite the original image on turn 1. Always generate the preview and present it first.
2. **Ignoring Ink Bleed / Using Harsh Antialiasing**:
   - Digital text rendered with standard PIL often looks unnaturally crisp compared to printed/scanned paper. Always use the `--ink-bleed` filter (0.3-0.4) to blend edges into the paper texture.
3. **Breaking Metadata / Lowering Quality**:
   - Re-saving JPEGs without preserving `dpi` or using low quality settings will visibly blur the entire document. Always preserve `dpi`, `exif`, `icc_profile`, and use `quality=95` with `subsampling=0`.
4. **Over-erasing**:
   - Only erase the specific characters being replaced. Leave identical prefix/suffix characters (e.g. `2026. `) completely untouched.
