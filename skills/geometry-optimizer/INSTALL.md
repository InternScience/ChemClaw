# Geometry Optimizer - 安装指南

## 系统要求

- Python 3.8+
- xTB 6.3+（半经验量子化学程序）

## 安装步骤

### 1. 安装 Python 依赖

```bash
cd /home/administratorlulaiao/.openclaw/workspace/skills/geometry-optimizer
pip install -r requirements.txt
```

或直接安装：

```bash
pip install rdkit
```

### 2. 安装 xTB

xTB 是该 skill 的核心依赖，必须安装。以下是几种安装方式：

#### 方式 A: Conda（推荐）

```bash
conda install -c conda-forge xtb
```

验证安装：

```bash
xtb --version
```

#### 方式 B: Ubuntu/Debian

检查系统仓库：

```bash
apt-cache search xtb
```

如果仓库中没有，需要从源码编译或使用 Conda。

#### 方式 C: 源码编译

```bash
# 安装依赖
sudo apt install cmake gfortran libblas-dev liblapack-dev

# 克隆源码
git clone https://github.com/grimme-lab/xtb.git
cd xtb

# 编译
mkdir build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=$HOME/.local
make -j4
make install

# 添加到 PATH
export PATH=$HOME/.local/bin:$PATH
```

详细编译说明：https://xtb-docs.readthedocs.io/en/latest/installation.html

### 3. 验证安装

运行测试脚本：

```bash
python scripts/test_xtb_backend.py
```

预期输出：

```
✓ xTB is available: xtb version X.X.X
✓ Full optimization tests can be run!
```

### 4. 运行示例

单分子优化：

```bash
python scripts/main_script.py --smiles "CCO" --name "乙醇" --output-dir ./results
```

批量优化：

```bash
python scripts/main_script.py --input input.json --output output.json --output-dir ./results
```

## 常见问题

### xTB 命令未找到

```
xTB not available: xtb command not found
```

**解决方案：** 按照上述步骤安装 xTB。推荐使用 Conda 安装。

### RDKit 导入错误

```
ModuleNotFoundError: No module named 'rdkit'
```

**解决方案：**

```bash
pip install rdkit
# 或
conda install -c conda-forge rdkit
```

### 3D 构象生成失败

某些复杂分子可能无法自动生成 3D 构象。

**解决方案：**
- 提供已有的 XYZ 坐标文件而非 SMILES
- 检查 SMILES 是否正确

### 优化不收敛

**解决方案：**
- 增加 `--max-cycles` 参数（如 500）
- 尝试不同方法：`--method gfn1` 或 `--method gfnff`
- 检查初始结构是否合理

## 可选：安装 CREST（构象搜索）

如需进行构象搜索，可安装 CREST：

```bash
# Conda
conda install -c conda-forge crest

# 或从源码：https://github.com/grimme-lab/crest
```

验证：

```bash
crest --version
```

## 参考资料

- xTB 官方文档：https://xtb-docs.readthedocs.io
- CREST 官方文档：https://crest-docs.readthedocs.io
- GFN-xTB 论文：https://doi.org/10.1021/acs.jctc.9b00143
- RDKit 文档：https://www.rdkit.org/docs/
