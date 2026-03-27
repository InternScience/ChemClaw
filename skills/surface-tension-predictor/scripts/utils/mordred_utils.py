#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import pickle
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from mordred import Calculator, descriptors
from rdkit import Chem
from sklearn.impute import SimpleImputer


_MORDRED_CALCULATOR = Calculator(descriptors, ignore_3D=True)


def _safe_float(value):
    """
    将 Mordred 描述符尽量转成 float。
    无法转换、缺失、NaN、inf 时统一返回 np.nan，
    以便后续按上游脚本逻辑用 SimpleImputer(mean) 填补。
    """
    try:
        if value is None:
            return np.nan

        value = float(value)

        if math.isnan(value) or math.isinf(value):
            return np.nan

        return value
    except Exception:
        return np.nan


def compute_mordred_feature_dict(smiles: str) -> Dict[str, float]:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"无效 SMILES: {smiles}")

    result = _MORDRED_CALCULATOR(mol)
    feature_dict: Dict[str, float] = {}

    for key, value in result.items():
        feature_name = str(key)
        feature_dict[feature_name] = _safe_float(value)

    return feature_dict


def _load_object_with_joblib_or_pickle(path: str) -> Any:
    try:
        return joblib.load(path)
    except Exception:
        pass

    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception:
        pass

    raise ValueError(f"无法读取参数文件: {path}")


def load_upstream_parameter_bundle(params_path: str) -> Tuple[List[str], List[float], List[float], Any]:
    """
    按上游 properties_prediction.py 的真实语义读取参数文件：
    上游写法：
        mordred_descriptors, scale_min, scale_max = joblib.load(name+".joblib_parameters")
    所以这里优先按 tuple/list 长度>=3 解析。
    """
    obj = _load_object_with_joblib_or_pickle(params_path)

    if isinstance(obj, (tuple, list)) and len(obj) >= 3:
        mordred_descriptors = list(obj[0])
        scale_min = list(obj[1])
        scale_max = list(obj[2])
        return (
            [str(x) for x in mordred_descriptors],
            scale_min,
            scale_max,
            obj,
        )

    raise ValueError(
        f"参数文件格式与上游脚本预期不一致，无法解析为 "
        f"(mordred_descriptors, scale_min, scale_max): {type(obj).__name__}"
    )


def build_upstream_style_feature_matrix(
    smiles: str,
    feature_names: List[str],
    scale_min: List[float],
    scale_max: List[float],
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    忠实复现上游 properties_prediction.py 的核心预处理逻辑：

    1. 计算 Mordred 描述符
    2. 取出参数文件指定的特征列
    3. 在底部追加 scale_max / scale_min 两行
    4. 转置后做逐变量缩放:
         var = (var - var[-1]) / (var[-2] - var[-1])
       这里对应的是:
         (x - scale_min) / (scale_max - scale_min)
    5. 再转回 DataFrame
    6. 用 SimpleImputer(mean) 填补缺失
    7. 丢掉最后两行，只保留真正要预测的样本行
    """
    feature_dict = compute_mordred_feature_dict(smiles)

    if len(feature_names) != len(scale_min) or len(feature_names) != len(scale_max):
        raise ValueError(
            f"参数文件长度不一致："
            f"feature_names={len(feature_names)}, "
            f"scale_min={len(scale_min)}, "
            f"scale_max={len(scale_max)}"
        )

    # 样本行
    sample_row = [feature_dict.get(name, np.nan) for name in feature_names]

    # 对齐上游：先数据，再 scale_max，再 scale_min
    filter_md = pd.DataFrame([sample_row], columns=feature_names)
    filter_md = pd.concat(
        [
            filter_md,
            pd.DataFrame([scale_max], columns=feature_names),
            pd.DataFrame([scale_min], columns=feature_names),
        ],
        ignore_index=True,
    )

    filter_md_array = np.array(filter_md, dtype=float).T

    # 上游逐列缩放
    for i, var in enumerate(filter_md_array):
        denom = var[-2] - var[-1]  # scale_max - scale_min
        if np.isnan(denom) or denom == 0:
            # 避免除零；保持为 NaN，后续交给 imputer
            scaled = np.full_like(var, np.nan, dtype=float)
        else:
            scaled = (var - var[-1]) / denom
        filter_md_array[i] = scaled

    x_array = filter_md_array.T
    df = pd.DataFrame(x_array)

    imp = SimpleImputer(missing_values=np.nan, strategy="mean")
    x_array2 = imp.fit_transform(df)

    # 去掉最后两行（scale_max / scale_min）
    x_predict = x_array2[:-2, :]

    missing_feature_count = int(np.sum(pd.isna(sample_row)))
    missing_features = [
        name for name, value in zip(feature_names, sample_row) if pd.isna(value)
    ]

    debug_info = {
        "feature_count": len(feature_names),
        "missing_feature_count": missing_feature_count,
        "missing_features": missing_features[:50],
        "preprocess_style": "upstream_properties_prediction_py",
        "scaling_rows_added": 2,
    }

    return x_predict, debug_info