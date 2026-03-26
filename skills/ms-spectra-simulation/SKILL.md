---
name: ms-spectra-simulation
description: Predict and visualize MS/MS spectra from a single SMILES using the bundled local Fiora installation inside this skill directory. Use when the user wants a mass spectrum, MGF output, or a plotted stick spectrum from SMILES, with optional custom Name, precursor type, collision energy, and instrument settings.
---

# MS Spectra Simulation Skill

## When to use this
Use this skill when the user provides a **SMILES** string and wants:
- Predicted **MS/MS spectrum**
- Standard **MGF** output
- A quick **stick-spectrum PNG** visualization
- Simple defaults without manually preparing a CSV

## Inputs
- **SMILES** string (required)
- `--name` (optional, default: `mol1`)
- `--precursor` (optional, default: `[M+H]+`)
- `--ce` (optional, default: `20`)
- `--instrument` (optional, default: `HCD`)
- `--output-stem` (optional, default: `predicted_ms`)
- `--plot / --no-plot` (optional, default: plot enabled)
- `--show-title / --no-show-title` (optional, default: no title on the plot)

## Outputs
- `/tmp/chemclaw/predicted_ms.mgf`
- `/tmp/chemclaw/predicted_ms.png`

If `--output-stem mol1` is used, the outputs become:
- `/tmp/chemclaw/mol1.mgf`
- `/tmp/chemclaw/mol1.png`

## Agent response
When returning results to the user, include the generated spectrum image directly in the response when a PNG was created.

## New environment (from zero)

```bash
conda create -n fiora-osx python=3.10 pip -y
conda activate fiora-osx

cd ms-spectra-simulation/assets/fiora
pip install .

cd ../..
python ms_spectra_simulation.py CCO
```

- This skill bundles its own `assets/fiora/` subdirectory.
- Run the script inside the `fiora-osx` environment so `torch`, `rdkit`, and `fiora` are available.

## How to use (environment already prepared)

### Fastest default run
```bash
cd ms-spectra-simulation
python ms_spectra_simulation.py CCO
```

This uses:
- `name=mol1`
- `precursor=[M+H]+`
- `ce=20`
- `instrument=HCD`
- plot enabled
- plot title hidden

### Custom metadata
```bash
cd ms-spectra-simulation
python ms_spectra_simulation.py "CCO" \
  --name mol1 \
  --precursor "[M+H]+" \
  --ce 20 \
  --instrument HCD
```

### Keep the spectrum but skip PNG
```bash
cd ms-spectra-simulation
python ms_spectra_simulation.py "CCO" --no-plot
```

### Show the title on the figure
```bash
cd ms-spectra-simulation
python ms_spectra_simulation.py "CCO" --show-title
```
