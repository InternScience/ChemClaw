#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
from typing import Any, Dict, List, Optional, Tuple


def check_xtb_available() -> Tuple[bool, str]:
    """
    检查 xTB 是否可用。
    
    返回:
        (available, message): available=True 表示 xTB 可用；否则为 False 并附带错误信息。
    """
    try:
        result = subprocess.run(
            ["xtb", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            version_info = result.stdout.strip() or result.stderr.strip()
            return True, f"xTB found: {version_info}"
        else:
            return False, f"xTB command failed: {result.stderr.strip()}"
    except FileNotFoundError:
        return False, "xtb command not found. Please install xTB (https://xtb-docs.readthedocs.io)."
    except subprocess.TimeoutExpired:
        return False, "xTB version check timed out."
    except Exception as e:
        return False, f"Error checking xTB: {str(e)}"


def parse_xtb_output(output_path: str) -> Dict[str, Any]:
    """
    解析 xTB 输出文件，提取能量、收敛状态等信息。
    
    返回:
        包含能量、收敛状态等信息的字典。
    """
    result = {
        "energy_hartree": None,
        "energy_kcal_mol": None,
        "converged": False,
        "num_atoms": 0,
        "final_gradient": None,
        "optimization_cycles": 0,
        "warnings": [],
    }

    # xTB 6.x 默认输出文件是 xtbopt.log（几何优化）或 xtb.out（单点）
    # 如果指定路径不存在，尝试可能的文件名
    if not os.path.exists(output_path):
        # 尝试当前目录下的可能文件
        for fallback in ["xtb.out", "xtbopt.log", os.path.join(os.path.dirname(output_path), "xtb.out"), os.path.join(os.path.dirname(output_path), "xtbopt.log")]:
            if os.path.exists(fallback):
                output_path = fallback
                break
        else:
            result["warnings"].append(f"Output file not found: {output_path}")
            return result

    with open(output_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    # 检查是否是 xtbopt.log 格式（每行包含 energy 和 gnorm）
    # 格式示例：24  energy: -42.153889261330 gnorm: 0.000678304269 xtb: 6.6.1
    for line in lines:
        if "energy:" in line and "gnorm:" in line:
            try:
                parts = line.split()
                for j, p in enumerate(parts):
                    if p == "energy:" and j + 1 < len(parts):
                        result["energy_hartree"] = float(parts[j + 1])
                        result["energy_kcal_mol"] = result["energy_hartree"] * 627.509
                    elif p == "gnorm:" and j + 1 < len(parts):
                        result["final_gradient"] = float(parts[j + 1])
                        # xTB 收敛标准：gnorm < 0.001 Eh/a0
                        if result["final_gradient"] < 0.001:
                            result["converged"] = True
            except (ValueError, IndexError):
                pass

        # 提取最终能量（xtb.out 格式）
        if "FINAL SINGLE POINT ENERGY" in line:
            try:
                parts = line.split()
                result["energy_hartree"] = float(parts[-1])
                result["energy_kcal_mol"] = result["energy_hartree"] * 627.509
            except (ValueError, IndexError):
                pass

        # 检查收敛（xtb.out 格式）
        if "GEOMETRY OPTIMIZATION CONVERGED" in line:
            result["converged"] = True

        # 提取梯度（xtb.out 格式）
        if "LAST GRADIENT NORM" in line or "| gradient norm |" in line.lower():
            try:
                parts = line.replace("|", " ").split()
                for j, p in enumerate(parts):
                    if p.replace(".", "").replace("-", "").isdigit():
                        result["final_gradient"] = float(p)
                        break
            except (ValueError, IndexError):
                pass

        # 提取原子数
        if "number of atoms" in line.lower():
            try:
                parts = line.split(":")
                if len(parts) >= 2:
                    result["num_atoms"] = int(parts[1].strip())
            except (ValueError, IndexError):
                pass

        # 统计优化步数（xtbopt.log 中的 CYCLE）
        if "CYCLE" in line and "..." in line:
            result["optimization_cycles"] += 1

        # 检测警告
        if "WARNING" in line or "!!! " in line:
            result["warnings"].append(line.strip())

    # 如果能量有值但原子数为 0，尝试从文件开头读取
    if result["energy_hartree"] and result["num_atoms"] == 0:
        # 读取第一个 XYZ 块获取原子数
        for i, line in enumerate(lines):
            if line.strip().isdigit():
                try:
                    result["num_atoms"] = int(line.strip())
                    break
                except ValueError:
                    pass

    return result


def extract_optimized_geometry(output_path: str) -> List[Dict[str, float]]:
    """
    从 xTB 输出文件中提取优化后的几何结构。
    
    返回:
        原子坐标列表，每项为 {'element': str, 'x': float, 'y': float, 'z': float}
    """
    atoms = []

    if not os.path.exists(output_path):
        return atoms

    with open(output_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    # 查找优化后的坐标部分
    in_coord_section = False
    for line in lines:
        if "$coord" in line.lower():
            in_coord_section = True
            continue
        if in_coord_section:
            if "$end" in line.lower():
                break
            parts = line.strip().split()
            if len(parts) >= 4:
                try:
                    atoms.append({
                        "element": parts[3].capitalize(),
                        "x": float(parts[0]),
                        "y": float(parts[1]),
                        "z": float(parts[2]),
                    })
                except (ValueError, IndexError):
                    pass

    return atoms


def build_xtb_command(
    input_xyz: str,
    output_prefix: str,
    method: str = "gfn2",
    charge: int = 0,
    uhf: int = 0,
    solvent: Optional[str] = None,
    max_cycles: int = 200,
) -> List[str]:
    """
    构建 xTB 命令行。
    
    参数:
        input_xyz: 输入 XYZ 文件路径
        output_prefix: 输出文件前缀（用于 --prefix 指定输出文件前缀）
        method: xTB 方法 (gfn2, gfn1, gfnff)
        charge: 电荷
        uhf: 未成对电子数
        solvent: 溶剂模型 (可选)
        max_cycles: 最大优化步数（通过 xcontrol 文件设置）
    
    返回:
        命令行参数列表
    
    注意:
        xTB 6.x 版本的参数格式:
        - --opt 用于几何优化
        - --chrg 指定电荷
        - --uhf 指定未成对电子数
        - --gfn1/--gfn2 指定方法（不是 -- gfn2）
        - --alpb 溶剂模型
        - 最大循环数通过 xcontrol 文件设置
    """
    cmd = [
        "xtb",
        input_xyz,
        "--opt",
        "--chrg", str(charge),
        "--uhf", str(uhf),
    ]

    # xTB 6.x 方法参数格式
    if method == "gfn1":
        cmd.append("--gfn1")
    elif method == "gfnff":
        cmd.append("--gfnff")
    # gfn2 是默认值，不需要额外参数

    if solvent:
        cmd.extend(["--alpb", solvent])

    return cmd
