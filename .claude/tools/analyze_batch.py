#!/usr/bin/env python3
"""
Batch Analysis Tool for buildOS
Provides reusable analysis functions for classified element batches
"""

import json
import sys
from pathlib import Path
from collections import Counter
from typing import Dict, List, Any


def analyze_batch_file(batch_file: str) -> Dict[str, Any]:
    """
    Analyze a batch elements JSON file and return comprehensive statistics.

    Args:
        batch_file: Path to the batch JSON file (e.g., batch_1_elements.json)

    Returns:
        Dictionary with analysis results including:
        - total_elements: Number of elements
        - element_types: Counter of element types
        - material_categories: Counter of material categories
        - average_confidence: Mean confidence score
        - completeness: Data completeness metrics
    """
    batch_path = Path(batch_file)

    if not batch_path.exists():
        raise FileNotFoundError(f"Batch file not found: {batch_file}")

    with open(batch_path, 'r') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Batch file must contain a JSON array of elements")

    total = len(data)

    if total == 0:
        return {
            "total_elements": 0,
            "element_types": {},
            "material_categories": {},
            "average_confidence": 0.0,
            "completeness": {}
        }

    # Count element types
    element_types = Counter(d.get('element_type', 'Unknown') for d in data)

    # Count material categories
    material_categories = Counter(
        d.get('material_primary', {}).get('category', 'Unknown')
        for d in data
    )

    # Calculate average confidence
    confidences = [d.get('confidence', 0.0) for d in data]
    avg_confidence = sum(confidences) / total if total > 0 else 0.0

    # Calculate completeness metrics
    with_volume = sum(1 for d in data if d.get('volume_m3') is not None)
    with_area = sum(1 for d in data if d.get('area_m2') is not None)
    with_materials = sum(1 for d in data if d.get('material_primary'))
    with_properties = sum(1 for d in data if d.get('properties'))

    completeness = {
        "with_volume": {"count": with_volume, "percentage": (with_volume / total) * 100},
        "with_area": {"count": with_area, "percentage": (with_area / total) * 100},
        "with_materials": {"count": with_materials, "percentage": (with_materials / total) * 100},
        "with_properties": {"count": with_properties, "percentage": (with_properties / total) * 100},
    }

    return {
        "total_elements": total,
        "element_types": dict(element_types),
        "material_categories": dict(material_categories),
        "average_confidence": round(avg_confidence, 2),
        "completeness": completeness
    }


def print_analysis(results: Dict[str, Any]) -> None:
    """Pretty print analysis results."""
    print(f"\n{'='*60}")
    print("BATCH ANALYSIS RESULTS")
    print(f"{'='*60}\n")

    print(f"Total Elements: {results['total_elements']}\n")

    print("Element Types:")
    for elem_type, count in sorted(results['element_types'].items(), key=lambda x: -x[1]):
        percentage = (count / results['total_elements']) * 100
        print(f"  {elem_type}: {count} ({percentage:.1f}%)")

    print("\nMaterial Categories:")
    for material, count in sorted(results['material_categories'].items(), key=lambda x: -x[1]):
        percentage = (count / results['total_elements']) * 100
        print(f"  {material}: {count} ({percentage:.1f}%)")

    print(f"\nAverage Confidence: {results['average_confidence']:.2f}")

    print("\nData Completeness:")
    for metric, data in results['completeness'].items():
        print(f"  {metric.replace('with_', '').title()}: {data['count']}/{results['total_elements']} ({data['percentage']:.1f}%)")

    print(f"\n{'='*60}\n")


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_batch.py <batch_file.json>")
        print("\nExample:")
        print("  python analyze_batch.py batch_1_elements.json")
        sys.exit(1)

    batch_file = sys.argv[1]

    try:
        results = analyze_batch_file(batch_file)
        print_analysis(results)

        # Return 0 for success
        sys.exit(0)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {batch_file}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
