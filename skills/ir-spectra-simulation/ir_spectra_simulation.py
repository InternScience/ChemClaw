#!/usr/bin/env python3
"""
IR Spectra Simulation Tool

Compute and visualize IR Spectra from input XYZ file with MLatom.

Requirements:
    pip install mlatom numpy matplotlib pyscf geometric rdkit
    Default (xTB): conda install -c conda-forge xtb  # macOS 必裝

Usage:
    python ir_spectra_simulation.py <smiles_or_xyz> [exp_txt_file]
    Input: SMILES string (e.g. CCO) or path to XYZ file

Outputs (under /tmp/chemclaw):
    - optimized_geometry.md
    - theoretical_ir.md
    - theoretical_ir.png
    - exp_ir.png (optional, if experimental data provided)
    - comparison_ir.png (optional, if experimental data provided)
"""

import sys
import os
import numpy as np
# Use non-interactive backend for headless/save-only plotting
import matplotlib
matplotlib.use('Agg')
import mlatom as ml
from mlatom.spectra import ir

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
    """Parse xTB vibspectrum file for IR and Raman intensities."""
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
    """當 MLatom 未取得 infrared_intensities 時，從 xTB vibspectrum 解析。"""
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
            [xtb_bin, xyz_path, '--hess', '--ptb', '--namespace', 'vib'],
            cwd=tmp, capture_output=True, text=True, timeout=120
        )
        vib_path = os.path.join(tmp, 'vib.vibspectrum')
        if not os.path.exists(vib_path) or result.returncode != 0:
            return False
        ir_vals, raman_vals = _parse_vibspectrum(vib_path)
        n_freq = len(mol.frequencies)
        if len(ir_vals) >= n_freq:
            mol.infrared_intensities = np.array(ir_vals[:n_freq])
            return True
    return False


def optimize_and_calculate_ir(xyz_file):
    """
    Optimize geometry and calculate IR spectrum with GFN2-xTB.
    
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
    print("Calculating frequencies and IR intensities (GFN2-xTB)...")
    _ = ml.freq(molecule=mol, model=model, ir=True, raman=False, program='xtb')
    if not hasattr(mol, 'infrared_intensities') or mol.infrared_intensities is None:
        print("  MLatom 未取得 IR 強度，改從 xTB vibspectrum 解析...")
        if _fill_intensities_from_xtb_vibspectrum(mol):
            print("  已從 xTB vibspectrum 取得 IR 強度")
    return mol


def save_optimized_geometry(mol, output_file=None):
    """
    Save optimized geometry to markdown file.
    
    Args:
        mol: Molecule object
        output_file: Output file path
    """
    if output_file is None:
        output_file = os.path.join(OUTPUT_DIR, 'optimized_geometry.md')
    xyz_string = mol.get_xyz_string()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Optimized Geometry\n\n")
        f.write("```\n")
        f.write(xyz_string)
        f.write("\n```\n")
    
    print(f"Optimized geometry saved to {output_file}")


def save_theoretical_ir_table(mol, output_file=None):
    """
    Save theoretical IR data as a markdown table.
    
    Args:
        mol: Molecule object with frequencies
        output_file: Output file path
    """
    if output_file is None:
        output_file = os.path.join(OUTPUT_DIR, 'theoretical_ir.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Theoretical IR Spectrum\n\n")
        f.write("| Mode | Frequency (cm⁻¹) | Reduced Mass (AMU) | Force Constant (mDyne/A) | IR Intensity |\n")
        f.write("|------|------------------|-------------------|---------------------------|--------------|\n")
        
        for ii in range(len(mol.frequencies)):
            # Get IR intensity if available (MLatom 使用 infrared_intensities)
            ir_intensity = ""
            if hasattr(mol, 'infrared_intensities') and mol.infrared_intensities is not None:
                ir_intensity = f"{mol.infrared_intensities[ii]:.4f}"
            
            f.write(f"| {ii} | {mol.frequencies[ii]:.4f} | {mol.reduced_masses[ii]:.4f} | {mol.force_constants[ii]:.4f} | {ir_intensity} |\n")
    
    print(f"Theoretical IR table saved to {output_file}")


def plot_theoretical_ir(mol, output_file=None):
    """
    Plot theoretical IR spectrum.
    
    Args:
        mol: Molecule object with frequencies and IR intensities
        output_file: Output file path
    """
    if output_file is None:
        output_file = os.path.join(OUTPUT_DIR, 'theoretical_ir.png')
    print("Generating theoretical IR spectrum plot...")
    
    # Ensure infrared_intensities exist (use force constants as proxy if missing)
    if not hasattr(mol, 'infrared_intensities') or mol.infrared_intensities is None:
        mol.infrared_intensities = np.abs(mol.force_constants) if hasattr(mol, 'force_constants') else np.ones(len(mol.frequencies))
    
    # Create Lorentzian-broadened spectrum from molecule
    spectrum_range = np.arange(500, 4001)
    theoretical_spectrum = ir.lorentzian(molecule=mol, fwhm=30, spectrum_range=spectrum_range)
    
    # Plot and save using mlatom's plot_ir
    ml.spectra.plot_ir(
        spectra=[theoretical_spectrum],
        filename=output_file,
        plotstart=500,
        plotend=4000,
        title='Theoretical IR Spectrum'
    )
    
    print(f"Theoretical IR plot saved to {output_file}")


def plot_experimental_ir(exp_file, output_file=None):
    """
    Plot experimental IR spectrum.
    
    Args:
        exp_file: Path to experimental data file (txt format)
        output_file: Output file path
        
    Returns:
        exp_spectrum: Experimental spectrum object
    """
    if output_file is None:
        output_file = os.path.join(OUTPUT_DIR, 'exp_ir.png')
    print(f"Loading experimental spectrum from {exp_file}...")
    exp_spectrum = ml.spectra.ir.load(exp_file, format='txt')
    
    print("Generating experimental IR spectrum plot...")
    exp_spectrum.plot(
        output_file,
        plotstart=500,
        plotend=4000,
        title='Experimental IR Spectrum'
    )
    
    print(f"Experimental IR plot saved to {output_file}")
    return exp_spectrum


def plot_comparison(mol, exp_spectrum, output_file=None):
    """
    Plot comparison between experimental and theoretical IR spectra.
    
    Args:
        mol: Molecule object with frequencies
        exp_spectrum: Experimental spectrum object
        output_file: Output file path
    """
    if output_file is None:
        output_file = os.path.join(OUTPUT_DIR, 'comparison_ir.png')
    print("Generating comparison plot...")
    
    # Ensure infrared_intensities exist
    if not hasattr(mol, 'infrared_intensities') or mol.infrared_intensities is None:
        mol.infrared_intensities = np.abs(mol.force_constants) if hasattr(mol, 'force_constants') else np.ones(len(mol.frequencies))
    
    # Create Lorentzian-broadened theoretical spectrum
    spectrum_range = np.arange(500, 4001)
    theoretical_spectrum = ir.lorentzian(molecule=mol, fwhm=30, spectrum_range=spectrum_range)
    
    # Plot both spectra together
    ml.spectra.plot_ir(
        spectra=[exp_spectrum, theoretical_spectrum],
        molecule=mol,
        normalize='average',
        labels=['Experiment', 'Theory'],
        lorentzian=False,  # already broadened
        scaling_factor=0.958,
        plotstart=500,
        plotend=4000,
        filename=output_file
    )
    
    print(f"Comparison plot saved to {output_file}")


def main():
    """Main function to run IR spectra simulation."""
    args_list = [a for a in sys.argv[1:] if not a.startswith('--')]
    
    if len(args_list) < 1:
        print("Usage: python ir_spectra_simulation.py <xyz_file> [exp_txt_file]")
        print("\nExample:")
        print("  python ir_spectra_simulation.py CCO")
        print("  python ir_spectra_simulation.py /path/to/structure.xyz")
        print("  python ir_spectra_simulation.py CCO exp.txt")
        sys.exit(1)
    
    input_str = args_list[0]
    exp_file = args_list[1] if len(args_list) > 1 else None

    # Resolve input: SMILES -> XYZ, or use XYZ path directly
    ensure_output_dir()
    xyz_file = resolve_input_to_xyz(input_str)
    
    # Check if experimental file exists (if provided)
    if exp_file and not os.path.exists(exp_file):
        print(f"Error: Experimental data file '{exp_file}' not found.")
        sys.exit(1)
    
    print("=" * 60)
    print("IR Spectra Simulation with MLatom")
    print("=" * 60)
    
    # Step 1: Optimize geometry and calculate IR
    mol = optimize_and_calculate_ir(xyz_file)
    
    # Step 2: Save optimized geometry
    save_optimized_geometry(mol)
    
    # Step 3: Save theoretical IR data table
    save_theoretical_ir_table(mol)
    
    # Step 4: Plot theoretical IR spectrum
    plot_theoretical_ir(mol)
    
    # Step 5 & 6: If experimental data provided, plot experimental and comparison
    if exp_file:
        exp_spectrum = plot_experimental_ir(exp_file)
        plot_comparison(mol, exp_spectrum)
    
    print("\n" + "=" * 60)
    print("IR Spectra Simulation Complete!")
    print("=" * 60)
    print(f"\nOutputs (in {OUTPUT_DIR}):")
    print(f"  - {OUTPUT_DIR}/optimized_geometry.md")
    print(f"  - {OUTPUT_DIR}/theoretical_ir.md")
    print(f"  - {OUTPUT_DIR}/theoretical_ir.png")
    if exp_file:
        print(f"  - {OUTPUT_DIR}/exp_ir.png")
        print(f"  - {OUTPUT_DIR}/comparison_ir.png")
    print()


if __name__ == "__main__":
    main()
