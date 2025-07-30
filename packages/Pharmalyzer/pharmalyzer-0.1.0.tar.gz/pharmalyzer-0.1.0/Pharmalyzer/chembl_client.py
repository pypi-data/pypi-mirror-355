"""
Pharmalyzer - ADME and Toxicity Screening Toolkit

Author: [Sorour Hassani]
Email: s.hassani@alum.semnan.ac.ir & sorour.hasani@gmail.com
License: MIT
"""
# Pharmalyzer/chembl_client.py

from chembl_webresource_client.new_client import new_client

class ChEMBLClient:
    """
    Class for accessing ChEMBL data via the official API.
    """

    def __init__(self):
        # Initialize molecule and activity clients
        self.molecule_client = new_client.molecule
        self.activity_client = new_client.activity

    def search_molecules(self, query, page_size=20):
        """
        Search for molecules based on name, InChIKey, or other fields.
        Returns a list of dictionaries with molecule information.

        Args:
            query (str): The search term (e.g., part of a molecule name or ID).
            page_size (int): Number of results to return (default 20).

        Returns:
            list: A list of dicts containing 'molecule_chembl_id', 'canonical_smiles', and 'pref_name'.
        """
        results = (
            self.molecule_client
            .filter(molecule_chembl_id__icontains=query)
            .only(['molecule_chembl_id', 'canonical_smiles', 'pref_name'])
            .order_by('molecule_chembl_id')
            .limit(page_size)
        )
        return list(results)

    def fetch_activity_by_target(self, target_chembl_id, activity_types=None, limit=100):
        """
        Retrieve activity data (e.g., IC50, Ki) for a specific target (e.g., CHEMBL25).
        Returns a list of dictionaries containing SMILES, activity type, value, and unit.

        Args:
            target_chembl_id (str): ChEMBL ID of the target (e.g., 'CHEMBL25').
            activity_types (str or list of str, optional): Activity type(s) to filter (e.g., "IC50", "Ki", or ["IC50", "Ki"]).
                                                             If None, retrieves all activity types.
            limit (int): Maximum number of records to retrieve (default 100).

        Returns:
            list: A list of dicts with keys 'smiles', 'activity_type', 'activity_value', and 'activity_unit'.
        """
        # If activity_types is a single string, convert it to a list
        if isinstance(activity_types, str):
            activity_types = [activity_types]

        # Start filtering by target
        query = self.activity_client.filter(target_chembl_id=target_chembl_id)

        # If specific activity types are requested, apply the 'standard_type__in' filter
        if activity_types:
            query = query.filter(standard_type__in=activity_types)

        # Retrieve only the desired fields
        records = (
            query
            .only(['canonical_smiles', 'standard_type', 'standard_value', 'standard_units'])
            .order_by('standard_value')
            .limit(limit)
        )

        dataset = []
        for entry in records:
            smiles = entry.get('canonical_smiles')
            act_type = entry.get('standard_type')
            value = entry.get('standard_value')
            unit = entry.get('standard_units')

            # Keep only entries with valid SMILES and numeric value, and accepted units
            if smiles and value and unit and unit.lower() in ['nm', 'µm', 'mm']:
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    continue
                dataset.append({
                    'smiles': smiles,
                    'activity_type': act_type,
                    'activity_value': float(value),
                    'activity_unit': unit
                })

        return dataset

    def fetch_molecule_by_chembl_id(self, chembl_id):
        """
        Retrieve full information for a molecule based on its ChEMBL ID (e.g., 'CHEMBL25').

        Args:
            chembl_id (str): The ChEMBL ID of the molecule.

        Returns:
            dict: A dictionary containing detailed molecule data.
        """
        return self.molecule_client.get(chembl_id)
