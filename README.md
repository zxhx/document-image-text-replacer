# Document Image Text Replacer (Antigravity Skill)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](https://www.python.org/)

An **Antigravity agent skill** and standalone CLI tool for **seamless, typography-matched text and date replacement** in scanned/photographed document images, forms, and tables.

---

## ✨ Features

- **Typography & Font Precision**: Automatically matches Chinese/English fonts (STSong, SimSun, Times New Roman, SimHei, Arial, etc.), point sizes, baselines, and kerning (e.g. half-width/full-width date dot spaces).
- **Scan & Ink Bleed Simulation**: Softens digital rasterization with subtle morphological dilation and edge blending to naturally match scanned paper texture and printer ink bleed.
- **Glyph Reuse**: Automatically reuses identical characters (like `0` or punctuation) present in untouched areas of the document to maximize visual authenticity.
- **Mandatory Preview Verification**: Generates side-by-side and 4x zoomed comparison previews before making any permanent changes to the image.
- **Lossless Metadata & Auto-Backup**: Preserves original image DPI, ICC color profile, and EXIF tags. Automatically creates a `_backup` copy before overwriting.

---

## 📂 Project Structure

```text
document-image-text-replacer/
├── SKILL.md                          # Skill definition & prompt instructions for Antigravity
├── README.md                         # Project documentation
├── requirements.txt                  # Python dependencies (Pillow, numpy)
├── LICENSE                           # MIT License
├── .gitignore                        # Git ignore patterns
├── scripts/
│   └── replacer.py                   # Core CLI tool (preview & apply)
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

> "帮我将表格图片中的日期 '2026.8.21' 改为 '2026.5.30'，文字大小和规格保持现状"
>
> *"Please replace the date '2026.8.21' in this table image with '2026.5.30', keeping font size, baseline, and scanned texture consistent."*

Antigravity will automatically:
1. Locate the text and analyze font metrics.
2. Render a cropped preview comparison (`preview_comparison.png`) for your review.
3. Upon your confirmation, backup the original file and apply the modification seamlessly.

---

## 🛠️ Standalone CLI Usage

You can also run the underlying tool directly from the command line:

### 1. Generate Preview
```bash
python scripts/replacer.py preview \
  --image "path/to/document.jpg" \
  --box 1250 368 1430 403 \
  --erase-box 95 0 175 35 \
  --text-x 97 --text-y -7 \
  --replace-text "5. 30" \
  --font-family stsong \
  --font-size 35 \
  --output-dir "./preview_output"
```

### 2. Apply Approved Modification
```bash
python scripts/replacer.py apply \
  --meta-file "./preview_output/preview_meta.json" \
  --backup-suffix "_backup"
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
