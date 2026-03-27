# xTB 参考资料

## 官方资源

- **xTB 官网**: https://xtb-docs.readthedocs.io
- **GitHub 仓库**: https://github.com/grimme-lab/xtb
- **安装指南**: https://xtb-docs.readthedocs.io/en/latest/installation.html
- **使用方法**: https://xtb-docs.readthedocs.io/en/latest/usage.html

## 几何优化命令

### 基本优化

```bash
xtb input.xyz --opt
```

### 指定方法

```bash
xtb input.xyz --opt -- gfn2
xtb input.xyz --opt -- gfn1
xtb input.xyz --opt -- gfnff
```

### 指定电荷和未成对电子

```bash
xtb input.xyz --opt --chrg 1 --uhf 1
```

### 溶剂模型

```bash
xtb input.xyz --opt --alpb water
xtb input.xyz --opt --alpb ethanol
xtb input.xyz --opt --alpb acetone
```

### 最大优化步数

```bash
xtb input.xyz --opt --maxcycles 500
```

### 输出前缀

```bash
xtb input.xyz --opt --prefix my_optimization
```

## 输出文件

| 文件 | 说明 |
|------|------|
| `xtb.out` | 主输出文件，包含能量、梯度、收敛信息 |
| `xtb.xyz` | 优化后的几何结构（XYZ 格式） |
| `xtb.trj` | 优化轨迹 |
| `xtb.grad` | 最终梯度 |
| `xtb.input` | 输入坐标副本 |

## 能量单位

- xTB 输出能量单位为 Hartree (Ha)
- 1 Hartree ≈ 627.509 kcal/mol
- 1 Hartree ≈ 2625.5 kJ/mol

## 收敛标准

xTB 默认收敛标准：
- 能量变化 < 1e-6 Hartree
- 梯度范数 < 0.0005 Hartree/Bohr

## GFN 方法选择

| 方法 | 适用场景 | 精度 | 速度 |
|------|----------|------|------|
| GFN2-xTB | 通用有机分子 | 高 | 中等 |
| GFN1-xTB | 某些无机体系 | 中等 | 中等 |
| GFN-FF | 大分子、生物分子 | 较低 | 快 |

## 常见问题

### 优化不收敛

1. 增加最大步数：`--maxcycles 500`
2. 尝试 GFN-FF 预优化，再用 GFN2 精修
3. 检查初始结构是否合理

### 内存不足

对于大体系，GFN-FF 是更好的选择：

```bash
xtb large_molecule.xyz --opt -- gfnff
```

## CREST 构象搜索

如需进行构象搜索，使用 CREST：

```bash
crest input.xyz --gfn2
```

输出：
- `crest_best.xyz` - 最低能构象
- `crest_ensemble.xyz` - 构象系综
- `crest.log` - 日志文件

参考资料：https://crest-docs.readthedocs.io
