# pKa Predictor

`pKa Predictor` 是一个面向 OpenClaw 的 pKa 预测 skill，用于对小分子进行酸碱解离常数预测。当前支持两类后端：

- `custom`：本地规则 / 官能团识别 / 可扩展模型预测
- `unipka`：基于 Uni-pKa 推理流程的预测后端

该 skill 主要用于为 OpenClaw 提供统一的 pKa 预测入口，支持单分子输入、批量输入和结构化结果输出。

---

## ⚡ 快速开始

### 1. 安装依赖

```bash
cd skills/pka-predictor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 下载模型权重（仅 unipka 后端需要）

```bash
# 安装 Hugging Face CLI
pip install huggingface_hub

# 下载模型文件（~571MB）
mkdir -p skills/pka-predictor/Uni-pKa/uni-pka-ckpt_v2
hf download Lai-ao/uni-pka-ckpt_v2 t_dwar_v_novartis_a_b.pt \
  --repo-type model \
  --local-dir skills/pka-predictor/Uni-pKa/uni-pka-ckpt_v2

# 下载模板文件
hf download Lai-ao/uni-pka-ckpt_v2 smarts_pattern.tsv \
  --repo-type model \
  --local-dir skills/pka-predictor/Uni-pKa/uni-pka-ckpt_v2

hf download Lai-ao/uni-pka-ckpt_v2 simple_smarts_pattern.tsv \
  --repo-type model \
  --local-dir skills/pka-predictor/Uni-pKa/uni-pka-ckpt_v2
```

### 3. 测试运行

```bash
# custom 后端
./run_with_venv.sh --smiles "CC(=O)O" --name "乙酸" --backend custom

# unipka 后端
./run_with_venv.sh --smiles "CC(=O)O" --name "乙酸" --backend unipka --cpu
```

---

## Features

- 支持单个 SMILES 的 pKa 预测
- 支持批量分子输入
- 支持 `JSON`、`CSV`、`TXT` 等结果输出形式
- 支持 `custom` 和 `unipka` 两种后端
- 返回结构化结果，便于 OpenClaw 调用
- 可用于本地测试、规则预测和模型推理流程接入

---

## Repository Layout

```text
pka-predictor/
├── README.md
├── SKILL.md
├── DEBUG_ENV.md
├── requirements.txt
├── run_with_venv.sh
├── scripts/
│   ├── predict_pka.py
│   ├── backends/
│   └── utils/
├── Uni-Core/
└── Uni-pKa/
    └── uni-pka-ckpt_v2/
        ├── t_dwar_v_novartis_a_b.pt    # 模型权重（需从 Hugging Face 下载）
        ├── smarts_pattern.tsv          # SMARTS 模板
        └── simple_smarts_pattern.tsv   # 简化 SMARTS 模板
```