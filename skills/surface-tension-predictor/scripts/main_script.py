#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backends.surface_tension_backend import predict_surface_tension_batch
from backends.public_joblib_backend import predict_surface_tension_batch_public_joblib
from utils.io_utils import load_input_records, dump_json


def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="根据 SMILES 预测分子表面张力。"
    )
    parser.add_argument(
        "--smiles",
        type=str,
        default=None,
        help="单个 SMILES 字符串。"
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="单分子模式下可选的分子名称。"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="批量输入 JSON 文件路径，格式为 [{'name', 'smiles'}]。"
    )
    parser.add_argument(
        "--backend",
        type=str,
        default="baseline",
        choices=["baseline", "public_joblib"],
        help="选择后端：baseline 或 public_joblib。默认 baseline。"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="模型文件路径。baseline 模式下为可选 joblib 模型；public_joblib 模式下建议显式指定。"
    )
    parser.add_argument(
        "--params-path",
        type=str,
        default=None,
        help="public_joblib 模式下所需的参数文件路径（linear_SurfaceTension.joblib_parameters）。"
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON 输出缩进。"
    )
    return parser


def main():
    parser = build_argparser()
    args = parser.parse_args()

    try:
        records = load_input_records(
            smiles=args.smiles,
            name=args.name,
            input_path=args.input
        )

        if args.backend == "baseline":
            result = predict_surface_tension_batch(
                records=records,
                model_path=args.model_path
            )
        elif args.backend == "public_joblib":
            result = predict_surface_tension_batch_public_joblib(
                records=records,
                model_path=args.model_path,
                params_path=args.params_path
            )
        else:
            raise ValueError(f"Unsupported backend: {args.backend}")

        print(dump_json(result, indent=args.indent))

    except Exception as exc:
        error_result = {
            "status": "failed",
            "message": str(exc),
        }
        print(dump_json(error_result, indent=args.indent))
        sys.exit(1)


if __name__ == "__main__":
    main()