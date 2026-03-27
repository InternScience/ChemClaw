#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import importlib.util
import json
import os
import shlex
import subprocess
import sys
import tempfile
from typing import Any, Dict, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bamboo-Mixer bridge script")
    parser.add_argument("--smiles", type=str, required=True, help="Input SMILES")
    parser.add_argument(
        "--temperature",
        type=float,
        default=25.0,
        help="Temperature in Celsius"
    )
    return parser.parse_args()


def _error_payload(message: str, **kwargs: Any) -> Dict[str, Any]:
    payload = {
        "success": False,
        "error_message": message,
    }
    payload.update(kwargs)
    return payload


def _resolve_optional_path(path_value: Optional[str]) -> Optional[str]:
    if not path_value:
        return path_value
    return os.path.abspath(os.path.expanduser(path_value))


def _load_python_adapter(adapter_path: str):
    spec = importlib.util.spec_from_file_location("bamboo_user_adapter", adapter_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load adapter module: {adapter_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "predict_properties"):
        raise AttributeError(
            "Adapter module must define function: "
            "predict_properties(smiles, temperature_celsius)"
        )

    return module.predict_properties


def _run_adapter_mode(
    smiles: str,
    temperature_celsius: float,
    adapter_path: str,
) -> Dict[str, Any]:
    adapter_path = _resolve_optional_path(adapter_path)

    if not adapter_path or not os.path.exists(adapter_path):
        return _error_payload(f"Adapter file not found: {adapter_path}")

    try:
        predict_func = _load_python_adapter(adapter_path)
        result = predict_func(
            smiles=smiles,
            temperature_celsius=temperature_celsius,
        )
    except Exception as exc:
        return _error_payload(f"Adapter mode failed: {exc}")

    if not isinstance(result, dict):
        return _error_payload("Adapter function must return a dict.")

    if "success" not in result:
        result["success"] = True

    return result


def _run_command_mode(
    smiles: str,
    temperature_celsius: float,
    command_template: str,
    repo_path: Optional[str],
    python_path: Optional[str],
) -> Dict[str, Any]:
    repo_path = _resolve_optional_path(repo_path) or ""
    python_path = _resolve_optional_path(python_path) or sys.executable

    with tempfile.TemporaryDirectory(prefix="bamboo_bridge_") as tmpdir:
        output_json = os.path.join(tmpdir, "bamboo_output.json")

        try:
            rendered = command_template.format(
                python=python_path,
                repo=repo_path,
                smiles=smiles,
                temperature=temperature_celsius,
                output_json=output_json,
            )
        except KeyError as exc:
            return _error_payload(f"Invalid command template placeholder: {exc}")

        cmd = shlex.split(rendered)

        env = os.environ.copy()
        if repo_path:
            existing_pythonpath = env.get("PYTHONPATH", "")
            if existing_pythonpath:
                env["PYTHONPATH"] = repo_path + os.pathsep + existing_pythonpath
            else:
                env["PYTHONPATH"] = repo_path

        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                cwd=repo_path if repo_path else None,
                env=env,
            )
        except Exception as exc:
            return _error_payload(f"Failed to execute Bamboo command: {exc}")

        stdout_text = (completed.stdout or "").strip()
        stderr_text = (completed.stderr or "").strip()

        if completed.returncode != 0:
            detail = stderr_text if stderr_text else stdout_text
            return _error_payload(
                "Bamboo command returned non-zero exit status.",
                command=rendered,
                stdout=stdout_text,
                stderr=stderr_text,
                details=detail,
            )

        if os.path.exists(output_json):
            try:
                with open(output_json, "r", encoding="utf-8") as f:
                    payload = json.load(f)
            except Exception as exc:
                return _error_payload(
                    f"Failed to read Bamboo output JSON: {exc}",
                    command=rendered,
                    stdout=stdout_text,
                    stderr=stderr_text,
                )

            if isinstance(payload, dict):
                if "success" not in payload:
                    payload["success"] = True
                return payload

            return _error_payload(
                "Bamboo output JSON must be a dict.",
                command=rendered,
                stdout=stdout_text,
                stderr=stderr_text,
            )

        if stdout_text:
            try:
                payload = json.loads(stdout_text)
                if isinstance(payload, dict):
                    if "success" not in payload:
                        payload["success"] = True
                    return payload
            except Exception:
                pass

        return _error_payload(
            "Bamboo command finished but no valid JSON output was found.",
            command=rendered,
            stdout=stdout_text,
            stderr=stderr_text,
        )


def main() -> None:
    args = parse_args()

    adapter_path = os.environ.get("BAMBOO_MIXER_ADAPTER_PY")
    command_template = os.environ.get("BAMBOO_MIXER_COMMAND_TEMPLATE")
    repo_path = os.environ.get("BAMBOO_MIXER_REPO")
    python_path = os.environ.get("BAMBOO_MIXER_PYTHON")

    if adapter_path:
        payload = _run_adapter_mode(
            smiles=args.smiles,
            temperature_celsius=args.temperature,
            adapter_path=adapter_path,
        )
        print(json.dumps(payload, ensure_ascii=False))
        return

    if command_template:
        payload = _run_command_mode(
            smiles=args.smiles,
            temperature_celsius=args.temperature,
            command_template=command_template,
            repo_path=repo_path,
            python_path=python_path,
        )
        print(json.dumps(payload, ensure_ascii=False))
        return

    payload = _error_payload(
        "Neither BAMBOO_MIXER_ADAPTER_PY nor BAMBOO_MIXER_COMMAND_TEMPLATE is configured."
    )
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()