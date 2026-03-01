from Bio.PDB import PDBParser, PDBIO, Select
import os

class RemoveWater(Select):
    def accept_residue(self, residue):
        return residue.get_resname() != "HOH"

def prepare_protein(input_path: str, output_path: str):
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("protein", input_path)

    io = PDBIO()
    io.set_structure(structure)
    io.save(output_path, RemoveWater())

    return output_path