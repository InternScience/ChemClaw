#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from typing import Any, Dict, List, Optional


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(obj: Any, indent: int = 2) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=indent)


def load_input_records(
    smiles: Optional[str] = None,
    name: Optional[str] = None,
    input_path: Optional[str] = None,
) -> List[Dict[str, str]]:
    if smiles:
        return [{
            "name": name or "",
            "smiles": smiles.strip(),
        }]

    if input_path:
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"输入文件不存在: {input_path}")

        data = load_json(input_path)
        if not isinstance(data, list):
            raise ValueError("输入 JSON 必须是列表格式。")

        records = []
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                raise ValueError(f"第 {i} 条记录不是 JSON 对象。")
            smiles_val = item.get("smiles")
            if not smiles_val:
                raise ValueError(f"第 {i} 条记录缺少 'smiles'。")
            records.append({
                "name": item.get("name", ""),
                "smiles": str(smiles_val).strip(),
            })
        return records

    raise ValueError("请至少提供 --smiles 或 --input 之一。")