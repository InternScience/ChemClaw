#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

import numpy as np


OUTPUT_DIR = Path("/tmp/chemclaw")
HELPER_ROOT = Path(__file__).resolve().parents[1] / "nmr-prediction"
NMRNET_DIR = HELPER_ROOT / "assets" / "NMRNet"
DICT_PATH = NMRNET_DIR / "oc_limit_dict.txt"
ZENODO_URL = "https://zenodo.org/records/19142375/files/weights.zip?download=1"
CHECKPOINT_REL = Path("cv_seed_42_fold_0/checkpoint_best.pt")
MODEL_DIR = Path(
    "/tmp/weights/finetune/solid/Organic Crystal/"
    "P_pretraining_organic_crystal_global_0_kener_gauss_atomdes_0_"
    "unimol_large_atom_regloss_mse_lr_1e-4_bs_16_0.06_5"
)
ZIP_PREFIX = (
    "weights/finetune/solid/Organic Crystal/"
    "P_pretraining_organic_crystal_global_0_kener_gauss_atomdes_0_"
    "unimol_large_atom_regloss_mse_lr_1e-4_bs_16_0.06_5"
)


def _ensure_nmrnet_in_path() -> None:
    if not NMRNET_DIR.is_dir():
        raise RuntimeError(f"NMRNet 代码目录不存在: {NMRNET_DIR}")
    if not DICT_PATH.is_file():
        raise RuntimeError(f"缺少字典文件: {DICT_PATH}")
    if str(NMRNET_DIR) not in sys.path:
        sys.path.insert(0, str(NMRNET_DIR))


def download_weights_and_scalers() -> None:
    try:
        from remotezip import RemoteZip
    except ImportError as exc:
        raise RuntimeError("请先安装 remotezip: pip install remotezip") from exc

    targets = [
        (f"{ZIP_PREFIX}/{CHECKPOINT_REL.as_posix()}", MODEL_DIR / CHECKPOINT_REL),
        (f"{ZIP_PREFIX}/target_scaler.ss", MODEL_DIR / "target_scaler.ss"),
    ]
    need = [(zp, lp) for zp, lp in targets if not lp.exists()]
    if not need:
        print("✓ 所有权重和 scaler 文件均已就绪")
        return

    print(f"连接到 Zenodo: {ZENODO_URL}")
    with RemoteZip(ZENODO_URL) as zf:
        for zip_path, local_path in need:
            size_hint = "~560 MB" if zip_path.endswith(".pt") else "< 1 KB"
            print(f"  [下载] {Path(zip_path).parent.name}/.../{Path(zip_path).name} ({size_hint})")
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(zf.read(zip_path))
            print(f"  [完成] → {local_path}")
    print("✓ 下载完毕")


def cif_to_data(cif_path: str) -> dict:
    from pymatgen.core import Structure

    structure = Structure.from_file(cif_path)
    atoms = [site.species.elements[0].symbol for site in structure]
    coords = np.array(structure.cart_coords, dtype=np.float32)
    atoms_target_mask = np.array([1 if atom == "P" else 0 for atom in atoms], dtype=np.int32)
    atoms_target = np.zeros(len(atoms), dtype=np.float32)
    return {
        "atoms": atoms,
        "coordinates": coords,
        "atoms_target": atoms_target,
        "atoms_target_mask": atoms_target_mask,
    }


def _make_model_args() -> argparse.Namespace:
    args = argparse.Namespace()
    args.encoder_layers = 15
    args.encoder_embed_dim = 512
    args.encoder_ffn_embed_dim = 2048
    args.encoder_attention_heads = 64
    args.dropout = 0.1
    args.emb_dropout = 0.1
    args.attention_dropout = 0.1
    args.activation_dropout = 0.0
    args.pooler_dropout = 0.0
    args.activation_fn = "gelu"
    args.pooler_activation_fn = "tanh"
    args.post_ln = False
    args.masked_token_loss = -1.0
    args.masked_coord_loss = -1.0
    args.masked_dist_loss = -1.0
    args.x_norm_loss = -1.0
    args.delta_pair_repr_norm_loss = -1.0
    args.lattice_loss = -1.0
    args.selected_atom = "P"
    args.num_classes = 1
    args.atom_descriptor = 0
    args.classification_head_name = "nmr_head"
    args.model_path = str(MODEL_DIR / CHECKPOINT_REL)
    args.dict_path = str(DICT_PATH)
    args.global_distance = False
    args.gaussian_kernel = True
    args.saved_dir = str(MODEL_DIR)
    args.max_atoms = 512
    args.max_seq_len = 1024
    args.seed = 1
    args.batch_size = 16
    return args


def _load_model(args, dictionary):
    from unicore import checkpoint_utils
    from uninmr.models import UniMatModel

    state = checkpoint_utils.load_checkpoint_to_cpu(args.model_path)
    state["model"] = {
        (k.replace("classification_heads", "node_classification_heads") if k.startswith("classification_heads") else k): v
        for k, v in state["model"].items()
    }
    model = UniMatModel(args, dictionary)
    model.register_node_classification_head(
        args.classification_head_name,
        num_classes=args.num_classes,
        extra_dim=args.atom_descriptor,
    )
    model.load_state_dict(state["model"], strict=False)
    model.float()
    model.eval()
    return model


def _build_dataset(record: dict, args, dictionary, target_scaler):
    import torch
    from torch.utils.data import Dataset
    from unicore.data import AppendTokenDataset, NestedDictionaryDataset, PrependTokenDataset, RightPadDataset, RightPadDataset2D, TokenizeDataset
    from uninmr.data import CroppingDataset, DistanceDataset, EdgeTypeDataset, FilterDataset, IndexDataset, KeyDataset, NormalizeDataset, PrependAndAppend2DDataset, RightPadDataset2D0, SelectTokenDataset, TargetScalerDataset, ToTorchDataset
    from uninmr.utils import parse_select_atom

    class _SingleDataset(Dataset):
        def __init__(self, item):
            self._item = item

        def __len__(self):
            return 1

        def __getitem__(self, idx):
            return self._item

    def _pa(ds, pre, app):
        return AppendTokenDataset(PrependTokenDataset(ds, pre), app)

    dataset = _SingleDataset(record)
    matid_dataset = IndexDataset(dataset)
    dataset = CroppingDataset(dataset, args.seed, "atoms", "coordinates", args.max_atoms)
    dataset = NormalizeDataset(dataset, "coordinates")
    token_dataset = TokenizeDataset(KeyDataset(dataset, "atoms"), dictionary, max_seq_len=args.max_seq_len)
    selected_token = parse_select_atom(dictionary, args.selected_atom)
    select_atom_dataset = SelectTokenDataset(
        token_dataset=token_dataset,
        token_mask_dataset=KeyDataset(dataset, "atoms_target_mask"),
        selected_token=selected_token,
    )

    keep = [0 if torch.all(select_atom_dataset[i] == 0) else 1 for i in range(len(select_atom_dataset))]
    if sum(keep) == 0:
        raise ValueError("结构中未找到 P 原子，无法预测")

    dataset = FilterDataset(dataset, keep)
    matid_dataset = FilterDataset(matid_dataset, keep)
    token_dataset = FilterDataset(token_dataset, keep)
    select_atom_dataset = FilterDataset(select_atom_dataset, keep)
    token_dataset = _pa(token_dataset, dictionary.bos(), dictionary.eos())
    select_atom_dataset = _pa(select_atom_dataset, dictionary.pad(), dictionary.pad())

    coord_dataset = ToTorchDataset(KeyDataset(dataset, "coordinates"), "float32")
    distance_dataset = PrependAndAppend2DDataset(DistanceDataset(coord_dataset), 0.0)
    distance_dataset = RightPadDataset2D(distance_dataset, pad_idx=0)
    coord_dataset = _pa(coord_dataset, 0.0, 0.0)
    edge_type = EdgeTypeDataset(token_dataset, len(dictionary))

    tgt_dataset = TargetScalerDataset(
        ToTorchDataset(KeyDataset(dataset, "atoms_target"), "float32"),
        target_scaler,
        args.num_classes,
    )
    tgt_dataset = _pa(ToTorchDataset(tgt_dataset, dtype="float32"), dictionary.pad(), dictionary.pad())

    return NestedDictionaryDataset(
        {
            "net_input": {
                "select_atom": RightPadDataset(select_atom_dataset, pad_idx=dictionary.pad()),
                "src_tokens": RightPadDataset(token_dataset, pad_idx=dictionary.pad()),
                "src_coord": RightPadDataset2D0(coord_dataset, pad_idx=0),
                "src_distance": distance_dataset,
                "src_edge_type": RightPadDataset2D(edge_type, pad_idx=0),
            },
            "target": {"finetune_target": RightPadDataset(tgt_dataset, pad_idx=0)},
            "matid": matid_dataset,
        }
    )


def predict_shifts(cif_path: str) -> np.ndarray:
    import torch
    from torch.utils.data import DataLoader
    from unicore.data import Dictionary
    from uninmr.utils import TargetScaler

    scaler_path = MODEL_DIR / "target_scaler.ss"
    if not scaler_path.exists():
        raise FileNotFoundError(f"缺少 scaler 文件: {scaler_path}\n请先运行: python p_nmr_simulation.py --setup")

    args = _make_model_args()
    dictionary = Dictionary.load(args.dict_path)
    dictionary.add_symbol("[MASK]", is_special=True)

    target_scaler = TargetScaler(str(MODEL_DIR))
    record = cif_to_data(cif_path)
    model = _load_model(args, dictionary)
    nest_dataset = _build_dataset(record, args, dictionary, target_scaler)

    loader = DataLoader(nest_dataset, batch_size=1, shuffle=False)
    preds = []
    with torch.no_grad():
        for batch in loader:
            net_input = {k[len("net_input."):]: v for k, v in batch.items() if k.startswith("net_input.")}
            out = model(**net_input, features_only=True, classification_head_name=args.classification_head_name)
            pred = target_scaler.inverse_transform(out[0].view(-1, args.num_classes).cpu().numpy()).astype("float32")
            preds.append(pred)
    return np.concatenate(preds).reshape(-1)


def plot_spectrum(shifts: np.ndarray, title: str, save_path: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x_lo = min(float(shifts.min()) - 20.0, -80.0)
    x_hi = max(float(shifts.max()) + 20.0, 150.0)
    x = np.linspace(x_lo, x_hi, 12000)
    gamma = 3.0
    spectrum = np.sum(1.0 / (1.0 + ((x[:, None] - shifts) / gamma) ** 2), axis=1)
    spectrum /= spectrum.max()

    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(x, spectrum, color="#5e3c99", linewidth=1.8, label="NMRNet 31P SSNMR prediction")
    ax.fill_between(x, spectrum, alpha=0.12, color="#5e3c99")
    for shift in shifts:
        ax.axvline(shift, color="#5e3c99", alpha=0.25, linewidth=0.7, linestyle="--")
    ax.set_xlim(x_hi, x_lo)
    ax.set_ylim(-0.05, 1.2)
    ax.set_xlabel("Chemical Shift δ (ppm)", fontsize=13)
    ax.set_ylabel("Relative Intensity", fontsize=13)
    ax.set_title(title, fontsize=13)
    ax.set_yticks([])
    ax.legend(fontsize=11, loc="upper left")
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_linewidth(1.5)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[输出] {save_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="NMRNet 固相 31P NMR 化学位移预测（输入 CIF 晶体结构）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("cif", nargs="?", help="输入 CIF 结构文件路径")
    parser.add_argument("--setup", action="store_true", help="下载对应固相模型权重与 scaler")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.setup:
        download_weights_and_scalers()
        return
    if not args.cif:
        parser.error("请提供 CIF 文件路径，或使用 --setup 下载所需文件")

    cif_path = Path(args.cif).expanduser().resolve()
    if not cif_path.exists():
        raise FileNotFoundError(f"CIF 文件不存在: {cif_path}")

    _ensure_nmrnet_in_path()
    shifts = predict_shifts(str(cif_path))
    safe_name = cif_path.stem
    png_path = OUTPUT_DIR / f"ssnmr_31P_{safe_name}.png"
    report_path = OUTPUT_DIR / f"ssnmr_31P_{safe_name}.md"
    plot_spectrum(shifts, f"Predicted 31P SSNMR — {cif_path.name}", str(png_path))

    sorted_shifts = sorted(shifts.tolist())
    lines = [
        f"# 31P Chemical Shifts — {cif_path.name}",
        "",
        "> Predicted by NMRNet (solid Organic Crystal model)",
        "",
        "| # | δ (ppm) |",
        "|---|---------|",
    ]
    for idx, shift in enumerate(sorted_shifts, 1):
        lines.append(f"| {idx} | {shift:.2f} |")
    report_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"\n{'=' * 50}")
    print(f"  31P NMR 预测结果  —  {cif_path.name}")
    print(f"{'=' * 50}")
    print(f"\n  化学位移 ({len(sorted_shifts)} 个原子):")
    for idx, shift in enumerate(sorted_shifts, 1):
        print(f"    {idx:>3}.  {shift:>8.2f} ppm")
    print("\n  输出文件:")
    print(f"    {png_path}")
    print(f"    {report_path}")


if __name__ == "__main__":
    main()
