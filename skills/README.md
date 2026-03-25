# ChemClaw Skills 总说明书

ChemClaw 是一套面向化学分子性质预测与处理的 OpenClaw Skills，提供从分子结构转换、3D 优化到多种物性预测的完整工具链。

---

## 📦 Skills 总览

| Skill | 功能 | 后端/模型 | 输入 | 输出 |
|-------|------|-----------|------|------|
| **iupac-to-smiles** | IUPAC 名称 → SMILES | OPSIN API | IUPAC 名称 | SMILES、分子式、分子量 |
| **mol-visualizer** | 分子结构可视化 | RDKit | SMILES / 名称 | PNG / SVG 结构图 |
| **geometry-optimizer** | 3D 几何结构优化 | GFN-xTB | SMILES / XYZ | 优化坐标、能量、收敛状态 |
| **density-predictor** | 密度预测 | Bamboo-Mixer | SMILES | 密度 (g/cm³) |
| **viscosity-predictor** | 黏度预测 | Bamboo-Mixer / baseline | SMILES | 黏度 (cP) |
| **surface-tension-predictor** | 表面张力预测 | baseline / public_joblib | SMILES | 表面张力 (mN/m) |
| **pka-predictor** | pKa 预测 | Uni-pKa / custom | SMILES | pKa 值、电荷态分析 |
| **molecular-properties-predictor** | 多物性综合预测 | Bamboo-Mixer | SMILES | 11 种物化性质 |

---

## 🔧 快速开始

### 1. 安装通用依赖

```bash
# 进入 skills 目录
cd ~/.openclaw/workspace/skills

# 安装 Python 依赖
pip install rdkit requests Pillow
```

### 2. 各 Skill 独立安装

每个 skill 都有独立的 `requirements.txt` 和安装说明：

```bash
# 示例：安装 geometry_optimizer
cd geometry_optimizer
pip install -r requirements.txt

# 示例：安装 pka-predictor
cd pka-predictor
./setup_models.sh  # 自动下载模型
```

---

## 📚 Skills 详细说明

### 1. IUPAC to SMILES (`iupac-to-smiles`)

**功能**: 将 IUPAC 化学名称转换为 SMILES 字符串

**核心特性**:
- ✅ 完全使用 OPSIN API（剑桥大学）
- ✅ 聚合物智能解析（`poly[...]` 格式）
- ✅ 连接基团识别（oxy, thio, imino 等）
- ✅ 批量转换

**使用方法**:
```bash
# 单个名称
python3 scripts/iupac_to_smiles.py --name "ethanol"

# 聚合物
python3 scripts/iupac_to_smiles.py --name "poly[oxy(1-methylethylene)]"

# 批量
python3 scripts/iupac_to_smiles.py --names "ethanol,benzene,poly[oxyethylene]"
```

**输出示例**:
```json
{
  "input_name": "ethanol",
  "smiles": "CCO",
  "molecular_formula": "C2H6O",
  "molecular_weight": 46.07,
  "status": "success"
}
```

**详细文档**: [`iupac-to-smiles/SKILL.md`](./iupac-to-smiles/SKILL.md)

---

### 2. Molecular Visualizer (`mol-visualizer`)

**功能**: 将 SMILES 或化学名称转换为 2D 分子结构图

**核心特性**:
- ✅ SMILES → PNG/SVG
- ✅ IUPAC 名称自动转换
- ✅ 聚合物结构渲染
- ✅ 自定义尺寸和样式

**使用方法**:
```bash
# 从 SMILES 生成
python3 scripts/mol_visualizer.py --smiles "CCO" --output ethanol.png

# 从名称生成
python3 scripts/mol_visualizer.py --name "aspirin" --output aspirin.svg

# 聚合物
python3 scripts/mol_visualizer.py --smiles "*OCC*" --output peo.png
```

**输出**: PNG 或 SVG 格式的分子结构图

**详细文档**: [`mol-visualizer/SKILL.md`](./mol-visualizer/SKILL.md)

---

### 3. Geometry Optimizer (`geometry-optimizer`)

**功能**: 使用 GFN-xTB 半经验方法对分子 3D 结构进行几何优化

**核心特性**:
- ✅ SMILES → 3D → 优化 全自动
- ✅ XYZ 文件输入支持
- ✅ GFN2-xTB 高精度方法
- ✅ 溶剂模型支持
- ✅ 批量处理

**方法对比**:
| 方法 | 精度 | 速度 | 适用场景 |
|------|------|------|----------|
| GFN2-xTB | 高 | 中等 | 通用有机分子（默认） |
| GFN1-xTB | 中等 | 中等 | 无机体系、过渡金属 |
| GFN-FF | 较低 | 快 | 大分子、生物分子 |

**使用方法**:
```bash
# SMILES 优化
python scripts/main_script.py --smiles "CCO" --name "乙醇" --output-dir ./results

# XYZ 文件优化
python scripts/main_script.py --input-xyz molecule.xyz --output-dir ./results

# 指定溶剂
python scripts/main_script.py --smiles "CCO" --solvent water --output-dir ./results
```

**系统依赖**:
```bash
# 安装 xTB
sudo apt install xtb  # Ubuntu/Debian
# 或
conda install -c conda-forge xtb
```

**输出示例**:
```json
{
  "status": "success",
  "converged": true,
  "energy_hartree": -11.394338789631,
  "energy_kcal_mol": -7150.05,
  "optimized_xyz_path": "./results/optimized.xyz",
  "log_path": "./results/xtbopt.log"
}
```

**详细文档**: [`geometry-optimizer/SKILL.md`](./geometry-optimizer/SKILL.md)

---

### 4. Density Predictor (`density-predictor`)

**功能**: 预测小分子质量密度

**后端**: Bamboo-Mixer 单分子物性模型

**模型信息**:
- Checkpoint: `hf_bamboo_mixer/ckpts/mono/optimal.pt`
- 单位: g/cm³
- 默认温度: 25°C

**使用方法**:
```bash
# 单分子
python scripts/main_script.py --smiles "CCO" --name "乙醇"

# 批量
python scripts/main_script.py --input molecules.json --output results.json
```

**输出字段**:
- `density_prediction`: 密度预测值
- `unit`: g/cm³
- `temperature_celsius`: 温度
- `backend_used`: bamboo_mixer

**详细文档**: [`density-predictor/SKILL.md`](./density-predictor/SKILL.md)

---

### 5. Viscosity Predictor (`viscosity-predictor`)

**功能**: 预测小分子液体动态黏度

**后端**:
| 后端 | 说明 | 依赖 |
|------|------|------|
| `bamboo_mixer` | Bamboo-Mixer 真实模型 | Bamboo-Mixer 环境 |
| `custom_baseline` | RDKit 描述符 + 启发式规则 | 本地可运行 |

**使用方法**:
```bash
# 使用 bamboo_mixer 后端
python scripts/main_script.py --smiles "CCO" --backend bamboo_mixer

# 使用 baseline 后端
python scripts/main_script.py --smiles "CCO" --backend custom_baseline
```

**输出单位**: cP (centipoise)

**详细文档**: [`viscosity-predictor/SKILL.md`](./viscosity-predictor/SKILL.md)

---

### 6. Surface Tension Predictor (`surface-tension-predictor`)

**功能**: 表面张力参考预测（表面活性剂任务相关）

**后端**:
| 后端 | 原理 | 适用场景 |
|------|------|----------|
| `baseline` | RDKit 描述符 + 启发式公式 | 快速估算、工程联调 |
| `public_joblib` | PLSRegression 公开模型 | surfactant 任务参考 |

**重要说明**:
- ⚠️ 当前输出为**参考值**，非严格实验校准结果
- ⚠️ `public_joblib` 后端针对 surfactant 任务，不推荐用于普通小分子纯液体
- ✅ 推荐使用 `baseline` 后端进行快速估算

**使用方法**:
```bash
# baseline 后端
python scripts/main_script.py --smiles "O=C(O)c1ccccc1" --backend baseline

# public_joblib 后端
python scripts/main_script.py --smiles "O=C(O)c1ccccc1" --backend public_joblib
```

**输出单位**: mN/m

**详细文档**: [`surface-tension-predictor/SKILL.md`](./surface-tension-predictor/SKILL.md)

---

### 7. pKa Predictor (`pka-predictor`)

**功能**: 预测小分子酸度常数 (pKa)

**后端**:
| 后端 | 原理 | 精度 | 依赖 |
|------|------|------|------|
| `unipka` | Uni-pKa 单文件权重 + 微观态枚举 | 高 (~0.17 MAE) | 需下载模型 |
| `custom` | 官能团规则 + 启发式 | 中等 | 本地可运行 |

**模型下载** (仅 unipka 后端需要):
```bash
cd pka-predictor
./setup_models.sh
```

**unipka 后端原理**:
1. 使用 SMARTS 模板枚举相邻电荷态微观态
2. 单文件权重模型预测各微观态自由能
3. Boltzmann / log-sum-exp 汇总
4. 输出 macro pKa transitions

**使用方法**:
```bash
# unipka 后端（推荐）
./run_with_venv.sh --smiles "CC(=O)O" --name "乙酸" --backend unipka --cpu

# custom 后端
./run_with_venv.sh --smiles "CC(=O)O" --name "乙酸" --backend custom
```

**输出示例**:
```json
{
  "dominant_neutral_to_anion_pka": 4.76,
  "dominant_cation_to_neutral_pka": -1.5,
  "all_predictions": [
    {"from_charge": 0, "to_charge": -1, "pka": 4.76}
  ]
}
```

**详细文档**: [`pka-predictor/SKILL.md`](./pka-predictor/SKILL.md)

---

### 8. Molecular Properties Predictor (`molecular-properties-predictor`)

**功能**: 一次性预测 11 种物化性质

**预测性质**:
| 性质 | 符号 | 单位 |
|------|------|------|
| 熔点 | Tm | K |
| 沸点 | bp | K |
| 折射率 | nD | - |
| 液体折射率 | nD_liquid | - |
| 介电常数 | dc | - |
| 表面张力 | ST | mN/m |
| 密度 | density | g/cm³ |
| 黏度 | vis | cP |
| 蒸气压 | vapP | Pa |
| 酸性 pKa | pka_a | - |
| 碱性 pKa | pka_b | - |

**后端**: Bamboo-Mixer 多任务模型

**⚠️ 特别说明**:

**pKa 预测**: 虽然输出 `pka_a`/`pka_b`，但**不推荐**用于精确 pKa 预测。请使用 [`pka-predictor`](./pka-predictor/SKILL.md)。

**表面张力**: 单一表面张力预测推荐使用 [`surface-tension-predictor`](./surface-tension-predictor/SKILL.md)。

**推荐策略**:
| 需求 | 推荐 Skill |
|------|-----------|
| 仅 pKa | `pka-predictor` (unipka) |
| 仅表面张力 | `surface-tension-predictor` |
| 多种物性 | `molecular-properties-predictor` |

**使用方法**:
```bash
# 预测全部性质
python scripts/main_script.py --smiles "CCO" --name "乙醇"

# 预测指定性质
python scripts/main_script.py --smiles "CCO" --properties bp,ST,density
```

**详细文档**: [`molecular-properties-predictor/SKILL.md`](./molecular-properties-predictor/SKILL.md)

---

## 🔗 推荐工作流

### 工作流 1: 从名称到物性预测

```bash
# 1. IUPAC 名称 → SMILES
python3 scripts/iupac_to_smiles.py --name "2-hydroxypropanoic acid" --output step1.json

# 2. SMILES → 结构图
python3 scripts/mol_visualizer.py --smiles "CC(O)C(=O)O" --output structure.png

# 3. 3D 结构优化
python scripts/main_script.py --smiles "CC(O)C(=O)O" --output-dir ./3d

# 4. 物性预测
python scripts/main_script.py --smiles "CC(O)C(=O)O" --output properties.json
```

### 工作流 2: 聚合物处理

```bash
# 1. 聚合物名称 → SMILES
python3 scripts/iupac_to_smiles.py --name "poly[oxy(1-methylethylene)]" --output polymer.json

# 2. 聚合物结构可视化
python3 scripts/mol_visualizer.py --smiles "*OCC(C)*" --output ppo_structure.png
```

### 工作流 3: 精确 pKa 预测

```bash
# 1. 确保模型已下载
cd pka-predictor && ./setup_models.sh

# 2. 使用 unipka 后端预测
./run_with_venv.sh --smiles "CC(=O)O" --name "乙酸" --backend unipka --cpu
```

---

## 📊 模型/后端对比

### Bamboo-Mixer 系列

| Skill | 模型 | Checkpoint | 性质 |
|-------|------|------------|------|
| density-predictor | Bamboo-Mixer Mono | `ckpts/mono/optimal.pt` | 密度 |
| viscosity-predictor | Bamboo-Mixer Mono | `ckpts/mono/optimal.pt` | 黏度 |
| molecular-properties-predictor | Bamboo-Mixer Mono | `ckpts/mono/optimal.pt` | 11 种物性 |

**环境变量**:
```bash
export BAMBOO_MIXER_ADAPTER_PY=../bamboo_mixer_properties_adapter.py
export BAMBOO_MIXER_REPO=../bamboo_mixer
export BAMBOO_MIXER_PYTHON=../bamboo_mixer/.venv/bin/python
export BAMBOO_MIXER_MONO_CKPT=../bamboo_mixer/hf_bamboo_mixer/ckpts/mono/optimal.pt
```

### Uni-pKa

| Skill | 模型 | 文件 | 大小 |
|-------|------|------|------|
| pka-predictor | Uni-pKa | `t_dwar_v_novartis_a_b.pt` | ~571MB |

**下载方式**:
```bash
hf download Lai-ao/uni-pka-ckpt_v2 t_dwar_v_novartis_a_b.pt \
  --repo-type model --local-dir Uni-pKa/uni-pka-ckpt_v2
```

### 本地后端

| Skill | 后端 | 依赖 | 说明 |
|-------|------|------|------|
| iupac-to-smiles | OPSIN API | 网络 | 剑桥大学 API |
| mol-visualizer | RDKit | 本地 | 2D 渲染 |
| geometry-optimizer | xTB | xTB 二进制 | 半经验量化 |
| surface-tension-predictor | baseline | RDKit | 启发式估算 |
| viscosity-predictor | custom_baseline | RDKit | 启发式估算 |
| pka-predictor | custom | RDKit | 官能团规则 |

---

## ⚠️ 注意事项

### 精度说明

| 性质 | 推荐 Skill | 预期误差 |
|------|-----------|----------|
| pKa | pka-predictor (unipka) | ~0.17 MAE |
| 密度 | molecular-properties-predictor | ~5% |
| 黏度 | molecular-properties-predictor | ~10% |
| 表面张力 | surface-tension-predictor (baseline) | ~5% |
| 沸点/熔点 | molecular-properties-predictor | ~10-15K |

### 使用建议

1. **筛选 vs 精确**: Bamboo-Mixer 适合快速筛选，精确结果需用高精度方法复核
2. **pKa 专用**: pKa 预测请使用 `pka-predictor`，不要用 `molecular-properties-predictor`
3. **表面张力**: 单一表面张力用 `surface-tension-predictor`，多物性用 `molecular-properties-predictor`
4. **3D 优化**: xTB 适合预优化，DFT 计算前建议先用 xTB 预优化

### 系统要求

- **Python**: 3.8+
- **xTB**: 6.x (geometry-optimizer 必需)
- **网络**: OPSIN API、Hugging Face 下载需要网络连接
- **内存**: Bamboo-Mixer 推理约需 2-4GB RAM

---

## 📖 参考资料

- **Bamboo-Mixer**: 单分子物性预测模型
- **Uni-pKa**: 基于 Bohrium notebook 的 pKa 预测流程
- **GFN-xTB**: https://xtb-docs.readthedocs.io
- **OPSIN**: https://opsin.ch.cam.ac.uk/
- **RDKit**: https://www.rdkit.org/

---

## 🗂️ 目录结构

```
skills/
├── README.md                      # 本文件
├── iupac-to-smiles/
│   ├── SKILL.md
│   ├── scripts/
│   └── requirements.txt
├── mol-visualizer/
│   ├── SKILL.md
│   ├── scripts/
│   └── requirements.txt
├── geometry-optimizer/
│   ├── SKILL.md
│   ├── scripts/
│   └── requirements.txt
├── density-predictor/
│   ├── SKILL.md
│   ├── scripts/
│   └── requirements.txt
├── viscosity-predictor/
│   ├── SKILL.md
│   ├── scripts/
│   └── requirements.txt
├── surface-tension-predictor/
│   ├── SKILL.md
│   ├── scripts/
│   └── requirements.txt
├── pka-predictor/
│   ├── SKILL.md
│   ├── scripts/
│   ├── Uni-pKa/
│   └── requirements.txt
└── molecular-properties-predictor/
    ├── SKILL.md
    ├── scripts/
    └── requirements.txt
```

---

**版本**: 1.0  
**更新日期**: 2026-03-23
