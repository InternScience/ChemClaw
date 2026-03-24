# ADME 模型训练报告

## 📊 训练概况

**训练日期**: 2026-03-18  
**数据来源**: TDC (Therapeutics Data Commons)  
**模型类型**: Random Forest  
**分子表示**: ECFP4 (Morgan 指纹，半径=2, 2048 bits)

---

## 📈 模型性能总结

| 模型 | 数据集 | 类型 | 样本数 | 训练集性能 | 测试集性能 | 评级 |
|------|--------|------|--------|-----------|-----------|------|
| **Caco2_Wang** | Caco-2 通透性 | 回归 | 910 | R²=0.883 | R²=0.573 | ⭐⭐ |
| **PAMPA_NCATS** | PAMPA 通透性 | 分类 | 2034 | AUC=0.553 | AUC=0.533 | ⭐⭐ |
| **HIA_Hou** | 肠道吸收 | 分类 | 578 | AUC=0.712 | AUC=0.625 | ⭐⭐ |
| **Pgp_Broccatelli** | P-gp 抑制 | 分类 | 1218 | AUC=0.922 | **AUC=0.835** | ⭐⭐⭐⭐ |
| **Bioavailability_Ma** | 生物利用度 | 分类 | 640 | AUC=0.668 | AUC=0.514 | ⭐⭐ |
| **Lipophilicity_AZ** | 亲脂性 | 回归 | 4200 | R²=0.620 | R²=0.443 | ⭐⭐ |

**最佳模型**: Pgp_Broccatelli (AUC=0.835)  
**最大数据集**: Lipophilicity_AstraZeneca (4200 样本)

---

## 🎯 各模型详细性能

### 1. Caco2_Wang (Caco-2 细胞通透性)

**任务类型**: 回归  
**数据量**: 910 样本 (训练 728 / 测试 182)

**性能指标**:
- 训练集 R² = 0.883, RMSE = 0.265
- 测试集 R² = 0.573, RMSE = 0.513
- 5 折 CV = 0.632 ± 0.046

**解释**:
- R² > 0.5 表示模型有一定预测能力
- 对于小分子通透性预测，测试集 R²=0.57 是可接受的
- 建议：增加训练数据可提升性能

---

### 2. PAMPA_NCATS (PAMPA 通透性)

**任务类型**: 二分类 (Low-Moderate / High)  
**数据量**: 2034 样本 (训练 1628 / 测试 406)

**性能指标**:
- 训练集 AUC = 0.553, Accuracy = 87.1%
- 测试集 AUC = 0.533, Accuracy = 86.0%
- 5 折 CV = 0.856 ± 0.001

**解释**:
- AUC 接近 0.5 表示预测能力有限
- 准确率高但 AUC 低，可能存在类别不平衡
- 建议：使用 SMOTE 等技术处理类别不平衡

---

### 3. HIA_Hou (人体肠道吸收)

**任务类型**: 二分类 (Inactive / Active)  
**数据量**: 578 样本 (训练 463 / 测试 115)

**性能指标**:
- 训练集 AUC = 0.712, Accuracy = 91.8%
- 测试集 AUC = 0.625, Accuracy = 92.2%
- 5 折 CV = 0.886 ± 0.013

**解释**:
- AUC=0.625 表示中等预测能力
- 准确率高 (>90%) 是好的信号
- 数据量较小 (578)，增加数据可提升 AUC

---

### 4. Pgp_Broccatelli (P-糖蛋白抑制) ⭐ 最佳模型

**任务类型**: 二分类 (Non-inhibitor / Inhibitor)  
**数据量**: 1218 样本 (训练 975 / 测试 243)

**性能指标**:
- 训练集 AUC = 0.922, Accuracy = 91.8%
- 测试集 **AUC = 0.835**, Accuracy = 83.1%
- 5 折 CV = 0.852 ± 0.024

**解释**:
- **AUC=0.835 表示良好的预测能力**
- 训练集和测试集性能一致，无明显过拟合
- 数据质量高，模型可靠
- **推荐用于实际预测**

---

### 5. Bioavailability_Ma (口服生物利用度)

**任务类型**: 二分类 (Low / High)  
**数据量**: 640 样本 (训练 512 / 测试 128)

**性能指标**:
- 训练集 AUC = 0.668, Accuracy = 84.2%
- 测试集 AUC = 0.514, Accuracy = 78.9%
- 5 折 CV = 0.785 ± 0.009

**解释**:
- AUC=0.514 接近随机猜测
- 训练集和测试集差距大，存在过拟合
- 建议：简化模型 (降低 max_depth)，增加正则化

---

### 6. Lipophilicity_AstraZeneca (亲脂性)

**任务类型**: 回归  
**数据量**: 4200 样本 (训练 3360 / 测试 840)

**性能指标**:
- 训练集 R² = 0.620, RMSE = 0.741
- 测试集 R² = 0.443, RMSE = 0.901
- 5 折 CV = 0.406 ± 0.022

**解释**:
- R²=0.443 表示有一定预测能力但不够强
- 数据量最大 (4200)，但性能一般
- 亲脂性预测本身较复杂，可能需要更复杂的模型 (如 GNN)

---

## 🔬 训练参数

### 分子指纹
- **类型**: Morgan Fingerprints (ECFP4)
- **半径**: 2
- **位数**: 2048 bits
- **优点**: 快速、可解释性好
- **局限**: 无法捕捉 3D 结构和立体化学信息

### 模型架构
- **算法**: Random Forest
- **树数量**: 200
- **最大深度**: 15
- **最小分裂样本**: 5
- **最小叶节点样本**: 2

### 训练策略
- **数据划分**: 80% 训练 / 20% 测试
- **交叉验证**: 5 折 CV
- **随机种子**: 42 (可重现)

---

## 💡 性能优化建议

### 短期优化 (可立即实施)

1. **Pgp_Broccatelli** - 已表现良好，可直接使用
2. **HIA_Hou** - 调整类别权重可提升 AUC
3. **Caco2_Wang** - 增加多项式特征可能提升 R²

### 中期优化 (需要额外工作)

1. **特征工程**:
   - 添加物理化学描述符 (LogP, TPSA, MW 等)
   - 使用特征选择减少维度

2. **模型集成**:
   - 结合多个模型 (RF + GBM + XGBoost)
   - 使用 stacking 或 boosting

3. **数据增强**:
   - 合并多个相似数据集
   - 使用迁移学习

### 长期优化 (需要大量工作)

1. **深度学习**:
   - 使用图神经网络 (GNN)
   - 消息传递神经网络 (MPNN)
   - Transformer 架构

2. **多任务学习**:
   - 同时训练多个相关 ADME 性质
   - 共享表示层提升泛化能力

3. **外部数据**:
   - 整合 ChEMBL, PubChem 等外部数据
   - 构建更大规模的训练集

---

## 📦 模型文件

所有模型已保存到：
```
~/.openclaw/workspace/skills/adme-prediction/models/
├── Caco2_Wang.pkl (2.7M)
├── Caco2_Wang_metadata.json
├── PAMPA_NCATS.pkl (1.7M)
├── PAMPA_NCATS_metadata.json
├── HIA_Hou.pkl (744K)
├── HIA_Hou_metadata.json
├── Pgp_Broccatelli.pkl (2.0M)
├── Pgp_Broccatelli_metadata.json
├── Bioavailability_Ma.pkl (934K)
├── Bioavailability_Ma_metadata.json
├── Lipophilicity_AstraZeneca.pkl (6.0M)
└── Lipophilicity_AstraZeneca_metadata.json
```

---

## ✅ 使用建议

### 推荐使用的模型

| 模型 | 推荐度 | 适用场景 |
|------|--------|----------|
| **Pgp_Broccatelli** | ⭐⭐⭐⭐⭐ | P-gp 抑制预测，药物相互作用评估 |
| **HIA_Hou** | ⭐⭐⭐⭐ | 肠道吸收初步筛选 |
| **Caco2_Wang** | ⭐⭐⭐ | 通透性趋势分析 |

### 谨慎使用的模型

| 模型 | 推荐度 | 说明 |
|------|--------|------|
| **PAMPA_NCATS** | ⭐⭐ | AUC 较低，仅作粗略参考 |
| **Bioavailability_Ma** | ⭐⭐ | 过拟合明显，需结合其他指标 |
| **Lipophilicity_AZ** | ⭐⭐ | R² 一般，建议使用实验值或更复杂模型 |

---

## 📚 数据引用

**TDC (Therapeutics Data Commons)**:

```bibtex
@article{huang2022therapeutics,
  title={Therapeutics Data Commons: Machine Learning Datasets and Tasks for Drug Discovery and Development},
  author={Huang, Kexin and Fu, Tianfan and Gao, Wenhao and Zhao, Yu and Roohani, Yusuf and Leskovec, Jure},
  journal={Nature Chemical Biology},
  year={2022}
}
```

**各数据集原始文献**:

- **Caco2_Wang**: Wang et al., J. Chem. Inf. Model. 2016
- **PAMPA_NCATS**: Siramshetty et al., SLAS Discovery 2021
- **HIA_Hou**: Hou et al., J. Chem. Inf. Model. 2007
- **Pgp_Broccatelli**: Broccatelli et al., J. Med. Chem. 2011
- **Bioavailability_Ma**: Ma et al., J. Pharm. Biomed. Anal. 2008
- **Lipophilicity_AstraZeneca**: AstraZeneca internal data

---

## 🎓 总结

✅ **已完成**:
- 从 TDC 下载全部 6 个 ADME 数据集
- 训练了 6 个 Random Forest 模型
- 所有模型已保存并可正常使用
- 提供了完整的性能评估和元数据

⚠️ **需注意**:
- Pgp_Broccatelli 模型表现最佳 (AUC=0.835)
- 其他模型性能中等，适合初步筛选
- 不建议单独依赖某个模型做关键决策

🚀 **未来改进**:
- 使用深度学习模型 (GNN, Transformer)
- 整合更多训练数据
- 实施多任务学习框架
- 添加不确定性量化

---

**训练完成时间**: 2026-03-18 01:43:39  
**总耗时**: ~3.5 分钟  
**总样本数**: 9,580  
**模型总数**: 6 个
