#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
document-image-text-replacer: CLI tool for seamless typography-matched text replacement
in document and table images.
"""

import os
import sys
import time

# Ensure UTF-8 I/O on Windows
if sys.platform == "win32":
    try:
        if sys.stdin: sys.stdin.reconfigure(encoding="utf-8")
        if sys.stdout: sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr: sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import json
import argparse
import shutil
import numpy as np
from PIL import Image, ImageFont, ImageDraw, ImageFilter

# Optional high-speed dependencies
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from rapidocr_onnxruntime import RapidOCR
    HAS_RAPIDOCR = True
except ImportError:
    HAS_RAPIDOCR = False


def load_image(image_path: str) -> Image.Image:
    """Load image safely supporting non-ASCII / Chinese paths on Windows."""
    norm_path = os.path.abspath(image_path)
    if not os.path.exists(norm_path):
        raise FileNotFoundError(f"Image not found: {norm_path}")
    return Image.open(norm_path)


def save_image(img: Image.Image, output_path: str, orig_img: Image.Image = None, quality: int = 95):
    """Save image preserving DPI, ICC profile, and EXIF."""
    save_kwargs = {}
    if orig_img is not None:
        if "dpi" in orig_img.info:
            save_kwargs["dpi"] = orig_img.info["dpi"]
        if "exif" in orig_img.info:
            save_kwargs["exif"] = orig_img.info["exif"]
        if "icc_profile" in orig_img.info:
            save_kwargs["icc_profile"] = orig_img.info["icc_profile"]

    ext = os.path.splitext(output_path)[1].lower()
    if ext in [".jpg", ".jpeg"]:
        save_kwargs["quality"] = quality
        save_kwargs["subsampling"] = 0
        img.convert("RGB").save(output_path, "JPEG", **save_kwargs)
    elif ext in [".png"]:
        img.save(output_path, "PNG", **save_kwargs)
    else:
        img.save(output_path, **save_kwargs)


def find_font(font_name: str = None) -> str:
    """Find installed font path on Windows or fallback."""
    windows_fonts = r"C:\Windows\Fonts"
    font_map = {
        "stsong": os.path.join(windows_fonts, "STSONG.TTF"),
        "simsun": os.path.join(windows_fonts, "simsun.ttc"),
        "simsunb": os.path.join(windows_fonts, "simsunb.ttf"),
        "times": os.path.join(windows_fonts, "times.ttf"),
        "times_bold": os.path.join(windows_fonts, "timesbd.ttf"),
        "timesbd": os.path.join(windows_fonts, "timesbd.ttf"),
        "simhei": os.path.join(windows_fonts, "simhei.ttf"),
        "msyh": os.path.join(windows_fonts, "msyh.ttc"),
        "msyhbd": os.path.join(windows_fonts, "msyhbd.ttc"),
        "arial": os.path.join(windows_fonts, "arial.ttf"),
        "arialbd": os.path.join(windows_fonts, "arialbd.ttf"),
        "kaiti": os.path.join(windows_fonts, "simkai.ttf"),
        "fangsong": os.path.join(windows_fonts, "simfang.ttf")
    }
    if font_name and font_name.lower() in font_map and os.path.exists(font_map[font_name.lower()]):
        return font_map[font_name.lower()]
    if font_name and os.path.exists(font_name):
        return font_name
    for cand in [font_map["stsong"], font_map["simsun"], font_map["times"]]:
        if os.path.exists(cand):
            return cand
    return None


def enhance_glyph_ink(canvas: Image.Image, bleed_ratio: float = 0.28) -> Image.Image:
    """Simulate printed/scanned ink bleed via morphological min filter."""
    if bleed_ratio <= 0.0:
        return canvas
    arr = np.array(canvas, dtype=float)
    arr_pil = Image.fromarray(arr.astype(np.uint8))
    dilated = np.array(arr_pil.filter(ImageFilter.MinFilter(3)), dtype=float)
    blended = arr * (1.0 - bleed_ratio) + dilated * bleed_ratio
    return Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8))


def auto_locate_text(img: Image.Image, search_text: str, roi=None):
    """
    Locate search_text using RapidOCR.
    roi: Optional [x1, y1, x2, y2] to restrict search area for massive speedup.
    Returns: ((x1, y1, x2, y2), matched_text, score)
    """
    if not HAS_RAPIDOCR:
        raise RuntimeError("RapidOCR is not installed. Please install 'rapidocr-onnxruntime'.")

    engine = RapidOCR()
    w_full, h_full = img.size

    x_offset, y_offset = 0, 0
    if roi and len(roi) == 4:
        rx1, ry1, rx2, ry2 = roi
        ocr_img = img.crop((rx1, ry1, rx2, ry2))
        x_offset, y_offset = rx1, ry1
    else:
        ocr_img = img

    ocr_np = np.array(ocr_img)
    result, _ = engine(ocr_np)
    if not result:
        return None

    clean_search = search_text.replace(" ", "").strip()

    best_match = None
    highest_score = -1.0

    for item in result:
        box, text, score = item
        clean_item_text = text.replace(" ", "").strip()
        score_val = float(score) if isinstance(score, (float, int, str)) else 0.0

        if clean_search in clean_item_text:
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            full_box = (
                int(min(xs)) + x_offset,
                int(min(ys)) + y_offset,
                int(max(xs)) + x_offset,
                int(max(ys)) + y_offset
            )
            return full_box, text, score_val

        # Fuzzy containment (for minor OCR punctuation noise)
        if len(clean_search) >= 3 and (clean_search in clean_item_text or clean_item_text in clean_search):
            if score_val > highest_score:
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                full_box = (
                    int(min(xs)) + x_offset,
                    int(min(ys)) + y_offset,
                    int(max(xs)) + x_offset,
                    int(max(ys)) + y_offset
                )
                best_match = (full_box, text, score_val)
                highest_score = score_val

    return best_match


def auto_fit_font(target_crop_gray: np.ndarray, search_text: str):
    """
    Automatically fits the best font family, size, and (dx, dy) offset
    by minimizing difference against the target text crop.
    """
    th, tw = target_crop_gray.shape
    is_cjk = any('\u4e00' <= char <= '\u9fff' for char in search_text)

    # Estimate height from dark pixels
    dark = target_crop_gray < 160
    rows = np.where(np.sum(dark, axis=1) > 0)[0]
    est_h = (rows[-1] - rows[0] + 1) if len(rows) > 0 else th
    base_sz = max(12, int(est_h * 1.35))

    candidate_sizes = [base_sz - 2, base_sz - 1, base_sz, base_sz + 1, base_sz + 2]

    if is_cjk:
        cand_fonts = ["stsong", "simsun", "simhei", "msyh", "kaiti", "fangsong"]
    else:
        cand_fonts = ["times_bold", "times", "simsun", "stsong", "arialbd", "arial"]

    best_match = None
    min_diff = 1e9

    for fname in cand_fonts:
        fpath = find_font(fname)
        if not fpath or not os.path.exists(fpath):
            continue

        for sz in candidate_sizes:
            try:
                f = ImageFont.truetype(fpath, sz)
            except Exception:
                continue

            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    c = Image.new("L", (tw, th), 255)
                    d = ImageDraw.Draw(c)
                    d.text((dx, dy), search_text, font=f, fill=0)
                    c_arr = np.array(c)
                    diff = np.mean(np.abs(target_crop_gray.astype(float) - c_arr.astype(float)))
                    if diff < min_diff:
                        min_diff = diff
                        best_match = {
                            "font_family": fname,
                            "font_path": fpath,
                            "font_size": sz,
                            "offset_x": dx,
                            "offset_y": dy,
                            "diff": float(diff)
                        }

    return best_match


def inpaint_text_background(crop_img: Image.Image, rel_box: tuple) -> Image.Image:
    """
    Seamlessly erases old text inside rel_box while preserving paper texture,
    scanner noise, and table borders.
    """
    crop_np = np.array(crop_img)
    rx1, ry1, rx2, ry2 = rel_box

    if HAS_CV2:
        gray = cv2.cvtColor(crop_np, cv2.COLOR_RGB2GRAY)
        mask = np.zeros_like(gray)
        target_roi = gray[ry1:ry2, rx1:rx2]
        
        # Estimate background brightness
        bright_pixels = target_roi[target_roi > 180]
        bg_val = np.median(bright_pixels) if len(bright_pixels) > 0 else 250.0
        
        # Select dark text strokes within target box
        ink_pixels = target_roi < (bg_val - 35)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        ink_dilated = cv2.dilate(ink_pixels.astype(np.uint8), kernel, iterations=1)
        mask[ry1:ry2, rx1:rx2] = ink_dilated * 255
        
        # Telea inpainting preserves natural texture
        inpainted = cv2.inpaint(crop_np, mask, 3, cv2.INPAINT_TELEA)
        return Image.fromarray(inpainted)
    else:
        # Fallback without OpenCV: local patch sampling
        mod = crop_img.copy()
        mod_arr = np.array(mod)
        bg_val = int(np.median(mod_arr[max(0, ry1-10):ry1, :]))
        mod_arr[ry1:ry2, rx1:rx2] = bg_val
        return Image.fromarray(mod_arr)


def cmd_auto(params: dict):
    """
    High-speed end-to-end automated replacement command.
    """
    t0 = time.time()
    image_path = params["image"]
    search_text = params["search_text"]
    replace_text = params["replace_text"]
    output_dir = params.get("output_dir", "./preview")
    roi = params.get("roi")
    ink_bleed = params.get("ink_bleed", 0.28)
    specified_font = params.get("font_family")
    specified_size = params.get("font_size")

    os.makedirs(output_dir, exist_ok=True)
    img = load_image(image_path)
    w_full, h_full = img.size

    # Step 1: Rapid Auto-Localization
    t_loc_0 = time.time()
    loc_res = auto_locate_text(img, search_text, roi=roi)
    if not loc_res:
        raise ValueError(f"Could not locate text '{search_text}' in image.")
    target_box, detected_text, ocr_score = loc_res
    t_loc = time.time() - t_loc_0

    # Padded crop for context view
    pad_x = params.get("pad_x", 50)
    pad_y = params.get("pad_y", 30)
    crop_x1 = max(0, target_box[0] - pad_x)
    crop_y1 = max(0, target_box[1] - pad_y)
    crop_x2 = min(w_full, target_box[2] + pad_x)
    crop_y2 = min(h_full, target_box[3] + pad_y)

    crop = img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
    rel_box = (
        target_box[0] - crop_x1,
        target_box[1] - crop_y1,
        target_box[2] - crop_x1,
        target_box[3] - crop_y1
    )

    # Step 2: Auto Font Matching
    t_font_0 = time.time()
    crop_gray = np.array(crop.convert("L"))
    target_gray = crop_gray[rel_box[1]:rel_box[3], rel_box[0]:rel_box[2]]

    if specified_font and specified_size:
        font_path = find_font(specified_font)
        best_font = {
            "font_family": specified_font,
            "font_path": font_path,
            "font_size": specified_size,
            "offset_x": 0,
            "offset_y": 0,
            "diff": 0.0
        }
    else:
        best_font = auto_fit_font(target_gray, search_text)
        if not best_font:
            default_f = find_font("times_bold" if not any('\u4e00' <= c <= '\u9fff' for c in search_text) else "stsong")
            best_font = {
                "font_family": "auto_fallback",
                "font_path": default_f,
                "font_size": 35,
                "offset_x": 0,
                "offset_y": 0,
                "diff": 0.0
            }
    t_font = time.time() - t_font_0

    # Step 3: Seamless Background Inpainting
    t_inpaint_0 = time.time()
    inpainted_crop = inpaint_text_background(crop, rel_box)
    t_inpaint = time.time() - t_inpaint_0

    # Step 4: Text Rendering with Ink Bleed & Baseline Alignment
    f = ImageFont.truetype(best_font["font_path"], best_font["font_size"])
    c_text = Image.new("L", inpainted_crop.size, 255)
    td = ImageDraw.Draw(c_text)

    # Calculate draw position
    draw_x = rel_box[0] + best_font.get("offset_x", 0)
    draw_y = rel_box[1] + best_font.get("offset_y", 0)
    td.text((draw_x, draw_y), replace_text, font=f, fill=0)

    # Apply ink bleed
    enh_text = enhance_glyph_ink(c_text, bleed_ratio=ink_bleed)

    # Sample ink color from original dark pixels
    orig_np = np.array(crop)
    target_orig = orig_np[rel_box[1]:rel_box[3], rel_box[0]:rel_box[2]]
    dark_mask = target_gray < 100
    if np.any(dark_mask):
        ink_r = int(np.median(target_orig[:, :, 0][dark_mask]))
        ink_g = int(np.median(target_orig[:, :, 1][dark_mask]))
        ink_b = int(np.median(target_orig[:, :, 2][dark_mask]))
        ink_color = (ink_r, ink_g, ink_b)
    else:
        ink_color = (25, 25, 25)

    # Composite text onto inpainted background
    mask = Image.eval(enh_text, lambda p: 255 - p if p < 240 else 0)
    mod_crop = inpainted_crop.copy()
    mod_crop.paste(Image.new("RGB", mod_crop.size, ink_color), (0, 0), mask)

    # Step 5: Generate Comparison Previews
    cw, ch = crop.size
    preview_comp = Image.new("RGB", (cw * 2 + 40, ch + 60), (250, 251, 252))
    pd = ImageDraw.Draw(preview_comp)
    preview_comp.paste(crop, (15, 40))
    preview_comp.paste(mod_crop, (cw + 25, 40))
    pd.text((15, 15), f"Original: [{search_text}]", fill=(60, 60, 60))
    pd.text((cw + 25, 15), f"Modified: [{replace_text}] ({best_font['font_family']} {best_font['font_size']}pt)", fill=(0, 102, 204))

    comp_path = os.path.join(output_dir, "preview_comparison.png")
    preview_comp.save(comp_path)

    # 4x Zoom Detail
    tight_orig = crop.crop(rel_box)
    # Give replace_text its corresponding crop width
    text_bbox = f.getbbox(replace_text)
    mod_w = max(rel_box[2] - rel_box[0], text_bbox[2] - text_bbox[0] + 10)
    tight_mod = mod_crop.crop((rel_box[0], rel_box[1], rel_box[0] + mod_w, rel_box[3]))

    zh = (rel_box[3] - rel_box[1]) * 4
    tight_orig_4x = tight_orig.resize((tight_orig.width * 4, zh), Image.Resampling.NEAREST)
    tight_mod_4x = tight_mod.resize((tight_mod.width * 4, zh), Image.Resampling.NEAREST)

    zw = tight_orig_4x.width + tight_mod_4x.width + 40
    zoom_preview = Image.new("RGB", (zw, zh + 40), (250, 251, 252))
    zd = ImageDraw.Draw(zoom_preview)
    zoom_preview.paste(tight_orig_4x, (15, 25))
    zoom_preview.paste(tight_mod_4x, (tight_orig_4x.width + 25, 25))
    zd.text((15, 5), f"4x Zoom Original", fill=(60, 60, 60))
    zd.text((tight_orig_4x.width + 25, 5), f"4x Zoom Modified", fill=(0, 102, 204))

    zoom_path = os.path.join(output_dir, "preview_zoomed.png")
    zoom_preview.save(zoom_path)

    patch_path = os.path.join(output_dir, "modified_patch.png")
    mod_crop.save(patch_path)

    total_time = (time.time() - t0) * 1000

    meta = {
        "image": os.path.abspath(image_path),
        "box": [crop_x1, crop_y1, crop_x2, crop_y2],
        "search_text": search_text,
        "replace_text": replace_text,
        "patch_file": os.path.abspath(patch_path),
        "comparison_preview": os.path.abspath(comp_path),
        "zoomed_preview": os.path.abspath(zoom_path),
        "font_family": best_font["font_family"],
        "font_size": best_font["font_size"],
        "timings_ms": {
            "locate": round(t_loc * 1000, 1),
            "font_matching": round(t_font * 1000, 1),
            "inpaint": round(t_inpaint * 1000, 1),
            "total": round(total_time, 1)
        }
    }
    meta_path = os.path.join(output_dir, "preview_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    result_json = {
        "status": "success",
        "message": f"Auto replacement preview generated in {total_time:.1f}ms",
        "comparison_preview": os.path.abspath(comp_path),
        "zoomed_preview": os.path.abspath(zoom_path),
        "meta_file": os.path.abspath(meta_path),
        "matched_font": f"{best_font['font_family']} {best_font['font_size']}pt",
        "target_box": target_box,
        "timings": meta["timings_ms"]
    }
    print(json.dumps(result_json, ensure_ascii=False))


def cmd_preview(params: dict):
    """Manual/specified preview generation (retained for backward compatibility)."""
    image_path = params["image"]
    img = load_image(image_path)
    output_dir = params["output_dir"]
    os.makedirs(output_dir, exist_ok=True)

    box = params.get("box")
    if not box or len(box) != 4:
        raise ValueError("Must provide 'box': [x1, y1, x2, y2]")
    x1, y1, x2, y2 = box

    crop = img.crop((x1, y1, x2, y2))
    crop_w, crop_h = crop.size

    font_path = find_font(params.get("font_family", "stsong"))
    font_size = params.get("font_size", 35)
    font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()

    erase_box = params.get("erase_box", [0, 0, crop_w, crop_h])
    inpainted = inpaint_text_background(crop, erase_box)

    draw_x = params.get("text_x", erase_box[0])
    draw_y = params.get("text_y", erase_box[1])

    replace_text = params.get("replace_text", "")
    mod_img = inpainted.copy()
    if replace_text:
        t_canvas = Image.new("L", (crop_w, crop_h), 255)
        d = ImageDraw.Draw(t_canvas)
        d.text((draw_x, draw_y), replace_text, font=font, fill=0)

        bleed = params.get("ink_bleed", 0.28)
        if bleed > 0:
            t_canvas = enhance_glyph_ink(t_canvas, bleed)

        mask = Image.eval(t_canvas, lambda p: 255 - p)
        mod_img.paste(t_canvas, (0, 0), mask)

    # Save previews
    preview_comp = Image.new("RGB", (crop_w * 2 + 40, crop_h + 50), (255, 255, 255))
    pd = ImageDraw.Draw(preview_comp)
    preview_comp.paste(crop, (15, 30))
    preview_comp.paste(mod_img, (crop_w + 25, 30))
    pd.text((15, 10), f"Original: [{params.get('search_text', 'Target')}]", fill=0)
    pd.text((crop_w + 25, 10), f"Modified: [{replace_text}]", fill=0)

    comp_path = os.path.join(output_dir, "preview_comparison.png")
    preview_comp.save(comp_path)

    patch_path = os.path.join(output_dir, "modified_patch.png")
    mod_img.save(patch_path)

    meta = {
        "image": os.path.abspath(image_path),
        "box": [x1, y1, x2, y2],
        "search_text": params.get("search_text", ""),
        "replace_text": replace_text,
        "patch_file": os.path.abspath(patch_path),
        "comparison_preview": os.path.abspath(comp_path),
        "font_family": params.get("font_family", "stsong"),
        "font_size": font_size
    }
    meta_path = os.path.join(output_dir, "preview_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(json.dumps({
        "status": "success",
        "message": "Preview generated successfully.",
        "comparison_preview": os.path.abspath(comp_path),
        "meta_file": os.path.abspath(meta_path)
    }, ensure_ascii=False))


def cmd_apply(meta_file: str, backup_suffix: str = "_backup", quality: int = 95):
    """Apply the approved preview patch to the original image with backup."""
    with open(meta_file, "r", encoding="utf-8") as f:
        meta = json.load(f)

    image_path = meta["image"]
    x1, y1, x2, y2 = meta["box"]
    patch_path = meta["patch_file"]

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Target image not found: {image_path}")
    if not os.path.exists(patch_path):
        raise FileNotFoundError(f"Patch file not found: {patch_path}")

    dir_name, base_name = os.path.split(image_path)
    name_part, ext_part = os.path.splitext(base_name)
    backup_path = os.path.join(dir_name, f"{name_part}{backup_suffix}{ext_part}")

    if not os.path.exists(backup_path):
        shutil.copy2(image_path, backup_path)

    orig_img = load_image(image_path)
    patch_img = load_image(patch_path)

    full_mod = orig_img.copy()
    full_mod.paste(patch_img, (x1, y1))

    save_image(full_mod, image_path, orig_img=orig_img, quality=quality)

    print(json.dumps({
        "status": "success",
        "message": "Modification applied successfully.",
        "target_file": image_path,
        "backup_file": backup_path
    }, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Document Image Text Replacer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: auto (Recommended high-speed path)
    p_auto = subparsers.add_parser("auto", help="High-speed end-to-end auto replacement")
    p_auto.add_argument("--config", help="Path to JSON config file")
    p_auto.add_argument("--image", help="Path to input image")
    p_auto.add_argument("--search-text", "--search", help="Original text to locate and replace")
    p_auto.add_argument("--replace-text", "--replace", help="Replacement text")
    p_auto.add_argument("--roi", type=int, nargs=4, metavar=("X1", "Y1", "X2", "Y2"), help="Coarse ROI search region")
    p_auto.add_argument("--pad-x", type=int, default=50, help="Horizontal padding around text box for preview")
    p_auto.add_argument("--pad-y", type=int, default=30, help="Vertical padding around text box for preview")
    p_auto.add_argument("--font-family", help="Override auto-detected font family")
    p_auto.add_argument("--font-size", type=int, help="Override auto-detected font size")
    p_auto.add_argument("--ink-bleed", type=float, default=0.28, help="Ink bleed ratio (default: 0.28)")
    p_auto.add_argument("--output-dir", default="./preview", help="Directory to save preview artifacts")

    # Subcommand: preview (Manual fallback)
    p_preview = subparsers.add_parser("preview", help="Generate preview comparison with manual box")
    p_preview.add_argument("--config", help="Path to JSON config file")
    p_preview.add_argument("--image", help="Path to input image")
    p_preview.add_argument("--search-text", default="", help="Original text")
    p_preview.add_argument("--replace-text", default="", help="Replacement text")
    p_preview.add_argument("--box", type=int, nargs=4, metavar=("X1", "Y1", "X2", "Y2"), help="Bounding box")
    p_preview.add_argument("--erase-box", type=int, nargs=4, metavar=("EX1", "EY1", "EX2", "EY2"), help="Erase box")
    p_preview.add_argument("--text-x", type=int, help="X position of rendered text in crop")
    p_preview.add_argument("--text-y", type=int, help="Y position of rendered text in crop")
    p_preview.add_argument("--font-family", default="stsong", help="Font family name")
    p_preview.add_argument("--font-size", type=int, default=35, help="Font size")
    p_preview.add_argument("--ink-bleed", type=float, default=0.28, help="Ink bleed ratio")
    p_preview.add_argument("--output-dir", default="./preview", help="Directory to save preview artifacts")

    # Subcommand: apply
    p_apply = subparsers.add_parser("apply", help="Apply approved modification to image")
    p_apply.add_argument("--meta-file", required=True, help="Path to preview_meta.json")
    p_apply.add_argument("--backup-suffix", default="_backup", help="Suffix for backup file")
    p_apply.add_argument("--quality", type=int, default=95, help="JPEG quality")

    args = parser.parse_args()

    if args.command == "auto":
        if args.config:
            with open(args.config, "r", encoding="utf-8") as f:
                params = json.load(f)
        else:
            params = {
                "image": args.image,
                "search_text": args.search_text,
                "replace_text": args.replace_text,
                "roi": args.roi,
                "pad_x": args.pad_x,
                "pad_y": args.pad_y,
                "font_family": args.font_family,
                "font_size": args.font_size,
                "ink_bleed": args.ink_bleed,
                "output_dir": args.output_dir
            }
        cmd_auto(params)

    elif args.command == "preview":
        if args.config:
            with open(args.config, "r", encoding="utf-8") as f:
                params = json.load(f)
        else:
            params = {
                "image": args.image,
                "search_text": args.search_text,
                "replace_text": args.replace_text,
                "box": args.box,
                "erase_box": args.erase_box,
                "text_x": args.text_x,
                "text_y": args.text_y,
                "font_family": args.font_family,
                "font_size": args.font_size,
                "ink_bleed": args.ink_bleed,
                "output_dir": args.output_dir
            }
        cmd_preview(params)

    elif args.command == "apply":
        cmd_apply(args.meta_file, backup_suffix=args.backup_suffix, quality=args.quality)


if __name__ == "__main__":
    main()
