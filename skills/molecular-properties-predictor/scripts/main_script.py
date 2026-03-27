#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from backends.bamboo_backend import predict_with_bamboo_mixer
from utils.io_utils import (
    ensure_parent_dir,
    load_input_records,
    save_json,
    summarize_results,
)
from utils.smiles_utils import canonicalize_smiles


SUPPORTED_BACKENDS = {
    "bamboo_mixer",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Predict multiple molecular physicochemical properties."
    )

    parser.add_argument(
        "--smiles",
        type=str,
        default=None,
        help="Single-molecule SMILES string."
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Optional molecule name for single-molecule mode."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Input JSON file path for batch prediction."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional output JSON file path."
    )
    parser.add_argument(
        "--backend",
        type=str,
        default="bamboo_mixer",
        choices=sorted(SUPPORTED_BACKENDS),
        help="Prediction backend."
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=25.0,
        help="Temperature in Celsius. Default: 25.0"
    )
    parser.add_argument(
        "--bamboo-script",
        type=str,
        default=None,
        help=(
            "Optional path to Bamboo bridge script. "
            "If omitted, backend will use BAMBOO_MIXER_PREDICT_SCRIPT "
            "or the built-in bridge script."
        )
    )
    parser.add_argument(
        "--properties",
        type=str,
        default=None,
        help=(
            "Comma-separated list of properties to output. "
            "Supported: Tm, bp, nD, nD_liquid, pka_a, pka_b, dc, ST, density, vis, vapP. "
            "Example: --properties bp,ST,density"
        )
    )

    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not args.smiles and not args.input:
        raise ValueError("Either --smiles or --input must be provided.")

    if args.smiles and args.input:
        raise ValueError("Please provide only one of --smiles or --input, not both.")

    if args.input and not os.path.exists(args.input):
        raise FileNotFoundError(f"Input JSON file not found: {args.input}")


def build_single_input_record(smiles: str, name: Optional[str]) -> List[Dict[str, Any]]:
    return [{
        "name": name if name else smiles,
        "smiles": smiles,
    }]


def dispatch_prediction(
    smiles: str,
    name: Optional[str],
    backend: str,
    temperature_celsius: float,
    bamboo_script: Optional[str] = None,
) -> Dict[str, Any]:
    canonical_smiles = canonicalize_smiles(smiles)

    if canonical_smiles is None:
        return {
            "name": name if name else smiles,
            "smiles": smiles,
            "status": "error",
            "error_message": "Invalid SMILES string.",
            "backend_used": backend,
        }

    if backend == "bamboo_mixer":
        return predict_with_bamboo_mixer(
            smiles=canonical_smiles,
            name=name,
            temperature_celsius=temperature_celsius,
            bamboo_script=bamboo_script,
        )

    return {
        "name": name if name else smiles,
        "smiles": smiles,
        "canonical_smiles": canonical_smiles,
        "status": "error",
        "error_message": f"Unsupported backend: {backend}",
        "backend_used": backend,
    }


def run_predictions(
    records: List[Dict[str, Any]],
    backend: str,
    temperature_celsius: float,
    bamboo_script: Optional[str] = None,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    for record in records:
        smiles = record.get("smiles")
        name = record.get("name")

        if not smiles:
            results.append({
                "name": name if name else None,
                "smiles": smiles,
                "status": "error",
                "error_message": "Missing required field: smiles",
                "backend_used": backend,
            })
            continue

        result = dispatch_prediction(
            smiles=smiles,
            name=name,
            backend=backend,
            temperature_celsius=temperature_celsius,
            bamboo_script=bamboo_script,
        )
        results.append(result)

    return results


def filter_properties(
    summary: Dict[str, Any],
    properties_filter: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Filter output to only include requested properties."""
    if not properties_filter:
        return summary

    # Normalize property names (case-insensitive)
    filter_lower = [p.strip().lower() for p in properties_filter]

    # Map common aliases to internal property names
    property_map = {
        "tm": "Tm",
        "melting": "Tm",
        "melting_point": "Tm",
        "bp": "bp",
        "boiling": "bp",
        "boiling_point": "bp",
        "nd": "nD",
        "refractive_index": "nD",
        "nd_liquid": "nD_liquid",
        "pka_a": "pka_a",
        "acidic_pka": "pka_a",
        "pka_b": "pka_b",
        "basic_pka": "pka_b",
        "dc": "dc",
        "dielectric": "dc",
        "st": "ST",
        "surface_tension": "ST",
        "density": "density",
        "vis": "vis",
        "viscosity": "vis",
        "vapP": "vapP",
        "vapor_pressure": "vapP",
    }

    # Resolve filter to internal property names
    resolved_filter = set()
    for f in filter_lower:
        if f in property_map:
            resolved_filter.add(property_map[f])
        else:
            # Try direct match (case-insensitive)
            for internal_name in property_map.values():
                if internal_name.lower() == f:
                    resolved_filter.add(internal_name)
                    break

    if not resolved_filter:
        return summary

    # Filter results
    filtered_summary = summary.copy()
    filtered_results = []

    for result in summary.get("results", []):
        filtered_result = result.copy()

        if "properties" in filtered_result and isinstance(filtered_result["properties"], dict):
            filtered_props = {
                k: v for k, v in filtered_result["properties"].items()
                if k in resolved_filter
            }
            filtered_result["properties"] = filtered_props

        if "property_units" in filtered_result and isinstance(filtered_result["property_units"], dict):
            filtered_units = {
                k: v for k, v in filtered_result["property_units"].items()
                if k in resolved_filter
            }
            filtered_result["property_units"] = filtered_units

        filtered_results.append(filtered_result)

    filtered_summary["results"] = filtered_results
    return filtered_summary


def main() -> None:
    try:
        args = parse_args()
        validate_args(args)

        if args.smiles:
            records = build_single_input_record(args.smiles, args.name)
        else:
            records = load_input_records(args.input)

        results = run_predictions(
            records=records,
            backend=args.backend,
            temperature_celsius=args.temperature,
            bamboo_script=args.bamboo_script,
        )

        summary = summarize_results(results, backend_used=args.backend)

        # Filter properties if requested
        if args.properties:
            properties_list = [p.strip() for p in args.properties.split(",")]
            summary = filter_properties(summary, properties_list)

        if args.output:
            ensure_parent_dir(args.output)
            save_json(args.output, summary)

        print(json.dumps(summary, ensure_ascii=False, indent=2))

    except Exception as exc:
        error_payload = {
            "status": "failed",
            "backend_used": None,
            "total": 0,
            "success": 0,
            "error": 1,
            "results": [],
            "error_message": str(exc),
        }
        print(json.dumps(error_payload, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()