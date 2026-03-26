#!/usr/bin/env python3
"""
XRD Spectrum from CIF

Input .cif structure file → calculate XRD pattern (Cu Kα) → save PNG.

Usage:
    python xrd_spectra_simulation.py 1100157.cif
    python xrd_spectra_simulation.py path/to/structure.cif --output /tmp/chemclaw/xrd.png

Outputs:
    - /tmp/chemclaw/xrd_spectrum.png
"""

import sys
import os
import argparse

import matplotlib
matplotlib.use('Agg')

OUTPUT_DIR = '/tmp/chemclaw'


def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)


def main():
    parser = argparse.ArgumentParser(description='XRD spectrum from CIF structure')
    parser.add_argument('cif', help='Path to .cif structure file')
    parser.add_argument('--output', default=os.path.join(OUTPUT_DIR, 'xrd_spectrum.png'), help='Output PNG path')
    parser.add_argument('--wavelength', default='CuKa', help='Radiation (CuKa, MoKa, etc.)')
    args = parser.parse_args()

    if not os.path.exists(args.cif):
        print(f'Error: CIF file not found: {args.cif}')
        sys.exit(1)

    try:
        from pymatgen.core.structure import Structure
        from pymatgen.analysis.diffraction.xrd import XRDCalculator
    except ImportError:
        print('Error: pymatgen not installed. Run: pip install pymatgen')
        sys.exit(1)

    ensure_output_dir()
    print('=' * 60)
    print('XRD Spectrum Simulation')
    print('=' * 60)
    print(f'Loading: {args.cif}')
    structure = Structure.from_file(args.cif)
    print(f'  Formula: {structure.formula}')
    xrd_calc = XRDCalculator(wavelength=args.wavelength)
    ax = xrd_calc.get_plot(structure)
    ax.get_figure().savefig(args.output, dpi=150, bbox_inches='tight')
    print(f'Saved: {args.output}')
    print('=' * 60)


if __name__ == '__main__':
    main()
