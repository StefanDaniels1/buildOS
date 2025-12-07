#!/usr/bin/env python3
"""
Batch Preparation CLI Tool for buildOS
Splits parsed IFC elements into batches for parallel classification.

Usage:
    python prepare_batches.py <parsed_data.json> <batches.json> [batch_size]

Example:
    python prepare_batches.py parsed_data.json batches.json 50
"""

import json
import sys
from pathlib import Path
from collections import Counter
from datetime import datetime


def prepare_batches(parsed_json_path: str, output_path: str, batch_size: int = 50) -> dict:
    """
    Prepare element batches for classification.

    Args:
        parsed_json_path: Path to parsed IFC JSON
        output_path: Path to save batches JSON
        batch_size: Number of elements per batch (default: 50)

    Returns:
        Dictionary with batch information
    """
    try:
        # Load parsed data
        with open(parsed_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        elements = data.get("elements", [])

        # Filter geometric elements
        geometric_types = [
            "IfcBeam", "IfcColumn", "IfcWall", "IfcSlab", "IfcRoof",
            "IfcFooting", "IfcPile", "IfcPlate", "IfcMember", "IfcDoor",
            "IfcWindow", "IfcStair", "IfcRailing", "IfcCovering"
        ]

        geometric_elements = [
            e for e in elements
            if e.get("ifc_type") in geometric_types
        ]

        # Create batches
        batches = []
        for i in range(0, len(geometric_elements), batch_size):
            batch_elements = geometric_elements[i:i + batch_size]

            # Count IFC types in this batch
            ifc_types = Counter(e.get("ifc_type", "Unknown") for e in batch_elements)

            # Extract storeys
            storeys = Counter(
                e.get("spatial_structure", {}).get("storey", "Unknown")
                for e in batch_elements
            )

            batches.append({
                "batch_id": len(batches) + 1,
                "start_index": i,
                "end_index": i + len(batch_elements) - 1,
                "element_count": len(batch_elements),
                "elements": batch_elements,
                "summary": {
                    "ifc_types": dict(ifc_types),
                    "storeys": dict(storeys)
                }
            })

        # Prepare output
        output_data = {
            "metadata": {
                "source_file": str(Path(parsed_json_path).name),
                "total_elements": len(geometric_elements),
                "batch_size": batch_size,
                "num_batches": len(batches),
                "created_at": datetime.now().isoformat()
            },
            "batches": batches
        }

        # Ensure output directory exists
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        # Save batches
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        return {
            "success": True,
            "output_file": str(output_path),
            "num_batches": len(batches),
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


def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print("Usage: python prepare_batches.py <parsed_data.json> <batches.json> [batch_size]")
        print("\nExample:")
        print("  python prepare_batches.py parsed_data.json batches.json 50")
        sys.exit(1)

    parsed_json_path = sys.argv[1]
    output_path = sys.argv[2]
    batch_size = int(sys.argv[3]) if len(sys.argv) > 3 else 50

    if not Path(parsed_json_path).exists():
        print(f"Error: Parsed JSON file not found: {parsed_json_path}")
        sys.exit(1)

    print(f"\nPreparing batches from: {parsed_json_path}")
    print(f"Batch size: {batch_size}")
    print(f"Output: {output_path}")

    result = prepare_batches(parsed_json_path, output_path, batch_size)

    if result["success"]:
        print(f"\n{'='*60}")
        print("BATCH PREPARATION COMPLETE")
        print(f"{'='*60}")
        print(f"Total elements: {result['total_elements']}")
        print(f"Batches created: {result['num_batches']}")
        print(f"Batch size: ~{result['batch_size']} elements per batch")
        print(f"Output file: {result['output_file']}")
        print(f"{'='*60}\n")
    else:
        print(f"\nError: {result['error']}")
        if "traceback" in result:
            print(result["traceback"])
        sys.exit(1)


if __name__ == "__main__":
    main()
