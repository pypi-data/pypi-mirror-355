from pathlib import Path
import yaml
from typing import Optional, Dict, Any
import string

def get_next_ligand_id(config: Dict[str, Any], index: int) -> str:
    """Get the next available ligand ID based on existing IDs in the config.
    
    Parameters
    ----------
    config : Dict[str, Any]
        The configuration dictionary.
    index : int
        The index of the current ligand.
        
    Returns
    -------
    str
        The next available ligand ID.
    """
    # Find the base ligand ID from the template
    base_id = None
    for item in config["sequences"]:
        if "ligand" in item:
            base_id = item["ligand"]["id"]
            break
    
    if base_id is None:
        raise ValueError("No ligand ID found in template")
    
    # Remove any trailing digits from the base ID
    base_id = ''.join(c for c in base_id if not c.isdigit())
    
    # Append the index to the base ID
    return f"{base_id}{index}"

def generate_yamls_from_sdfs(
    template_yaml: Path,
    sdf_dir: Path,
    output_dir: Path,
    yaml_prefix: str = "config_",
    start_index: int = 1,
) -> None:
    """Generate YAML files from a template and a folder of SDF files.
    
    Parameters
    ----------
    template_yaml : Path
        Path to the template YAML file.
    sdf_dir : Path
        Path to the directory containing SDF files.
    output_dir : Path
        Path to the output directory where YAML files will be saved.
    yaml_prefix : str, optional
        Prefix for output YAML filenames, by default "config_".
    start_index : int, optional
        Starting index for output filenames, by default 1.
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load template YAML
    with open(template_yaml) as f:
        template = yaml.safe_load(f)
    
    # Get all SDF files
    sdf_files = sorted(sdf_dir.glob("*.sdf"))
    
    # Generate YAML for each SDF
    for i, sdf_file in enumerate(sdf_files):
        # Create a copy of the template
        config = template.copy()
        
        # Get next available ligand ID using start_index
        ligand_id = get_next_ligand_id(config, start_index + i)
        
        # Update ligand information
        for item in config["sequences"]:
            if "ligand" in item:
                item["ligand"]["id"] = ligand_id
                item["ligand"]["sdf"] = str(sdf_file)
        
        # Update affinity information if present
        if "properties" in config:
            for prop in config["properties"]:
                if "affinity" in prop:
                    prop["affinity"]["binder"] = ligand_id
        
        # Write YAML file
        output_file = output_dir / f"{yaml_prefix}{start_index + i}.yaml"
        with open(output_file, "w") as f:
            yaml.dump(
                config,
                f,
                default_flow_style=False,
                sort_keys=False,  # Maintain original order
            )
        
        print(f"Created {output_file} with ligand ID {ligand_id}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate YAML files from a template and SDF files")
    parser.add_argument("template_yaml", type=str, help="Path to template YAML file")
    parser.add_argument("sdf_dir", type=str, help="Path to directory containing SDF files")
    parser.add_argument("output_dir", type=str, help="Path to output directory")
    parser.add_argument("--yaml-prefix", type=str, default="config_", help="Prefix for output YAML filenames")
    parser.add_argument("--start-index", type=int, default=1, help="Starting index for output filenames")
    
    args = parser.parse_args()
    
    generate_yamls_from_sdfs(
        template_yaml=Path(args.template_yaml),
        sdf_dir=Path(args.sdf_dir),
        output_dir=Path(args.output_dir),
        yaml_prefix=args.yaml_prefix,
        start_index=args.start_index,
    )

if __name__ == "__main__":
    main() 