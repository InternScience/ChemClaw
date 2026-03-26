#!/usr/bin/env python3
"""
Raman Spectra Simulation Tool

Compute and visualize Raman Spectra from input XYZ file with MLatom.

Requirements:
    pip install mlatom numpy matplotlib pyscf geometric rdkit
    Default (xTB): conda install -c conda-forge xtb  # macOS 必裝

Usage:
    python raman_spectra_simulation.py <smiles_or_xyz> [exp_txt_file]
    Input: SMILES string (e.g. CCO) or path to XYZ file

Outputs (under /tmp/chemclaw):
    - optimized_geometry.md
    - theoretical_raman.md
    - theoretical_raman.png
    - exp_raman.png (optional, if experimental data provided)
    - comparison_raman.png (optional, if experimental data provided)

"""

import sys
import os
import numpy as np
# Use non-interactive backend for headless/save-only plotting
import matplotlib
matplotlib.use('Agg')
import mlatom as ml
from mlatom.spectra import raman

OUTPUT_DIR = '/tmp/chemclaw'


def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)


def smiles2xyz(smiles, output_path=None):
    """
    Convert SMILES to XYZ file using RDKit (embed 3D, MMFF optimize).
    
    Args:
        smiles: SMILES string (e.g. CCO for ethanol)
        output_path: Path to save XYZ file
        
    Returns:
        output_path: Path to the generated XYZ file
    """
    if output_path is None:
        output_path = os.path.join(OUTPUT_DIR, 'mol_from_smiles.xyz')
    from rdkit import Chem
    from rdkit.Chem import AllChem

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    mol = Chem.AddHs(mol)

    # Embed 3D coordinates
    result = AllChem.EmbedMolecule(mol, randomSeed=42)
    if result != 0:
        result = AllChem.EmbedMolecule(mol, useRandomCoords=True)
    if result != 0:
        raise ValueError(f"Failed to generate 3D coordinates for SMILES: {smiles}")

    # MMFF optimization for better initial geometry
    AllChem.MMFFOptimizeMolecule(mol, maxIters=200)

    # Write XYZ
    block = Chem.rdmolfiles.MolToXYZBlock(mol)
    ensure_output_dir()
    with open(output_path, 'w') as f:
        f.write(block)
    return output_path


def resolve_input_to_xyz(input_str):
    """Resolve input to XYZ file path. Input can be SMILES or path to XYZ file."""
    if os.path.isfile(input_str):
        return input_str
    # Treat as SMILES
    print(f"Interpreting input as SMILES: {input_str}")
    return smiles2xyz(input_str)


def _parse_vibspectrum(vib_path):
    """
    Parse xTB vibspectrum file for IR and Raman intensities.
    xTB 6.7+ 輸出 vibspectrum，格式：mode, symmetry, wave_number, IR_intensity, Raman_activity, ...
    MLatom 的 xTB 介面只讀 dipd/polard（conda-forge xtb 不產生），故需直接解析 vibspectrum。
    """
    ir_intensities = []
    raman_intensities = []
    with open(vib_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('$') or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) >= 5:
                try:
                    ir_intensities.append(float(parts[3]))
                    raman_intensities.append(float(parts[4]))
                except (ValueError, IndexError):
                    continue
    return ir_intensities, raman_intensities


def _fill_intensities_from_xtb_vibspectrum(mol, workdir=None):
    """
    When MLatom 未取得 raman_intensities，用系統 xtb 跑 --hess --ptb --raman 並解析 vibspectrum。
    """
    if workdir is None:
        workdir = OUTPUT_DIR
    import shutil
    import subprocess
    import tempfile
    xtb_bin = shutil.which('xtb')
    if not xtb_bin:
        return False
    ensure_output_dir()
    xyz_path = os.path.abspath(os.path.join(workdir, '_opt_for_vib.xyz'))
    mol.write_file_with_xyz_coordinates(filename=xyz_path)
    with tempfile.TemporaryDirectory() as tmp:
        result = subprocess.run(
            [xtb_bin, xyz_path, '--hess', '--ptb', '--raman', '--namespace', 'vib'],
            cwd=tmp, capture_output=True, text=True, timeout=120
        )
        vib_path = os.path.join(tmp, 'vib.vibspectrum')
        if not os.path.exists(vib_path) or result.returncode != 0:
            return False
        ir_vals, raman_vals = _parse_vibspectrum(vib_path)
        n_freq = len(mol.frequencies)
        if len(raman_vals) >= n_freq:
            mol.raman_intensities = np.array(raman_vals[:n_freq])
            mol.infrared_intensities = np.array(ir_vals[:n_freq])
            return True
    return False


def optimize_and_calculate_raman(xyz_file):
    """
    Optimize geometry and calculate Raman spectrum with GFN2-xTB.
    
    Returns:
        mol: Molecule object with optimized geometry and frequencies
    """
    import shutil
    print(f"Loading molecule from {xyz_file}...")
    mol = ml.molecule.from_xyz_file(xyz_file)
    
    system_xtb = shutil.which('xtb')
    if system_xtb:
        import mlatom.interfaces.xtb_interface as _xtb_mod
        _xtb_mod.__file__ = system_xtb
        print(f"Using system xtb: {system_xtb}")
    else:
        print("Using MLatom bundled xtb (may fail on macOS)")
    model = ml.methods(method='GFN2-xTB', program='xtb')
    print("Optimizing geometry with GFN2-xTB...")
    _ = ml.optimize_geometry(molecule=mol, model=model, program='geometric')
    print("Calculating frequencies and IR/Raman intensities (GFN2-xTB)...")
    _ = ml.freq(molecule=mol, model=model, ir=True, raman=True, program='xtb')
    # MLatom 的 xTB 介面依賴 dipd/polard，conda-forge xtb 不產生這些檔，改從 vibspectrum 解析
    if not hasattr(mol, 'raman_intensities') or mol.raman_intensities is None:
        print("  MLatom 未取得 Raman 強度，改從 xTB vibspectrum 解析...")
        if _fill_intensities_from_xtb_vibspectrum(mol):
            print("  已從 xTB vibspectrum 取得 IR/Raman 強度")
    return mol


def save_optimized_geometry(mol, output_file=None):
    """Save optimized geometry to markdown file."""
    if output_file is None:
        output_file = os.path.join(OUTPUT_DIR, 'optimized_geometry.md')
    xyz_string = mol.get_xyz_string()
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Optimized Geometry\n\n")
        f.write("```\n")
        f.write(xyz_string)
        f.write("\n```\n")
    print(f"Optimized geometry saved to {output_file}")


def save_theoretical_raman_table(mol, output_file=None):
    """Save theoretical Raman data as a markdown table."""
    if output_file is None:
        output_file = os.path.join(OUTPUT_DIR, 'theoretical_raman.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Theoretical Raman Spectrum\n\n")
        f.write("| Mode | Frequency (cm⁻¹) | Reduced Mass (AMU) | Force Constant (mDyne/A) | Raman Intensity |\n")
        f.write("|------|------------------|-------------------|---------------------------|------------------|\n")
        
        for ii in range(len(mol.frequencies)):
            raman_intensity = ""
            if hasattr(mol, 'raman_intensities') and mol.raman_intensities is not None:
                raman_intensity = f"{mol.raman_intensities[ii]:.4f}"
            
            f.write(f"| {ii} | {mol.frequencies[ii]:.4f} | {mol.reduced_masses[ii]:.4f} | {mol.force_constants[ii]:.4f} | {raman_intensity} |\n")
    
    print(f"Theoretical Raman table saved to {output_file}")


def plot_theoretical_raman(mol, output_file=None):
    """
    Plot theoretical Raman spectrum.
    
    Raman intensities require polarizability derivatives. PySCF interface in MLatom
    does not implement them; Sparrow has none. When raman_intensities is missing,
    we use force constants as proxy (spectrum shape similar to IR - frequencies only).
    """
    if output_file is None:
        output_file = os.path.join(OUTPUT_DIR, 'theoretical_raman.png')
    print("Generating theoretical Raman spectrum plot...")
    
    # Ensure raman_intensities exist (use force constants as proxy if missing)
    if not hasattr(mol, 'raman_intensities') or mol.raman_intensities is None:
        mol.raman_intensities = np.abs(mol.force_constants) if hasattr(mol, 'force_constants') else np.ones(len(mol.frequencies))
        print("  Note: Raman intensities not available from model; using force constants as proxy (spectrum shape ~ IR).")
    
    spectrum_range = np.arange(500, 4001)
    theoretical_spectrum = raman.lorentzian(molecule=mol, fwhm=30, spectrum_range=spectrum_range)
    
    theoretical_spectrum.plot(
        filename=output_file,
        title='Theoretical Raman Spectrum'
    )
    
    print(f"Theoretical Raman plot saved to {output_file}")


def plot_experimental_raman(exp_file, output_file=None):
    """Plot experimental Raman spectrum."""
    if output_file is None:
        output_file = os.path.join(OUTPUT_DIR, 'exp_raman.png')
    print(f"Loading experimental spectrum from {exp_file}...")
    exp_spectrum = raman.load(exp_file, format='txt')
    
    print("Generating experimental Raman spectrum plot...")
    exp_spectrum.plot(
        output_file,
        title='Experimental Raman Spectrum'
    )
    
    print(f"Experimental Raman plot saved to {output_file}")
    return exp_spectrum


def plot_comparison(mol, exp_spectrum, output_file=None):
    """Plot comparison between experimental and theoretical Raman spectra."""
    if output_file is None:
        output_file = os.path.join(OUTPUT_DIR, 'comparison_raman.png')
    print("Generating comparison plot...")
    
    if not hasattr(mol, 'raman_intensities') or mol.raman_intensities is None:
        mol.raman_intensities = np.abs(mol.force_constants) if hasattr(mol, 'force_constants') else np.ones(len(mol.frequencies))
    
    spectrum_range = np.arange(500, 4001)
    theoretical_spectrum = raman.lorentzian(molecule=mol, fwhm=30, spectrum_range=spectrum_range)
    
    # Normalize for comparison
    theoretical_spectrum.normalize(method='average')
    exp_spectrum_copy = raman(x=exp_spectrum.x, y=exp_spectrum.y)
    exp_spectrum_copy.normalize(method='average')
    
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.plot(theoretical_spectrum.x, theoretical_spectrum.y, 'b-', label='Theory', linewidth=1.5)
    ax.plot(exp_spectrum_copy.x, exp_spectrum_copy.y, 'r-', label='Experiment', linewidth=1.5)
    ax.set_xlabel('Wavenumber (cm$^{-1}$)', fontsize=14)
    ax.set_ylabel('Normalized intensity', fontsize=14)
    ax.set_title('Raman Spectrum Comparison', fontsize=16)
    ax.invert_xaxis()
    ax.legend()
    ax.set_xlim(4000, 500)
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Comparison plot saved to {output_file}")


def main():
    """Main function to run Raman spectra simulation."""
    args_list = [a for a in sys.argv[1:] if not a.startswith('--')]
    
    if len(args_list) < 1:
        print("Usage: python raman_spectra_simulation.py <xyz_file> [exp_txt_file]")
        print("\nExample:")
        print("  python raman_spectra_simulation.py CCO")
        print("  python raman_spectra_simulation.py /path/to/structure.xyz")
        print("  python raman_spectra_simulation.py CCO exp.txt")
        sys.exit(1)
    
    input_str = args_list[0]
    exp_file = args_list[1] if len(args_list) > 1 else None

    ensure_output_dir()
    xyz_file = resolve_input_to_xyz(input_str)
    
    if exp_file and not os.path.exists(exp_file):
        print(f"Error: Experimental data file '{exp_file}' not found.")
        sys.exit(1)
    
    print("=" * 60)
    print("Raman Spectra Simulation with MLatom")
    print("=" * 60)
    
    mol = optimize_and_calculate_raman(xyz_file)
    
    save_optimized_geometry(mol)
    save_theoretical_raman_table(mol)
    plot_theoretical_raman(mol)
    
    if exp_file:
        exp_spectrum = plot_experimental_raman(exp_file)
        plot_comparison(mol, exp_spectrum)
    
    print("\n" + "=" * 60)
    print("Raman Spectra Simulation Complete!")
    print("=" * 60)
    print(f"\nOutputs (in {OUTPUT_DIR}):")
    print(f"  - {OUTPUT_DIR}/optimized_geometry.md")
    print(f"  - {OUTPUT_DIR}/theoretical_raman.md")
    print(f"  - {OUTPUT_DIR}/theoretical_raman.png")
    if exp_file:
        print(f"  - {OUTPUT_DIR}/exp_raman.png")
        print(f"  - {OUTPUT_DIR}/comparison_raman.png")
    print()


if __name__ == "__main__":
    main()
