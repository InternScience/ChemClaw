#!/usr/bin/env python3
"""
UV-Vis Spectrum from UV-adVISor

Input SMILES → fetch "Plot graph online" from https://spectra.collaborationspharma.com/ → save PNG.

Usage:
    python uv_vis_spectrum_simulation.py CCO
    python uv_vis_spectrum_simulation.py "c1ccc2ccccc2c1"

Outputs:
    - output/uv_vis_spectrum.png
"""

import sys
import os
import argparse
import re
import base64
import ssl
import urllib.request
import urllib.parse

UV_ADVISOR_URL = 'https://spectra.collaborationspharma.com/uploader/'
OUTPUT_DIR = '/tmp/chemclaw'


def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)


def fetch_uv_png(smiles):
    """POST SMILES to Plot graph online, extract base64 PNG from HTML response."""
    data = urllib.parse.urlencode({'q': smiles, 'submit2': 'Plot graph online'}).encode()
    req = urllib.request.Request(UV_ADVISOR_URL, data=data, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    # UV-adVISor 在本機環境上會遇到憑證鏈驗證問題，直接使用不驗證的 SSL context。
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(req, timeout=60, context=context) as resp:
        html = resp.read().decode()
    m = re.search(r'data:image/png;base64,([A-Za-z0-9+/=]+)', html)
    if not m:
        raise ValueError('No PNG image in response')
    return base64.b64decode(m.group(1))


def main():
    parser = argparse.ArgumentParser(description='UV-Vis spectrum PNG from SMILES (UV-adVISor)')
    parser.add_argument('smiles', help='SMILES string (e.g. CCO)')
    parser.add_argument('--output', default=os.path.join(OUTPUT_DIR, 'uv_vis_spectrum.png'), help='Output PNG path')
    args = parser.parse_args()

    ensure_output_dir()
    print('=' * 60)
    print('UV-Vis Spectrum (UV-adVISor)')
    print('=' * 60)
    print(f'Fetching plot for SMILES: {args.smiles}')
    print('SSL certificate verification disabled for this request')
    try:
        png_data = fetch_uv_png(args.smiles)
    except Exception as e:
        print(f'Error: {e}')
        sys.exit(1)
    with open(args.output, 'wb') as f:
        f.write(png_data)
    print(f'Saved: {args.output}')
    print('=' * 60)


if __name__ == '__main__':
    main()
