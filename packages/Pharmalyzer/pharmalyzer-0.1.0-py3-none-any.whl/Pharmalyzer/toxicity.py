"""
Pharmalyzer - ADME and Toxicity Screening Toolkit

Author: [Sorour Hassani]
Email: s.hassani@alum.semnan.ac.ir & sorour.hasani@gmail.com
License: MIT
"""
from rdkit import Chem

TOXIC_SUBSTRUCTURES = {
    "Nitro group": "[N+](=O)[O-]",
    "Azo group": "N=N",
    "Nitrile": "C#N",
    "Aromatic amine": "c1ccc(N)cc1",
    "Hydrazine": "NN",
    "Halogen (Cl, Br, I)": "[Cl,Br,I]",
    "Epoxide": "C1OC1",
    "Acyl chloride": "C(=O)Cl",
    "Isocyanate": "N=C=O",
    "Thiol": "[SH]",
    "Diazo": "N=[N+]",
}

def check_toxic_substructures(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    found = []
    for name, smarts in TOXIC_SUBSTRUCTURES.items():
        pattern = Chem.MolFromSmarts(smarts)
        if mol.HasSubstructMatch(pattern):
            found.append(name)
    return found

def filter_toxic_compounds(data, smiles_key='smiles'):
    filtered_data = []
    for row in data:
        smiles = row.get(smiles_key, "")
        toxic_features = check_toxic_substructures(smiles)
        if toxic_features is None:
            print(f"Warning: Invalid SMILES '{smiles}'")
            continue
        if not toxic_features:
            filtered_data.append(row)
        else:
            print(f"Removed compound {smiles} due to toxic groups: {', '.join(toxic_features)}")
    return filtered_data

