#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import Any, Dict, List, Optional

import joblib
import numpy as np

from utils.mordred_utils import (
    build_upstream_style_feature_matrix,
    load_upstream_parameter_bundle,
)
from utils.smiles_utils import canonicalize_smiles


DEFAULT_MODEL_PATH = "references/models/linear_SurfaceTension.joblib"
DEFAULT_PARAMS_PATH = "references/models/linear_SurfaceTension.joblib_parameters"


def resolve_path(path_value: Optional[str], default_path: str) -> str:
    if path_value:
        return path_value
    return default_path


def extract_predictor_object(obj: Any) -> Any:
    """
    从 joblib.load 得到的对象中递归提取真正可调用 .predict() 的模型对象。
    支持：
    - sklearn 模型本体
    - tuple / list 包装
    - dict 包装
    """
    if hasattr(obj, "predict") and callable(getattr(obj, "predict")):
        return obj

    if isinstance(obj, (tuple, list)):
        for item in obj:
            found = extract_predictor_object(item)
            if found is not None:
                return found

    if isinstance(obj, dict):
        candidate_keys = ["model", "estimator", "predictor", "regressor", "pls", "pipeline"]
        for key in candidate_keys:
            if key in obj:
                found = extract_predictor_object(obj[key])
                if found is not None:
                    return found

        for value in obj.values():
            found = extract_predictor_object(value)
            if found is not None:
                return found

    return None


def summarize_loaded_object(obj: Any) -> Dict[str, Any]:
    summary = {
        "loaded_object_type": type(obj).__name__,
    }

    if isinstance(obj, (tuple, list)):
        summary["loaded_container_length"] = len(obj)
        summary["loaded_item_types"] = [type(x).__name__ for x in obj[:10]]
    elif isinstance(obj, dict):
        summary["loaded_keys_preview"] = list(obj.keys())[:20]

    return summary


def load_required_model_and_params(
    model_path: Optional[str],
    params_path: Optional[str],
):
    resolved_model_path = resolve_path(model_path, DEFAULT_MODEL_PATH)
    resolved_params_path = resolve_path(params_path, DEFAULT_PARAMS_PATH)

    if not os.path.exists(resolved_model_path):
        raise FileNotFoundError(f"public_joblib 模型文件不存在: {resolved_model_path}")
    if not os.path.exists(resolved_params_path):
        raise FileNotFoundError(f"public_joblib 参数文件不存在: {resolved_params_path}")

    raw_loaded_obj = joblib.load(resolved_model_path)
    predictor = extract_predictor_object(raw_loaded_obj)
    object_summary = summarize_loaded_object(raw_loaded_obj)

    if predictor is None:
        raise ValueError(
            f"模型文件已加载，但未能从中提取出可调用 predict() 的模型对象。"
            f" 加载对象摘要: {object_summary}"
        )

    feature_names, scale_min, scale_max, raw_params_obj = load_upstream_parameter_bundle(
        resolved_params_path
    )

    params_summary = {
        "params_object_type": type(raw_params_obj).__name__,
        "feature_count": len(feature_names),
        "scale_min_count": len(scale_min),
        "scale_max_count": len(scale_max),
    }

    return (
        predictor,
        feature_names,
        scale_min,
        scale_max,
        resolved_model_path,
        resolved_params_path,
        object_summary,
        params_summary,
    )


def predict_one_public_joblib(
    record: Dict[str, Any],
    model,
    feature_names: List[str],
    scale_min: List[float],
    scale_max: List[float],
    resolved_model_path: str,
    resolved_params_path: str,
    object_summary: Dict[str, Any],
    params_summary: Dict[str, Any],
) -> Dict[str, Any]:
    name = record.get("name") or ""
    smiles = record.get("smiles") or ""

    try:
        canonical_smiles = canonicalize_smiles(smiles)

        x_predict, preprocess_info = build_upstream_style_feature_matrix(
            smiles=canonical_smiles,
            feature_names=feature_names,
            scale_min=scale_min,
            scale_max=scale_max,
        )

        y_pred = model.predict(x_predict)

        # 上游脚本对 PLSRegression 的结果做 flatten
        pred_array = np.asarray(y_pred).reshape(-1)
        pred_value = float(pred_array[0])

        return {
            "name": name,
            "smiles": smiles,
            "canonical_smiles": canonical_smiles,
            "status": "success",
            "surface_tension_prediction": round(float(pred_value), 4),
            "unit": "mN/m",
            "model_source": "public_joblib_model_upstream_aligned",
            "model_path": resolved_model_path,
            "params_path": resolved_params_path,
            "feature_count": preprocess_info["feature_count"],
            "missing_feature_count": preprocess_info["missing_feature_count"],
            "missing_features": preprocess_info["missing_features"],
            "loaded_object_summary": object_summary,
            "params_summary": params_summary,
            "predictor_type": type(model).__name__,
            "preprocess_style": preprocess_info["preprocess_style"],
        }

    except Exception as exc:
        return {
            "name": name,
            "smiles": smiles,
            "status": "error",
            "message": str(exc),
            "loaded_object_summary": object_summary,
            "params_summary": params_summary,
            "predictor_type": type(model).__name__ if model is not None else None,
        }


def predict_surface_tension_batch_public_joblib(
    records: List[Dict[str, Any]],
    model_path: Optional[str] = None,
    params_path: Optional[str] = None,
) -> Dict[str, Any]:
    (
        model,
        feature_names,
        scale_min,
        scale_max,
        resolved_model_path,
        resolved_params_path,
        object_summary,
        params_summary,
    ) = load_required_model_and_params(
        model_path=model_path,
        params_path=params_path
    )

    results = [
        predict_one_public_joblib(
            record=record,
            model=model,
            feature_names=feature_names,
            scale_min=scale_min,
            scale_max=scale_max,
            resolved_model_path=resolved_model_path,
            resolved_params_path=resolved_params_path,
            object_summary=object_summary,
            params_summary=params_summary,
        )
        for record in records
    ]

    success_count = sum(1 for x in results if x.get("status") == "success")
    error_count = sum(1 for x in results if x.get("status") == "error")

    return {
        "status": "completed",
        "backend_used": "surface_tension_public_joblib",
        "total": len(records),
        "success": success_count,
        "error": error_count,
        "results": results,
    }