"""
Pharmalyzer - ADME and Toxicity Screening Toolkit

Author: [Sorour Hassani]
Email: s.hassani@alum.semnan.ac.ir & sorour.hasani@gmail.com
License: MIT
"""
# Pharmalyzer/qsar.py

import os
import pickle
import math
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

class QSARModel:
    """
    A generic QSAR trainer/predictor for multiple numeric properties.

    Given:
      - a list of dicts (or DataFrame rows) where each row has:
          'SMILES', <prop_1>, <prop_2>, ..., <prop_n>
      - a directory path to save models as '{property_name}_model.pkl'
    It will:
      - compute a fixed set of descriptors for each SMILES
      - for each property column, train a separate RandomForestRegressor
      - save each trained model as a .pkl file under the specified models directory
      - expose a `predict` method to load a saved model and predict for a new SMILES
    """

    def __init__(self, models_dir="qsar_models"):
        """
        Args:
            models_dir (str): folder where trained model pickles will be written/read.
        """
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)

    def compute_descriptors(self, smiles):
        """
        Compute a fixed set of descriptors from a SMILES string.
        Returns a list of descriptor values in consistent order.
        """
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None

        mw = Descriptors.MolWt(mol)
        logp = Descriptors.MolLogP(mol)
        tpsa = rdMolDescriptors.CalcTPSA(mol)
        hbd = Descriptors.NumHDonors(mol)
        hba = Descriptors.NumHAcceptors(mol)
        rot_bonds = Descriptors.NumRotatableBonds(mol)
        ring_count = mol.GetRingInfo().NumRings()
        heavy_atoms = mol.GetNumHeavyAtoms()

        return [
            mw,
            logp,
            tpsa,
            hbd,
            hba,
            rot_bonds,
            ring_count,
            heavy_atoms
        ]

    def prepare_dataset(self, rows, property_name):
        """
        Given an iterable of dict-like rows, extract:
          - X: list of descriptor lists
          - y: list of target values for property_name
        Skip any row where descriptors fail or property is missing/non-numeric.

        Args:
            rows: list of dicts (or DataFrame rows) with keys 'SMILES' and property_name
            property_name (str): column/key indicating the numeric target variable

        Returns:
            X_list (list of descriptor lists), y_list (list of floats)
        """
        X_list = []
        y_list = []
        for r in rows:
            smi = r.get("SMILES")
            if smi is None:
                continue
            desc = self._compute_descriptors(smi)
            if desc is None:
                continue
            if any(math.isnan(d) for d in desc):
                 print(f"[WARN] Skipping SMILES due to NaN descriptors: {smi}")
                 continue
            val = r.get(property_name)
            try:
                val_f = float(val)
            except (ValueError, TypeError):
                continue
            X_list.append(desc)
            y_list.append(val_f)
        return X_list, y_list

    def train_and_save(self, dataset_rows, property_names, test_size=0.2, random_state=42):
        """
        For each property in property_names, train a RandomForestRegressor
        and save the model to self.models_dir + "/{prop}_model.pkl".

        Args:
            dataset_rows (list of dicts): each dict must have 'SMILES' plus all properties
            property_names (list of str): list of column names to train on
            test_size (float): fraction for test split
            random_state (int): for reproducibility

        Returns:
            report (dict): for each property, a dict with train/test metrics
        """
        report = {}
        for prop in property_names:
            X, y = self._prepare_dataset(dataset_rows, prop)
            if len(X) < 10:
                report[prop] = {
                    "status": "skipped (insufficient data)",
                    "n_samples": len(X)
                }
                continue

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )

            model = RandomForestRegressor(n_estimators=100, random_state=random_state)
            model.fit(X_train, y_train)

            preds = model.predict(X_test)
            mse = mean_squared_error(y_test, preds)
            r2 = r2_score(y_test, preds)

            model_filename = os.path.join(self.models_dir, f"{prop}_model.pkl")
            with open(model_filename, "wb") as fout:
                pickle.dump(model, fout)

            report[prop] = {
                "status": "trained",
                "n_samples": len(X),
                "mse_test": mse,
                "r2_test": r2,
                "model_file": model_filename
            }

        return report

    def predict(self, property_name, smiles_list):
        """
        Load the saved model for property_name and predict values for each SMILES in smiles_list.

        Args:
            property_name (str): which property’s model to load (must match training name)
            smiles_list (list of str): list of SMILES strings to predict

        Returns:
            A list of predicted floats (same length as smiles_list). If a SMILES fails to parse,
            the corresponding output will be None.
        """
        model_path = os.path.join(self.models_dir, f"{property_name}_model.pkl")
        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        with open(model_path, "rb") as fin:
            model = pickle.load(fin)

        preds = []
        for smi in smiles_list:
            desc = self._compute_descriptors(smi)
            if desc is None:
                preds.append(None)
            else:
                preds.append(float(model.predict([desc])[0]))
        return preds

