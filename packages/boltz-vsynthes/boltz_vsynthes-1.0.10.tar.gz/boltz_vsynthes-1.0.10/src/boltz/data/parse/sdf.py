from pathlib import Path
from typing import Optional

from rdkit import Chem
from rdkit.Chem.rdchem import Mol

from boltz.data.types import Target
from boltz.data.parse.yaml import parse_boltz_schema


def parse_sdf(
    path: Path,
    ccd: dict[str, Mol],
    mol_dir: Path,
    boltz2: bool = False,
) -> Target:
    """Parse an SDF file.

    Parameters
    ----------
    path : Path
        Path to the SDF file.
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
    # Read SDF file
    supplier = Chem.SDMolSupplier(str(path))
    
    # Convert to yaml format
    sequences = []
    for i, mol in enumerate(supplier):
        if mol is not None:
            # Get SMILES
            smiles = Chem.MolToSmiles(mol)
            
            molecule = {
                "ligand": {
                    "id": f"L{i+1}",  # Use L1, L2, etc. as chain IDs
                    "smiles": smiles,
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