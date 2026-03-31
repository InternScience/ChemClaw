---
name: p-nmr-simulation
description: Predict solid-state 31P NMR chemical shifts from a CIF crystal structure using the NMRNet organic-crystal model. Outputs per-atom shift values (ppm) and a simulated spectrum PNG.
---

# 31P Solid-State NMR Simulation Skill

## When to use this
Use this skill when the user provides a **CIF crystal structure file** and wants:
- Per-atom **31P solid-state NMR** chemical shifts (ppm)
- A simulated **31P solid-state NMR spectrum PNG**
- A quick deep-learning based prediction using NMRNet's organic-crystal model

## Inputs
- **CIF file path** (required)

## Outputs
- `/tmp/chemclaw/ssnmr_31P_<cif_stem>.png`
- `/tmp/chemclaw/ssnmr_31P_<cif_stem>.md`

## Shared assets
- Required shared paths:
  - `../nmr-prediction/assets/NMRNet`
  - `../nmr-prediction/assets/Uni-Core`

## Environment setup

### 1. Install Uni-Core once
```bash
cd nmr-prediction/assets/Uni-Core
python setup.py install
```

### 2. Install Python dependencies
```bash
cd p-nmr-simulation
pip install -r requirements.txt
# 如果还没装 torch：pip install torch  (CPU 版即可)
```

### 3. Download 31P solid-state weights
```bash
cd p-nmr-simulation
python p_nmr_simulation.py --setup
```

下载目标：
- `weights/finetune/solid/Organic Crystal/P_.../cv_seed_42_fold_0/checkpoint_best.pt`
- `weights/finetune/solid/Organic Crystal/P_.../target_scaler.ss`

## How to run

```bash
cd p-nmr-simulation
python p_nmr_simulation.py path/to/structure.cif
```

## Notes
- This is a **solid-state** NMR skill, not liquid-phase SMILES prediction.
- Input should be a crystal structure file (`.cif`), not a SMILES string.
- The script is self-contained and only reuses NMRNet / Uni-Core assets.
