from pathlib import Path
from typing import Union, List, Optional

import yaml
from rdkit.Chem.rdchem import Mol

from boltz.data.parse.schema import parse_boltz_schema, parse_boltz_directory
from boltz.data.types import Target


def parse_yaml(
    path: Path,
    ccd: dict[str, Mol],
    mol_dir: Path,
    boltz2: bool = False,
    output_dir: Optional[Path] = None,
) -> Union[Target, List[Target]]:
    """Parse a Boltz input yaml / json file or directory.

    The input file should be a yaml file with the following format:

    sequences:
        - protein:
            id: A
            sequence: "MADQLTEEQIAEFKEAFSLF"
        - protein:
            id: [B, C]
            sequence: "AKLSILPWGHC"
        - rna:
            id: D
            sequence: "GCAUAGC"
        - ligand:
            id: E
            smiles: "CC1=CC=CC=C1"
        - ligand:
            id: [F, G]
            ccd: []
    constraints:
        - bond:
            atom1: [A, 1, CA]
            atom2: [A, 2, N]
        - pocket:
            binder: E
            contacts: [[B, 1], [B, 2]]
    templates:
        - path: /path/to/template.pdb
          ids: [A] # optional, specify which chains to template

    version: 1

    Parameters
    ----------
    path : Path
        Path to the YAML input file or directory containing YAML files.
    ccd : Dict
        Dictionary of CCD components.
    mol_dir : Path
        Path to the directory containing molecules.
    boltz2 : bool, optional
        Whether to parse the input for Boltz2.
    output_dir : Path, optional
        Path to the output directory where results will be saved.

    Returns
    -------
    Union[Target, List[Target]]
        The parsed target(s).

    """
    path = Path(path)
    
    if path.is_dir():
        return parse_boltz_directory(path, output_dir or path, ccd, mol_dir, boltz2)
    else:
        with path.open("r") as file:
            data = yaml.safe_load(file)
        name = path.stem
        return parse_boltz_schema(name, data, ccd, mol_dir, boltz2, output_dir)
