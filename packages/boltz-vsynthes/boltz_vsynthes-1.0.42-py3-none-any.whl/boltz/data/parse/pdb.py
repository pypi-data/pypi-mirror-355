import os
from pathlib import Path
from typing import Optional

from Bio import PDB
from Bio.PDB.PDBParser import PDBParser
from Bio.PDB.Polypeptide import PPBuilder
from Bio.Data.IUPACData import protein_letters_3to1
from rdkit import Chem
from rdkit.Chem.rdchem import Mol

from boltz.data.types import Target
from boltz.data.parse.schema import parse_boltz_schema


def parse_pdb(
    pdb_path: Path,
    ccd: dict[str, Mol],
    mol_dir: Path,
    boltz2: bool = False,
) -> dict:
    """Parse a PDB file.

    Parameters
    ----------
    pdb_path : Path
        Path to the PDB file.
    ccd : Dict
        Dictionary of CCD components.
    mol_dir : Path
        Path to the directory containing the molecules.
    boltz2 : bool, optional
        Whether to use Boltz2 format, by default False.

    Returns
    -------
    dict
        Dictionary containing sequences and bonds.
    """
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