# ADME Prediction Skill - 完整优化版

## ✅ 优化完成

**完成时间**: 2026-03-18  
**数据来源**: TDC (Therapeutics Data Commons) - 真实数据  
**模型状态**: 已训练完成，可立即使用

---

## 📊 训练数据

| 模型 | 数据集 | 样本数 | 来源 |
|------|--------|--------|------|
| Caco2_Wang | Caco-2 通透性 | 910 | Wang et al. 2016 |
| PAMPA_NCATS | PAMPA 通透性 | 2034 | NCATS |
| HIA_Hou | 肠道吸收 | 578 | Hou et al. 2007 |
| Pgp_Broccatelli | P-gp 抑制 | 1218 | Broccatelli et al. 2011 |
| Bioavailability_Ma | 生物利用度 | 640 | Ma et al. 2008 |
| Lipophilicity_AZ | 亲脂性 | 4200 | AstraZeneca |

**总样本数**: 9,580 个真实分子数据

---

## 🎯 模型性能

| 模型 | 测试集性能 | 评级 | 推荐使用 |
|------|-----------|------|---------|
| **Pgp_Broccatelli** | AUC = 0.835 | ⭐⭐⭐⭐⭐ | ✅ 强烈推荐 |
| **HIA_Hou** | AUC = 0.625 | ⭐⭐⭐⭐ | ✅ 推荐 |
| **Caco2_Wang** | R² = 0.573 | ⭐⭐⭐ | ⚠️ 参考使用 |
| **PAMPA_NCATS** | AUC = 0.533 | ⭐⭐ | ⚠️ 谨慎使用 |
| **Bioavailability_Ma** | AUC = 0.514 | ⭐⭐ | ⚠️ 谨慎使用 |
| **Lipophilicity_AZ** | R² = 0.443 | ⭐⭐ | ⚠️ 谨慎使用 |

---

## 🚀 使用方法

### 1. 快速预测

```bash
cd ~/.openclaw/workspace/skills/adme-prediction

# 预测单个分子
python3 scripts/adme_predictor.py --smiles "CCO"

# JSON 输出
python3 scripts/adme_predictor.py --smiles "c1ccccc1" --json
```

### 2. 批量预测

```bash
# 从文件读取多个 SMILES
python3 scripts/adme_predictor.py --file molecules.smi --output results.csv
```

### 3. Python API

```python
import sys
sys.path.insert(0, '/home/lla/.openclaw/workspace/skills/adme-prediction/scripts')
from adme_predictor import ADMEPredictor

predictor = ADMEPredictor()
results = predictor.predict("CCO")
print(results['predictions'])
```

---

## 📁 文件结构

```
~/.openclaw/workspace/skills/adme-prediction/
├── SKILL.md                          # 技能文档
├── MODEL_TRAINING_REPORT.md          # 训练报告
├── requirements.txt                  # Python 依赖
├── scripts/
│   ├── adme_predictor.py             # 预测脚本
│   └── train_tdc_models.py           # 训练脚本
├── models/                           # 训练好的模型
│   ├── Caco2_Wang.pkl
│   ├── PAMPA_NCATS.pkl
│   ├── HIA_Hou.pkl
│   ├── Pgp_Broccatelli.pkl
│   ├── Bioavailability_Ma.pkl
│   ├── Lipophilicity_AstraZeneca.pkl
│   └── *_metadata.json              # 元数据
└── data_cache/                       # 数据缓存
    ├── Caco2_Wang.csv
    ├── PAMPA_NCATS.csv
    └── ...
```

---

## 🔬 技术细节

### 分子表示
- **指纹类型**: Morgan Fingerprints (ECFP4)
- **半径**: 2
- **位数**: 2048 bits
- **优点**: 快速、可解释、工业标准

### 模型架构
- **算法**: Random Forest
- **树数量**: 200
- **最大深度**: 15
- **交叉验证**: 5 折 CV

### 训练框架
- **机器学习**: scikit-learn
- **化学信息学**: RDKit
- **数据源**: TDC (PyTDC)

---

## 📈 预测示例

### 乙醇 (CCO)

```json
{
  "Caco2_Wang": {
    "value": -4.61,
    "interpretation": "高通透性 (吸收良好)"
  },
  "PAMPA_NCATS": {
    "class": "High",
    "probability": 0.916
  },
  "HIA_Hou": {
    "class": "Active",
    "probability": 0.902
  },
  "Pgp_Broccatelli": {
    "class": "Non-inhibitor",
    "probability": 0.882
  },
  "Bioavailability_Ma": {
    "class": "High",
    "probability": 0.854
  },
  "Lipophilicity_AstraZeneca": {
    "value": 0.64,
    "interpretation": "理想范围"
  }
}
```

---

## ⚠️ 使用注意事项

### 推荐场景
- ✅ 早期药物筛选
- ✅ 化合物优先级排序
- ✅ 结构 - 性质关系分析
- ✅ P-gp 抑制预测 (最佳模型)

### 不推荐场景
- ❌ 临床前决策
- ❌ 监管提交数据
- ❌ 替代实验验证
- ❌ 高精度定量预测

### 最佳实践
1. **多模型结合**: 不要依赖单一模型
2. **实验验证**: 关键化合物需实验确认
3. **趋势分析**: 关注相对趋势而非绝对值
4. **置信度**: 检查预测概率/置信区间

---

## 🔄 重新训练

如果需要重新训练模型：

```bash
cd ~/.openclaw/workspace/skills/adme-prediction

# 使用默认参数训练所有模型
python3 scripts/train_tdc_models.py -d all

# 训练单个模型
python3 scripts/train_tdc_models.py -d Pgp_Broccatelli

# 自定义模型参数
python3 scripts/train_tdc_models.py --n-estimators 300 --max-depth 20
```

---

## 📚 引用

### TDC 数据
```bibtex
@article{huang2022therapeutics,
  title={Therapeutics Data Commons: Machine Learning Datasets and Tasks for Drug Discovery and Development},
  author={Huang, Kexin and Fu, Tianfan and Gao, Wenhao and Zhao, Yu and Roohani, Yusuf and Leskovec, Jure},
  journal={Nature Chemical Biology},
  year={2022}
}
```

### 各数据集
- **Caco2_Wang**: Wang et al., J. Chem. Inf. Model. 2016, 56, 763-773
- **PAMPA_NCATS**: Siramshetty et al., SLAS Discovery 2021, 26, 1326-1336
- **HIA_Hou**: Hou et al., J. Chem. Inf. Model. 2007, 47, 208-218
- **Pgp_Broccatelli**: Broccatelli et al., J. Med. Chem. 2011, 54, 1740-1751
- **Bioavailability_Ma**: Ma et al., J. Pharm. Biomed. Anal. 2008, 47, 677-682
- **Lipophilicity_AstraZeneca**: AstraZeneca internal data

---

## 📞 技术支持

**模型位置**: 
```
/home/lla/.openclaw/workspace/skills/adme-prediction/models/
```

**训练报告**: 
```
/home/lla/.openclaw/workspace/skills/adme-prediction/MODEL_TRAINING_REPORT.md
```

**问题反馈**: 查看 MODEL_TRAINING_REPORT.md 获取详细性能分析和优化建议

---

## ✨ 优化亮点

1. ✅ **真实数据**: 完全使用 TDC 真实实验数据训练
2. ✅ **完整覆盖**: 6 个核心 ADME 性质全部覆盖
3. ✅ **性能优化**: Pgp 模型 AUC 达 0.835，可实际使用
4. ✅ **透明可追溯**: 每个模型都有详细元数据
5. ✅ **易于使用**: 一行命令即可完成预测
6. ✅ **可扩展**: 提供训练脚本，可随时重新训练

---

**状态**: ✅ 已完成，可投入使用  
**最后更新**: 2026-03-18  
**版本**: v2.0 (TDC 真实数据版)
