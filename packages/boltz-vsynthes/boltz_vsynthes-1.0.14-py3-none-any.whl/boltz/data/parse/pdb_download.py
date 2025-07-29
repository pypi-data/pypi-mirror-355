import os
from pathlib import Path
from typing import Optional

import requests
from Bio import PDB
from Bio.Data.IUPACData import protein_letters_3to1
from rdkit import Chem
from rdkit.Chem.rdchem import Mol

from boltz.data.types import Target
from boltz.data.parse.yaml import parse_boltz_schema


def download_pdb(pdb_id: str, cache_dir: Path) -> Path:
    """Download a PDB file by ID.

    Parameters
    ----------
    pdb_id : str
        The PDB ID to download.
    cache_dir : Path
        The directory to cache the downloaded file.

    Returns
    -------
    Path
        The path to the downloaded PDB file.
    """
    # Create cache directory if it doesn't exist
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if file already exists in cache
    pdb_path = cache_dir / f"{pdb_id.lower()}.pdb"
    if pdb_path.exists():
        return pdb_path
    
    # Download from RCSB PDB
    url = f"https://files.rcsb.org/download/{pdb_id.lower()}.pdb"
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    # Save to cache
    with pdb_path.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    return pdb_path


def parse_pdb_id(
    pdb_id: str,
    ccd: dict[str, Mol],
    mol_dir: Path,
    cache_dir: Path,
    boltz2: bool = False,
) -> Target:
    """Parse a PDB file by ID.

    Parameters
    ----------
    pdb_id : str
        The PDB ID to parse.
    ccd : Dict
        Dictionary of CCD components.
    mol_dir : Path
        Path to the directory containing the molecules.
    cache_dir : Path
        The directory to cache downloaded PDB files.
    boltz2 : bool
        Whether to parse the input for Boltz2.

    Returns
    -------
    Target
        The parsed target.
    """
    # Download PDB file
    pdb_path = download_pdb(pdb_id, cache_dir)
    
    # Read PDB file
    parser = PDB.PDBParser(QUIET=True)
    structure = parser.get_structure("protein", str(pdb_path))

    # Convert to yaml format
    sequences = []
    for model in structure:
        for chain in model:
            # Get chain sequence
            seq = ""
            for residue in chain:
                if residue.id[0] == " ":  # Only standard residues
                    try:
                        seq += protein_letters_3to1[residue.resname]
                    except KeyError:
                        continue

            if seq:  # Only add if sequence is not empty
                molecule = {
                    "protein": {
                        "id": chain.id,
                        "sequence": seq,
                        "modifications": [],
                    },
                }
                sequences.append(molecule)

    data = {
        "sequences": sequences,
        "bonds": [],
        "version": 1,
    }

    return parse_boltz_schema(pdb_id, data, ccd, mol_dir, boltz2) 