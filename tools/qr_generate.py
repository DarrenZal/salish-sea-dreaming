"""
Generate QR code PNG for gallery visitor URL.

Usage:
    python tools/qr_generate.py https://ssd-gallery.cfargotunnel.com
    python tools/qr_generate.py https://ssd-gallery.cfargotunnel.com --output qr_gallery.png --size 10

Output: qr_gallery.png (or specified path)
Size: cm dimension for print (default 10cm at 300dpi)
Dependencies: qrcode[pil]
"""
import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Generate gallery QR code")
    parser.add_argument("url", help="URL to encode (e.g. https://ssd-gallery.cfargotunnel.com)")
    parser.add_argument("--output", default="qr_gallery.png", help="Output PNG path")
    parser.add_argument("--size", type=float, default=10.0, help="Print size in cm (default: 10cm)")
    args = parser.parse_args()

    try:
        import qrcode
        from PIL import Image
    except ImportError:
        print("ERROR: Install dependencies: pip install 'qrcode[pil]'")
        sys.exit(1)

    qr = qrcode.QRCode(
        version=None,  # auto-size
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # high error correction for print
        box_size=10,
        border=4,
    )
    qr.add_data(args.url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Calculate pixel size for print (300 DPI)
    dpi = 300
    px = int(args.size / 2.54 * dpi)  # cm to inches to pixels
    img = img.resize((px, px), Image.LANCZOS)

    out_path = Path(args.output)
    img.save(out_path, dpi=(dpi, dpi))
    print(f"QR code saved: {out_path} ({px}x{px}px @ {dpi}dpi, {args.size}cm print size)")
    print(f"URL encoded: {args.url}")


if __name__ == "__main__":
    main()
