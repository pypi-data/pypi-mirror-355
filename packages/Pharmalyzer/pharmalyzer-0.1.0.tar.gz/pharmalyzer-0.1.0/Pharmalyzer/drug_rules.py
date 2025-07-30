"""
Pharmalyzer - ADME and Toxicity Screening Toolkit

Author: [Sorour Hassani]
Email: s.hassani@alum.semnan.ac.ir & sorour.hasani@gmail.com
License: MIT
"""
def check_lipinski_rule(data):
    passed = []
    failed = []

    for row in data:
        try:
            mw = float(row.get("molecular_weight", 0))
            logp = float(row.get("logp", 0))
            h_donors = int(row.get("h_donors", 0))
            h_acceptors = int(row.get("h_acceptors", 0))

            if (
                mw <= 500 and
                logp <= 5 and
                h_donors <= 5 and
                h_acceptors <= 10
            ):
                passed.append(row)
            else:
                failed.append(row)

        except (ValueError, TypeError):
            continue

    return passed, failed


def filter_by_rule(data, rule_func):
    """
    Apply a rule function and return only the passing compounds.

    Parameters:
        data (list of dict)
        rule_func (function): A function like check_lipinski_rule

    Returns:
        list of dict: Compounds passing the rule
    """
    passed, _ = rule_func(data)
    return passed



def check_veber_rule(data):
    """
    Check Veber's rule for drug-likeness:
    - Rotatable bonds ≤ 10
    - Polar Surface Area (PSA) ≤ 140

    Parameters:
        data (list of dict)

    Returns:
        tuple: (passed, failed)
    """
    passed = []
    failed = []

    for row in data:
        try:
            rb = int(row.get("rotatable_bonds", 0))
            psa = float(row.get("psa", 0))

            if rb <= 10 and psa <= 140:
                passed.append(row)
            else:
                failed.append(row)
        except (ValueError, TypeError):
            continue

    return passed, failed



def check_egan_rule(data):
    """
    Check Egan's rule:
    - logP ≤ 5.88
    - PSA ≤ 131.6

    Parameters:
        data (list of dict)

    Returns:
        tuple: (passed, failed)
    """
    passed = []
    failed = []

    for row in data:
        try:
            logp = float(row.get("logp", 0))
            psa = float(row.get("psa", 0))

            if logp <= 5.88 and psa <= 131.6:
                passed.append(row)
            else:
                failed.append(row)
        except (ValueError, TypeError):
            continue

    return passed, failed


def check_muegge_rule(row):
    try:
        mw = float(row.get("molecular_weight", 0))
        logp = float(row.get("logp", 0))
        tpsa = float(row.get("tpsa", 0))
        rings = int(row.get("ring_count", 0))
        carbon = int(row.get("carbon_count", 0))

        return (200 <= mw <= 600 and
                -2 <= logp <= 5 and
                tpsa <= 150 and
                rings <= 7 and
                carbon >= 4)
    except (ValueError, TypeError):
        return False


def check_ghose_filter(row):
    try:
        mw = float(row.get("molecular_weight", 0))
        logp = float(row.get("logp", 0))
        atoms = int(row.get("atom_count", 0))
        refractivity = float(row.get("molar_refractivity", 0))

        return (160 <= mw <= 480 and
                0.13 <= logp <= 5.6 and
                40 <= atoms <= 70 and
                20 <= refractivity <= 130)
    except (ValueError, TypeError):
        return False



def evaluate_drug_rules(data):
    results = []

    for row in data:
        compound_id = row.get("id", "unknown")

        result = {
            "id": compound_id,
            "Lipinski": check_lipinski_rule(row),
            "Ghose": check_ghose_filter(row),
            "Veber": check_veber_rule(row),
            "Egan": check_egan_rule(row),
            "Muegge": check_muegge_rule(row)
        }

        results.append(result)

    return results



