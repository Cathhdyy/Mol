from rdkit import Chem
from rdkit.Chem import AllChem
import os

def prepare_ligand(input_path: str, output_path: str):
    mol = Chem.MolFromMolFile(input_path, removeHs=False)

    if mol is None:
        raise ValueError("Invalid ligand file")

    # Add hydrogens
    mol = Chem.AddHs(mol)

    # Generate 3D conformer
    AllChem.EmbedMolecule(mol, AllChem.ETKDG())

    # Optimize geometry
    AllChem.UFFOptimizeMolecule(mol)

    # Save prepared ligand
    Chem.MolToMolFile(mol, output_path)

    return output_path