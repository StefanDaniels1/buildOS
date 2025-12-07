#!/usr/bin/env python3
"""
IFC Parsing CLI Tool for buildOS
Parses IFC files and extracts building elements for CO2 analysis.

Usage:
    python parse_ifc.py <input.ifc> <output.json>

Example:
    python parse_ifc.py /path/to/building.ifc .context/session/parsed_data.json
"""

import json
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from ifc_comprehensive_parser import ComprehensiveIfcParser
except ImportError:
    print("Error: ifc_comprehensive_parser not found in project root")
    sys.exit(1)


def parse_ifc_file(ifc_path: str, output_path: str, include_validation: bool = True) -> dict:
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

        # Count geometric elements
        geometric_types = [
            "IfcBeam", "IfcColumn", "IfcWall", "IfcSlab", "IfcRoof",
            "IfcStair", "IfcRailing", "IfcDoor", "IfcWindow",
            "IfcFooting", "IfcPile", "IfcPlate", "IfcMember", "IfcCovering"
        ]
        geometric_count = sum(1 for e in elements if e.get("ifc_type") in geometric_types)

        # Prepare output
        output_data = {
            "metadata": {
                "ifc_file": str(Path(ifc_path).name),
                "total_entities": len(elements),
                "geometric_elements": geometric_count,
                "parser_version": "1.0.0"
            },
            "elements": elements,
            "validation": validation_report
        }

        # Ensure output directory exists
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        return {
            "success": True,
            "output_file": str(output_path),
            "total_entities": len(elements),
            "geometric_elements": geometric_count
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print("Usage: python parse_ifc.py <input.ifc> <output.json>")
        print("\nExample:")
        print("  python parse_ifc.py building.ifc parsed_data.json")
        sys.exit(1)

    ifc_path = sys.argv[1]
    output_path = sys.argv[2]

    if not Path(ifc_path).exists():
        print(f"Error: IFC file not found: {ifc_path}")
        sys.exit(1)

    print(f"\nParsing IFC file: {ifc_path}")
    print(f"Output: {output_path}")

    result = parse_ifc_file(ifc_path, output_path)

    if result["success"]:
        print(f"\n{'='*60}")
        print("IFC PARSING COMPLETE")
        print(f"{'='*60}")
        print(f"Total entities: {result['total_entities']}")
        print(f"Geometric elements: {result['geometric_elements']}")
        print(f"Output file: {result['output_file']}")
        print(f"{'='*60}\n")
    else:
        print(f"\nError: {result['error']}")
        if "traceback" in result:
            print(result["traceback"])
        sys.exit(1)


if __name__ == "__main__":
    main()
