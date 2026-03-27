#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import Any, Dict, List, Optional

import joblib
import numpy as np

from utils.descriptors import (
    DESCRIPTOR_ORDER,
    compute_descriptor_dict,
    descriptor_dict_to_vector,
)
from utils.smiles_utils import canonicalize_smiles


def baseline_surface_tension_estimate(desc: Dict[str, float]) -> float:
    """
    本地启发式基线估算器。
    注意：
    - 这是工程上可运行的 baseline
    - 不是基于真实 PE-12 数据训练得到的正式模型
    """
    mol_wt = desc["MolWt"]
    tpsa = desc["TPSA"]
    logp = desc["MolLogP"]
    hbd = desc["NumHDonors"]
    hba = desc["NumHAcceptors"]
    ring_count = desc["RingCount"]
    heavy = desc["HeavyAtomCount"]
    frac_csp3 = desc["FractionCSP3"]

    pred = (
        15.0
        + 0.08 * mol_wt
        + 0.18 * tpsa
        + 1.80 * logp
        + 2.50 * hbd
        + 0.80 * hba
        + 1.20 * ring_count
        + 0.35 * heavy
        - 2.20 * frac_csp3
    )

    pred = max(5.0, min(120.0, pred))
    return round(float(pred), 4)


def load_optional_model(model_path: Optional[str]):
    if not model_path:
        return None
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"模型文件不存在: {model_path}")
    return joblib.load(model_path)


def predict_one(record: Dict[str, Any], model=None) -> Dict[str, Any]:
    name = record.get("name") or ""
    smiles = record.get("smiles") or ""

    try:
        canonical_smiles = canonicalize_smiles(smiles)
        desc = compute_descriptor_dict(canonical_smiles)
        x = descriptor_dict_to_vector(desc).reshape(1, -1)

        if model is not None:
            y_pred = model.predict(x)
            pred_value = float(np.asarray(y_pred).reshape(-1)[0])
            model_source = "joblib_model"
        else:
            pred_value = baseline_surface_tension_estimate(desc)
            model_source = "baseline_heuristic"

        return {
            "name": name,
            "smiles": smiles,
            "canonical_smiles": canonical_smiles,
            "status": "success",
            "surface_tension_prediction": round(float(pred_value), 4),
            "unit": "mN/m",
            "model_source": model_source,
            "descriptors": desc,
            "descriptor_order": DESCRIPTOR_ORDER,
        }

    except Exception as exc:
        return {
            "name": name,
            "smiles": smiles,
            "status": "error",
            "message": str(exc),
        }


def predict_surface_tension_batch(
    records: List[Dict[str, Any]],
    model_path: Optional[str] = None
) -> Dict[str, Any]:
    model = load_optional_model(model_path)

    results = [predict_one(record, model=model) for record in records]
    success_count = sum(1 for x in results if x.get("status") == "success")
    error_count = sum(1 for x in results if x.get("status") == "error")

    return {
        "status": "completed",
        "backend_used": "surface_tension_baseline",
        "total": len(records),
        "success": success_count,
        "error": error_count,
        "results": results,
    }