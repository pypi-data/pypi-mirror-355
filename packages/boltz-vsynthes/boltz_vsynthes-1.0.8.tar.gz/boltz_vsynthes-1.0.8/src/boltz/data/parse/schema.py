from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import click
import numpy as np
from Bio import Align
from chembl_structure_pipeline.exclude_flag import exclude_flag
from chembl_structure_pipeline.standardizer import standardize_mol
from rdkit import Chem, rdBase
from rdkit.Chem import AllChem, HybridizationType
from rdkit.Chem.MolStandardize import rdMolStandardize
from rdkit.Chem.rdchem import BondStereo, Conformer, Mol
from rdkit.Chem.rdDistGeom import GetMoleculeBoundsMatrix
from rdkit.Chem.rdMolDescriptors import CalcNumHeavyAtoms
from scipy.optimize import linear_sum_assignment

from boltz.data import const
from boltz.data.mol import load_molecules
from boltz.data.parse.mmcif import parse_mmcif
from boltz.data.types import (
    AffinityInfo,
    Atom,
    AtomV2,
    Bond,
    BondV2,
    Chain,
    ChainInfo,
    ChiralAtomConstraint,
    Connection,
    Coords,
    Ensemble,
    InferenceOptions,
    Interface,
    PlanarBondConstraint,
    PlanarRing5Constraint,
    PlanarRing6Constraint,
    RDKitBoundsConstraint,
    Record,
    Residue,
    ResidueConstraints,
    StereoBondConstraint,
    Structure,
    StructureInfo,
    StructureV2,
    Target,
    TemplateInfo,
)

####################################################################################################
# DATACLASSES
####################################################################################################


@dataclass(frozen=True)
class ParsedAtom:
    """A parsed atom object."""

    name: str
    element: int
    charge: int
    coords: tuple[float, float, float]
    conformer: tuple[float, float, float]
    is_present: bool
    chirality: int


@dataclass(frozen=True)
class ParsedBond:
    """A parsed bond object."""

    atom_1: int
    atom_2: int
    type: int


@dataclass(frozen=True)
class ParsedRDKitBoundsConstraint:
    """A parsed RDKit bounds constraint object."""

    atom_idxs: tuple[int, int]
    is_bond: bool
    is_angle: bool
    upper_bound: float
    lower_bound: float


@dataclass(frozen=True)
class ParsedChiralAtomConstraint:
    """A parsed chiral atom constraint object."""

    atom_idxs: tuple[int, int, int, int]
    is_reference: bool
    is_r: bool


@dataclass(frozen=True)
class ParsedStereoBondConstraint:
    """A parsed stereo bond constraint object."""

    atom_idxs: tuple[int, int, int, int]
    is_check: bool
    is_e: bool


@dataclass(frozen=True)
class ParsedPlanarBondConstraint:
    """A parsed planar bond constraint object."""

    atom_idxs: tuple[int, int, int, int, int, int]


@dataclass(frozen=True)
class ParsedPlanarRing5Constraint:
    """A parsed planar bond constraint object."""

    atom_idxs: tuple[int, int, int, int, int]


@dataclass(frozen=True)
class ParsedPlanarRing6Constraint:
    """A parsed planar bond constraint object."""

    atom_idxs: tuple[int, int, int, int, int, int]


@dataclass(frozen=True)
class ParsedResidue:
    """A parsed residue object."""

    name: str
    type: int
    idx: int
    atoms: list[ParsedAtom]
    bonds: list[ParsedBond]
    orig_idx: Optional[int]
    atom_center: int
    atom_disto: int
    is_standard: bool
    is_present: bool
    rdkit_bounds_constraints: Optional[list[ParsedRDKitBoundsConstraint]] = None
    chiral_atom_constraints: Optional[list[ParsedChiralAtomConstraint]] = None
    stereo_bond_constraints: Optional[list[ParsedStereoBondConstraint]] = None
    planar_bond_constraints: Optional[list[ParsedPlanarBondConstraint]] = None
    planar_ring_5_constraints: Optional[list[ParsedPlanarRing5Constraint]] = None
    planar_ring_6_constraints: Optional[list[ParsedPlanarRing6Constraint]] = None


@dataclass(frozen=True)
class ParsedChain:
    """A parsed chain object."""

    entity: str
    type: int
    residues: list[ParsedResidue]
    cyclic_period: int
    sequence: Optional[str] = None
    affinity: Optional[bool] = False
    affinity_mw: Optional[float] = None


@dataclass(frozen=True)
class Alignment:
    """A parsed alignment object."""

    query_st: int
    query_en: int
    template_st: int
    template_en: int


####################################################################################################
# HELPERS
####################################################################################################


def convert_atom_name(name: str) -> tuple[int, int, int, int]:
    """Convert an atom name to a standard format.

    Parameters
    ----------
    name : str
        The atom name.

    Returns
    -------
    Tuple[int, int, int, int]
        The converted atom name.

    """
    name = name.strip()
    name = [ord(c) - 32 for c in name]
    name = name + [0] * (4 - len(name))
    return tuple(name)


def compute_3d_conformer(mol: Mol, version: str = "v3") -> bool:
    """Generate 3D coordinates using EKTDG method.

    Taken from `pdbeccdutils.core.component.Component`.

    Parameters
    ----------
    mol: Mol
        The RDKit molecule to process
    version: str, optional
        The ETKDG version, defaults ot v3

    Returns
    -------
    bool
        Whether computation was successful.

    """
    if version == "v3":
        options = AllChem.ETKDGv3()
    elif version == "v2":
        options = AllChem.ETKDGv2()
    else:
        options = AllChem.ETKDGv2()

    options.clearConfs = False
    conf_id = -1

    try:
        conf_id = AllChem.EmbedMolecule(mol, options)

        if conf_id == -1:
            print(
                f"WARNING: RDKit ETKDGv3 failed to generate a conformer for molecule "
                f"{Chem.MolToSmiles(AllChem.RemoveHs(mol))}, so the program will start with random coordinates. "
                f"Note that the performance of the model under this behaviour was not tested."
            )
            options.useRandomCoords = True
            conf_id = AllChem.EmbedMolecule(mol, options)

        AllChem.UFFOptimizeMolecule(mol, confId=conf_id, maxIters=1000)

    except RuntimeError:
        pass  # Force field issue here
    except ValueError:
        pass  # sanitization issue here

    if conf_id != -1:
        conformer = mol.GetConformer(conf_id)
        conformer.SetProp("name", "Computed")
        conformer.SetProp("coord_generation", f"ETKDG{version}")

        return True

    return False


def get_conformer(mol: Mol) -> Conformer:
    """Retrieve an rdkit object for a deemed conformer.

    Inspired by `pdbeccdutils.core.component.Component`.

    Parameters
    ----------
    mol: Mol
        The molecule to process.

    Returns
    -------
    Conformer
        The desired conformer, if any.

    Raises
    ------
    ValueError
        If there are no conformers of the given tyoe.

    """
    # Try using the computed conformer
    for c in mol.GetConformers():
        try:
            if c.GetProp("name") == "Computed":
                return c
        except KeyError:  # noqa: PERF203
            pass

    # Fallback to the ideal coordinates
    for c in mol.GetConformers():
        try:
            if c.GetProp("name") == "Ideal":
                return c
        except KeyError:  # noqa: PERF203
            pass

    # Fallback to boltz2 format
    conf_ids = [int(conf.GetId()) for conf in mol.GetConformers()]
    if len(conf_ids) > 0:
        conf_id = conf_ids[0]
        conformer = mol.GetConformer(conf_id)
        return conformer

    msg = "Conformer does not exist."
    raise ValueError(msg)


def compute_geometry_constraints(mol: Mol, idx_map):
    if mol.GetNumAtoms() <= 1:
        return []

    # Ensure RingInfo is initialized
    mol.UpdatePropertyCache(strict=False)
    Chem.GetSymmSSSR(mol)  # Compute ring information

    bounds = GetMoleculeBoundsMatrix(
        mol,
        set15bounds=True,
        scaleVDW=True,
        doTriangleSmoothing=True,
        useMacrocycle14config=False,
    )
    bonds = set(
        tuple(sorted(b)) for b in mol.GetSubstructMatches(Chem.MolFromSmarts("*~*"))
    )
    angles = set(
        tuple(sorted([a[0], a[2]]))
        for a in mol.GetSubstructMatches(Chem.MolFromSmarts("*~*~*"))
    )

    constraints = []
    for i, j in zip(*np.triu_indices(mol.GetNumAtoms(), k=1)):
        if i in idx_map and j in idx_map:
            constraint = ParsedRDKitBoundsConstraint(
                atom_idxs=(idx_map[i], idx_map[j]),
                is_bond=tuple(sorted([i, j])) in bonds,
                is_angle=tuple(sorted([i, j])) in angles,
                upper_bound=bounds[i, j],
                lower_bound=bounds[j, i],
            )
            constraints.append(constraint)
    return constraints


def compute_chiral_atom_constraints(mol, idx_map):
    constraints = []
    if all([atom.HasProp("_CIPRank") for atom in mol.GetAtoms()]):
        for center_idx, orientation in Chem.FindMolChiralCenters(
            mol, includeUnassigned=False
        ):
            center = mol.GetAtomWithIdx(center_idx)
            neighbors = [
                (neighbor.GetIdx(), int(neighbor.GetProp("_CIPRank")))
                for neighbor in center.GetNeighbors()
            ]
            neighbors = sorted(
                neighbors, key=lambda neighbor: neighbor[1], reverse=True
            )
            neighbors = tuple(neighbor[0] for neighbor in neighbors)
            is_r = orientation == "R"

            if len(neighbors) > 4 or center.GetHybridization() != HybridizationType.SP3:
                continue

            atom_idxs = (*neighbors[:3], center_idx)
            if all(i in idx_map for i in atom_idxs):
                constraints.append(
                    ParsedChiralAtomConstraint(
                        atom_idxs=tuple(idx_map[i] for i in atom_idxs),
                        is_reference=True,
                        is_r=is_r,
                    )
                )

            if len(neighbors) == 4:
                for skip_idx in range(3):
                    chiral_set = neighbors[:skip_idx] + neighbors[skip_idx + 1 :]
                    if skip_idx % 2 == 0:
                        atom_idxs = chiral_set[::-1] + (center_idx,)
                    else:
                        atom_idxs = chiral_set + (center_idx,)
                    if all(i in idx_map for i in atom_idxs):
                        constraints.append(
                            ParsedChiralAtomConstraint(
                                atom_idxs=tuple(idx_map[i] for i in atom_idxs),
                                is_reference=False,
                                is_r=is_r,
                            )
                        )
    return constraints


def compute_stereo_bond_constraints(mol, idx_map):
    constraints = []
    if all([atom.HasProp("_CIPRank") for atom in mol.GetAtoms()]):
        for bond in mol.GetBonds():
            stereo = bond.GetStereo()
            if stereo in {BondStereo.STEREOE, BondStereo.STEREOZ}:
                start_atom_idx, end_atom_idx = (
                    bond.GetBeginAtomIdx(),
                    bond.GetEndAtomIdx(),
                )
                start_neighbors = [
                    (neighbor.GetIdx(), int(neighbor.GetProp("_CIPRank")))
                    for neighbor in mol.GetAtomWithIdx(start_atom_idx).GetNeighbors()
                    if neighbor.GetIdx() != end_atom_idx
                ]
                start_neighbors = sorted(
                    start_neighbors, key=lambda neighbor: neighbor[1], reverse=True
                )
                start_neighbors = [neighbor[0] for neighbor in start_neighbors]
                end_neighbors = [
                    (neighbor.GetIdx(), int(neighbor.GetProp("_CIPRank")))
                    for neighbor in mol.GetAtomWithIdx(end_atom_idx).GetNeighbors()
                    if neighbor.GetIdx() != start_atom_idx
                ]
                end_neighbors = sorted(
                    end_neighbors, key=lambda neighbor: neighbor[1], reverse=True
                )
                end_neighbors = [neighbor[0] for neighbor in end_neighbors]
                is_e = stereo == BondStereo.STEREOE

                atom_idxs = (
                    start_neighbors[0],
                    start_atom_idx,
                    end_atom_idx,
                    end_neighbors[0],
                )
                if all(i in idx_map for i in atom_idxs):
                    constraints.append(
                        ParsedStereoBondConstraint(
                            atom_idxs=tuple(idx_map[i] for i in atom_idxs),
                            is_check=True,
                            is_e=is_e,
                        )
                    )

                if len(start_neighbors) == 2 and len(end_neighbors) == 2:
                    atom_idxs = (
                        start_neighbors[1],
                        start_atom_idx,
                        end_atom_idx,
                        end_neighbors[1],
                    )
                    if all(i in idx_map for i in atom_idxs):
                        constraints.append(
                            ParsedStereoBondConstraint(
                                atom_idxs=tuple(idx_map[i] for i in atom_idxs),
                                is_check=False,
                                is_e=is_e,
                            )
                        )
    return constraints


def compute_flatness_constraints(mol, idx_map):
    planar_double_bond_smarts = Chem.MolFromSmarts("[C;X3;^2](*)(*)=[C;X3;^2](*)(*)")
    aromatic_ring_5_smarts = Chem.MolFromSmarts("[ar5^2]1[ar5^2][ar5^2][ar5^2][ar5^2]1")
    aromatic_ring_6_smarts = Chem.MolFromSmarts(
        "[ar6^2]1[ar6^2][ar6^2][ar6^2][ar6^2][ar6^2]1"
    )

    planar_double_bond_constraints = []
    aromatic_ring_5_constraints = []
    aromatic_ring_6_constraints = []
    for match in mol.GetSubstructMatches(planar_double_bond_smarts):
        if all(i in idx_map for i in match):
            planar_double_bond_constraints.append(
                ParsedPlanarBondConstraint(atom_idxs=tuple(idx_map[i] for i in match))
            )
    for match in mol.GetSubstructMatches(aromatic_ring_5_smarts):
        if all(i in idx_map for i in match):
            aromatic_ring_5_constraints.append(
                ParsedPlanarRing5Constraint(atom_idxs=tuple(idx_map[i] for i in match))
            )
    for match in mol.GetSubstructMatches(aromatic_ring_6_smarts):
        if all(i in idx_map for i in match):
            aromatic_ring_6_constraints.append(
                ParsedPlanarRing6Constraint(atom_idxs=tuple(idx_map[i] for i in match))
            )

    return (
        planar_double_bond_constraints,
        aromatic_ring_5_constraints,
        aromatic_ring_6_constraints,
    )


def get_global_alignment_score(query: str, template: str) -> float:
    """Align a sequence to a template.

    Parameters
    ----------
    query : str
        The query sequence.
    template : str
        The template sequence.

    Returns
    -------
    float
        The global alignment score.

    """
    aligner = Align.PairwiseAligner(scoring="blastp")
    aligner.mode = "global"
    score = aligner.align(query, template)[0].score
    return score


def get_local_alignments(query: str, template: str) -> list[Alignment]:
    """Align a sequence to a template.

    Parameters
    ----------
    query : str
        The query sequence.
    template : str
        The template sequence.

    Returns
    -------
    Alignment
        The alignment between the query and template.

    """
    aligner = Align.PairwiseAligner(scoring="blastp")
    aligner.mode = "local"
    aligner.open_gap_score = -1000
    aligner.extend_gap_score = -1000

    alignments = []
    for result in aligner.align(query, template):
        coordinates = result.coordinates
        alignment = Alignment(
            query_st=int(coordinates[0][0]),
            query_en=int(coordinates[0][1]),
            template_st=int(coordinates[1][0]),
            template_en=int(coordinates[1][1]),
        )
        alignments.append(alignment)

    return alignments


def get_template_records_from_search(
    template_id: str,
    chain_ids: list[str],
    sequences: dict[str, str],
    template_chain_ids: list[str],
    template_sequences: dict[str, str],
) -> list[TemplateInfo]:
    """Get template records from an alignment."""
    # Compute pairwise scores
    score_matrix = []
    for chain_id in chain_ids:
        row = []
        for template_chain_id in template_chain_ids:
            chain_seq = sequences[chain_id]
            template_seq = template_sequences[template_chain_id]
            score = get_global_alignment_score(chain_seq, template_seq)
            row.append(score)
        score_matrix.append(row)

    # Find optimal mapping
    row_ind, col_ind = linear_sum_assignment(score_matrix, maximize=True)

    # Get alignment records
    template_records = []

    for row_idx, col_idx in zip(row_ind, col_ind):
        chain_id = chain_ids[row_idx]
        template_chain_id = template_chain_ids[col_idx]
        chain_seq = sequences[chain_id]
        template_seq = template_sequences[template_chain_id]
        alignments = get_local_alignments(chain_seq, template_seq)

        for alignment in alignments:
            template_record = TemplateInfo(
                name=template_id,
                query_chain=chain_id,
                query_st=alignment.query_st,
                query_en=alignment.query_en,
                template_chain=template_chain_id,
                template_st=alignment.template_st,
                template_en=alignment.template_en,
            )
            template_records.append(template_record)

    return template_records


def get_template_records_from_matching(
    template_id: str,
    chain_ids: list[str],
    sequences: dict[str, str],
    template_chain_ids: list[str],
    template_sequences: dict[str, str],
) -> list[TemplateInfo]:
    """Get template records from a given matching."""
    template_records = []

    for chain_id, template_chain_id in zip(chain_ids, template_chain_ids):
        # Align the sequences
        chain_seq = sequences[chain_id]
        template_seq = template_sequences[template_chain_id]
        alignments = get_local_alignments(chain_seq, template_seq)
        for alignment in alignments:
            template_record = TemplateInfo(
                name=template_id,
                query_chain=chain_id,
                query_st=alignment.query_st,
                query_en=alignment.query_en,
                template_chain=template_chain_id,
                template_st=alignment.template_st,
                template_en=alignment.template_en,
            )
            template_records.append(template_record)

    return template_records


def get_mol(ccd: str, mols: dict, moldir: str) -> Mol:
    """Get mol from CCD code.

    Return mol with ccd from mols if it is in mols. Otherwise load it from moldir,
    add it to mols, and return the mol.
    """
    # Skip if it's a SMILES string (starts with LIG)
    if ccd.startswith("LIG"):
        return None
    mol = mols.get(ccd)
    if mol is None:
        mol = load_molecules(moldir, [ccd])[ccd]
    return mol


####################################################################################################
# PARSING
####################################################################################################


def parse_ccd_residue(
    name: str, ref_mol: Mol, res_idx: int, drop_leaving_atoms: bool = False
) -> Optional[ParsedResidue]:
    """Parse an MMCIF ligand.

    First tries to get the SMILES string from the RCSB.
    Then, tries to infer atom ordering using RDKit.

    Parameters
    ----------
    name: str
        The name of the molecule to parse.
    ref_mol: Mol
        The reference molecule to parse.
    res_idx : int
        The residue index.

    Returns
    -------
    ParsedResidue, optional
       The output ParsedResidue, if successful.

    """
    # Skip if it's a SMILES string (starts with LIG)
    if name.startswith("LIG"):
        return None
        
    unk_chirality = const.chirality_type_ids[const.unk_chirality_type]

    # Check if this is a single heavy atom CCD residue
    if CalcNumHeavyAtoms(ref_mol) == 1:
        # Remove hydrogens
        ref_mol = AllChem.RemoveHs(ref_mol, sanitize=False)

        pos = (0, 0, 0)
        ref_atom = ref_mol.GetAtoms()[0]
        chirality_type = const.chirality_type_ids.get(
            str(ref_atom.GetChiralTag()), unk_chirality
        )
        atom = ParsedAtom(
            name=ref_atom.GetProp("name"),
            element=ref_atom.GetAtomicNum(),
            charge=ref_atom.GetFormalCharge(),
            coords=pos,
            conformer=(0, 0, 0),
            is_present=True,
            chirality=chirality_type,
        )
        unk_prot_id = const.unk_token_ids["PROTEIN"]
        residue = ParsedResidue(
            name=name,
            type=unk_prot_id,
            atoms=[atom],
            bonds=[],
            idx=res_idx,
            orig_idx=None,
            atom_center=0,  # Placeholder, no center
            atom_disto=0,  # Placeholder, no center
            is_standard=False,
            is_present=True,
        )
        return residue

    # Get reference conformer coordinates
    conformer = get_conformer(ref_mol)

    # Parse each atom in order of the reference mol
    atoms = []
    atom_idx = 0
    idx_map = {}  # Used for bonds later

    for i, atom in enumerate(ref_mol.GetAtoms()):
        # Ignore Hydrogen atoms
        if atom.GetAtomicNum() == 1:
            continue

        # Get atom name, charge, element and reference coordinates
        atom_name = atom.GetProp("name")

        # Drop leaving atoms for non-canonical amino acids.
        if drop_leaving_atoms and int(atom.GetProp('leaving_atom')):
            continue

        charge = atom.GetFormalCharge()
        element = atom.GetAtomicNum()
        ref_coords = conformer.GetAtomPosition(atom.GetIdx())
        ref_coords = (ref_coords.x, ref_coords.y, ref_coords.z)
        chirality_type = const.chirality_type_ids.get(
            str(atom.GetChiralTag()), unk_chirality
        )

        # Get PDB coordinates, if any
        coords = (0, 0, 0)
        atom_is_present = True

        # Add atom to list
        atoms.append(
            ParsedAtom(
                name=atom_name,
                element=element,
                charge=charge,
                coords=coords,
                conformer=ref_coords,
                is_present=atom_is_present,
                chirality=chirality_type,
            )
        )
        idx_map[i] = atom_idx
        atom_idx += 1

    # Load bonds
    bonds = []
    unk_bond = const.bond_type_ids[const.unk_bond_type]
    for bond in ref_mol.GetBonds():
        idx_1 = bond.GetBeginAtomIdx()
        idx_2 = bond.GetEndAtomIdx()

        # Skip bonds with atoms ignored
        if (idx_1 not in idx_map) or (idx_2 not in idx_map):
            continue

        idx_1 = idx_map[idx_1]
        idx_2 = idx_map[idx_2]
        start = min(idx_1, idx_2)
        end = max(idx_1, idx_2)
        bond_type = bond.GetBondType().name
        bond_type = const.bond_type_ids.get(bond_type, unk_bond)
        bonds.append(ParsedBond(start, end, bond_type))

    rdkit_bounds_constraints = compute_geometry_constraints(ref_mol, idx_map)
    chiral_atom_constraints = compute_chiral_atom_constraints(ref_mol, idx_map)
    stereo_bond_constraints = compute_stereo_bond_constraints(ref_mol, idx_map)
    planar_bond_constraints, planar_ring_5_constraints, planar_ring_6_constraints = (
        compute_flatness_constraints(ref_mol, idx_map)
    )

    unk_prot_id = const.unk_token_ids["PROTEIN"]
    return ParsedResidue(
        name=name,
        type=unk_prot_id,
        atoms=atoms,
        bonds=bonds,
        idx=res_idx,
        atom_center=0,
        atom_disto=0,
        orig_idx=None,
        is_standard=False,
        is_present=True,
        rdkit_bounds_constraints=rdkit_bounds_constraints,
        chiral_atom_constraints=chiral_atom_constraints,
        stereo_bond_constraints=stereo_bond_constraints,
        planar_bond_constraints=planar_bond_constraints,
        planar_ring_5_constraints=planar_ring_5_constraints,
        planar_ring_6_constraints=planar_ring_6_constraints,
    )


def parse_polymer(
    sequence: list[str],
    raw_sequence: str,
    entity: str,
    chain_type: str,
    components: dict[str, Mol],
    cyclic: bool,
    mol_dir: Path,
) -> Optional[ParsedChain]:
    """Process a sequence into a chain object.

    Performs alignment of the full sequence to the polymer
    residues. Loads coordinates and masks for the atoms in
    the polymer, following the ordering in const.atom_order.

    Parameters
    ----------
    sequence : list[str]
        The full sequence of the polymer.
    entity : str
        The entity id.
    entity_type : str
        The entity type.
    components : dict[str, Mol]
        The preprocessed PDB components dictionary.

    Returns
    -------
    ParsedChain, optional
        The output chain, if successful.

    Raises
    ------
    ValueError
        If the alignment fails.

    """
    ref_res = set(const.tokens)
    unk_chirality = const.chirality_type_ids[const.unk_chirality_type]

    # Get coordinates and masks
    parsed = []
    for res_idx, res_name in enumerate(sequence):
        # Check if modified residue
        # Map MSE to MET
        res_corrected = res_name if res_name != "MSE" else "MET"

        # Handle non-standard residues
        if res_corrected not in ref_res:
            ref_mol = get_mol(res_corrected, components, mol_dir)
            residue = parse_ccd_residue(
                name=res_corrected,
                ref_mol=ref_mol,
                res_idx=res_idx,
                drop_leaving_atoms=True,
            )
            parsed.append(residue)
            continue

        # Load ref residue
        ref_mol = get_mol(res_corrected, components, mol_dir)
        ref_mol = AllChem.RemoveHs(ref_mol, sanitize=False)
        ref_conformer = get_conformer(ref_mol)

        # Only use reference atoms set in constants
        ref_name_to_atom = {a.GetProp("name"): a for a in ref_mol.GetAtoms()}
        ref_atoms = [ref_name_to_atom[a] for a in const.ref_atoms[res_corrected]]

        # Iterate, always in the same order
        atoms: list[ParsedAtom] = []

        for ref_atom in ref_atoms:
            # Get atom name
            atom_name = ref_atom.GetProp("name")
            idx = ref_atom.GetIdx()

            # Get conformer coordinates
            ref_coords = ref_conformer.GetAtomPosition(idx)
            ref_coords = (ref_coords.x, ref_coords.y, ref_coords.z)

            # Set 0 coordinate
            atom_is_present = True
            coords = (0, 0, 0)

            # Add atom to list
            atoms.append(
                ParsedAtom(
                    name=atom_name,
                    element=ref_atom.GetAtomicNum(),
                    charge=ref_atom.GetFormalCharge(),
                    coords=coords,
                    conformer=ref_coords,
                    is_present=atom_is_present,
                    chirality=const.chirality_type_ids.get(
                        str(ref_atom.GetChiralTag()), unk_chirality
                    ),
                )
            )

        atom_center = const.res_to_center_atom_id[res_corrected]
        atom_disto = const.res_to_disto_atom_id[res_corrected]
        parsed.append(
            ParsedResidue(
                name=res_corrected,
                type=const.token_ids[res_corrected],
                atoms=atoms,
                bonds=[],
                idx=res_idx,
                atom_center=atom_center,
                atom_disto=atom_disto,
                is_standard=True,
                is_present=True,
                orig_idx=None,
            )
        )

    if cyclic:
        cyclic_period = len(sequence)
    else:
        cyclic_period = 0

    # Return polymer object
    return ParsedChain(
        entity=entity,
        residues=parsed,
        type=chain_type,
        cyclic_period=cyclic_period,
        sequence=raw_sequence,
    )


def token_spec_to_ids(
    chain_name, residue_index_or_atom_name, chain_to_idx, atom_idx_map, chains
):
    # TODO: unfinished
    if chains[chain_name].type == const.chain_type_ids["NONPOLYMER"]:
        # Non-polymer chains are indexed by atom name
        _, _, atom_idx = atom_idx_map[(chain_name, 0, residue_index_or_atom_name)]
        return (chain_to_idx[chain_name], atom_idx)
    else:
        # Polymer chains are indexed by residue index
        contacts.append((chain_to_idx[chain_name], residue_index_or_atom_name - 1))


def parse_boltz_schema(schema: dict) -> dict:
    """Parse the Boltz input schema.

    Parameters
    ----------
    schema : dict
        The input schema.

    Returns
    -------
    dict
        The parsed schema.

    """
    # Check version
    if "version" not in schema:
        msg = "Schema must have a version field"
        raise ValueError(msg)

    # Group items by entity type and sequence
    items_to_group = {}
    chain_name_to_entity_type = {}

    # Keep track of ligand IDs
    ligand_id = 1
    ligand_id_map = {}

    # Parse sequences
    for item in schema["sequences"]:
        entity_type = list(item.keys())[0]
        entity_id = item[entity_type]["id"]
        entity_id = [entity_id] if isinstance(entity_id, str) else entity_id

        # Get sequence
        if entity_type == "protein":
            if "sequence" in item[entity_type]:
                seq = item[entity_type]["sequence"]
            elif "pdb" in item[entity_type]:
                pdb_input = item[entity_type]["pdb"]
                if pdb_input.startswith(("http://", "https://")):
                    # It's a PDB ID
                    import requests
                    response = requests.get(f"https://files.rcsb.org/download/{pdb_input}.pdb")
                    if response.status_code != 200:
                        msg = f"Failed to download PDB file: {pdb_input}"
                        raise FileNotFoundError(msg)
                    pdb_data = response.text
                else:
                    # It's a file path
                    pdb_path = Path(pdb_input)
                    if not pdb_path.exists():
                        msg = f"PDB file not found: {pdb_path}"
                        raise FileNotFoundError(msg)
                    with pdb_path.open("r") as f:
                        pdb_data = f.read()

                # Parse PDB data
                from Bio.PDB import PDBParser
                from io import StringIO
                parser = PDBParser()
                structure = parser.get_structure("protein", StringIO(pdb_data))
                
                # Extract sequence
                seq = ""
                for model in structure:
                    for chain in model:
                        for residue in chain:
                            if residue.id[0] == " ":  # Only standard residues
                                seq += residue.resname
                seq = "".join(seq)
            else:
                msg = "Protein must have either 'sequence' or 'pdb' field"
                raise ValueError(msg)
        elif entity_type == "ligand":
            # Support for SMILES, CCD, and SDF
            if "smiles" in item[entity_type]:
                seq = str(item[entity_type]["smiles"])
                # Map user-provided ID to internal LIG1, LIG2, etc.
                for id in entity_id:
                    ligand_id_map[id] = f"LIG{ligand_id}"
                ligand_id += 1
            elif "ccd" in item[entity_type]:
                seq = str(item[entity_type]["ccd"])
                # For CCD ligands, use the CCD code as the internal ID
                for id in entity_id:
                    ligand_id_map[id] = seq
            elif "sdf" in item[entity_type]:
                sdf_path = Path(item[entity_type]["sdf"])
                if not sdf_path.exists():
                    msg = f"SDF file not found: {sdf_path}"
                    raise FileNotFoundError(msg)
                # Read SDF and convert to SMILES
                from rdkit import Chem
                mol = Chem.SDMolSupplier(str(sdf_path))[0]
                if mol is None:
                    msg = f"Failed to read SDF file: {sdf_path}"
                    raise ValueError(msg)
                seq = Chem.MolToSmiles(mol)
                # Map user-provided ID to internal LIG1, LIG2, etc.
                for id in entity_id:
                    ligand_id_map[id] = f"LIG{ligand_id}"
                ligand_id += 1
            else:
                msg = "Ligand must have either 'smiles', 'ccd', or 'sdf' field"
                raise ValueError(msg)

        # Group items by entity
        items_to_group.setdefault((entity_type, seq), []).append(item)

        # Map chain names to entity types
        chain_names = item[entity_type]["id"]
        chain_names = [chain_names] if isinstance(chain_names, str) else chain_names
        for chain_name in chain_names:
            chain_name_to_entity_type[chain_name] = entity_type

    # Get all proteins and ligands
    proteins = []
    ligands = []
    for item in schema["sequences"]:
        entity_type = list(item.keys())[0]
        entity_id = item[entity_type]["id"]
        entity_id = [entity_id] if isinstance(entity_id, str) else entity_id
        if entity_type == "protein":
            proteins.extend(entity_id)
        elif entity_type == "ligand":
            ligands.extend(entity_id)

    # Generate properties for each protein-ligand pair
    new_properties = []
    for prop in schema.get("properties", []):
        if "affinity" in prop:
            affinity = prop["affinity"]
            # Handle protein as binder
            if "protein" in affinity:
                binder = affinity["protein"]
                if binder not in proteins:
                    msg = f"Protein {binder} not found in sequences"
                    raise ValueError(msg)
                # Generate pairs with all ligands
                for ligand in ligands:
                    if ligand in ligand_id_map:
                        ligand = ligand_id_map[ligand]  # Convert to internal LIG1, LIG2, etc.
                    new_properties.append({
                        "affinity": {
                            "binder": binder,
                            "ligand": ligand
                        }
                    })
            # Handle ligand as binder (backward compatibility)
            elif "binder" in affinity:
                binder = affinity["binder"]
                if binder not in proteins:
                    msg = f"Protein {binder} not found in sequences"
                    raise ValueError(msg)
                # Generate pairs with all ligands
                for ligand in ligands:
                    if ligand in ligand_id_map:
                        ligand = ligand_id_map[ligand]  # Convert to internal LIG1, LIG2, etc.
                    new_properties.append({
                        "affinity": {
                            "binder": binder,
                            "ligand": ligand
                        }
                    })

    # Update schema with generated properties
    schema["properties"] = new_properties

    return schema


def standardize(smiles: str) -> Optional[str]:
    """Standardize a molecule and return its SMILES and a flag indicating whether the molecule is valid.
    This version has exception handling, which the original in mol-finder/data doesn't have. I didn't change the mol-finder/data
    since there are a lot of other functions that depend on it and I didn't want to break them.
    """
    LARGEST_FRAGMENT_CHOOSER = rdMolStandardize.LargestFragmentChooser()

    mol = Chem.MolFromSmiles(smiles, sanitize=False)

    exclude = exclude_flag(mol, includeRDKitSanitization=False)

    if exclude:
        raise ValueError("Molecule is excluded")

    # Standardize with ChEMBL data curation pipeline. During standardization, the molecule may be broken
    # Choose molecule with largest component
    mol = LARGEST_FRAGMENT_CHOOSER.choose(mol)
    # Standardize with ChEMBL data curation pipeline. During standardization, the molecule may be broken
    mol = standardize_mol(mol)
    smiles = Chem.MolToSmiles(mol)

    # Check if molecule can be parsed by RDKit (in rare cases, the molecule may be broken during standardization)
    if Chem.MolFromSmiles(smiles) is None:
        raise ValueError("Molecule is broken")

    return smiles
