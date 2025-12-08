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


@tool(
    name="generate_excel_report",
    description="Generate an Excel spreadsheet using Claude's Excel skill. Use this for creating formatted Excel reports with data analysis, charts, and proper formatting. The data_json parameter can be either a JSON string or a file path to a JSON file.",
    input_schema={
        "prompt": str,
        "output_dir": str,
        "data_json": str  # Optional: JSON string OR file path to JSON file
    }
)
async def generate_excel_report(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate an Excel report using Claude's Excel skill.
    
    Args:
        prompt: Description of what Excel file to create
        output_dir: Directory to save the output file
        data_json: Optional JSON string OR file path to a JSON file
        
    Returns:
        Success status and file path
    """
    try:
        import os
        from pathlib import Path
        
        # First, try to use the Skills API if available
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        # Load data from file path or parse JSON string
        data_str = ""
        if args.get("data_json"):
            data_json_input = args["data_json"]
            
            # Check if it's a file path
            if data_json_input.startswith("/") or data_json_input.startswith("./"):
                try:
                    with open(data_json_input, 'r') as f:
                        data = json.load(f)
                        data_str = json.dumps(data, indent=2)
                except FileNotFoundError:
                    return {
                        "content": [{
                            "type": "text",
                            "text": json.dumps({
                                "success": False,
                                "error": f"Data file not found: {data_json_input}"
                            }, indent=2)
                        }],
                        "is_error": True
                    }
                except json.JSONDecodeError as e:
                    return {
                        "content": [{
                            "type": "text",
                            "text": json.dumps({
                                "success": False,
                                "error": f"Invalid JSON in file {data_json_input}: {str(e)}"
                            }, indent=2)
                        }],
                        "is_error": True
                    }
            else:
                # Try to parse as JSON string
                try:
                    data = json.loads(data_json_input)
                    data_str = json.dumps(data, indent=2)
                except json.JSONDecodeError:
                    # Use as-is if not valid JSON
                    data_str = data_json_input
        
        # Try Skills API first (if anthropic package is available and API key is set)
        if api_key:
            try:
                from skills_client import SkillsClient
                
                client = SkillsClient(api_key=api_key)
                
                # Build prompt with data
                full_prompt = args["prompt"]
                if data_str:
                    full_prompt = f"""Using the following data:

```json
{data_str}
```

{args["prompt"]}
"""
                
                result = await client.generate_excel(
                    prompt=full_prompt,
                    output_dir=args["output_dir"]
                )
                
                if result["success"] and result["files"]:
                    return {
                        "content": [{
                            "type": "text",
                            "text": json.dumps({
                                "success": True,
                                "files": result["files"],
                                "response": result["response"][:500] if result["response"] else "",
                                "method": "claude_skills_api"
                            }, indent=2)
                        }]
                    }
                else:
                    # Skills API failed, fall through to openpyxl fallback
                    print(f"Skills API failed: {result.get('error')}, trying openpyxl fallback")
                    
            except ImportError:
                print("anthropic package not available, using openpyxl fallback")
            except Exception as e:
                print(f"Skills API error: {e}, using openpyxl fallback")
        
        # Fallback: Use openpyxl to create Excel file locally
        return await _generate_excel_with_openpyxl(args, data_str)
        
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


async def _generate_excel_with_openpyxl(args: Dict[str, Any], data_str: str) -> Dict[str, Any]:
    """
    Fallback Excel generation using openpyxl.
    Creates a basic Excel file with the provided data.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.utils import get_column_letter
        from pathlib import Path
        from datetime import datetime
        
        # Parse data if available
        data = None
        if data_str:
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                pass
        
        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Report"
        
        # Style definitions
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        title_font = Font(bold=True, size=14)
        
        # Add title
        ws['A1'] = "Generated Report"
        ws['A1'].font = title_font
        ws['A2'] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ws['A3'] = f"Prompt: {args['prompt'][:100]}..."
        
        row = 5
        
        # If we have structured data, try to render it
        if data and isinstance(data, dict):
            # Handle CO2 report format
            if 'summary' in data:
                ws[f'A{row}'] = "Summary"
                ws[f'A{row}'].font = title_font
                row += 1
                
                summary = data['summary']
                for key, value in summary.items():
                    ws[f'A{row}'] = key.replace('_', ' ').title()
                    ws[f'B{row}'] = str(value)
                    row += 1
                row += 1
            
            # Handle by_category
            if 'by_category' in data:
                ws[f'A{row}'] = "By Category"
                ws[f'A{row}'].font = title_font
                row += 1
                
                headers = ["Category", "Count", "CO2 (kg)", "Mass (kg)", "Percentage"]
                for col, header in enumerate(headers, 1):
                    cell = ws.cell(row=row, column=col)
                    cell.value = header
                    cell.font = header_font
                    cell.fill = header_fill
                row += 1
                
                for category, details in data['by_category'].items():
                    ws.cell(row=row, column=1).value = category
                    ws.cell(row=row, column=2).value = details.get('count', 0)
                    ws.cell(row=row, column=3).value = details.get('co2_kg', 0)
                    ws.cell(row=row, column=4).value = details.get('mass_kg', 0)
                    ws.cell(row=row, column=5).value = details.get('percentage', 0)
                    row += 1
                row += 1
            
            # Handle detailed_results
            if 'detailed_results' in data and data['detailed_results']:
                ws[f'A{row}'] = "Detailed Results"
                ws[f'A{row}'].font = title_font
                row += 1
                
                # Get headers from first item
                first_item = data['detailed_results'][0]
                headers = list(first_item.keys())
                for col, header in enumerate(headers, 1):
                    cell = ws.cell(row=row, column=col)
                    cell.value = header.replace('_', ' ').title()
                    cell.font = header_font
                    cell.fill = header_fill
                row += 1
                
                for item in data['detailed_results']:
                    for col, key in enumerate(headers, 1):
                        ws.cell(row=row, column=col).value = item.get(key, '')
                    row += 1
        
        # Adjust column widths
        for col in range(1, 15):
            ws.column_dimensions[get_column_letter(col)].width = 18
        
        # Save file
        output_dir = Path(args["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"report_{timestamp}.xlsx"
        wb.save(str(output_file))
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "files": [str(output_file)],
                    "response": f"Excel file created using openpyxl: {output_file}",
                    "method": "openpyxl_fallback"
                }, indent=2)
            }]
        }
        
    except ImportError:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": "Neither anthropic (for Skills API) nor openpyxl (for local generation) is available. Install one of: pip install anthropic OR pip install openpyxl"
                }, indent=2)
            }],
            "is_error": True
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
    name="generate_presentation",
    description="Generate a PowerPoint presentation using Claude's PowerPoint skill. Use this for creating professional presentations with slides, charts, and formatting. The data_json parameter can be either a JSON string or a file path to a JSON file.",
    input_schema={
        "prompt": str,
        "output_dir": str,
        "data_json": str  # Optional: JSON string OR file path to JSON file
    }
)
async def generate_presentation(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a PowerPoint presentation using Claude's PPTX skill.
    
    Args:
        prompt: Description of what presentation to create
        output_dir: Directory to save the output file
        data_json: Optional JSON string OR file path to a JSON file
        
    Returns:
        Success status and file path
    """
    try:
        import os
        
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "success": False,
                        "error": "ANTHROPIC_API_KEY not set. Required for PowerPoint skill. Note: PowerPoint generation requires the Claude Skills API (no local fallback available)."
                    }, indent=2)
                }],
                "is_error": True
            }
        
        # Load data from file path or parse JSON string
        data_str = ""
        if args.get("data_json"):
            data_json_input = args["data_json"]
            
            # Check if it's a file path
            if data_json_input.startswith("/") or data_json_input.startswith("./"):
                try:
                    with open(data_json_input, 'r') as f:
                        data = json.load(f)
                        data_str = json.dumps(data, indent=2)
                except FileNotFoundError:
                    return {
                        "content": [{
                            "type": "text",
                            "text": json.dumps({
                                "success": False,
                                "error": f"Data file not found: {data_json_input}"
                            }, indent=2)
                        }],
                        "is_error": True
                    }
                except json.JSONDecodeError as e:
                    return {
                        "content": [{
                            "type": "text",
                            "text": json.dumps({
                                "success": False,
                                "error": f"Invalid JSON in file {data_json_input}: {str(e)}"
                            }, indent=2)
                        }],
                        "is_error": True
                    }
            else:
                # Try to parse as JSON string
                try:
                    data = json.loads(data_json_input)
                    data_str = json.dumps(data, indent=2)
                except json.JSONDecodeError:
                    data_str = data_json_input
        
        from skills_client import SkillsClient
        
        client = SkillsClient(api_key=api_key)
        
        full_prompt = args["prompt"]
        if data_str:
            full_prompt = f"""Using the following data:

```json
{data_str}
```

{args["prompt"]}
"""
        
        result = await client.generate_presentation(
            prompt=full_prompt,
            output_dir=args["output_dir"]
        )
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": result["success"],
                    "files": result["files"],
                    "response": result["response"][:500] if result["response"] else "",
                    "error": result.get("error")
                }, indent=2)
            }],
            "is_error": not result["success"]
        }
        
    except ImportError:
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": "anthropic package not installed. PowerPoint generation requires the Claude Skills API. Install with: pip install anthropic"
                }, indent=2)
            }],
            "is_error": True
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
    - mcp__ifc__generate_excel_report
    - mcp__ifc__generate_presentation
    """
    return create_sdk_mcp_server(
        name="ifc",
        version="1.0.0",
        tools=[
            parse_ifc_file, 
            prepare_batches, 
            calculate_co2,
            generate_excel_report,
            generate_presentation
        ]
    )

