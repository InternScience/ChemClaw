---
name: xrd-spectra-simulation
description: XRD spectrum from CIF structure file using pymatgen (Cu Kα).
---

# XRD Spectrum Simulation Skill

## When to use this
Use this skill when the user provides a **.cif structure file** and wants:
- Simulated XRD pattern (Cu Kα by default)
- Publication-ready PNG plot

## Inputs
- **.cif file path** (user provides crystal structure)

## Outputs
- `/tmp/chemclaw/xrd_spectrum.png` — XRD pattern plot

## New environment (from zero)

```bash
conda create -n spec python=3.12 -y
conda activate spec
cd xrd-spectra-simulation
pip install -r requirements.txt

python xrd_spectra_simulation.py example/1100157.cif
```

- 仓库内附范例 `example/1100157.cif` 可直接测试。

## How to use

```bash
cd xrd-spectra-simulation
python xrd_spectra_simulation.py example/1100157.cif
python xrd_spectra_simulation.py path/to/structure.cif --output /tmp/chemclaw/my_xrd.png
```

### Optional
```bash
cd xrd-spectra-simulation
python xrd_spectra_simulation.py structure.cif --wavelength MoKa
```

## Dependencies (`requirements.txt`)
- pymatgen
- matplotlib

## Notes
- Uses pymatgen XRDCalculator
- Default: Cu Kα radiation
- Available: CuKa, MoKa, CrKa, FeKa, CoKa, AgKa, etc.
