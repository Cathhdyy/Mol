import subprocess
import os
import json

VINA_PATH = r"C:\Users\sansk\MolCule\backend\vina\vina.exe"


# ============================
# Convert to PDBQT
# ============================
def convert_to_pdbqt(input_file, output_file, is_protein=False):

    if is_protein:
        command = [
            "obabel",
            input_file,
            "-O",
            output_file,
            "-xr",   # remove waters
            "-xh"    # add hydrogens
        ]
    else:
        command = [
            "obabel",
            input_file,
            "-O",
            output_file,
            "--gen3d",
            "-xh"
        ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"OpenBabel conversion failed:\n{result.stderr}")


# ============================
# Calculate Protein Center
# ============================
def calculate_protein_center(pdbqt_file):

    xs, ys, zs = [], [], []

    with open(pdbqt_file, "r") as f:
        for line in f:
            if line.startswith("ATOM") or line.startswith("HETATM"):
                try:
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    xs.append(x)
                    ys.append(y)
                    zs.append(z)
                except:
                    continue

    if not xs:
        raise ValueError("Could not calculate protein center — no atoms found.")

    center_x = sum(xs) / len(xs)
    center_y = sum(ys) / len(ys)
    center_z = sum(zs) / len(zs)

    return round(center_x, 3), round(center_y, 3), round(center_z, 3)


# ============================
# Run Docking
# ============================
def run_docking(ligand_path, protein_path, output_dir):

    ligand_pdbqt = os.path.join(output_dir, "ligand.pdbqt")
    protein_pdbqt = os.path.join(output_dir, "protein.pdbqt")
    output_pdbqt = os.path.join(output_dir, "docked.pdbqt")
    docked_pdb = os.path.join(output_dir, "docked.pdb")
    last_result_file = os.path.join(output_dir, "last_result.json")

    try:
        # Convert input structures
        convert_to_pdbqt(ligand_path, ligand_pdbqt, is_protein=False)
        convert_to_pdbqt(protein_path, protein_pdbqt, is_protein=True)

        # Calculate protein center
        center_x, center_y, center_z = calculate_protein_center(protein_pdbqt)

        # Run Vina
        command = [
            VINA_PATH,
            "--receptor", protein_pdbqt,
            "--ligand", ligand_pdbqt,
            "--center_x", str(center_x),
            "--center_y", str(center_y),
            "--center_z", str(center_z),
            "--size_x", "50",
            "--size_y", "50",
            "--size_z", "50",
            "--cpu", "1",
            "--exhaustiveness", "8",
            "--out", output_pdbqt
        ]

        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            return {
                "error": "Vina execution failed",
                "vina_stderr": result.stderr
            }

        # Convert docked output to PDB (for 3D viewer)
        subprocess.run(
            ["obabel", output_pdbqt, "-O", docked_pdb],
            capture_output=True,
            text=True
        )

        # Parse docking results safely
        docking_table = []

        for line in result.stdout.split("\n"):
            line = line.strip()
            parts = line.split()

            # Only accept real docking rows like:
            # 1   -5.286   0   0
            if len(parts) >= 2:
                if parts[0].isdigit() and parts[1].startswith("-"):
                    docking_table.append({
                        "mode": parts[0],
                        "affinity": parts[1]
                    })

        # Define binding energy properly
        binding_energy = docking_table[0]["affinity"] if docking_table else None

        # Save JSON for viewer energy display
        result_data = {
            "binding_energy_kcal_mol": binding_energy,
            "poses": docking_table
        }

        with open(last_result_file, "w") as f:
            json.dump(result_data, f)

        return {
            "binding_energy_kcal_mol": binding_energy,
            "grid_center": {
                "x": center_x,
                "y": center_y,
                "z": center_z
            },
            "poses": docking_table,
            "output_file": output_pdbqt,
            "vina_output": result.stdout,
            "visualization_file": docked_pdb
        }

    except Exception as e:
        return {
            "error": str(e)
        }