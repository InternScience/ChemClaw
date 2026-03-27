#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import subprocess
import sys
from typing import Any, Dict, Optional


PROPERTY_UNITS = {
    "Tm": "K",
    "bp": "K",
    "nD": "unitless",
    "nD_liquid": "unitless",
    "pka_a": "unitless",
    "pka_b": "unitless",
    "dc": "unitless",
    "ST": "mN/m",
    "density": "g/cm^3",
    "vis": "cP",
    "vapP": "Pa",
}


def _default_bridge_script_path() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    scripts_dir = os.path.dirname(current_dir)
    return os.path.join(scripts_dir, "bridges", "bamboo_mixer_bridge.py")


def _resolve_bridge_script(bamboo_script: Optional[str] = None) -> str:
    if bamboo_script:
        return bamboo_script

    env_path = os.environ.get("BAMBOO_MIXER_PREDICT_SCRIPT")
    if env_path:
        return env_path

    return _default_bridge_script_path()


def predict_with_bamboo_mixer(
    smiles: str,
    name: Optional[str] = None,
    temperature_celsius: float = 25.0,
    bamboo_script: Optional[str] = None,
) -> Dict[str, Any]:
    bridge_script = _resolve_bridge_script(bamboo_script)

    if not os.path.exists(bridge_script):
        return {
            "name": name if name else smiles,
            "smiles": smiles,
            "canonical_smiles": smiles,
            "status": "error",
            "error_message": f"Bamboo bridge script not found: {bridge_script}",
            "backend_used": "bamboo_mixer",
        }

    cmd = [
        sys.executable,
        bridge_script,
        "--smiles",
        smiles,
        "--temperature",
        str(float(temperature_celsius)),
    ]

    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as exc:
        return {
            "name": name if name else smiles,
            "smiles": smiles,
            "canonical_smiles": smiles,
            "status": "error",
            "error_message": f"Failed to execute Bamboo bridge script: {exc}",
            "backend_used": "bamboo_mixer",
        }

    stdout_text = (completed.stdout or "").strip()
    stderr_text = (completed.stderr or "").strip()

    if completed.returncode != 0:
        detail = stderr_text if stderr_text else stdout_text
        return {
            "name": name if name else smiles,
            "smiles": smiles,
            "canonical_smiles": smiles,
            "status": "error",
            "error_message": (
                "Bamboo bridge script returned non-zero exit status. "
                f"Details: {detail}"
            ),
            "backend_used": "bamboo_mixer",
        }

    if not stdout_text:
        return {
            "name": name if name else smiles,
            "smiles": smiles,
            "canonical_smiles": smiles,
            "status": "error",
            "error_message": "Bamboo bridge script returned empty stdout.",
            "backend_used": "bamboo_mixer",
        }

    try:
        payload = json.loads(stdout_text)
    except json.JSONDecodeError as exc:
        return {
            "name": name if name else smiles,
            "smiles": smiles,
            "canonical_smiles": smiles,
            "status": "error",
            "error_message": (
                "Failed to parse Bamboo bridge JSON output. "
                f"Details: {exc}. Raw stdout: {stdout_text}"
            ),
            "backend_used": "bamboo_mixer",
        }

    if not payload.get("success", True):
        return {
            "name": name if name else smiles,
            "smiles": smiles,
            "canonical_smiles": payload.get("canonical_smiles", smiles),
            "status": "error",
            "error_message": payload.get(
                "error_message",
                "Bamboo bridge reported failure."
            ),
            "backend_used": "bamboo_mixer",
            "raw_backend_output": payload,
        }

    properties = payload.get("properties")
    if not isinstance(properties, dict):
        return {
            "name": name if name else smiles,
            "smiles": smiles,
            "canonical_smiles": payload.get("canonical_smiles", smiles),
            "status": "error",
            "error_message": "Bamboo bridge succeeded but did not return 'properties'.",
            "backend_used": "bamboo_mixer",
            "raw_backend_output": payload,
        }

    normalized_properties = {}
    for key, value in properties.items():
        try:
            normalized_properties[key] = float(value) if value is not None else None
        except Exception:
            normalized_properties[key] = value

    return {
        "name": name if name else smiles,
        "smiles": smiles,
        "canonical_smiles": payload.get("canonical_smiles", smiles),
        "status": "success",
        "temperature_celsius": float(temperature_celsius),
        "backend_used": "bamboo_mixer",
        "model_source": payload.get("model_source", "bamboo_mixer"),
        "properties": normalized_properties,
        "property_units": PROPERTY_UNITS,
        "raw_backend_output": payload,
    }