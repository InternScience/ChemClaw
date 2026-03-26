#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Predict and visualize an MS/MS spectrum from a single SMILES using Fiora."
    )
    parser.add_argument("smiles", help="Input SMILES string, for example CCO.")
    parser.add_argument("--name", default="mol1", help="Spectrum name. Default: mol1.")
    parser.add_argument(
        "--precursor",
        default="[M+H]+",
        help="Precursor ion type. Default: [M+H]+.",
    )
    parser.add_argument(
        "--ce",
        type=float,
        default=20.0,
        help="Collision energy. Default: 20.",
    )
    parser.add_argument(
        "--instrument",
        default="HCD",
        help="Instrument type. Default: HCD.",
    )
    parser.add_argument(
        "--output-stem",
        default="predicted_ms",
        help="Base name for output files inside output/. Default: predicted_ms.",
    )
    parser.add_argument("--dev", default="cpu", help="Device passed to Fiora. Default: cpu.")
    parser.add_argument("--model", default="default", help="Model path passed to Fiora.")
    parser.add_argument(
        "--min-prob",
        type=float,
        default=0.001,
        help="Minimum peak probability recorded in the spectrum.",
    )
    parser.add_argument("--rt", action=argparse.BooleanOptionalAction, default=False, help="Predict RT.")
    parser.add_argument("--ccs", action=argparse.BooleanOptionalAction, default=False, help="Predict CCS.")
    parser.add_argument(
        "--annotation",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Annotate predicted peaks with fragment SMILES.",
    )
    parser.add_argument(
        "--plot",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Generate a PNG stick spectrum. Default: true.",
    )
    parser.add_argument(
        "--show-title",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Show the molecule name at the top of the plot. Default: false.",
    )
    parser.add_argument("--debug", action=argparse.BooleanOptionalAction, default=False, help="Enable Fiora debug output.")
    return parser.parse_args()


def run_command(command: list[str], env: dict[str, str]) -> None:
    subprocess.run(command, check=True, env=env)


def main() -> None:
    args = parse_args()

    skill_dir = Path(__file__).resolve().parent
    fiora_dir = skill_dir / "assets" / "fiora"
    predict_script = fiora_dir / "scripts" / "predict-single-smiles.py"
    plot_script = fiora_dir / "fiora" / "visualization" / "plot_spectrum.py"

    if not predict_script.exists():
        raise FileNotFoundError(f"Missing Fiora prediction script: {predict_script}")
    if not plot_script.exists():
        raise FileNotFoundError(f"Missing Fiora plotting script: {plot_script}")

    output_dir = Path('/tmp/chemclaw')
    output_dir.mkdir(parents=True, exist_ok=True)
    mgf_path = output_dir / f"{args.output_stem}.mgf"
    png_path = output_dir / f"{args.output_stem}.png"

    env = os.environ.copy()
    env.setdefault("MPLBACKEND", "Agg")

    predict_command = [
        sys.executable,
        str(predict_script),
        "--smiles",
        args.smiles,
        "--name",
        args.name,
        "--precursor",
        args.precursor,
        "--ce",
        str(args.ce),
        "--instrument",
        args.instrument,
        "--output",
        str(mgf_path),
        "--model",
        args.model,
        "--dev",
        args.dev,
        "--min-prob",
        str(args.min_prob),
    ]
    if args.rt:
        predict_command.append("--rt")
    if args.ccs:
        predict_command.append("--ccs")
    if args.annotation:
        predict_command.append("--annotation")
    if args.debug:
        predict_command.append("--debug")

    run_command(predict_command, env)

    if args.plot:
        plot_command = [
            sys.executable,
            str(plot_script),
            "-f",
            str(mgf_path),
            "-n",
            args.name,
            "-o",
            str(png_path),
        ]
        if args.show_title:
            plot_command.append("--show-title")
        run_command(plot_command, env)
        print(f"Plot written to {png_path}")

    print(f"Spectrum written to {mgf_path}")


if __name__ == "__main__":
    main()
