# Geometry Optimizer

使用半经验方法（xTB）对分子三维结构进行几何优化。

## 功能概述

该 skill 用于**分子三维几何结构优化**，基于半经验量子化学方法，提供快速、可落地的本地优化能力。

### 核心能力

- ✅ 基于 `xTB` 完成单结构几何优化
- ✅ 支持 SMILES 自动转换为 3D 结构后优化
- ✅ 支持 XYZ、MOL、SDF 等坐标文件输入
- ✅ 支持电荷、未成对电子数、溶剂模型等参数
- ✅ 输出优化后坐标、能量、收敛状态、日志文件

### 支持的方法

- **GFN2-xTB**（默认）：高精度，适合有机分子
- **GFN1-xTB**：较早版本，某些体系可能更稳定
- **GFN-FF**：力场模式，适合大体系快速优化

## 安装依赖

### 系统依赖

需要安装 xTB：

```bash
# Ubuntu/Debian
sudo apt install xtb

# Conda
conda install -c conda-forge xtb

# 或从源码编译：https://github.com/grimme-lab/xtb
```

### Python 依赖

```bash
pip install rdkit
```

## 使用方法

### 单分子 SMILES 输入

```bash
python scripts/main_script.py --smiles "CCO" --name "乙醇"
```

### 单分子 XYZ 文件输入

```bash
python scripts/main_script.py --input-xyz molecule.xyz --output-dir ./results
```

### 批量输入

```bash
python scripts/main_script.py --input input.json --output output.json --output-dir ./results
```

### 指定方法和参数

```bash
python scripts/main_script.py \
  --smiles "CCO" \
  --method gfn2 \
  --charge 0 \
  --uhf 0 \
  --solvent water \
  --max-cycles 100 \
  --output-dir ./results
```

## 输入格式

### 单分子模式

- `--smiles`: SMILES 字符串
- `--input-xyz`: XYZ 文件路径
- `--name`: 分子名称（可选）

### 批量模式

输入 JSON 文件格式：

```json
[
  {"name": "乙醇", "smiles": "CCO"},
  {"name": "水", "smiles": "O"},
  {"name": "自定义分子", "input_xyz": "path/to/molecule.xyz"}
]
```

## 输出字段

### 成功结果

```json
{
  "name": "乙醇",
  "input_type": "smiles",
  "smiles": "CCO",
  "canonical_smiles": "CCO",
  "status": "success",
  "backend_used": "xtb",
  "method": "gfn2",
  "charge": 0,
  "uhf": 0,
  "solvent": null,
  "converged": true,
  "energy_hartree": -154.123456,
  "energy_kcal_mol": -96712.345,
  "final_gradient": 0.0012,
  "num_atoms": 9,
  "optimized_xyz_path": "./results/optimized.xyz",
  "log_path": "./results/xtb_opt.out",
  "runtime_seconds": 3.45,
  "warnings": [],
  "message": "Geometry optimization completed. Converged."
}
```

### 批量结果汇总

```json
{
  "status": "completed",
  "backend_used": "xtb",
  "total": 3,
  "success": 2,
  "partial_success": 1,
  "error": 0,
  "results": [...]
}
```

## 状态说明

- **success**: 优化完成且收敛
- **partial_success**: 优化完成但未完全收敛，仍提供最终结构
- **error**: 优化失败（输入错误、依赖缺失等）

## 常见问题

### xTB 未找到

```
xTB not available: xtb command not found
```

请安装 xTB，参考：https://xtb-docs.readthedocs.io/en/latest/installation.html

### 3D 构象生成失败

某些复杂分子可能无法自动生成合理的 3D 构象。建议：
- 提供已有的 XYZ 坐标文件
- 检查 SMILES 是否正确

### 优化不收敛

- 增加 `--max-cycles`
- 尝试不同方法（`--method gfn1` 或 `--method gfnff`）
- 检查初始结构是否合理

## 文件结构

```
geometry_optimizer/
├── SKILL.md              # Skill 说明文档
├── README.md             # 本文件
├── requirements.txt      # Python 依赖
├── scripts/
│   ├── main_script.py    # 主入口脚本
│   ├── backends/
│   │   └── xtb_backend.py    # xTB 后端实现
│   └── utils/
│       ├── io_utils.py       # 输入输出工具
│       ├── smiles_utils.py   # SMILES 处理工具
│       └── xtb_utils.py      # xTB 调用工具
└── references/           # 参考资料
```

## 参考资料

- xTB 文档：https://xtb-docs.readthedocs.io
- CREST 文档：https://crest-docs.readthedocs.io
- GFN-xTB 论文：https://doi.org/10.1021/acs.jctc.9b00143
