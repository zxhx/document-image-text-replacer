#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
document-image-text-replacer: CLI tool for seamless typography-matched text replacement
in document and table images.
"""

import os
import sys

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


def load_image(image_path: str) -> Image.Image:
    """Load image safely supporting Chinese paths on Windows."""
    # Normalize path
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


def find_font(font_name: str = None):
    """Find installed font path on Windows or fallback."""
    windows_fonts = r"C:\Windows\Fonts"
    font_map = {
        "stsong": os.path.join(windows_fonts, "STSONG.TTF"),
        "simsun": os.path.join(windows_fonts, "simsun.ttc"),
        "simsunb": os.path.join(windows_fonts, "simsunb.ttf"),
        "times": os.path.join(windows_fonts, "times.ttf"),
        "timesbd": os.path.join(windows_fonts, "timesbd.ttf"),
        "simhei": os.path.join(windows_fonts, "simhei.ttf"),
        "msyh": os.path.join(windows_fonts, "msyh.ttc"),
        "arial": os.path.join(windows_fonts, "arial.ttf"),
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


def enhance_glyph_ink(canvas: Image.Image, bleed_ratio: float = 0.35) -> Image.Image:
    """Simulate printed/scanned ink bleed via subtle morphological min filter."""
    arr = np.array(canvas, dtype=float)
    arr_pil = Image.fromarray(arr.astype(np.uint8))
    dilated = np.array(arr_pil.filter(ImageFilter.MinFilter(3)), dtype=float)
    blended = arr * (1.0 - bleed_ratio) + dilated * bleed_ratio
    return Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8))


def cmd_preview(params: dict):
    """Generate preview comparison for text replacement."""
    image_path = params["image"]
    img = load_image(image_path)
    w_full, h_full = img.size
    
    output_dir = params["output_dir"]
    os.makedirs(output_dir, exist_ok=True)
    
    # Coordinates of target box
    box = params.get("box")
    if not box or len(box) != 4:
        raise ValueError("Must provide 'box': [x1, y1, x2, y2] to specify target crop area")
    x1, y1, x2, y2 = box
    
    crop = img.crop((x1, y1, x2, y2))
    crop_w, crop_h = crop.size
    
    # Font setup
    font_path = find_font(params.get("font_family", "stsong"))
    font_size = params.get("font_size", 35)
    font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
    
    modified = crop.copy()
    mod_arr = np.array(modified)
    
    erase_box = params.get("erase_box")
    if erase_box and len(erase_box) == 4:
        ex1, ey1, ex2, ey2 = erase_box
    else:
        ex1, ey1, ex2, ey2 = 0, 0, crop_w, crop_h
    
    # Fill erased region with background color
    bg_val = 255
    mod_arr[ey1:ey2, ex1:ex2] = bg_val
    mod_img = Image.fromarray(mod_arr)
    
    draw_x = params.get("text_x", ex1)
    draw_y = params.get("text_y", ey1)
    
    replace_text = params.get("replace_text", "")
    if replace_text:
        t_canvas = Image.new("L", (crop_w, crop_h), 255)
        d = ImageDraw.Draw(t_canvas)
        d.text((draw_x, draw_y), replace_text, font=font, fill=0)
        
        bleed = params.get("ink_bleed", 0.35)
        if bleed > 0:
            t_canvas = enhance_glyph_ink(t_canvas, bleed)
        
        mask = Image.eval(t_canvas, lambda p: 255 - p)
        mod_img.paste(t_canvas, (0, 0), mask)
    
    # Optional glyph clone
    clone_box = params.get("clone_box")
    clone_dest = params.get("clone_dest")
    if clone_box and clone_dest:
        cloned_glyph = crop.crop(tuple(clone_box))
        mod_img.paste(cloned_glyph, tuple(clone_dest))
    
    # Build comparison preview
    preview_comp = Image.new("RGB", (crop_w + 40, crop_h * 2 + 60), (255, 255, 255))
    d_p = ImageDraw.Draw(preview_comp)
    preview_comp.paste(crop, (20, 20))
    d_p.text((20, 5), f"Original [{params.get('search_text', 'Target')}]:", fill=(0, 0, 0))
    preview_comp.paste(mod_img, (20, crop_h + 35))
    d_p.text((20, crop_h + 20), f"Modified [{replace_text}]:", fill=(0, 0, 0))
    
    comp_path = os.path.join(output_dir, "preview_comparison.png")
    preview_comp.save(comp_path)
    
    # 4x Zoom comparison
    zoom_orig = crop.resize((crop_w * 4, crop_h * 4), Image.Resampling.NEAREST)
    zoom_mod = mod_img.resize((crop_w * 4, crop_h * 4), Image.Resampling.NEAREST)
    zoom_comp = Image.new("RGB", (crop_w * 4, crop_h * 8 + 30), (255, 255, 255))
    zoom_comp.paste(zoom_orig, (0, 0))
    zoom_comp.paste(zoom_mod, (0, crop_h * 4 + 15))
    
    zoom_path = os.path.join(output_dir, "preview_zoomed.png")
    zoom_comp.save(zoom_path)
    
    patch_path = os.path.join(output_dir, "modified_patch.png")
    mod_img.save(patch_path)
    
    meta = {
        "image": image_path,
        "box": [x1, y1, x2, y2],
        "search_text": params.get("search_text", ""),
        "replace_text": replace_text,
        "patch_file": patch_path,
        "comparison_preview": comp_path,
        "zoomed_preview": zoom_path,
        "font_family": params.get("font_family", "stsong"),
        "font_size": font_size
    }
    meta_path = os.path.join(output_dir, "preview_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    print(json.dumps({
        "status": "success",
        "message": "Preview generated successfully.",
        "comparison_preview": comp_path,
        "zoomed_preview": zoom_path,
        "meta_file": meta_path
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
    
    # Avoid overwriting existing backup if it already exists
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
    
    # Subcommand: preview
    p_preview = subparsers.add_parser("preview", help="Generate preview comparison")
    p_preview.add_argument("--config", help="Path to JSON config file (recommended for non-ASCII paths)")
    p_preview.add_argument("--image", help="Path to input image")
    p_preview.add_argument("--search-text", default="", help="Original text")
    p_preview.add_argument("--replace-text", default="", help="Replacement text")
    p_preview.add_argument("--box", type=int, nargs=4, metavar=("X1", "Y1", "X2", "Y2"), help="Bounding box")
    p_preview.add_argument("--erase-box", type=int, nargs=4, metavar=("EX1", "EY1", "EX2", "EY2"), help="Erase box")
    p_preview.add_argument("--text-x", type=int, help="X position of rendered text in crop")
    p_preview.add_argument("--text-y", type=int, help="Y position of rendered text in crop")
    p_preview.add_argument("--font-family", default="stsong", help="Font family name")
    p_preview.add_argument("--font-size", type=int, default=35, help="Font size")
    p_preview.add_argument("--ink-bleed", type=float, default=0.35, help="Ink bleed ratio")
    p_preview.add_argument("--clone-box", type=int, nargs=4, help="Box of glyph to clone")
    p_preview.add_argument("--clone-dest", type=int, nargs=2, help="Dest (X, Y) for cloned glyph")
    p_preview.add_argument("--output-dir", help="Directory to save preview artifacts")
    
    # Subcommand: apply
    p_apply = subparsers.add_parser("apply", help="Apply approved modification to image")
    p_apply.add_argument("--meta-file", required=True, help="Path to preview_meta.json")
    p_apply.add_argument("--backup-suffix", default="_backup", help="Suffix for backup file")
    p_apply.add_argument("--quality", type=int, default=95, help="JPEG quality")
    
    args = parser.parse_args()
    if args.command == "preview":
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
                "clone_box": args.clone_box,
                "clone_dest": args.clone_dest,
                "output_dir": args.output_dir
            }
        cmd_preview(params)
    elif args.command == "apply":
        cmd_apply(args.meta_file, backup_suffix=args.backup_suffix, quality=args.quality)


if __name__ == "__main__":
    main()
