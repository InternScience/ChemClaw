#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, Tuple

from rdkit import Chem
from rdkit.Chem import AllChem


def canonicalize_smiles(smiles: str) -> Optional[str]:
    """将 SMILES 转换为标准形式。"""
    if not smiles:
        return None

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    return Chem.MolToSmiles(mol, canonical=True)


def smiles_to_3d_xyz(smiles: str, output_xyz_path: str) -> Tuple[bool, str]:
    """
    使用 RDKit 从 SMILES 生成初始 3D 构象，并保存为 XYZ 文件。
    
    返回:
        (success, message): 成功时 success=True，message 为输出路径；失败时 success=False，message 为错误信息。
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False, "Invalid SMILES string."

        # 添加氢原子
        mol = Chem.AddHs(mol)

        # 生成 3D 构象
        params = AllChem.ETKDGv3()
        params.randomSeed = 42
        result = AllChem.EmbedMolecule(mol, params)

        if result == -1:
            return False, "Failed to generate 3D conformation."

        # 可选：使用 UFF 进行初步优化
        try:
            AllChem.UFFOptimizeMolecule(mol, maxIters=200)
        except Exception:
            pass  # UFF 优化失败不影响后续 xTB 优化

        # 写入 XYZ 文件
        from rdkit.Chem import rdMolTransforms

        conf = mol.GetConformer()
        num_atoms = mol.GetNumAtoms()

        with open(output_xyz_path, "w", encoding="utf-8") as f:
            f.write(f"{num_atoms}\n")
            f.write(f"Generated from SMILES: {smiles}\n")
            for i in range(num_atoms):
                atom = mol.GetAtomWithIdx(i)
                pos = conf.GetAtomPosition(i)
                f.write(f"{atom.GetSymbol()} {pos.x:.6f} {pos.y:.6f} {pos.z:.6f}\n")

        return True, output_xyz_path

    except Exception as e:
        return False, f"Error generating 3D structure: {str(e)}"


def get_charge_and_uhf_from_smiles(smiles: str) -> Tuple[int, int]:
    """
    从 SMILES 推断电荷和未成对电子数。
    
    返回:
        (charge, uhf): charge 为形式电荷，uhf 为未成对电子数。
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return 0, 0

    # 计算形式电荷
    charge = sum(atom.GetFormalCharge() for atom in mol.GetAtoms())

    # 简化处理：假设闭壳层，uhf=0
    # 更复杂的自由基检测可以后续扩展
    uhf = 0

    return charge, uhf
