---
name: raman-spectra-simulation
description: Compute and visualize Raman Spectra from input SMILES or XYZ file with MLatom.
---

# Raman Spectra Simulation Skill

## When to use this
Use this skill when the user provides a **SMILES** or **XYZ file** (coordinates) and wants:
- Optimized geometry
- Theoretically calculated Raman spectrum in a summarized table
- Quick overview of simulated Raman spectrum
- Publication-ready image file

## Inputs
- **SMILES string** (e.g. CCO for ethanol) or **XYZ file path** (necessary)
- A corresponding experimental Raman spectrum (optional, .txt format)

## Outputs
- `/tmp/chemclaw/optimized_geometry.md`
- `/tmp/chemclaw/theoretical_raman.md`
- `/tmp/chemclaw/theoretical_raman.png`
- `/tmp/chemclaw/exp_raman.png` (optional, if experimental data provided)
- `/tmp/chemclaw/comparison_raman.png` (optional, if experimental data provided)

## Agent response
When returning results to the user, **include the generated spectrum image(s) in the response** so the user sees them directly. Use markdown image syntax with the correct path to the PNG file(s), e.g. `![Raman spectrum](path/to/theoretical_raman.png)`. Include `comparison_raman.png` if experimental data was provided.

## New environment (from zero)

```bash
conda create -n spec python=3.12 -y
conda activate spec
conda install -c conda-forge xtb -y   # macOS 必装（MLatom 内建 xTB 为 Linux 版）
pip install mlatom numpy matplotlib pyscf geometric rdkit

cd raman-spectra-simulation
python raman_spectra_simulation.py CCO
# optional: python raman_spectra_simulation.py /path/to/structure.xyz
# optional: python raman_spectra_simulation.py CCO experimental_raman.txt
```

- 请在 skill 目录内执行脚本。
- macOS 若仍误用 MLatom 内建 Linux 版 xTB，可 `export PATH="$CONDA_PREFIX/bin:$PATH"` 让系统先找到 conda 的 `xtb`。

## How to use（已装好环境时）

**SMILES:**
```bash
cd raman-spectra-simulation
python raman_spectra_simulation.py CCO
```

**XYZ（用户提供坐标文件）:**
```bash
cd raman-spectra-simulation
python raman_spectra_simulation.py /path/to/structure.xyz
```

**含实验谱对照:**
```bash
cd raman-spectra-simulation
python raman_spectra_simulation.py CCO experimental_raman.txt
```

