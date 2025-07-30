"""
Pharmalyzer - ADME and Toxicity Screening Toolkit

Author: [Sorour Hassani]
Email: s.hassani@alum.semnan.ac.ir & sorour.hasani@gmail.com
License: MIT
"""

from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem

def compute_tanimoto(smiles1, smiles2):
    mol1 = Chem.MolFromSmiles(smiles1)
    mol2 = Chem.MolFromSmiles(smiles2)
    if mol1 is None or mol2 is None:
        return None
    fp1 = AllChem.GetMorganFingerprintAsBitVect(mol1, radius=2, nBits=2048)
    fp2 = AllChem.GetMorganFingerprintAsBitVect(mol2, radius=2, nBits=2048)

    Similarity = DataStructs.TanimotoSimilarity(fp1, fp2)
    return Similarity

