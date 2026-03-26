---
name: md-vib-spectra-simulation
description: Compute vibrational spectra from MD trajectory — power spectrum (velocity autocorrelation) or IR (dipole autocorrelation) via MLatom.
---

# MD Vibrational Spectra Simulation Skill

## When to use this
Use this skill when the user has an **MD trajectory** and wants:
- **Power spectrum** — velocity autocorrelation（仅需速度）
- **IR spectrum** — dipole moment autocorrelation（需偶极矩，见 [MLatom 文档](https://aitomistic.com/mlatom/tutorial_md2vibr.html)）

## Inputs
- **h5md file** — coords + velocities（IR 时需含 dipole，如 AIQM1/MNDO 轨迹）
- **xyz + vxyz** — coordinates and velocities（IR 时另需 --dp 偶极档）
- **SMILES or xyz** — 可 --run-md 先跑 GFN2-xTB MD

## Outputs
- `/tmp/chemclaw/power_spectrum.png` — power spectrum（--spectrum ps）
- `/tmp/chemclaw/ir_spectrum.png` — IR spectrum（--spectrum ir，需轨迹含 dipole）

## Theory
- **Power spectrum**: 速度自相关的傅立叶变换
- **IR spectrum**: 偶极矩自相关的傅立叶变换（需 dipole moments）

## New environment (from zero)

```bash
conda create -n spec python=3.12 -y
conda activate spec
conda install -c conda-forge xtb -y
cd md-vib-spectra-simulation
pip install -r requirements.txt

python power_spectrum_simulation.py CCO --run-md --spectrum ps --time 20 --temp 300 --md-dt 0.5 --autocorr 8 --zeropad 16
```

- 仅处理**已有轨迹档**（h5md / xyz+vxyz）时，可不装 `xtb`；`requirements.txt` 已涵盖主要依赖。
- macOS 上 `--run-md` 与 IR/Raman 相同，需系统可用的 `xtb`（conda-forge）。

## How to use

### 1. From h5md trajectory
```bash
cd md-vib-spectra-simulation
python power_spectrum_simulation.py ethanol_traj.h5 --dt 0.5
```

### 2. From xyz + vxyz
```bash
cd md-vib-spectra-simulation
python power_spectrum_simulation.py assets/ethanol_traj.xyz --vxyz assets/ethanol_traj.vxyz --dt 0.5
```

### 3. IR spectrum（需轨迹含 dipole）
```bash
cd md-vib-spectra-simulation
# h5md 来自 AIQM1/MNDO 等有 dipole 的方法
python power_spectrum_simulation.py ethanol_traj.h5 --spectrum ir

# xyz + vxyz + dp（每行 dx dy dz）
python power_spectrum_simulation.py traj.xyz --vxyz traj.vxyz --dp traj.dp --spectrum ir

# 同时输出 power spectrum 与 IR
python power_spectrum_simulation.py ethanol_traj.h5 --spectrum both
```

### 4. Run MD first (SMILES or xyz)
```bash
cd md-vib-spectra-simulation
# GFN2-xTB（可直接算 power spectrum）
python power_spectrum_simulation.py CCO --run-md --time 1000 --temp 300 --md-dt 0.5

# GFN2-xTB（有 dipole，可算 IR + power spectrum）
python power_spectrum_simulation.py CCO --run-md --spectrum both --time 500
```

### 5. Optional parameters
```bash
cd md-vib-spectra-simulation
python power_spectrum_simulation.py traj.h5 \
  --dt 0.5 \
  --autocorr 1024 \
  --zeropad 1024 \
  --lb 0 --ub 10000 \
  --output /tmp/chemclaw/power_spectrum.png
```

**Note**: `--autocorr` must be ≤ trajectory length (in fs). For short trajectories (e.g. 60 fs), use `--autocorr 32 --zeropad 64`.

## Dependencies (requirements.txt)
- mlatom>=3.0
- numpy
- matplotlib
- h5py
- pyh5md (for h5md format)
- rdkit (for --run-md with SMILES)

## Notes
- **Power spectrum**: 仅需速度。
- **IR spectrum**: 需 dipole moments。AIQM1+MNDO、Gaussian、GFN2-xTB MD 等有 dipole。
- **--run-md**: 目前固定使用 `GFN2-xTB`。
