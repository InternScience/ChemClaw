#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from rdkit import Chem


def canonicalize_smiles(smiles: str) -> str:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"无效 SMILES: {smiles}")
    return Chem.MolToSmiles(mol, canonical=True)