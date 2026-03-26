---
name: uv-vis-spectrum-simulation
description: UV-Vis spectrum from SMILES via UV-adVISor (https://spectra.collaborationspharma.com/). Input SMILES, auto-fetch, plot PNG.
---

# UV-Vis Spectrum Simulation Skill

## When to use this
Use this skill when the user provides **SMILES** and wants:
- Predicted UV-Vis spectrum (400-700 nm)
- Publication-ready PNG plot
- No manual website steps — script fetches from UV-adVISor automatically

## Inputs
- **SMILES string** (e.g. CCO for ethanol)
- Or **CSV file path** (if previously exported)

## Outputs
- `/tmp/chemclaw/uv_vis_spectrum.png` — spectrum plot

## New environment (from zero)

- 仅需 **Python 3.8+**（建议 3.10–3.12），无需额外 pip 套件。
- 需可连外网（脚本会 POST 到 UV-adVISor）。
- 脚本目前预设即停用 SSL 凭证验证，以避免 macOS / Python 组合下的 `CERTIFICATE_VERIFY_FAILED`。

```bash
cd uv-vis-spectrum-simulation
python uv_vis_spectrum_simulation.py CCO
```

## How to use

```bash
cd uv-vis-spectrum-simulation
python uv_vis_spectrum_simulation.py CCO
python uv_vis_spectrum_simulation.py "c1ccc2ccccc2c1"  # naphthalene
python uv_vis_spectrum_simulation.py path/to.csv       # or from CSV
```

### Optional
```bash
cd uv-vis-spectrum-simulation
python uv_vis_spectrum_simulation.py CCO --output /tmp/chemclaw/ethanol_uv.png
```

## Dependencies
- None（仅标准库：urllib, re, base64）

## Notes
- **UV-adVISor**: ML model at spectra.collaborationspharma.com
- Script POSTs SMILES → "Plot graph online" → extracts PNG from HTML → saves
- **Requires network connection**
- 脚本预设使用 insecure SSL context，以绕过本机 `CERTIFICATE_VERIFY_FAILED` 问题。
