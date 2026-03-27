```markdown
# Surface Tension Predictor

根据分子结构提供与 **surfactant（表面活性剂）任务相关** 的表面张力参考预测结果的 OpenClaw skill。

---

## 1. 项目定位

本项目当前不是一个“通用小分子纯液体表面张力预测器”，而是一个：

- 面向 **OpenClaw 接入**
- 面向 **本地 WSL 可运行**
- 面向 **工程联调与公开模型接入验证**
- 面向 **surfactant 任务相关表面张力参考预测**

的双后端 skill。

当前支持两个后端：

- `baseline`：启发式工程基线
- `public_joblib`：公开 surfactant 模型参考后端

---

## 2. 当前能力边界

### 2.1 这个 skill 适合做什么

适合：

- 根据 SMILES 给出一个表面张力相关参考值
- 对比多个分子在当前模型下的相对输出
- 本地跑通表面张力相关 skill
- 作为 OpenClaw 化学类 skill 的一部分集成
- 验证公开模型接入与推理链路

### 2.2 这个 skill 当前不适合做什么

当前不适合直接用于：

- 通用普通小分子纯液体表面张力精确预测
- 任意温度下的真实表面张力定量预测
- 已实验严格校准的最终科研结论输出
- 对明显超出 surfactant 任务分布的分子进行强结论解释

---

## 3. 目录结构

```text
surface-tension-predictor/
├── README.md
├── SKILL.md
├── requirements.txt
├── references/
│   └── models/
│       ├── linear_SurfaceTension.joblib
│       └── linear_SurfaceTension.joblib_parameters
└── scripts/
    ├── main_script.py
    ├── check_env.py
    ├── backends/
    │   ├── __init__.py
    │   ├── surface_tension_backend.py
    │   └── public_joblib_backend.py
    └── utils/
        ├── __init__.py
        ├── io_utils.py
        ├── smiles_utils.py
        ├── descriptors.py
        └── mordred_utils.py