"""
Direct IFC Tools - Callable functions without SDK wrapper

These are direct Python functions that can be called from standalone scripts.
They wrap the ComprehensiveIfcParser for direct usage.
"""

from pathlib import Path
import json
import sys

# Import the comprehensive parser
sys.path.insert(0, str(Path(__file__).parent.parent))
from ifc_comprehensive_parser import ComprehensiveIfcParser


def parse_ifc_file_direct(ifc_path: str, output_path: str, include_validation: bool = True) -> dict:
    """
    Parse IFC file and extract all building elements.

    Args:
        ifc_path: Path to the IFC file
        output_path: Path to save parsed JSON
        include_validation: Include validation report

    Returns:
        Dictionary with success status and parsed data
    """
    try:
        # Initialize parser
        parser = ComprehensiveIfcParser(ifc_path)

        # Load IFC file
        if not parser.load():
            return {
                "success": False,
                "error": f"Failed to load IFC file at {ifc_path}"
            }

        # Extract all data
        elements = parser.extract_all_data()

        # Validate if requested
        validation_report = None
        if include_validation:
            validation_report = parser.validate_data()

        # Prepare output
        output_data = {
            "metadata": {
                "ifc_file": str(ifc_path),
                "total_elements": len(elements),
                "parser_version": "1.0.0"
            },
            "elements": elements,
            "validation": validation_report
        }

        # Save to file
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        return {
            "success": True,
            "output_file": str(output_path),
            "entities_parsed": len(elements),
            "element_types": list(set(e.get("ifc_type") for e in elements if e.get("ifc_type")))
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


def get_geometric_elements_direct(parsed_json_path: str) -> dict:
    """
    Extract geometric elements from parsed IFC JSON.

    Args:
        parsed_json_path: Path to parsed IFC JSON file

    Returns:
        Dictionary with element counts by type
    """
    try:
        # Load parsed data
        with open(parsed_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        elements = data.get("elements", [])

        # Count by IFC type
        element_counts = {}
        for element in elements:
            ifc_type = element.get("ifc_type", "Unknown")
            element_counts[ifc_type] = element_counts.get(ifc_type, 0) + 1

        # Filter for geometric/structural elements
        geometric_types = [
            "IfcBeam", "IfcColumn", "IfcWall", "IfcSlab", "IfcRoof",
            "IfcStair", "IfcRailing", "IfcDoor", "IfcWindow",
            "IfcFooting", "IfcPile", "IfcPlate", "IfcMember"
        ]

        geometric_elements = {
            k: v for k, v in element_counts.items()
            if k in geometric_types
        }

        return {
            "success": True,
            "elements": element_counts,
            "geometric_elements": geometric_elements,
            "total_elements": len(elements),
            "total_types": len(element_counts)
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


def prepare_classification_batches_direct(parsed_json_path: str, batch_size: int = 100) -> dict:
    """
    Prepare element batches for classification.

    Args:
        parsed_json_path: Path to parsed IFC JSON
        batch_size: Number of elements per batch

    Returns:
        Dictionary with batch information
    """
    try:
        # Load parsed data
        with open(parsed_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        elements = data.get("elements", [])

        # Filter geometric elements
        geometric_elements = [
            e for e in elements
            if e.get("ifc_type") in [
                "IfcBeam", "IfcColumn", "IfcWall", "IfcSlab", "IfcRoof",
                "IfcFooting", "IfcPile", "IfcPlate", "IfcMember"
            ]
        ]

        # Create batches
        batches = []
        for i in range(0, len(geometric_elements), batch_size):
            batch = geometric_elements[i:i + batch_size]
            batches.append({
                "batch_id": len(batches),
                "elements": batch,
                "element_count": len(batch)
            })

        # Save batches
        output_dir = Path(parsed_json_path).parent
        batches_file = output_dir / "batches.json"

        with open(batches_file, 'w', encoding='utf-8') as f:
            json.dump(batches, f, indent=2)

        return {
            "success": True,
            "batches_file": str(batches_file),
            "total_batches": len(batches),
            "total_elements": len(geometric_elements),
            "batch_size": batch_size
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }
