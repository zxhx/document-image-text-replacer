# Document Image Text Replacer (Antigravity Skill)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](https://www.python.org/)

An **Antigravity agent skill** and standalone high-speed CLI tool for **seamless, typography-matched text, date, and number replacement** in scanned/photographed document images, forms, and tables.

> [!NOTE]
> **Update: optimise execution speed**

---

## ✨ Features

- **🚀 High-Speed Auto Pipeline (`auto` mode)**: Powered by local RapidOCR and OpenCV, automatically locates target text, fits font & size, in-paints background, and generates side-by-side comparison previews in **under 7 seconds** in a single step.
- **🔍 Seamless OpenCV Inpainting**: Utilizes Telea inpainting on character strokes to erase old text while preserving paper texture, scanner grain, and adjacent table borders without artificial white boxes or seams.
- **🎨 Auto Font & Size Fitting**: Automatically fits the closest standard font family (华文宋体, 中易宋体, Times New Roman Bold, 黑体, Arial, etc.), point size, and baseline offset.
- **🖨️ Scan & Ink Bleed Simulation**: Softens digital rasterization with morphological edge dilation and ink blending to naturally match scanned paper texture and printer ink spread.
- **🛡️ Mandatory Preview Verification**: Generates side-by-side and 4x zoomed comparison previews before making any permanent changes to the image.
- **💾 Lossless Metadata & Auto-Backup**: Preserves original image DPI (e.g. 120 or 300 DPI), ICC color profile, and EXIF tags. Automatically creates a `_backup` copy before overwriting.

---

## 📂 Project Structure

```text
document-image-text-replacer/
├── SKILL.md                          # Skill definition & prompt instructions for Antigravity
├── README.md                         # Project documentation
├── requirements.txt                  # Python dependencies (Pillow, numpy, rapidocr, opencv)
├── LICENSE                           # MIT License
├── .gitignore                        # Git ignore patterns
├── scripts/
│   └── replacer.py                   # Core CLI tool (auto, preview, apply)
└── references/
    └── typography_guidelines.md      # Font size mapping, DPI conversions & typography rules
```

---

## 🚀 Installation

### As an Antigravity Global Skill (Recommended)

Clone this repository directly into your Antigravity global configuration directory:

#### Windows (PowerShell):
```powershell
git clone https://github.com/zxhx/document-image-text-replacer.git "$HOME\.gemini\config\skills\document-image-text-replacer"
pip install -r "$HOME\.gemini\config\skills\document-image-text-replacer\requirements.txt"
```

#### macOS / Linux:
```bash
git clone https://github.com/zxhx/document-image-text-replacer.git ~/.gemini/config/skills/document-image-text-replacer
pip install -r ~/.gemini/config/skills/document-image-text-replacer/requirements.txt
```

Once cloned, Antigravity will automatically discover and load the skill across all projects and chat sessions!

---

## 💬 Usage with Antigravity AI

Simply ask Antigravity naturally in any workspace:

> "帮我将表格图片中的地点 '44506' 改为 '43411'，文字大小和规格保持现状"
>
> *"Please replace '44506' with '43411' in this table image, keeping font size, baseline, and scanned texture consistent."*

Antigravity will automatically:
1. Run the `auto` pipeline to locate the text, match font metrics, and inpaint background.
2. Render a cropped preview comparison (`preview_comparison.png`) for your review.
3. Upon your confirmation, backup the original file and apply the modification seamlessly.

---

## 🛠️ Standalone CLI Usage

### 1. High-Speed Auto Mode (Recommended)
Automatically detects target text coordinates and fits typography:
```bash
python scripts/replacer.py auto \
  --image "path/to/document.jpg" \
  --search "44506" \
  --replace "43411" \
  --output-dir "./preview_output"
```

*(Optional)* Speed up OCR by restricting search to a coarse region:
```bash
python scripts/replacer.py auto \
  --image "path/to/document.jpg" \
  --search "44506" \
  --replace "43411" \
  --roi 1000 400 1600 650 \
  --output-dir "./preview_output"
```

### 2. Manual Preview Mode
For manual bounding box specifications:
```bash
python scripts/replacer.py preview \
  --image "path/to/document.jpg" \
  --box 1250 368 1430 403 \
  --search-text "2026.8.21" \
  --replace-text "2026.5.30" \
  --output-dir "./preview_output"
```

### 3. Apply Approved Modification
```bash
python scripts/replacer.py apply \
  --meta-file "./preview_output/preview_meta.json" \
  --backup-suffix "_backup"
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
