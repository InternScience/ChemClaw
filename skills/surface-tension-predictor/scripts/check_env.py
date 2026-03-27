#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import platform
import sys
from typing import Dict, List, Tuple


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MODEL_PATH = os.path.join(ROOT_DIR, "references", "models", "linear_SurfaceTension.joblib")
DEFAULT_PARAMS_PATH = os.path.join(ROOT_DIR, "references", "models", "linear_SurfaceTension.joblib_parameters")


def safe_import_version(module_name: str, attr_name: str = "__version__") -> Tuple[bool, str]:
    try:
        mod = __import__(module_name)
        version = getattr(mod, attr_name, "unknown")
        return True, str(version)
    except Exception as exc:
        return False, str(exc)


def parse_version_numbers(version_str: str) -> Tuple[int, int]:
    """
    只取主版本号和次版本号，便于做简单判断。
    例如:
    1.2.1 -> (1, 2)
    3.11.11 -> (3, 11)
    """
    try:
        parts = version_str.strip().split(".")
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        return major, minor
    except Exception:
        return -1, -1


def file_status(path: str) -> Dict[str, object]:
    return {
        "path": path,
        "exists": os.path.exists(path),
        "size_bytes": os.path.getsize(path) if os.path.exists(path) else None,
    }


def evaluate_baseline_ready(
    py_version: str,
    imported: Dict[str, Dict[str, object]],
) -> Tuple[bool, List[str]]:
    reasons = []

    rdkit_ok = imported["rdkit"]["ok"]
    numpy_ok = imported["numpy"]["ok"]
    joblib_ok = imported["joblib"]["ok"]

    if not rdkit_ok:
        reasons.append("未检测到 rdkit，baseline 后端无法计算 RDKit 描述符。")
    if not numpy_ok:
        reasons.append("未检测到 numpy。")
    if not joblib_ok:
        reasons.append("未检测到 joblib。")

    ready = rdkit_ok and numpy_ok and joblib_ok

    if ready:
        reasons.append("当前环境满足 baseline 后端运行条件。")

    return ready, reasons


def evaluate_public_joblib_ready(
    py_version: str,
    imported: Dict[str, Dict[str, object]],
    model_info: Dict[str, object],
    params_info: Dict[str, object],
) -> Tuple[bool, List[str]]:
    reasons = []

    py_major, py_minor = parse_version_numbers(py_version)
    sklearn_ok = imported["sklearn"]["ok"]
    rdkit_ok = imported["rdkit"]["ok"]
    mordred_ok = imported["mordred"]["ok"]
    pandas_ok = imported["pandas"]["ok"]
    numpy_ok = imported["numpy"]["ok"]
    joblib_ok = imported["joblib"]["ok"]

    sklearn_version = imported["sklearn"]["version"] if sklearn_ok else ""

    if not rdkit_ok:
        reasons.append("未检测到 rdkit，public_joblib 后端无法做分子解析。")
    if not mordred_ok:
        reasons.append("未检测到 mordred，public_joblib 后端无法计算 Mordred 描述符。")
    if not pandas_ok:
        reasons.append("未检测到 pandas。")
    if not numpy_ok:
        reasons.append("未检测到 numpy。")
    if not joblib_ok:
        reasons.append("未检测到 joblib。")
    if not sklearn_ok:
        reasons.append("未检测到 scikit-learn。")
    else:
        sk_major, sk_minor = parse_version_numbers(sklearn_version)
        if (sk_major, sk_minor) != (1, 2):
            reasons.append(
                f"当前 scikit-learn 版本为 {sklearn_version}，公开模型当前推荐使用 1.2.1。"
            )

    if not model_info["exists"]:
        reasons.append(f"模型文件不存在：{model_info['path']}")
    if not params_info["exists"]:
        reasons.append(f"参数文件不存在：{params_info['path']}")

    if (py_major, py_minor) != (3, 11):
        reasons.append(
            f"当前 Python 版本为 {py_version}，公开模型当前推荐使用 Python 3.11 环境。"
        )

    ready = (
        rdkit_ok
        and mordred_ok
        and pandas_ok
        and numpy_ok
        and joblib_ok
        and sklearn_ok
        and imported["sklearn"]["version"] == "1.2.1"
        and model_info["exists"]
        and params_info["exists"]
        and (py_major, py_minor) == (3, 11)
    )

    if ready:
        reasons.append("当前环境满足 public_joblib 后端运行条件。")

    return ready, reasons


def main():
    python_version = platform.python_version()
    executable = sys.executable

    imported = {
        "numpy": {},
        "joblib": {},
        "pandas": {},
        "sklearn": {},
        "rdkit": {},
        "mordred": {},
    }

    ok, ver = safe_import_version("numpy")
    imported["numpy"] = {"ok": ok, "version": ver}

    ok, ver = safe_import_version("joblib")
    imported["joblib"] = {"ok": ok, "version": ver}

    ok, ver = safe_import_version("pandas")
    imported["pandas"] = {"ok": ok, "version": ver}

    ok, ver = safe_import_version("sklearn")
    imported["sklearn"] = {"ok": ok, "version": ver}

    ok, ver = safe_import_version("rdkit")
    imported["rdkit"] = {"ok": ok, "version": ver}

    ok, ver = safe_import_version("mordred")
    imported["mordred"] = {"ok": ok, "version": ver}

    model_info = file_status(DEFAULT_MODEL_PATH)
    params_info = file_status(DEFAULT_PARAMS_PATH)

    baseline_ready, baseline_reasons = evaluate_baseline_ready(
        py_version=python_version,
        imported=imported,
    )
    public_ready, public_reasons = evaluate_public_joblib_ready(
        py_version=python_version,
        imported=imported,
        model_info=model_info,
        params_info=params_info,
    )

    recommended_backend = None
    if public_ready:
        recommended_backend = "public_joblib"
    elif baseline_ready:
        recommended_backend = "baseline"
    else:
        recommended_backend = "none"

    result = {
        "status": "completed",
        "python_version": python_version,
        "python_executable": executable,
        "root_dir": ROOT_DIR,
        "imports": imported,
        "model_file": model_info,
        "params_file": params_info,
        "backend_check": {
            "baseline": {
                "ready": baseline_ready,
                "reasons": baseline_reasons,
            },
            "public_joblib": {
                "ready": public_ready,
                "reasons": public_reasons,
            },
        },
        "recommended_backend": recommended_backend,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()