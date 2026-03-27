#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict

import numpy as np
from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, Lipinski, rdMolDescriptors


DESCRIPTOR_ORDER = [
    "MolWt",
    "TPSA",
    "MolLogP",
    "NumHDonors",
    "NumHAcceptors",
    "RingCount",
    "HeavyAtomCount",
    "FractionCSP3",
]


def compute_descriptor_dict(smiles: str) -> Dict[str, float]:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")

    desc = {
        "MolWt": round(float(Descriptors.MolWt(mol)), 6),
        "TPSA": round(float(rdMolDescriptors.CalcTPSA(mol)), 6),
        "MolLogP": round(float(Crippen.MolLogP(mol)), 6),
        "NumHDonors": int(Lipinski.NumHDonors(mol)),
        "NumHAcceptors": int(Lipinski.NumHAcceptors(mol)),
        "RingCount": int(rdMolDescriptors.CalcNumRings(mol)),
        "HeavyAtomCount": int(mol.GetNumHeavyAtoms()),
        "FractionCSP3": round(float(rdMolDescriptors.CalcFractionCSP3(mol)), 6),
    }
    return desc


def descriptor_dict_to_vector(desc: Dict[str, float]) -> np.ndarray:
    return np.asarray([desc[k] for k in DESCRIPTOR_ORDER], dtype=float)