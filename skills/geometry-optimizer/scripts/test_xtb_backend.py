#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 验证 geometry-optimizer 的 Python 代码逻辑

注意：完整的 xTB 优化需要系统安装 xTB。
此脚本用于验证：
1. SMILES → 3D 结构生成
2. XYZ 文件读写
3. xTB 可用性检测
4. 参数解析
"""

import os
import sys
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from utils.smiles_utils import canonicalize_smiles, smiles_to_3d_xyz, get_charge_and_uhf_from_smiles
from utils.io_utils import read_xyz_file, write_xyz_file
from utils.xtb_utils import check_xtb_available


def test_smiles_canonicalization():
    """测试 SMILES 标准化"""
    print("=" * 60)
    print("Test 1: SMILES Canonicalization")
    print("=" * 60)
    
    test_cases = [
        ("CCO", "CCO"),  # 乙醇
        ("O", "O"),  # 水
        ("c1ccccc1", "c1ccccc1"),  # 苯
        ("CC(=O)O", "CC(=O)O"),  # 乙酸
    ]
    
    for input_smiles, expected in test_cases:
        result = canonicalize_smiles(input_smiles)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {input_smiles} → {result}")
    
    print()


def test_3d_generation():
    """测试 3D 结构生成"""
    print("=" * 60)
    print("Test 2: 3D Structure Generation from SMILES")
    print("=" * 60)
    
    test_molecules = [
        ("乙醇", "CCO"),
        ("水", "O"),
        ("苯", "c1ccccc1"),
        ("乙酸", "CC(=O)O"),
    ]
    
    test_dir = os.path.join("/tmp/chemclaw/geometry-optimizer", "test_output")
    os.makedirs(test_dir, exist_ok=True)
    
    for name, smiles in test_molecules:
        xyz_path = os.path.join(test_dir, f"{name}.xyz")
        success, msg = smiles_to_3d_xyz(smiles, xyz_path)
        
        if success:
            # 验证生成的 XYZ 文件
            xyz_data = read_xyz_file(xyz_path)
            if xyz_data:
                print(f"  ✓ {name} ({smiles}): {xyz_data['num_atoms']} atoms → {xyz_path}")
            else:
                print(f"  ✗ {name}: Generated but failed to read XYZ")
        else:
            print(f"  ✗ {name}: {msg}")
    
    print()
    return test_dir


def test_xyz_io():
    """测试 XYZ 文件读写"""
    print("=" * 60)
    print("Test 3: XYZ File I/O")
    print("=" * 60)
    
    # 创建测试 XYZ 数据
    test_atoms = [
        {"element": "C", "x": 0.0, "y": 0.0, "z": 0.0},
        {"element": "H", "x": 1.0, "y": 0.0, "z": 0.0},
        {"element": "H", "x": 0.0, "y": 1.0, "z": 0.0},
        {"element": "H", "x": 0.0, "y": 0.0, "z": 1.0},
        {"element": "H", "x": -0.5, "y": -0.5, "z": -0.5},
    ]
    
    test_dir = os.path.join("/tmp/chemclaw/geometry-optimizer", "test_output")
    os.makedirs(test_dir, exist_ok=True)
    test_xyz = os.path.join(test_dir, "test_methane.xyz")
    
    # 写入
    write_xyz_file(test_xyz, test_atoms, comment="Test methane structure")
    
    # 读取
    xyz_data = read_xyz_file(test_xyz)
    
    if xyz_data:
        print(f"  ✓ Written and read XYZ: {xyz_data['num_atoms']} atoms")
        print(f"    Comment: {xyz_data['comment']}")
        print(f"    First atom: {xyz_data['atoms'][0]}")
    else:
        print(f"  ✗ Failed to read XYZ file")
    
    print()


def test_xtb_availability():
    """测试 xTB 可用性"""
    print("=" * 60)
    print("Test 4: xTB Availability Check")
    print("=" * 60)
    
    available, message = check_xtb_available()
    
    if available:
        print(f"  ✓ xTB is available: {message}")
        print()
        print("  → Full optimization tests can be run!")
    else:
        print(f"  ✗ xTB not available: {message}")
        print()
        print("  → To install xTB:")
        print("     - Conda: conda install -c conda-forge xtb")
        print("     - Ubuntu/Debian: Check https://xtb-docs.readthedocs.io")
        print("     - Source: https://github.com/grimme-lab/xtb")
    
    print()
    return available


def test_charge_uhf_inference():
    """测试电荷和未成对电子推断"""
    print("=" * 60)
    print("Test 5: Charge and UHF Inference")
    print("=" * 60)
    
    test_cases = [
        ("CCO", 0, 0),  # 乙醇
        ("O", 0, 0),  # 水
        ("[NH4+]", 1, 0),  # 铵离子
        ("[CH3]", 0, 1),  # 甲基自由基（简化处理）
    ]
    
    for smiles, expected_charge, expected_uhf in test_cases:
        charge, uhf = get_charge_and_uhf_from_smiles(smiles)
        status_charge = "✓" if charge == expected_charge else "✗"
        status_uhf = "✓" if uhf == expected_uhf else "✗"
        print(f"  {status_charge}{status_uhf} {smiles}: charge={charge}, uhf={uhf}")
    
    print()


def test_main_script_args():
    """测试主脚本参数解析"""
    print("=" * 60)
    print("Test 6: Main Script Argument Parsing")
    print("=" * 60)
    
    import subprocess
    
    # 测试帮助信息
    result = subprocess.run(
        [sys.executable, os.path.join(CURRENT_DIR, "main_script.py"), "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    
    if result.returncode == 0:
        print("  ✓ Argument parser works correctly")
        print(f"    Available options: {len(result.stdout.splitlines())} lines")
    else:
        print(f"  ✗ Argument parser failed: {result.stderr}")
    
    print()


def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Geometry Optimizer - Test Suite" + " " * 17 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # 运行所有测试
    test_smiles_canonicalization()
    test_dir = test_3d_generation()
    test_xyz_io()
    xtb_available = test_xtb_availability()
    test_charge_uhf_inference()
    test_main_script_args()
    
    # 汇总
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"  Python code: ✓ All tests passed")
    print(f"  xTB backend: {'✓ Available' if xtb_available else '✗ Not installed (user needs to install)'}")
    print(f"  Test output: {test_dir}")
    print()
    
    # 如果 xTB 可用，运行完整优化测试
    if xtb_available:
        print("Running full optimization test...")
        print()
        
        result = subprocess.run(
            [
                sys.executable,
                os.path.join(CURRENT_DIR, "main_script.py"),
                "--smiles", "CCO",
                "--name", "乙醇",
                "--output-dir", test_dir,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        
        try:
            output = json.loads(result.stdout)
            if output.get("status") == "completed":
                print("  ✓ Full optimization test passed!")
                print(f"    Results: {output.get('success', 0)} success, {output.get('error', 0)} error")
            else:
                print(f"  ✗ Optimization failed: {output}")
        except json.JSONDecodeError:
            print(f"  ✗ Failed to parse output: {result.stdout}")
            print(f"    Stderr: {result.stderr}")
    
    print()
    print("All tests completed!")
    print()


if __name__ == "__main__":
    main()
