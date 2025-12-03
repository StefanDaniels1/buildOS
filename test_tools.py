#!/usr/bin/env python3
"""
Test script for MCP tools in agent_system5

Tests the three IFC analysis tools:
1. parse_ifc_file - Parse IFC and extract elements
2. prepare_batches - Create classification batches
3. calculate_co2 - Calculate CO2 emissions
"""

import asyncio
import json
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sdk_tools import parse_ifc_file, prepare_batches, calculate_co2


async def test_parse_ifc():
    """Test IFC parsing tool."""
    print("\n" + "="*60)
    print("TEST 1: Parse IFC File")
    print("="*60)

    # Setup paths
    ifc_path = "../Small_condo.ifc"
    output_path = "./workspace/.context/test/parsed_elements.json"

    print(f"Input:  {ifc_path}")
    print(f"Output: {output_path}")

    # Create output directory
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Call tool
    result = await parse_ifc_file({
        "ifc_path": ifc_path,
        "output_path": output_path
    })

    # Parse result
    result_data = json.loads(result["content"][0]["text"])

    if result_data.get("success"):
        print(f"✅ SUCCESS: Parsed {result_data['entities_parsed']} elements")
        print(f"   Output: {result_data['output_file']}")

        # Read and display sample
        with open(output_path) as f:
            parsed_data = json.load(f)
            print(f"   Total elements: {parsed_data['total_count']}")
            print(f"   Sample element types:")
            types = {}
            for elem in parsed_data['elements'][:10]:
                ifc_type = elem['ifc_type']
                types[ifc_type] = types.get(ifc_type, 0) + 1
            for ifc_type, count in sorted(types.items()):
                print(f"      - {ifc_type}: {count}")

        return output_path
    else:
        print(f"❌ FAILED: {result_data.get('error')}")
        return None


async def test_prepare_batches(json_path):
    """Test batch preparation tool."""
    print("\n" + "="*60)
    print("TEST 2: Prepare Classification Batches")
    print("="*60)

    output_path = "./workspace/.context/test/batches.json"
    batch_size = 100

    print(f"Input:  {json_path}")
    print(f"Output: {output_path}")
    print(f"Batch size: {batch_size}")

    # Call tool
    result = await prepare_batches({
        "json_path": json_path,
        "batch_size": batch_size,
        "output_path": output_path
    })

    # Parse result
    result_data = json.loads(result["content"][0]["text"])

    if result_data.get("success"):
        print(f"✅ SUCCESS: Created {result_data['total_batches']} batches")
        print(f"   Total elements: {result_data['total_elements']}")
        print(f"   Output: {result_data['output_file']}")

        # Read and display batch info
        with open(output_path) as f:
            batch_data = json.load(f)
            print(f"   Batch details:")
            for batch in batch_data['batches']:
                print(f"      - Batch {batch['batch_id']}: {batch['element_count']} elements")

        return output_path
    else:
        print(f"❌ FAILED: {result_data.get('error')}")
        return None


async def test_calculate_co2():
    """Test CO2 calculation tool (mock classified data)."""
    print("\n" + "="*60)
    print("TEST 3: Calculate CO2 Emissions")
    print("="*60)

    # Create mock classified data
    classified_path = "./workspace/.context/test/classified_mock.json"
    database_path = "./.claude/tools/durability_database.json"
    output_path = "./workspace/.context/test/co2_results.json"

    # Create mock classified elements
    mock_classified = {
        "elements": [
            {
                "guid": "test-001",
                "ifc_type": "IfcWall",
                "concrete_type": "Concrete_Structural",
                "volume_m3": 10.5
            },
            {
                "guid": "test-002",
                "ifc_type": "IfcSlab",
                "concrete_type": "Concrete_Floor",
                "volume_m3": 25.0
            },
            {
                "guid": "test-003",
                "ifc_type": "IfcColumn",
                "concrete_type": "Concrete_Structural",
                "volume_m3": 3.2
            }
        ]
    }

    with open(classified_path, 'w') as f:
        json.dump(mock_classified, f, indent=2)

    print(f"Classified: {classified_path} (3 mock elements)")
    print(f"Database:   {database_path}")
    print(f"Output:     {output_path}")

    # Call tool
    result = await calculate_co2({
        "classified_path": classified_path,
        "database_path": database_path,
        "output_path": output_path
    })

    # Parse result
    result_data = json.loads(result["content"][0]["text"])

    if result_data.get("success"):
        print(f"✅ SUCCESS: Calculated CO2 for {result_data['element_count']} elements")
        print(f"   Total CO2: {result_data['total_co2_kg']:.2f} kg")
        print(f"   Output: {result_data['output_file']}")

        # Read and display CO2 breakdown
        with open(output_path) as f:
            co2_data = json.load(f)
            print(f"   CO2 breakdown:")
            for elem in co2_data['elements']:
                print(f"      - {elem['ifc_type']}: {elem['volume_m3']:.1f} m³ × {elem['co2_factor']:.1f} = {elem['co2_kg']:.1f} kg CO2")

        return output_path
    else:
        print(f"❌ FAILED: {result_data.get('error')}")
        return None


async def main():
    """Run all tool tests."""
    print("\n" + "="*60)
    print("MCP TOOLS TEST SUITE - agent_system5")
    print("="*60)

    try:
        # Test 1: Parse IFC
        parsed_json = await test_parse_ifc()
        if not parsed_json:
            print("\n❌ Test suite aborted: IFC parsing failed")
            return 1

        # Test 2: Prepare batches
        batches_json = await test_prepare_batches(parsed_json)
        if not batches_json:
            print("\n❌ Test suite aborted: Batch preparation failed")
            return 1

        # Test 3: Calculate CO2 (with mock data)
        co2_results = await test_calculate_co2()
        if not co2_results:
            print("\n❌ Test suite aborted: CO2 calculation failed")
            return 1

        # Summary
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nMCP tools are working correctly:")
        print("  ✓ parse_ifc_file")
        print("  ✓ prepare_batches")
        print("  ✓ calculate_co2")
        print("\nNext step: Test orchestrator with ClaudeSDKClient")

        return 0

    except Exception as e:
        import traceback
        print(f"\n❌ TEST SUITE FAILED")
        print(f"Error: {e}")
        print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
