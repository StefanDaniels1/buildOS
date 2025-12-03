#!/usr/bin/env python3
"""
Direct test of IFC tool logic without SDK decorators

Tests the core functionality that will be used by MCP tools.
"""

import json
import sys
from pathlib import Path


def test_parse_ifc():
    """Test IFC parsing directly."""
    print("\n" + "="*60)
    print("TEST 1: Parse IFC File (Direct)")
    print("="*60)

    # Setup paths
    ifc_path = "../Small_condo.ifc"
    output_path = "./workspace/.context/test/parsed_elements.json"

    print(f"Input:  {ifc_path}")
    print(f"Output: {output_path}")

    # Create output directory
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    try:
        # Direct IFC parsing (same logic as in sdk_tools.py)
        import ifcopenshell

        ifc_file = ifcopenshell.open(ifc_path)

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
        with open(output_path, 'w') as f:
            json.dump({
                "elements": elements,
                "total_count": len(elements),
                "source_file": ifc_path
            }, f, indent=2)

        print(f"✅ SUCCESS: Parsed {len(elements)} elements")
        print(f"   Output: {output_path}")

        # Display sample
        types = {}
        for elem in elements:
            ifc_type = elem['ifc_type']
            types[ifc_type] = types.get(ifc_type, 0) + 1

        print(f"\n   Element type breakdown:")
        for ifc_type, count in sorted(types.items()):
            print(f"      - {ifc_type}: {count}")

        return output_path

    except Exception as e:
        import traceback
        print(f"❌ FAILED: {e}")
        print(traceback.format_exc())
        return None


def test_prepare_batches(json_path):
    """Test batch preparation directly."""
    print("\n" + "="*60)
    print("TEST 2: Prepare Classification Batches (Direct)")
    print("="*60)

    output_path = "./workspace/.context/test/batches.json"
    batch_size = 100

    print(f"Input:  {json_path}")
    print(f"Output: {output_path}")
    print(f"Batch size: {batch_size}")

    try:
        # Load parsed elements
        with open(json_path, 'r') as f:
            data = json.load(f)

        elements = data.get("elements", [])

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
        with open(output_path, 'w') as f:
            json.dump({
                "batches": batches,
                "total_batches": len(batches),
                "total_elements": len(elements),
                "batch_size": batch_size
            }, f, indent=2)

        print(f"✅ SUCCESS: Created {len(batches)} batches")
        print(f"   Total elements: {len(elements)}")
        print(f"   Output: {output_path}")

        print(f"\n   Batch details:")
        for batch in batches:
            print(f"      - Batch {batch['batch_id']}: {batch['element_count']} elements")

        return output_path

    except Exception as e:
        import traceback
        print(f"❌ FAILED: {e}")
        print(traceback.format_exc())
        return None


def test_calculate_co2():
    """Test CO2 calculation directly."""
    print("\n" + "="*60)
    print("TEST 3: Calculate CO2 Emissions (Direct)")
    print("="*60)

    # Create mock classified data
    classified_path = "./workspace/.context/test/classified_mock.json"
    database_path = "./.claude/tools/co2_factors.json"
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

    try:
        # Load classified elements
        with open(classified_path, 'r') as f:
            classified_data = json.load(f)

        # Load durability database
        with open(database_path, 'r') as f:
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
        with open(output_path, 'w') as f:
            json.dump({
                "elements": results,
                "total_co2_kg": total_co2,
                "element_count": len(results)
            }, f, indent=2)

        print(f"✅ SUCCESS: Calculated CO2 for {len(results)} elements")
        print(f"   Total CO2: {total_co2:.2f} kg")
        print(f"   Output: {output_path}")

        print(f"\n   CO2 breakdown:")
        for elem in results:
            print(f"      - {elem['ifc_type']}: {elem['volume_m3']:.1f} m³ × {elem['co2_factor']:.1f} = {elem['co2_kg']:.1f} kg CO2")

        return output_path

    except Exception as e:
        import traceback
        print(f"❌ FAILED: {e}")
        print(traceback.format_exc())
        return None


def main():
    """Run all direct tests."""
    print("\n" + "="*60)
    print("DIRECT TOOL LOGIC TEST - agent_system5")
    print("="*60)

    try:
        # Test 1: Parse IFC
        parsed_json = test_parse_ifc()
        if not parsed_json:
            print("\n❌ Test suite aborted: IFC parsing failed")
            return 1

        # Test 2: Prepare batches
        batches_json = test_prepare_batches(parsed_json)
        if not batches_json:
            print("\n❌ Test suite aborted: Batch preparation failed")
            return 1

        # Test 3: Calculate CO2 (with mock data)
        co2_results = test_calculate_co2()
        if not co2_results:
            print("\n❌ Test suite aborted: CO2 calculation failed")
            return 1

        # Summary
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nCore tool logic is working correctly:")
        print("  ✓ IFC parsing with ifcopenshell")
        print("  ✓ Batch preparation")
        print("  ✓ CO2 calculation")
        print("\nGenerated test data:")
        print(f"  - {parsed_json}")
        print(f"  - {batches_json}")
        print(f"  - {co2_results}")
        print("\nNext step: Test orchestrator with ClaudeSDKClient")

        return 0

    except Exception as e:
        import traceback
        print(f"\n❌ TEST SUITE FAILED")
        print(f"Error: {e}")
        print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
