"""
SDK Tools: MCP Tool Registration for buildOS

Registers IFC analysis tools as MCP server for SDK access.
Tools are namespaced as: mcp__ifc__<tool_name>
"""

from claude_agent_sdk import tool, create_sdk_mcp_server
from typing import Dict, Any
import json
from pathlib import Path


@tool(
    name="parse_ifc_file",
    description="Parse IFC file and extract building element data to JSON format",
    input_schema={
        "ifc_path": str,
        "output_path": str
    }
)
async def parse_ifc_file(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse IFC file using ifcopenshell.

    Args:
        ifc_path: Path to input IFC file
        output_path: Path to output JSON file

    Returns:
        Success status and entity count
    """
    try:
        # Import IFC parser from tools
        import sys
        from pathlib import Path
        tools_path = Path(__file__).parent / ".claude" / "tools"
        sys.path.insert(0, str(tools_path))

        # Use existing IFC parser from agent_system4
        import ifcopenshell

        ifc_file = ifcopenshell.open(args["ifc_path"])

        # Extract all rooted entities (elements that have geometry)
        elements = []
        for element in ifc_file.by_type("IfcProduct"):
            if element.is_a() in [
                "IfcBeam", "IfcColumn", "IfcWall", "IfcSlab", "IfcDoor", "IfcWindow",
                "IfcRoof", "IfcStair", "IfcCovering", "IfcFurnishingElement", "IfcFooting"
            ]:
                elements.append({
                    "guid": element.GlobalId,
                    "ifc_type": element.is_a(),
                    "name": element.Name if hasattr(element, 'Name') else None,
                    "object_type": element.ObjectType if hasattr(element, 'ObjectType') else None,
                    "description": element.Description if hasattr(element, 'Description') else None
                })

        # Write to JSON
        output_path = Path(args["output_path"])
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump({
                "elements": elements,
                "total_count": len(elements),
                "source_file": args["ifc_path"]
            }, f, indent=2)

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "entities_parsed": len(elements),
                    "output_file": str(output_path)
                }, indent=2)
            }]
        }

    except Exception as e:
        import traceback
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }, indent=2)
            }],
            "is_error": True
        }


@tool(
    name="prepare_batches",
    description="Create element batches for parallel classification processing",
    input_schema={
        "json_path": str,
        "batch_size": int,
        "output_path": str
    }
)
async def prepare_batches(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Split elements into batches for parallel processing.

    Args:
        json_path: Path to parsed IFC JSON
        batch_size: Elements per batch (default: 100)
        output_path: Path to output batches.json

    Returns:
        Success status and batch count
    """
    try:
        # Load parsed elements
        with open(args["json_path"], 'r') as f:
            data = json.load(f)

        elements = data.get("elements", [])
        batch_size = args.get("batch_size", 100)

        # Create batches
        batches = []
        for i in range(0, len(elements), batch_size):
            batch = {
                "batch_id": len(batches) + 1,
                "elements": elements[i:i + batch_size],
                "element_count": len(elements[i:i + batch_size])
            }
            batches.append(batch)

        # Write batches
        output_path = Path(args["output_path"])
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump({
                "batches": batches,
                "total_batches": len(batches),
                "total_elements": len(elements),
                "batch_size": batch_size
            }, f, indent=2)

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "total_batches": len(batches),
                    "total_elements": len(elements),
                    "output_file": str(output_path)
                }, indent=2)
            }]
        }

    except Exception as e:
        import traceback
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }, indent=2)
            }],
            "is_error": True
        }


@tool(
    name="calculate_co2",
    description="Calculate CO2 impact from classified building elements using durability database",
    input_schema={
        "classified_path": str,
        "database_path": str,
        "output_path": str
    }
)
async def calculate_co2(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate CO2 emissions for classified elements.

    Args:
        classified_path: Path to classified elements JSON
        database_path: Path to durability database JSON
        output_path: Path to output CO2 results

    Returns:
        Success status and total CO2
    """
    try:
        # Load classified elements
        with open(args["classified_path"], 'r') as f:
            classified_data = json.load(f)

        # Load durability database
        with open(args["database_path"], 'r') as f:
            database = json.load(f)

        # Calculate CO2 for each element
        results = []
        total_co2 = 0.0

        for element in classified_data.get("elements", []):
            concrete_type = element.get("concrete_type", "Unknown")
            volume = element.get("volume_m3", 0.0)

            # Look up CO2 factor in database
            co2_factor = database.get(concrete_type, {}).get("co2_per_m3", 0.0)
            element_co2 = volume * co2_factor

            results.append({
                **element,
                "co2_kg": element_co2,
                "co2_factor": co2_factor
            })

            total_co2 += element_co2

        # Write results
        output_path = Path(args["output_path"])
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump({
                "elements": results,
                "total_co2_kg": total_co2,
                "element_count": len(results)
            }, f, indent=2)

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "total_co2_kg": total_co2,
                    "element_count": len(results),
                    "output_file": str(output_path)
                }, indent=2)
            }]
        }

    except Exception as e:
        import traceback
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }, indent=2)
            }],
            "is_error": True
        }


def create_ifc_tools_server():
    """
    Create MCP server with all IFC analysis tools.

    Tools become available as:
    - mcp__ifc__parse_ifc_file
    - mcp__ifc__prepare_batches
    - mcp__ifc__calculate_co2
    """
    return create_sdk_mcp_server(
        name="ifc",
        version="1.0.0",
        tools=[parse_ifc_file, prepare_batches, calculate_co2]
    )
