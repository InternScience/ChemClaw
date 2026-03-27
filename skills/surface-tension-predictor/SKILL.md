---
name: surface_tension_predictor
description: 基于 SMILES 提供与 surfactant（表面活性剂）任务相关的表面张力参考预测，支持 baseline 启发式后端与 public_joblib 公开模型参考后端。
trigger:
  [
    "surface tension",
    "表面张力",
    "界面张力",
    "surfactant",
    "表面活性剂",
    "表面活性剂性质",
    "mN/m",
    "表面性质",
    "PE-12"
  ]
---

# Surface Tension Predictor

该 skill 用于根据分子的 **SMILES** 输出与 **surfactant（表面活性剂）任务相关** 的表面张力参考预测结果。

## 核心定位

本 skill 当前的定位是：

- 一个 **工程上可运行** 的表面张力相关预测 skill
- 一个支持 **OpenClaw 调用** 的结构-性质预测组件
- 一个包含：
  - `baseline` 启发式工程基线
  - `public_joblib` 公开 surfactant 模型参考后端
  的双后端实现

**重要说明：**

本 skill 当前**不应**被解释为：

- 通用小分子纯液体表面张力预测器
- 任意温度下真实表面张力预测模型
- 已完成科学验证的最终正式模型

其中，`public_joblib` 后端更准确的理解应为：

- **公开 surfactant 任务相关模型的接入与参考推理后端**
- 输出值主要用于：
  - 公开模型接入验证
  - 工程联调
  - 与 baseline 对照
  - 在相近任务设定下做参考输出

---

## 适用场景

当用户有以下需求时，适合调用本 skill：

- 希望基于 SMILES 获得一个**表面张力相关参考值**
- 希望比较多个分子在当前模型下的相对输出差异
- 希望测试某个分子在 surfactant 相关公开模型上的推理结果
- 希望验证 OpenClaw 中表面张力相关 skill 的联调链路
- 希望对比 `baseline` 与 `public_joblib` 的输出差异
- 希望把表面张力相关预测能力接入本地化工作流

---

## 不建议的使用方式

以下场景下，不应直接把当前结果解释为真实物性结论：

- 将 `public_joblib` 输出直接视为**普通小分子纯液体**的真实表面张力
- 将结果用于声称“任意温度下的表面张力预测”
- 将当前输出当作已完成严格实验校准的最终数值
- 对明显不属于 surfactant 任务分布的分子做过强解释

---

## 当前支持的后端

本 skill 当前支持两个后端：

### 1）baseline

#### 用途

- 本地基线预测
- 工程联调
- 轻量、本地、低依赖运行
- 在无公开模型环境下给出一个可返回结果

#### 原理

- RDKit 解析分子
- 计算少量二维分子描述符
- 使用启发式经验公式得到估算值

#### 特点

- 本地稳定可跑
- 适合作为工程基线
- 不依赖公开模型文件
- 更适合联调、快速测试和占位输出

#### 局限

- 不属于正式训练模型
- 预测值是启发式工程估算
- 不应过度解释其物理意义

---

### 2）public_joblib

#### 用途

- 接入公开训练模型
- 验证公开模型推理链路
- 作为与 baseline 对照的参考后端
- 提供 surfactant 任务相关的表面张力参考输出

#### 原理

- RDKit 解析分子
- 计算 Mordred 描述符
- 根据 `linear_SurfaceTension.joblib_parameters` 提取并排序特征
- 使用 `linear_SurfaceTension.joblib` 中的预测器对象进行预测

#### 当前已确认

- 预测器对象类型为 `PLSRegression`
- 特征维度为 `130`
- 已在本地推理成功
- 部分分子会出现一定数量的缺失描述符
- 当前实现已对齐上游 `properties_prediction.py` 的核心推理逻辑

#### 更准确的语义

`public_joblib` 后端当前应理解为：

- **公开 surfactant 模型的接入版**
- **参考后端**
- **不是通用纯液体小分子表面张力最终模型**

---

## 输入形式

本 skill 当前支持以下输入形式：

- 单个 `SMILES` 字符串
- 分子名称 + `SMILES`
- 可扩展为批量 JSON 输入（若脚本实现中已支持）

推荐输入字段：

- `smiles`
- 可选 `name`

若脚本版本已支持，也可接收：

- `temperature_c`

但需要注意：

- 当前 `public_joblib` 后端即使接收温度参数，也**不代表实际使用温度参与预测**
- 因此不能把结果解释为温度显式建模结果

---

## 输出字段

### 主要输出字段

- `surface_tension_prediction`

如果当前实现中已加入更保守的语义字段，还可能包括：

- `surface_tension_reference_prediction`

### 通用字段

- `unit`
- `model_source`
- `canonical_smiles`
- `status`

### baseline 后端常见附加字段

- `descriptor_summary`
- 或其他基础描述符字段

### public_joblib 后端常见附加字段

- `model_path`
- `params_path`
- `feature_count`
- `missing_feature_count`
- `missing_feature_ratio`
- `missing_features`
- `loaded_object_summary`
- `params_summary`
- `predictor_type`
- `preprocess_style`
- `applicability_warning`
- `domain_risk_level`

---

## 结果解释建议

### baseline 结果

更适合解释为：

- 工程启发式基线输出
- 快速粗略估算值
- 用于本地联调与占位参考

### public_joblib 结果

更适合解释为：

- 公开 surfactant 任务模型下的参考输出
- 在当前特征空间与公开模型链路中的推理值
- 用于模型接入验证、相对比较和参考对照

不建议直接解释为：

- 普通小分子纯液体在标准条件下的真实表面张力

---

## 当前环境约定

由于公开模型后端存在 Python / sklearn 兼容要求，当前建议保留两套虚拟环境：

### 1）baseline 环境

```text
.venv