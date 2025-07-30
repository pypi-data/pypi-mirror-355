"""
Pharmalyzer - ADME and Toxicity Screening Toolkit

Author: [Sorour Hassani]
Email: s.hassani@alum.semnan.ac.ir & sorour.hasani@gmail.com
License: MIT
"""


def physicochemical_properties(smiles):
    mol = Chem.MolFromSmiles(smiles)
    return {
        "MolecularWeight": round(Descriptors.MolWt(mol), 2),
        "LogP": round(Descriptors.MolLogP(mol), 2),
        "TPSA": round(rdMolDescriptors.CalcTPSA(mol), 2),
        "HBD": Descriptors.NumHDonors(mol),
        "HBA": Descriptors.NumHAcceptors(mol),
        "RotatableBonds": Descriptors.NumRotatableBonds(mol),
        "Rings": mol.GetRingInfo().NumRings(),
        "HeavyAtoms": mol.GetNumHeavyAtoms()
    }


from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

def pharmacokinetics_properties(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {"GI_Absorption": "Unknown", "BBB_Permeability": "Unknown"}

    logp = Descriptors.MolLogP(mol)  # Approximate WLOGP
    tpsa = rdMolDescriptors.CalcTPSA(mol)

    # GI Absorption
    if tpsa <= 131.6 and (-0.7 <= logp <= 5.0):
        gi = "High"
    else:
        gi = "Low"

    # BBB Permeability
    if tpsa <= 90 and (-0.7 <= logp <= 5.0):
        bbb = "Yes"
    else:
        bbb = "No"

    return {"GI_Absorption": gi, "BBB_Permeability": bbb}


def filter_by_tpsa(data, column='tpsa', max_val=140):

    filtered = []
    for row in data:
        try:
            tpsa = float(row.get(column, 0))
            if tpsa <= max_val:
                filtered.append(row)
        except:
            continue
    return filtered

def filter_by_rotatable_bonds(data, column='rotatable_bonds', max_val=10):
    filtered = []
    for row in data:
        try:
            rb = int(row.get(column, 0))
            if rb <= max_val:
                filtered.append(row)
        except:
            continue
    return filtered

def filter_by_logS(data, column='logS', min_val=-6):
    filtered = []
    for row in data:
        try:
            logs = float(row.get(column, 0))
            if logs >= min_val:
                filtered.append(row)
        except:
            continue
    return filtered


def classify_logS_adme(logs):
    try:
        logs = float(logs)
        if logs > 0:
            return "Very Soluble"
        elif 0 >= logs > -2:
            return "Soluble"
        elif -2 >= logs > -4:
            return "Moderately Soluble"
        elif -4 >= logs > -6:
            return "Poorly Soluble"
        elif -6 >= logs > -10:
            return "Very Poorly Soluble"
        elif logs <= -10:
            return "Insoluble"
    except (ValueError, TypeError):
        return "Invalid logS"



def clean_adme_compounds(data, tpsa_max=140, rb_max=10, logs_min=-6):
    step1 = filter_by_tpsa(data, max_val=tpsa_max)
    step2 = filter_by_rotatable_bonds(step1, max_val=rb_max)
    step3 = filter_by_logS(step2, min_val=logs_min)
    return step3

from rdkit import Chem
from rdkit.Chem import Descriptors

def compute_logp(smiles: str) -> float:
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        return Descriptors.MolLogP(mol)
    except Exception as e:
        print(f"Error computing logP: {e}")
        return None


from rdkit import Chem
from rdkit.Chem import FilterCatalog
from rdkit.Chem.FilterCatalog import FilterCatalogParams

def contains_pains(smiles):
    """
    Check if a molecule contains PAINS substructures.
    Returns True if PAINS found, otherwise False.
    """
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        return False

    params = FilterCatalogParams()
    params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS_A)
    params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS_B)
    params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS_C)

    catalog = FilterCatalog.FilterCatalog(params)

    return catalog.HasMatch(mol)

def filter_pains(data, smiles_column='smiles'):
    """
    Remove molecules with PAINS substructures from the dataset.
    :param data: list of dicts (e.g., from CSV or JSON)
    :param smiles_column: column name containing SMILES strings
    :return: filtered list
    """
    filtered = []
    for row in data:
        smiles = row.get(smiles_column, '')
        if smiles and not contains_pains(smiles):
            filtered.append(row)
    return filtered

from rdkit import Chem
from rdkit.Chem import FilterCatalog
from rdkit.Chem.FilterCatalog import FilterCatalogParams

def contains_brenk(smiles):
    """
    Check if a molecule contains Brenk substructures.
    Returns True if matched, False otherwise.
    """
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        return False

    params = FilterCatalogParams()
    params.AddCatalog(FilterCatalogParams.FilterCatalogs.Brenk)
    catalog = FilterCatalog.FilterCatalog(params)

    return catalog.HasMatch(mol)

def filter_brenk(data, smiles_column='smiles'):
    """
    Remove molecules that contain Brenk alerts from the dataset.
    :param data: list of dicts (CSV or JSON rows)
    :param smiles_column: name of SMILES column
    :return: filtered data list
    """
    filtered = []
    for row in data:
        smiles = row.get(smiles_column, '')
        if smiles and not contains_brenk(smiles):
            filtered.append(row)
    return filtered


from rdkit import Chem
from rdkit.Chem import Descriptors, Crippen, Lipinski, rdMolDescriptors

def is_lead_like(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        return False

    mw = Descriptors.MolWt(mol)
    logp = Crippen.MolLogP(mol)
    h_donors = Lipinski.NumHDonors(mol)
    h_acceptors = Lipinski.NumHAcceptors(mol)
    rot_bonds = Lipinski.NumRotatableBonds(mol)
    tpsa = rdMolDescriptors.CalcTPSA(mol)

    return (
        250 <= mw <= 350 and
        logp <= 3.5 and
        h_donors <= 3 and
        h_acceptors <= 6 and
        rot_bonds <= 7 and
        tpsa <= 90
    )

def filter_lead_like(data, smiles_column='smiles'):
    filtered = []
    for row in data:
        smiles = row.get(smiles_column, '')
        if smiles and is_lead_like(smiles):
            filtered.append(row)
    return filtered


from rdkit import Chem
from rdkit.Chem import Descriptors

def compute_log_kp(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None, "Invalid SMILES"

    logP = Descriptors.MolLogP(mol)
    mw = Descriptors.MolWt(mol)

    log_kp = -2.72 + 0.71 * logP - 0.0061 * mw
    return round(log_kp, 4), classify_log_kp(log_kp)

def classify_log_kp(log_kp):
    if log_kp > -2:
        return "High permeability"
    elif -4 < log_kp <= -2:
        return "Moderate permeability"
    else:
        return "Low permeability"

from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

def predict_excretion(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return "Invalid SMILES"

    mw = Descriptors.MolWt(mol)
    logp = Descriptors.MolLogP(mol)
    tpsa = rdMolDescriptors.CalcTPSA(mol)

    if mw < 400 and logp < 3 and tpsa > 75:
        return "Likely Renal (kidney) Excretion"
    elif logp > 4 and tpsa < 60:
        return "Likely Biliary (liver/bile) Excretion"
    else:
        return "Mixed or Uncertain Excretion Pathway"

from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

def cyp_inhibition_prediction(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return "Invalid SMILES"

    logp = Descriptors.MolLogP(mol)
    tpsa = rdMolDescriptors.CalcTPSA(mol)
    hbd = Descriptors.NumHDonors(mol)
    hba = Descriptors.NumHAcceptors(mol)
    mw = Descriptors.MolWt(mol)
    aromatic_rings = len([r for r in mol.GetRingInfo().AtomRings()
                          if all(mol.GetAtomWithIdx(i).GetIsAromatic() for i in r)])

    prediction = {}

    # Rule-based estimations (based on literature & SwissADME tendencies)
    prediction['CYP1A2'] = "Likely Inhibitor" if logp > 2.5 and tpsa < 75 and aromatic_rings >= 2 else "Unlikely"
    prediction['CYP2C9'] = "Likely Inhibitor" if logp > 2.0 and mw > 300 else "Unlikely"
    prediction['CYP2C19'] = "Likely Inhibitor" if logp > 3.0 and hbd <= 2 else "Unlikely"
    prediction['CYP2D6'] = "Likely Inhibitor" if logp > 3.0 and hba >= 3 else "Unlikely"
    prediction['CYP3A4'] = "Likely Inhibitor" if logp > 3.5 and hbd <= 2 and mw > 350 else "Unlikely"

    return prediction
def cyp_substrate_prediction(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return "Invalid SMILES"

    logp = Descriptors.MolLogP(mol)
    mw = Descriptors.MolWt(mol)
    rot_bonds = Descriptors.NumRotatableBonds(mol)
    hbd = Descriptors.NumHDonors(mol)
    tpsa = rdMolDescriptors.CalcTPSA(mol)

    result = {}

    # Based on general trends (substrates often moderate size, moderate LogP, flexible)
    result['CYP3A4'] = "Likely Substrate" if mw > 350 and logp > 2.5 and rot_bonds > 5 else "Unlikely"
    result['CYP2D6'] = "Likely Substrate" if logp > 2.0 and hbd >= 1 else "Unlikely"
    result['CYP2C9'] = "Likely Substrate" if mw > 300 and tpsa < 90 else "Unlikely"
    result['CYP1A2'] = "Likely Substrate" if logp > 2.0 and tpsa < 70 else "Unlikely"

    return result
