#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from typing import Any, Dict, List


def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def load_input_records(path: str) -> List[Dict[str, Any]]:
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
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def summarize_results(results: List[Dict[str, Any]], backend_used: str) -> Dict[str, Any]:
    success_count = sum(1 for item in results if item.get("status") == "success")
    error_count = sum(1 for item in results if item.get("status") != "success")

    return {
        "status": "completed",
        "backend_used": backend_used,
        "total": len(results),
        "success": success_count,
        "error": error_count,
        "results": results,
    }