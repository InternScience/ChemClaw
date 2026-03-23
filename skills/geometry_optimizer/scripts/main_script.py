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

from backends.xtb_backend import optimize_with_xtb
from utils.io_utils import (
    ensure_parent_dir,
    load_input_records,
    save_json,
    summarize_results,
)
from utils.smiles_utils import canonicalize_smiles


SUPPORTED_BACKENDS = {
    "xtb",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Perform geometry optimization on molecular structures using semi-empirical methods (xTB)."
    )

    # 输入选项（互斥）
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--smiles",
        type=str,
        default=None,
        help="Single-molecule SMILES string."
    )
    input_group.add_argument(
        "--input-xyz",
        type=str,
        default=None,
        help="Input XYZ file path for single-molecule optimization."
    )
    input_group.add_argument(
        "--input",
        type=str,
        default=None,
        help="Input JSON file path for batch prediction."
    )

    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Optional molecule name for single-molecule mode."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional output JSON file path."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Optional output directory for XYZ and log files."
    )
    parser.add_argument(
        "--backend",
        type=str,
        default="xtb",
        choices=sorted(SUPPORTED_BACKENDS),
        help="Optimization backend."
    )
    parser.add_argument(
        "--method",
        type=str,
        default="gfn2",
        choices=["gfn2", "gfn1", "gfnff"],
        help="xTB method. Default: gfn2"
    )
    parser.add_argument(
        "--charge",
        type=int,
        default=None,
        help="Molecular charge. Default: auto-infer from SMILES or 0"
    )
    parser.add_argument(
        "--uhf",
        type=int,
        default=None,
        help="Number of unpaired electrons. Default: auto-infer from SMILES or 0"
    )
    parser.add_argument(
        "--solvent",
        type=str,
        default=None,
        help="Optional solvent model (e.g., water, ethanol, acetone)."
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=200,
        help="Maximum optimization cycles. Default: 200"
    )

    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not args.smiles and not args.input_xyz and not args.input:
        raise ValueError("One of --smiles, --input-xyz, or --input must be provided.")

    if args.input and not os.path.exists(args.input):
        raise FileNotFoundError(f"Input JSON file not found: {args.input}")

    if args.input_xyz and not os.path.exists(args.input_xyz):
        raise FileNotFoundError(f"Input XYZ file not found: {args.input_xyz}")


def build_single_input_record(
    smiles: Optional[str],
    input_xyz: Optional[str],
    name: Optional[str],
) -> List[Dict[str, Any]]:
    record = {"name": name if name else None}
    if smiles:
        record["smiles"] = smiles
    if input_xyz:
        record["input_xyz"] = input_xyz
    return [record]


def dispatch_optimization(
    record: Dict[str, Any],
    backend: str,
    method: str,
    charge: Optional[int],
    uhf: Optional[int],
    solvent: Optional[str],
    max_cycles: int,
    output_dir: Optional[str],
) -> Dict[str, Any]:
    """
    对单个分子进行几何优化。
    """
    smiles = record.get("smiles")
    input_xyz = record.get("input_xyz")
    name = record.get("name")

    if not smiles and not input_xyz:
        return {
            "name": name,
            "status": "error",
            "error_message": "Missing required field: 'smiles' or 'input_xyz'",
            "backend_used": backend,
        }

    if backend == "xtb":
        return optimize_with_xtb(
            smiles=smiles,
            input_xyz=input_xyz,
            name=name,
            method=method,
            charge=charge,
            uhf=uhf,
            solvent=solvent,
            max_cycles=max_cycles,
            output_dir=output_dir,
        )

    return {
        "name": name,
        "status": "error",
        "error_message": f"Unsupported backend: {backend}",
        "backend_used": backend,
    }


def run_optimizations(
    records: List[Dict[str, Any]],
    backend: str,
    method: str,
    charge: Optional[int],
    uhf: Optional[int],
    solvent: Optional[str],
    max_cycles: int,
    output_dir: Optional[str],
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    for record in records:
        result = dispatch_optimization(
            record=record,
            backend=backend,
            method=method,
            charge=charge,
            uhf=uhf,
            solvent=solvent,
            max_cycles=max_cycles,
            output_dir=output_dir,
        )
        results.append(result)

    return results


def main() -> None:
    try:
        args = parse_args()
        validate_args(args)

        if args.smiles or args.input_xyz:
            records = build_single_input_record(args.smiles, args.input_xyz, args.name)
        else:
            records = load_input_records(args.input)

        results = run_optimizations(
            records=records,
            backend=args.backend,
            method=args.method,
            charge=args.charge,
            uhf=args.uhf,
            solvent=args.solvent,
            max_cycles=args.max_cycles,
            output_dir=args.output_dir,
        )

        summary = summarize_results(results, backend_used=args.backend)

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
            "partial_success": 0,
            "error": 1,
            "results": [],
            "error_message": str(exc),
        }
        print(json.dumps(error_payload, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
