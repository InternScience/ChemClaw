#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional

from rdkit import Chem


def canonicalize_smiles(smiles: str) -> Optional[str]:
    if not smiles:
        return None

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    return Chem.MolToSmiles(mol, canonical=True)