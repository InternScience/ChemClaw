---
name: ir-spectra-simulation
description: Compute and visualize IR Spectra from input SMILES or XYZ file with MLatom.
---

# IR Spectra Simulation Skill

## When to use this
Use this skill when the user provides a **SMILES** or **XYZ file** (coordinates) and wants:
- Optimized geometry
- Theoretically calculated IR spectrum in a summarized table
- Quick overview of simulated IR
- Publication-ready image file

## Inputs
- **SMILES string** (e.g. CCO for ethanol) or **XYZ file path** (necessary)
- Experimental IR spectrum file (optional, .txt format)

## Outputs
- `/tmp/chemclaw/optimized_geometry.md`
- `/tmp/chemclaw/theoretical_ir.md`
- `/tmp/chemclaw/theoretical_ir.png`
- `/tmp/chemclaw/exp_ir.png` (可选，提供实验数据时)
- `/tmp/chemclaw/comparison_ir.png` (可选，提供实验数据时)

## New environment (from zero)

```bash
conda create -n spec python=3.12 -y
conda activate spec
conda install -c conda-forge xtb -y   # macOS 必装（MLatom 内建 xTB 为 Linux 版）
pip install mlatom numpy matplotlib pyscf geometric rdkit

cd ir-spectra-simulation
python ir_spectra_simulation.py CCO
# optional: python ir_spectra_simulation.py /path/to/structure.xyz
# optional: python ir_spectra_simulation.py CCO exp.txt
```

- 请在 skill 目录内执行脚本（`cd ir-spectra-simulation`）。
- macOS 若仍误用 MLatom 内建 Linux 版 xTB，可确保 `which xtb` 指向 conda 的 `xtb`（必要时 `export PATH="$CONDA_PREFIX/bin:$PATH"`）。

## How to run（已装好环境时）

### SMILES
```bash
cd ir-spectra-simulation
python ir_spectra_simulation.py CCO
```

### XYZ（用户提供坐标文件）
```bash
cd ir-spectra-simulation
python ir_spectra_simulation.py /path/to/structure.xyz
```

