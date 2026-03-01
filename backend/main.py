from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from docking.protein_prep import prepare_protein
import os
from docking.docking_engine import run_docking
from docking.ligand_prep import prepare_ligand
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="Molecular Docking API")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Molecular Docking API Running"}

@app.post("/prepare-ligand/")
async def upload_ligand(file: UploadFile = File(...)):
    input_path = os.path.join(UPLOAD_DIR, "ligand_input.sdf")

    with open(input_path, "wb") as f:
        f.write(await file.read())

    output_path = os.path.join(UPLOAD_DIR, "prepared_ligand.sdf")

    prepare_ligand(input_path, output_path)

    return {"prepared_file": output_path}

@app.post("/prepare-protein/")
async def upload_protein(file: UploadFile = File(...)):
    input_path = os.path.join(UPLOAD_DIR, "protein_input.pdb")

    with open(input_path, "wb") as f:
        f.write(await file.read())

    output_path = os.path.join(UPLOAD_DIR, "prepared_protein.pdb")

    prepare_protein(input_path, output_path)

    return {"prepared_protein": output_path}

@app.post("/dock/")
async def dock():
    ligand_path = os.path.join(UPLOAD_DIR, "prepared_ligand.sdf")
    protein_path = os.path.join(UPLOAD_DIR, "prepared_protein.pdb")

    result = run_docking(ligand_path, protein_path, UPLOAD_DIR)

    return result

@app.get("/viewer")
def get_viewer():
    return FileResponse("viewer.html")