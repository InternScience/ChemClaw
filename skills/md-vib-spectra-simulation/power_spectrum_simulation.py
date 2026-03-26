#!/usr/bin/env python3
"""
Vibrational Spectra from MD Trajectory

Compute vibrational spectra from MD trajectory using MLatom.
- Power spectrum: velocity autocorrelation (僅需速度)
- IR spectrum: dipole moment autocorrelation (需偶極矩，見 https://aitomistic.com/mlatom/tutorial_md2vibr.html)

Input: h5md file, or (xyz + vxyz), or SMILES/xyz to run MD first with GFN2-xTB.
IR 需軌跡含 dipole_moment：h5md 來自 AIQM1/MNDO/Gaussian 等，或提供 --dp 檔。

Usage:
    python power_spectrum_simulation.py ethanol_traj.h5
    python power_spectrum_simulation.py ethanol_traj.xyz --vxyz ethanol_traj.vxyz
    python power_spectrum_simulation.py ethanol_traj.h5 --spectrum ir   # IR (需 h5md 含 dipole)
    python power_spectrum_simulation.py traj.xyz --vxyz traj.vxyz --dp traj.dp --spectrum ir
    python power_spectrum_simulation.py CCO --run-md  # GFN2-xTB
    python power_spectrum_simulation.py CCO --run-md --spectrum both  # xTB 有 dipole，可算 IR

Outputs:
    - output/power_spectrum.png  (--spectrum ps)
    - output/ir_spectrum.png     (--spectrum ir)
"""

import sys
import os
import argparse
import numpy as np

# Non-interactive backend for headless
import matplotlib
matplotlib.use('Agg')

import mlatom as ml

OUTPUT_DIR = '/tmp/chemclaw'


def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)


def load_trajectory_h5md(path):
    """Load trajectory from h5md file."""
    traj = ml.data.molecular_trajectory()
    traj.load(filename=path, format='h5md')
    moldb = ml.data.molecular_database()
    moldb.molecules = [step.molecule for step in traj.steps]
    return moldb


def load_trajectory_xyz_vxyz(xyz_path, vxyz_path, dp_path=None):
    """Load trajectory from xyz + vxyz, optionally + dp (dipole moments, one line per frame: dx dy dz)."""
    moldb = ml.data.molecular_database.from_xyz_file(xyz_path)
    moldb.add_xyz_vectorial_properties_from_file(vxyz_path, 'xyz_velocities')
    if dp_path and os.path.exists(dp_path):
        with open(dp_path) as f:
            lines = f.readlines()
        for ii in range(min(len(moldb), len(lines))):
            moldb[ii].dipole_moment = [float(x) for x in lines[ii].strip().split()]
    return moldb


def _to_xyz(input_str):
    """Convert SMILES to xyz or return path if file."""
    from rdkit import Chem
    from rdkit.Chem import AllChem
    if os.path.isfile(input_str):
        return input_str
    mol = Chem.MolFromSmiles(input_str)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {input_str}")
    mol = Chem.AddHs(mol)
    AllChem.EmbedMolecule(mol, randomSeed=42)
    AllChem.MMFFOptimizeMolecule(mol, maxIters=200)
    xyz_path = os.path.join(OUTPUT_DIR, 'mol_from_smiles.xyz')
    ensure_output_dir()
    with open(xyz_path, 'w') as f:
        f.write(Chem.rdmolfiles.MolToXYZBlock(mol))
    return xyz_path


def run_md_and_get_trajectory(smiles_or_xyz, time_fs=1000, temp_k=300, dt_fs=0.5):
    """Run MD with GFN2-xTB. xTB 輸出 dipole，可算 IR spectrum."""
    import shutil
    xyz_file = _to_xyz(smiles_or_xyz)
    mol = ml.data.molecule.from_xyz_file(xyz_file)
    init_db = ml.generate_initial_conditions(
        molecule=mol,
        generation_method='maxwell-boltzmann',
        number_of_initial_conditions=1,
        initial_temperature=temp_k
    )
    mol_init = init_db.molecules[0]

    nose_hoover = ml.md.Nose_Hoover_thermostat(temperature=temp_k, molecule=mol_init)

    system_xtb = shutil.which('xtb')
    if system_xtb:
        import mlatom.interfaces.xtb_interface as _xtb_mod
        _xtb_mod.__file__ = system_xtb
    xtb_model = ml.methods(method='GFN2-xTB', program='xtb')
    md_model = xtb_model

    dyn = ml.md(
        model=md_model,
        molecule_with_initial_conditions=mol_init,
        thermostat=nose_hoover,
        ensemble='NVT',
        time_step=dt_fs,
        maximum_propagation_time=float(time_fs),
        dump_trajectory_interval=1,
    )
    ensure_output_dir()
    tmp_base = os.path.join(OUTPUT_DIR, '_md_traj_tmp')
    dyn.molecular_trajectory.dump(filename=tmp_base, format='plain_text')
    xyz_path = tmp_base + '.xyz'
    vxyz_path = tmp_base + '.vxyz'
    dp_path = tmp_base + '.dp' if os.path.exists(tmp_base + '.dp') else None
    if not os.path.exists(vxyz_path):
        raise RuntimeError('MD dump did not create .vxyz file')
    moldb = load_trajectory_xyz_vxyz(xyz_path, vxyz_path, dp_path=dp_path)
    for ext in ['.xyz', '.vxyz', '.dp', '.ekin', '.epot', '.etot', '.grad', '.temp']:
        p = tmp_base + ext
        if os.path.exists(p):
            os.remove(p)
    return moldb, dt_fs


def compute_power_spectrum(
    moldb,
    dt=0.5,
    autocorrelation_depth=1024,
    zero_padding=1024,
    lb=None,
    ub=None,
    output_png=None,
    output_npy=None,
):
    """Compute and save power spectrum from molecular_database with xyz_velocities."""
    if output_png is None:
        output_png = os.path.join(OUTPUT_DIR, 'power_spectrum.png')
    if output_npy is None:
        output_npy = os.path.join(OUTPUT_DIR, 'power_spectrum.npy')
    n_frames = len(moldb)
    if lb is None:
        lb = 0
    if ub is None:
        ub = n_frames * dt  # full trajectory

    vibr = ml.vibrational_spectrum(molecular_database=moldb, dt=dt)
    freqs, ints = vibr.plot_power_spectrum(
        filename=output_png,
        autocorrelation_depth=autocorrelation_depth,
        zero_padding=zero_padding,
        lb=lb,
        ub=ub,
        normalize=True,
        return_spectrum=True,
    )
    np.save(output_npy, np.array((freqs, ints)))
    return freqs, ints


def compute_infrared_spectrum(
    moldb,
    dt=0.5,
    autocorrelation_depth=1024,
    zero_padding=1024,
    lb=None,
    ub=None,
    output_png=None,
    output_npy=None,
):
    """Compute and save IR spectrum from molecular_database with dipole_moment (偶極矩自相關)."""
    if output_png is None:
        output_png = os.path.join(OUTPUT_DIR, 'ir_spectrum.png')
    if output_npy is None:
        output_npy = os.path.join(OUTPUT_DIR, 'ir_spectrum.npy')
    n_frames = len(moldb)
    if lb is None:
        lb = 0
    if ub is None:
        ub = n_frames * dt  # full trajectory

    vibr = ml.vibrational_spectrum(molecular_database=moldb, dt=dt)
    freqs, ints = vibr.plot_infrared_spectrum(
        filename=output_png,
        autocorrelation_depth=autocorrelation_depth,
        zero_padding=zero_padding,
        lb=lb,
        ub=ub,
        normalize=True,
        return_spectrum=True,
        format='vector',
    )
    np.save(output_npy, np.array((freqs, ints)))
    return freqs, ints


def _has_dipole_moments(moldb):
    """Check if moldb has dipole_moment for each molecule."""
    if not moldb.molecules:
        return False
    return getattr(moldb.molecules[0], 'dipole_moment', None) is not None


def main():
    parser = argparse.ArgumentParser(
        description='Vibrational spectra from MD (power spectrum / IR from dipole autocorrelation)'
    )
    parser.add_argument('input', help='h5md file, xyz file, or SMILES')
    parser.add_argument('--vxyz', help='vxyz file (required if input is xyz)')
    parser.add_argument('--dp', help='Dipole moments file (one line per frame: dx dy dz), for --spectrum ir with xyz input')
    parser.add_argument('--spectrum', choices=['ps', 'ir', 'both'], default='ps',
                        help='ps=power spectrum (速度自相關), ir=IR (偶極自相關), both=兩者')
    parser.add_argument('--run-md', action='store_true',
                        help='Run MD first with GFN2-xTB')
    parser.add_argument('--dt', type=float, default=0.5, help='Time step (fs)')
    parser.add_argument('--autocorr', type=int, default=1024, help='Autocorrelation depth (fs), 與 MLatom MD2vibr 一致')
    parser.add_argument('--zeropad', type=int, default=1024, help='Zero padding (fs), 與 MLatom MD2vibr 一致')
    parser.add_argument('--lb', type=float, default=None, help='Start time (fs)')
    parser.add_argument('--ub', type=float, default=None, help='End time (fs)')
    parser.add_argument('--output', default=os.path.join(OUTPUT_DIR, 'power_spectrum.png'), help='Output PNG path (ps 時)')
    parser.add_argument('--time', type=int, default=1000, help='MD time (fs) when --run-md')
    parser.add_argument('--temp', type=float, default=300, help='MD temperature (K) when --run-md')
    parser.add_argument('--md-dt', type=float, default=0.5, help='MD time step (fs) when --run-md')
    args = parser.parse_args()

    ensure_output_dir()

    want_ir = args.spectrum in ('ir', 'both')
    want_ps = args.spectrum in ('ps', 'both')

    print('=' * 60)
    print('Vibrational Spectra from MD Trajectory')
    print('=' * 60)

    # Determine input type and load moldb
    inp = args.input
    if args.run_md:
        print(f'Running MD with GFN2-xTB ({args.time} fs, dt={args.md_dt} fs, T={args.temp} K)...')
        moldb, dt = run_md_and_get_trajectory(
            inp, time_fs=args.time, temp_k=args.temp, dt_fs=args.md_dt
        )
        print(f'  Trajectory: {len(moldb)} frames')
    elif inp.lower().endswith('.h5') or inp.lower().endswith('.h5md'):
        print(f'Loading h5md: {inp}')
        moldb = load_trajectory_h5md(inp)
        print(f'  Frames: {len(moldb)}')
        dt = args.dt
    elif inp.lower().endswith('.xyz'):
        vxyz = args.vxyz
        if not vxyz:
            vxyz = inp.rsplit('.', 1)[0] + '.vxyz'
        if not os.path.exists(vxyz):
            print(f'Error: vxyz file required. Not found: {vxyz}')
            print('  Use --vxyz path/to/traj.vxyz')
            sys.exit(1)
        dp_path = args.dp or (inp.rsplit('.', 1)[0] + '.dp' if want_ir else None)
        print(f'Loading xyz: {inp}, vxyz: {vxyz}' + (f', dp: {dp_path}' if dp_path else ''))
        moldb = load_trajectory_xyz_vxyz(inp, vxyz, dp_path=dp_path)
        print(f'  Frames: {len(moldb)}')
        dt = args.dt
    else:
        print('Interpreting as SMILES, running MD with GFN2-xTB...')
        moldb, dt = run_md_and_get_trajectory(
            inp, time_fs=args.time, temp_k=args.temp, dt_fs=args.md_dt
        )
        print(f'  Trajectory: {len(moldb)} frames')

    # Check velocities for power spectrum
    if want_ps:
        has_vel = False
        try:
            v = moldb.get_xyz_vectorial_properties('xyz_velocities')
            has_vel = v is not None and (not hasattr(v, 'size') or v.size > 0)
        except Exception:
            pass
        if not has_vel and moldb.molecules:
            has_vel = getattr(moldb.molecules[0], 'xyz_velocities', None) is not None
        if not has_vel:
            print('Error: Trajectory has no xyz_velocities. Power spectrum requires velocities.')
            sys.exit(1)

    # Check dipole for IR
    if want_ir:
        if not _has_dipole_moments(moldb):
            print('Error: IR spectrum 需軌跡含 dipole_moment。')
            print('  - h5md 需來自 AIQM1/MNDO/Gaussian 等有 dipole 的方法')
            print('  - 或 xyz+vxyz 時提供 --dp 檔（每行 dx dy dz）')
            sys.exit(1)

    common_kw = dict(
        moldb=moldb,
        dt=dt,
        autocorrelation_depth=args.autocorr,
        zero_padding=args.zeropad,
        lb=args.lb,
        ub=args.ub,
    )

    if want_ps:
        out_ps = args.output if args.spectrum == 'ps' else os.path.join(OUTPUT_DIR, 'power_spectrum.png')
        print(f'Computing power spectrum (dt={dt} fs)...')
        compute_power_spectrum(**common_kw, output_png=out_ps, output_npy=out_ps.replace('.png', '.npy'))
        print(f'  Saved: {out_ps}')

    if want_ir:
        out_ir = os.path.join(OUTPUT_DIR, 'ir_spectrum.png')
        print(f'Computing IR spectrum (dipole autocorrelation, dt={dt} fs)...')
        compute_infrared_spectrum(**common_kw, output_png=out_ir, output_npy=out_ir.replace('.png', '.npy'))
        print(f'  Saved: {out_ir}')

    print('=' * 60)
    print('Done!')
    print('=' * 60)


if __name__ == '__main__':
    main()
