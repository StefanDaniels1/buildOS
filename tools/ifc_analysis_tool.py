"""
IFC Analysis Tool - SDK MCP Tool for BIM AI CO2 Analysis

This tool wraps the ComprehensiveIfcParser to provide structured IFC data
extraction capabilities to Claude Code agents via the MCP protocol.
"""

from claude_agent_sdk import tool
from typing import Any, Dict
from pathlib import Path
import json
import sys

# Import the comprehensive parser
sys.path.insert(0, str(Path(__file__).parent.parent))
from ifc_comprehensive_parser import ComprehensiveIfcParser


@tool(
    name="parse_ifc_file",
    description="Parse an IFC file and extract complete building element data for CO2 analysis",
    input_schema={
        "ifc_path": str,
        "output_path": str,
        "include_validation": bool
    }
)
async def parse_ifc_file(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse IFC file and extract all building elements with properties, quantities, and materials.

    Args:
        ifc_path: Path to the IFC file to parse
        output_path: Path where to save the parsed JSON output
        include_validation: Whether to include validation report (default: True)

    Returns:
        Dictionary with parsing results and summary statistics
    """
    try:
        ifc_path = args.get("ifc_path")
        output_path = args.get("output_path")
        include_validation = args.get("include_validation", True)

        if not ifc_path:
            return {
                "content": [{
                    "type": "text",
                    "text": "Error: ifc_path is required"
                }],
                "is_error": True
            }

        if not output_path:
            return {
                "content": [{
                    "type": "text",
                    "text": "Error: output_path is required"
                }],
                "is_error": True
            }

        # Initialize parser
        parser = ComprehensiveIfcParser(ifc_path)

        # Load IFC file
        if not parser.load():
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error: Failed to load IFC file at {ifc_path}"
                }],
                "is_error": True
            }

        # Extract all data
        elements = parser.extract_all_data()

        # Validate if requested
        validation_report = None
        if include_validation:
            validation_report = parser.validate_data()

        # Export to JSON
        parser.export_to_json(output_path)

        # Build structured result
        geometric_count = sum(1 for e in elements if e.get('is_geometric'))
        spatial_count = sum(1 for e in elements if e.get('is_spatial'))
        with_materials = sum(1 for e in elements if e.get('materials'))
        with_quantities = sum(1 for e in elements if e.get('quantities'))

        result_data = {
            "success": True,
            "source_file": Path(ifc_path).name,
            "output_path": str(output_path),
            "statistics": {
                "total_elements": len(elements),
                "geometric_elements": geometric_count,
                "spatial_elements": spatial_count,
                "elements_with_materials": with_materials,
                "elements_with_quantities": with_quantities
            }
        }

        if validation_report:
            completeness = validation_report.get('completeness', {})
            result_data["completeness"] = {
                "with_properties": completeness.get('with_properties', {}).get('percentage', 0),
                "with_quantities": completeness.get('with_quantities', {}).get('percentage', 0),
                "with_materials": completeness.get('with_materials', {}).get('percentage', 0),
                "with_spatial_context": completeness.get('with_spatial_context', {}).get('percentage', 0)
            }

        return {
            "content": [{
                "type": "text",
                "text": json.dumps(result_data, indent=2)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error parsing IFC file: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    name="get_geometric_elements",
    description="Filter and return only geometric building elements from parsed IFC data",
    input_schema={
        "json_path": str,
        "element_types": list  # Optional filter by IFC types like ["IfcWall", "IfcSlab"]
    }
)
async def get_geometric_elements(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract geometric elements suitable for CO2 analysis from parsed IFC data.

    Args:
        json_path: Path to the parsed IFC JSON file
        element_types: Optional list of IFC types to filter (e.g., ["IfcWall", "IfcSlab"])

    Returns:
        Dictionary with filtered geometric elements
    """
    try:
        json_path = args.get("json_path")
        element_types = args.get("element_types", [])

        if not json_path:
            return {
                "content": [{
                    "type": "text",
                    "text": "Error: json_path is required"
                }],
                "is_error": True
            }

        # Load parsed data
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        elements = data.get('elements', [])

        # Filter geometric elements
        geometric = [e for e in elements if e.get('is_geometric', False)]

        # Apply type filter if specified
        if element_types:
            geometric = [e for e in geometric if e.get('ifc_type') in element_types]

        # Count by type
        type_counts = {}
        for elem in geometric:
            ifc_type = elem.get('ifc_type', 'Unknown')
            type_counts[ifc_type] = type_counts.get(ifc_type, 0) + 1

        result_data = {
            "success": True,
            "source_file": str(json_path),
            "total_geometric_elements": len(geometric),
            "element_types": type_counts,
            "filtered_by_types": element_types if element_types else None
        }

        return {
            "content": [{
                "type": "text",
                "text": json.dumps(result_data, indent=2)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error filtering geometric elements: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    name="prepare_classification_batches",
    description="Prepare element batches for parallel AI classification",
    input_schema={
        "json_path": str,
        "batch_size": int,
        "output_path": str
    }
)
async def prepare_classification_batches(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare batches of building elements for parallel classification.

    Args:
        json_path: Path to the parsed IFC JSON file
        batch_size: Number of elements per batch (recommended: 50-100)
        output_path: Path to save batch configuration

    Returns:
        Dictionary with batch preparation results
    """
    try:
        json_path = args.get("json_path")
        batch_size = args.get("batch_size", 100)
        output_path = args.get("output_path")

        if not json_path or not output_path:
            return {
                "content": [{
                    "type": "text",
                    "text": "Error: json_path and output_path are required"
                }],
                "is_error": True
            }

        # Load parsed data
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        elements = data.get('elements', [])

        # Filter geometric elements for classification
        geometric = [e for e in elements if e.get('is_geometric', False)]

        # Create batches
        batches = []
        for i in range(0, len(geometric), batch_size):
            batch_elements = geometric[i:i + batch_size]

            # Simplify elements for classification (reduce payload)
            simplified = []
            for elem in batch_elements:
                simplified.append({
                    'global_id': elem.get('global_id'),
                    'ifc_type': elem.get('ifc_type'),
                    'name': elem.get('name'),
                    'materials': elem.get('materials', []),
                    'properties': elem.get('properties', {}),
                    'quantities': elem.get('quantities', {}),
                    'spatial_structure': elem.get('spatial_structure', {})
                })

            # Get spatial hint
            spatial_hints = set()
            for elem in batch_elements:
                storey = elem.get('spatial_structure', {}).get('storey')
                if storey:
                    spatial_hints.add(storey)

            batches.append({
                'batch_id': len(batches) + 1,
                'element_count': len(simplified),
                'elements': simplified,
                'spatial_hint': ', '.join(sorted(spatial_hints)) if spatial_hints else 'Unknown',
                'element_types': list(set(e.get('ifc_type') for e in batch_elements))
            })

        # Add total batch count to each batch
        for batch in batches:
            batch['total_batches'] = len(batches)

        # Extract shared context
        buildings = set()
        material_names = set()
        for elem in geometric:
            building = elem.get('spatial_structure', {}).get('building')
            if building:
                buildings.add(building)
            for mat in elem.get('materials', []):
                if mat.get('name'):
                    material_names.add(mat['name'])

        shared_context = {
            'total_elements': len(geometric),
            'buildings': sorted(buildings),
            'material_patterns': {
                'unique_materials': sorted(material_names)
            }
        }

        # Save batch configuration
        batch_config = {
            'batches': batches,
            'shared_context': shared_context,
            'metadata': {
                'source_file': data.get('source_file'),
                'total_geometric_elements': len(geometric),
                'batch_size': batch_size,
                'total_batches': len(batches)
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(batch_config, f, indent=2, ensure_ascii=False)

        result_data = {
            "success": True,
            "output_path": str(output_path),
            "total_elements": len(geometric),
            "batch_size": batch_size,
            "total_batches": len(batches),
            "buildings": sorted(buildings),
            "unique_materials": len(material_names)
        }

        return {
            "content": [{
                "type": "text",
                "text": json.dumps(result_data, indent=2)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error preparing batches: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    name="classify_elements",
    description="Classify building elements for CO2 analysis by reading batch data and spawning co2-classifier agent",
    input_schema={
        "batch_path": str,
        "batch_number": int,
        "output_path": str
    }
)
async def classify_elements(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify elements in a batch using the co2-classifier agent.

    This tool reads the batch data and provides it to the co2-classifier agent
    for expert classification. The agent will analyze materials, properties,
    and spatial context to categorize concrete types.

    Args:
        batch_path: Path to the batch configuration JSON file
        batch_number: Which batch to process (1-indexed)
        output_path: Where to save classification results

    Returns:
        Dictionary with classification instructions for the agent
    """
    try:
        batch_path = args.get("batch_path")
        batch_number = args.get("batch_number", 1)
        output_path = args.get("output_path")

        if not batch_path or not output_path:
            return {
                "content": [{
                    "type": "text",
                    "text": "Error: batch_path and output_path are required"
                }],
                "is_error": True
            }

        # Load batch configuration
        with open(batch_path, 'r', encoding='utf-8') as f:
            batch_config = json.load(f)

        batches = batch_config.get('batches', [])
        shared_context = batch_config.get('shared_context', {})

        if batch_number < 1 or batch_number > len(batches):
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error: batch_number {batch_number} out of range (1-{len(batches)})"
                }],
                "is_error": True
            }

        # Get the specific batch (convert to 0-indexed)
        batch = batches[batch_number - 1]

        # Prepare data for classification
        result_data = {
            "success": True,
            "instruction": "Use the co2-classifier agent to classify these elements",
            "batch_info": {
                "batch_id": batch.get('batch_id'),
                "element_count": batch.get('element_count'),
                "spatial_hint": batch.get('spatial_hint'),
                "element_types": batch.get('element_types')
            },
            "shared_context": shared_context,
            "elements": batch.get('elements', []),
            "output_path": str(output_path),
            "expected_format": {
                "example": {
                    "global_id": "element-guid",
                    "classification": "Concrete_Structural",
                    "confidence": 0.85,
                    "volume_m3": 12.5,
                    "reasoning": "Load-bearing column with C30/37 concrete..."
                }
            }
        }

        return {
            "content": [{
                "type": "text",
                "text": json.dumps(result_data, indent=2)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error preparing classification: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    name="aggregate_classifications",
    description="Aggregate classification results from multiple batches into a final CO2 report",
    input_schema={
        "classification_files": list,
        "output_path": str
    }
)
async def aggregate_classifications(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate classification results from multiple batch outputs.

    Args:
        classification_files: List of paths to classification result JSON files
        output_path: Where to save the aggregated report

    Returns:
        Dictionary with aggregated statistics and CO2 summary
    """
    try:
        classification_files = args.get("classification_files", [])
        output_path = args.get("output_path")

        if not classification_files or not output_path:
            return {
                "content": [{
                    "type": "text",
                    "text": "Error: classification_files and output_path are required"
                }],
                "is_error": True
            }

        # Aggregate all classifications
        all_classifications = []
        category_counts = {}
        total_volume = {}
        confidence_scores = []

        for file_path in classification_files:
            if not Path(file_path).exists():
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                classifications = json.load(f)

            if isinstance(classifications, list):
                all_classifications.extend(classifications)

                for item in classifications:
                    category = item.get('classification', 'Unknown')
                    volume = item.get('volume_m3', 0)
                    confidence = item.get('confidence', 0)

                    category_counts[category] = category_counts.get(category, 0) + 1
                    total_volume[category] = total_volume.get(category, 0) + volume
                    confidence_scores.append(confidence)

        # Calculate summary statistics
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

        # Build final report
        report = {
            "total_elements_classified": len(all_classifications),
            "average_confidence": round(avg_confidence, 3),
            "categories": {
                category: {
                    "count": count,
                    "total_volume_m3": round(total_volume.get(category, 0), 2)
                }
                for category, count in category_counts.items()
            },
            "all_classifications": all_classifications
        }

        # Save report
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        result_data = {
            "success": True,
            "output_path": str(output_path),
            "summary": {
                "total_classified": len(all_classifications),
                "average_confidence": round(avg_confidence, 3),
                "categories": category_counts,
                "total_volumes_m3": {k: round(v, 2) for k, v in total_volume.items()}
            }
        }

        return {
            "content": [{
                "type": "text",
                "text": json.dumps(result_data, indent=2)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error aggregating classifications: {str(e)}"
            }],
            "is_error": True
        }


# Export all tools
__all__ = [
    'parse_ifc_file',
    'get_geometric_elements',
    'prepare_classification_batches',
    'classify_elements',
    'aggregate_classifications'
]
