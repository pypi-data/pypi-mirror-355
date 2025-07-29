from pathlib import Path
from typing import Optional

from Bio import PDB
from Bio.Data.IUPACData import protein_letters_3to1
from rdkit import Chem
from rdkit.Chem.rdchem import Mol

from boltz.data.types import Target
from boltz.data.parse.yaml import parse_boltz_schema


def parse_pdb(
    path: Path,
    ccd: dict[str, Mol],
    mol_dir: Path,
    boltz2: bool = False,
) -> Target:
    """Parse a PDB file.

    Parameters
    ----------
    path : Path
        Path to the PDB file.
    ccd : Dict
        Dictionary of CCD components.
    mol_dir : Path
        Path to the directory containing the molecules.
    boltz2 : bool
        Whether to parse the input for Boltz2.

    Returns
    -------
    Target
        The parsed target.
    """
    # Read PDB file
    parser = PDB.PDBParser(QUIET=True)
    structure = parser.get_structure("protein", str(path))

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

    name = path.stem
    return parse_boltz_schema(name, data, ccd, mol_dir, boltz2) 