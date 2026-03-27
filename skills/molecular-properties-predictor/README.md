---
name: molecular_properties_predictor
description: Predict multiple molecular physicochemical properties for small molecules using an integrated Bamboo-Mixer mono-property backend.
trigger: ["molecular properties", "物性预测", "熔点", "沸点", "折射率", "介电常数", "表面张力", "密度", "黏度", "蒸气压", "pKa"]
---

# Molecular Properties Predictor

`molecular-properties-predictor` 是一个面向 ChemClaw / OpenClaw 的化学类 skill，用于预测**小分子的多种物化性质**。

当前版本已经完成对 **Bamboo-Mixer 单分子模型** 的真实接入，并一次最多可以返回以下 11 个性质：

- `Tm`：熔点（K）
- `bp`：沸点（K）
- `nD`：折射率（无单位）
- `nD_liquid`：液体折射率（无单位）
- `pka_a`：酸性 pKa
- `pka_b`：碱性 pKa
- `dc`：介电常数（无单位）
- `ST`：表面张力（mN/m）
- `density`：密度（g/cm^3）
- `vis`：黏度（cP）
- `vapP`：蒸气压（Pa）

本仓库将 `skills/bamboo_mixer/` 作为 **内置上游代码依赖** 一并管理，但默认**不提交本地虚拟环境和 checkpoint**。Bamboo-Mixer 上游仓库采用 Apache-2.0 许可证，公开 checkpoint 由 Hugging Face 提供。

---

## 1. 目录结构

```text
ChemClaw/
└── skills/
    ├── molecular-properties-predictor/
    │   ├── README.md
    │   ├── SKILL.md
    │   ├── requirements.txt
    │   └── scripts/
    │       ├── main_script.py
    │       ├── adapters/
    │       │   └── bamboo_mixer_properties_adapter.py
    │       ├── backends/
    │       │   └── bamboo_backend.py
    │       ├── bridges/
    │       │   └── bamboo_mixer_bridge.py
    │       ├── setup_bamboo_env.sh
    │       ├── download_bamboo_ckpt.sh
    │       └── utils/
    │           ├── io_utils.py
    │           └── smiles_utils.py
    └── bamboo_mixer/