#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from typing import Any, Dict, List, Optional


def ensure_parent_dir(path: str) -> None:
    """确保文件路径的父目录存在，不存在则创建。"""
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def load_input_records(path: str) -> List[Dict[str, Any]]:
    """从 JSON 文件加载输入记录列表。"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list of records.")

    normalized: List[Dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("Each input record must be a JSON object.")
        normalized.append(item)

    return normalized


def save_json(path: str, data: Any) -> None:
    """将数据保存为 JSON 文件。"""
    ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def summarize_results(results: List[Dict[str, Any]], backend_used: str) -> Dict[str, Any]:
    """汇总多个分子的计算结果。"""
    success_count = sum(1 for item in results if item.get("status") == "success")
    partial_count = sum(1 for item in results if item.get("status") == "partial_success")
    error_count = sum(1 for item in results if item.get("status") == "error")

    return {
        "status": "completed",
        "backend_used": backend_used,
        "total": len(results),
        "success": success_count,
        "partial_success": partial_count,
        "error": error_count,
        "results": results,
    }


def read_xyz_file(xyz_path: str) -> Optional[Dict[str, Any]]:
    """读取 XYZ 文件，返回原子数和坐标列表。"""
    if not os.path.exists(xyz_path):
        return None

    with open(xyz_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if len(lines) < 2:
        return None

    try:
        num_atoms = int(lines[0].strip())
    except ValueError:
        return None

    comment = lines[1].strip() if len(lines) > 1 else ""
    atoms = []

    for i in range(2, min(2 + num_atoms, len(lines))):
        parts = lines[i].strip().split()
        if len(parts) >= 4:
            atoms.append({
                "element": parts[0],
                "x": float(parts[1]),
                "y": float(parts[2]),
                "z": float(parts[3]),
            })

    return {
        "num_atoms": num_atoms,
        "comment": comment,
        "atoms": atoms,
    }


def write_xyz_file(xyz_path: str, atoms: List[Dict[str, Any]], comment: str = "") -> None:
    """将原子坐标写入 XYZ 文件。"""
    ensure_parent_dir(xyz_path)
    with open(xyz_path, "w", encoding="utf-8") as f:
        f.write(f"{len(atoms)}\n")
        f.write(f"{comment}\n")
        for atom in atoms:
            f.write(f"{atom['element']} {atom['x']:.6f} {atom['y']:.6f} {atom['z']:.6f}\n")
