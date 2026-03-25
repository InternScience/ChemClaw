#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import tempfile
import time
from typing import Any, Dict, Optional

from utils.io_utils import (
    ensure_parent_dir,
    read_xyz_file,
    write_xyz_file,
)
from utils.smiles_utils import (
    canonicalize_smiles,
    smiles_to_3d_xyz,
    get_charge_and_uhf_from_smiles,
)
from utils.xtb_utils import (
    check_xtb_available,
    parse_xtb_output,
    extract_optimized_geometry,
    build_xtb_command,
)


def optimize_with_xtb(
    smiles: Optional[str] = None,
    input_xyz: Optional[str] = None,
    name: Optional[str] = None,
    method: str = "gfn2",
    charge: Optional[int] = None,
    uhf: Optional[int] = None,
    solvent: Optional[str] = None,
    max_cycles: int = 200,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    使用 xTB 进行几何结构优化。
    
    参数:
        smiles: SMILES 字符串（可选，与 input_xyz 二选一）
        input_xyz: 输入 XYZ 文件路径（可选，与 smiles 二选一）
        name: 分子名称（可选）
        method: xTB 方法 (gfn2, gfn1, gfnff)
        charge: 电荷（可选，默认从 SMILES 推断或设为 0）
        uhf: 未成对电子数（可选，默认从 SMILES 推断或设为 0）
        solvent: 溶剂模型（可选）
        max_cycles: 最大优化步数
        output_dir: 输出目录（可选，默认使用临时目录）
    
    返回:
        包含优化结果的字典
    """
    start_time = time.time()
    
    # 确定输入类型
    input_type = None
    working_smiles = None
    temp_files = []

    try:
        # 检查 xTB 可用性
        xtb_available, xtb_message = check_xtb_available()
        if not xtb_available:
            return {
                "name": name if name else (smiles if smiles else input_xyz),
                "status": "error",
                "error_message": f"xTB not available: {xtb_message}",
                "backend_used": "xtb",
            }

        # 处理输入
        if smiles:
            input_type = "smiles"
            working_smiles = canonicalize_smiles(smiles)
            if working_smiles is None:
                return {
                    "name": name if name else smiles,
                    "input_type": "smiles",
                    "smiles": smiles,
                    "status": "error",
                    "error_message": "Invalid SMILES string.",
                    "backend_used": "xtb",
                }

            # 从 SMILES 生成 3D 结构
            if output_dir:
                ensure_parent_dir(os.path.join(output_dir, "temp.xyz"))
                initial_xyz = os.path.join(output_dir, "initial.xyz")
            else:
                temp_fd, initial_xyz = tempfile.mkstemp(suffix=".xyz")
                os.close(temp_fd)
                temp_files.append(initial_xyz)

            success, msg = smiles_to_3d_xyz(working_smiles, initial_xyz)
            if not success:
                return {
                    "name": name if name else working_smiles,
                    "input_type": "smiles",
                    "smiles": smiles,
                    "canonical_smiles": working_smiles,
                    "status": "error",
                    "error_message": f"Failed to generate 3D structure: {msg}",
                    "backend_used": "xtb",
                }

            # 从 SMILES 推断电荷和 uhf
            if charge is None or uhf is None:
                inferred_charge, inferred_uhf = get_charge_and_uhf_from_smiles(working_smiles)
                if charge is None:
                    charge = inferred_charge
                if uhf is None:
                    uhf = inferred_uhf

        elif input_xyz:
            input_type = "xyz"
            if not os.path.exists(input_xyz):
                return {
                    "name": name if name else input_xyz,
                    "input_type": "xyz",
                    "input_xyz": input_xyz,
                    "status": "error",
                    "error_message": f"Input XYZ file not found: {input_xyz}",
                    "backend_used": "xtb",
                }
            initial_xyz = input_xyz

            # 读取 XYZ 获取原子数
            xyz_data = read_xyz_file(input_xyz)
            if xyz_data is None:
                return {
                    "name": name if name else input_xyz,
                    "input_type": "xyz",
                    "input_xyz": input_xyz,
                    "status": "error",
                    "error_message": "Failed to parse input XYZ file.",
                    "backend_used": "xtb",
                }

        else:
            return {
                "name": name if name else None,
                "status": "error",
                "error_message": "Either 'smiles' or 'input_xyz' must be provided.",
                "backend_used": "xtb",
            }

        # 设置默认电荷和 uhf
        if charge is None:
            charge = 0
        if uhf is None:
            uhf = 0

        # 设置输出路径
        if output_dir:
            ensure_parent_dir(os.path.join(output_dir, "output.txt"))
            output_prefix = os.path.join(output_dir, "xtb_opt")
        else:
            temp_fd, output_prefix = tempfile.mkstemp(suffix="_xtb")
            os.close(temp_fd)
            output_prefix = output_prefix.rsplit(".", 1)[0]
            temp_files.append(output_prefix + ".xyz")
            temp_files.append(output_prefix + ".out")

        # 确定工作目录 - 必须是绝对路径
        if output_dir:
            work_dir = os.path.abspath(output_dir)
        else:
            work_dir = os.path.dirname(os.path.abspath(initial_xyz)) if input_xyz else tempfile.gettempdir()

        # 将输入文件路径转换为绝对路径，确保 subprocess 在 work_dir 中能正确访问
        initial_xyz_abs = os.path.abspath(initial_xyz)

        # 构建并执行 xTB 命令
        cmd = build_xtb_command(
            input_xyz=initial_xyz_abs,
            output_prefix=output_prefix,
            method=method,
            charge=charge,
            uhf=uhf,
            solvent=solvent,
            max_cycles=max_cycles,
        )

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 分钟超时
            cwd=work_dir,
        )

        # 解析输出 - xTB 6.x 在当前工作目录生成 xtbopt.log（几何优化）或 xtb.out
        # 先尝试 xtbopt.log，再尝试 xtb.out
        output_file = os.path.join(work_dir, "xtbopt.log")
        if not os.path.exists(output_file):
            output_file = os.path.join(work_dir, "xtb.out")
        xtb_result = parse_xtb_output(output_file)

        # 提取优化后的几何结构
        # xTB 6.x 输出优化后的结构到 xtbopt.xyz（在当前工作目录）
        xtbopt_xyz = os.path.join(work_dir, "xtbopt.xyz")
        
        # 优先从 xtbopt.xyz 读取，如果不存在再从输出日志提取
        optimized_atoms = []
        if os.path.exists(xtbopt_xyz):
            xtbopt_data = read_xyz_file(xtbopt_xyz)
            if xtbopt_data and xtbopt_data.get("atoms"):
                optimized_atoms = xtbopt_data["atoms"]
        
        if not optimized_atoms:
            optimized_atoms = extract_optimized_geometry(output_file)

        # 保存优化后的 XYZ 文件
        if output_dir:
            optimized_xyz_path = os.path.join(output_dir, "optimized.xyz")
        else:
            temp_fd, optimized_xyz_path = tempfile.mkstemp(suffix="_optimized.xyz")
            os.close(temp_fd)
            temp_files.append(optimized_xyz_path)

        if optimized_atoms:
            write_xyz_file(
                optimized_xyz_path,
                optimized_atoms,
                comment=f"Optimized with xTB {method}, energy={xtb_result.get('energy_hartree', 'N/A')} Ha"
            )
        elif os.path.exists(xtbopt_xyz):
            # 使用 xTB 直接输出的 xtbopt.xyz
            fallback_data = read_xyz_file(xtbopt_xyz)
            if fallback_data and fallback_data.get("atoms"):
                write_xyz_file(
                    optimized_xyz_path,
                    fallback_data["atoms"],
                    comment=f"Optimized with xTB {method}"
                )
        else:
            # 尝试使用带前缀的 .xyz 文件
            fallback_xyz = output_prefix + ".xyz"
            if os.path.exists(fallback_xyz):
                fallback_data = read_xyz_file(fallback_xyz)
                if fallback_data and fallback_data.get("atoms"):
                    write_xyz_file(
                        optimized_xyz_path,
                        fallback_data["atoms"],
                        comment=f"Optimized with xTB {method}"
                    )

        runtime_seconds = time.time() - start_time

        # 构建结果
        converged = xtb_result.get("converged", False)
        status = "success" if converged else "partial_success"

        result_dict = {
            "name": name if name else (working_smiles if working_smiles else input_xyz),
            "input_type": input_type,
            "smiles": smiles,
            "canonical_smiles": working_smiles,
            "status": status,
            "backend_used": "xtb",
            "method": method,
            "charge": charge,
            "uhf": uhf,
            "solvent": solvent,
            "converged": converged,
            "energy_hartree": xtb_result.get("energy_hartree"),
            "energy_kcal_mol": xtb_result.get("energy_kcal_mol"),
            "final_gradient": xtb_result.get("final_gradient"),
            "optimization_cycles": xtb_result.get("optimization_cycles"),
            "num_atoms": xtb_result.get("num_atoms"),
            "optimized_xyz_path": optimized_xyz_path,
            "log_path": output_file if os.path.exists(output_file) else (xtbopt_xyz if os.path.exists(xtbopt_xyz) else None),
            "runtime_seconds": round(runtime_seconds, 2),
            "warnings": xtb_result.get("warnings", []),
            "message": "Geometry optimization completed." + (" Converged." if converged else " Did not fully converge, but final structure available."),
        }

        if result.returncode != 0:
            result_dict["warnings"].append(f"xtb exited with code {result.returncode}: {result.stderr}")

        return result_dict

    except subprocess.TimeoutExpired:
        return {
            "name": name if name else (smiles if smiles else input_xyz),
            "input_type": input_type,
            "smiles": smiles,
            "canonical_smiles": working_smiles,
            "status": "error",
            "error_message": "xTB calculation timed out (5 minutes).",
            "backend_used": "xtb",
        }
    except Exception as e:
        return {
            "name": name if name else (smiles if smiles else input_xyz),
            "input_type": input_type,
            "smiles": smiles,
            "canonical_smiles": working_smiles,
            "status": "error",
            "error_message": f"Error during optimization: {str(e)}",
            "backend_used": "xtb",
        }
    finally:
        # 清理临时文件（如果使用了临时目录）
        if not output_dir:
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception:
                    pass
