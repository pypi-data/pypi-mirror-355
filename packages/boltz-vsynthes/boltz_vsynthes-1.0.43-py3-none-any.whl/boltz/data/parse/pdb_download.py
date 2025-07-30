import os
from pathlib import Path
from typing import Optional

import requests
from Bio import PDB
from Bio.PDB.PDBParser import PDBParser
from Bio.PDB.Polypeptide import PPBuilder
from rdkit import Chem
from rdkit.Chem.rdchem import Mol

from boltz.data.types import Target
from boltz.data.parse.schema import parse_boltz_schema


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
) -> dict:
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
    boltz2 : bool, optional
        Whether to use Boltz2 format, by default False.

    Returns
    -------
    dict
        Dictionary containing sequences and bonds.
    """
    # Download PDB file
    pdb_path = download_pdb(pdb_id, cache_dir)

    # Read PDB file
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("protein", str(pdb_path))
    ppb = PPBuilder()

    # Convert to yaml format
    sequences = []
    for model in structure:
        for chain in model:
            for pp in ppb.build_peptides(chain):
                seq = str(pp.get_sequence())
                if seq:  # Only add if sequence is not empty
                    sequences.append({
                        "protein": {
                            "id": chain.id,
                            "sequence": seq,
                            "modifications": [],
                        }
                    })

    return {
        "sequences": sequences,
        "bonds": [],
        "version": 1,
    } 