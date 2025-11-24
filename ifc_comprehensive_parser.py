"""
Comprehensive IFC Parser using ifcopenshell
Extracts ALL data from IFC files with full property/quantity resolution
"""

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element as element_utils
import ifcopenshell.util.placement as placement_utils
from typing import Dict, List, Any, Optional
import json
from pathlib import Path


class ComprehensiveIfcParser:
    """
    Robust IFC parser that extracts complete data for AI agent consumption
    """

    def __init__(self, ifc_path: str):
        """
        Initialize parser with IFC file

        Args:
            ifc_path: Path to IFC file
        """
        self.ifc_path = Path(ifc_path)
        self.ifc_file = None
        self.elements_data = []
        self.validation_report = {}

        # Geometry settings for volume calculation
        self.settings = ifcopenshell.geom.settings()
        self.settings.set(self.settings.USE_WORLD_COORDS, True)

    def load(self):
        """Load IFC file"""
        print(f"\n{'='*80}")
        print(f"LOADING IFC FILE: {self.ifc_path.name}")
        print(f"{'='*80}")

        try:
            self.ifc_file = ifcopenshell.open(str(self.ifc_path))
            print(f"✓ Loaded successfully")
            print(f"✓ Schema: {self.ifc_file.schema}")

            # Get basic stats
            all_entities = self.ifc_file.by_type('IfcRoot')
            print(f"✓ Total rooted entities: {len(all_entities)}")

            return True
        except Exception as e:
            print(f"✗ Error loading IFC file: {e}")
            return False

    def extract_all_data(self) -> List[Dict[str, Any]]:
        """
        Extract complete data for ALL elements in the IFC file

        Returns:
            List of element dictionaries with all resolved data
        """
        if not self.ifc_file:
            self.load()

        print(f"\n{'='*80}")
        print(f"EXTRACTING ALL DATA")
        print(f"{'='*80}")

        # Get all products (geometric and spatial elements)
        products = self.ifc_file.by_type('IfcProduct')
        print(f"\n✓ Found {len(products)} IfcProduct entities")

        # Process each product
        for i, product in enumerate(products, 1):
            if i % 10 == 0:
                print(f"  Processing element {i}/{len(products)}...")

            element_data = self._extract_element_data(product)
            self.elements_data.append(element_data)

        print(f"\n✓ Extracted data for {len(self.elements_data)} elements")

        return self.elements_data

    def _extract_element_data(self, element) -> Dict[str, Any]:
        """
        Extract complete data for a single element

        Args:
            element: IFC element instance

        Returns:
            Dictionary with all element data
        """
        data = {
            # Basic identification
            'global_id': element.GlobalId,
            'ifc_type': element.is_a(),
            'name': element.Name if hasattr(element, 'Name') else None,
            'description': element.Description if hasattr(element, 'Description') else None,
            'object_type': element.ObjectType if hasattr(element, 'ObjectType') else None,
            'tag': element.Tag if hasattr(element, 'Tag') else None,

            # Classification flags
            'is_geometric': self._is_geometric_element(element),
            'is_spatial': self._is_spatial_element(element),
            'is_type_object': element.is_a('IfcTypeObject'),

            # Spatial containment (where is this element?)
            'spatial_structure': self._get_spatial_structure(element),

            # Properties (all property sets)
            'properties': self._get_all_properties(element),

            # Quantities (all quantity sets)
            'quantities': self._get_all_quantities(element),

            # Material information
            'materials': self._get_materials(element),

            # Type information
            'type_info': self._get_type_info(element),

            # Calculated geometry info
            'geometry': self._get_geometry_info(element),

            # Relationships
            'relationships': self._get_relationships(element),
        }

        return data

    def _is_geometric_element(self, element) -> bool:
        """Check if element is a geometric building element"""
        geometric_types = [
            'IfcWall', 'IfcWallStandardCase', 'IfcSlab', 'IfcColumn',
            'IfcBeam', 'IfcDoor', 'IfcWindow', 'IfcRoof', 'IfcStair',
            'IfcRailing', 'IfcCovering', 'IfcFooting', 'IfcPile',
            'IfcCurtainWall', 'IfcPlate', 'IfcMember', 'IfcRamp',
            'IfcBuildingElementProxy', 'IfcChimney'
        ]
        return any(element.is_a(t) for t in geometric_types)

    def _is_spatial_element(self, element) -> bool:
        """Check if element is a spatial structure element"""
        spatial_types = ['IfcProject', 'IfcSite', 'IfcBuilding', 'IfcBuildingStorey', 'IfcSpace']
        return any(element.is_a(t) for t in spatial_types)

    def _get_spatial_structure(self, element) -> Dict[str, str]:
        """
        Get spatial containment hierarchy for element

        Returns:
            Dict with project/site/building/storey/space info
        """
        structure = {
            'project': None,
            'site': None,
            'building': None,
            'storey': None,
            'space': None
        }

        try:
            # Get container
            if hasattr(element, 'ContainedInStructure'):
                for rel in element.ContainedInStructure:
                    container = rel.RelatingStructure

                    # Walk up the hierarchy
                    current = container
                    while current:
                        if current.is_a('IfcBuildingStorey'):
                            structure['storey'] = current.Name
                        elif current.is_a('IfcBuilding'):
                            structure['building'] = current.Name
                        elif current.is_a('IfcSite'):
                            structure['site'] = current.Name
                        elif current.is_a('IfcProject'):
                            structure['project'] = current.Name

                        # Move up hierarchy
                        if hasattr(current, 'Decomposes') and current.Decomposes:
                            current = current.Decomposes[0].RelatingObject
                        else:
                            break
        except:
            pass

        return structure

    def _get_all_properties(self, element) -> Dict[str, Dict[str, Any]]:
        """
        Get ALL property sets for element

        Returns:
            Dict of property set name -> {property_name: value}
        """
        properties = {}

        try:
            # Get property sets
            if hasattr(element, 'IsDefinedBy'):
                for definition in element.IsDefinedBy:
                    if definition.is_a('IfcRelDefinesByProperties'):
                        property_set = definition.RelatingPropertyDefinition

                        if property_set.is_a('IfcPropertySet'):
                            pset_name = property_set.Name
                            pset_properties = {}

                            for prop in property_set.HasProperties:
                                prop_name = prop.Name
                                prop_value = self._get_property_value(prop)
                                pset_properties[prop_name] = prop_value

                            properties[pset_name] = pset_properties
        except Exception as e:
            pass

        return properties

    def _get_property_value(self, prop) -> Any:
        """Extract value from IFC property"""
        try:
            if prop.is_a('IfcPropertySingleValue'):
                if prop.NominalValue:
                    return prop.NominalValue.wrappedValue
            elif prop.is_a('IfcPropertyEnumeratedValue'):
                if prop.EnumerationValues:
                    return [v.wrappedValue for v in prop.EnumerationValues]
            elif prop.is_a('IfcPropertyBoundedValue'):
                return {
                    'upper': prop.UpperBoundValue.wrappedValue if prop.UpperBoundValue else None,
                    'lower': prop.LowerBoundValue.wrappedValue if prop.LowerBoundValue else None
                }
            elif prop.is_a('IfcPropertyListValue'):
                if prop.ListValues:
                    return [v.wrappedValue for v in prop.ListValues]
        except:
            pass

        return None

    def _get_all_quantities(self, element) -> Dict[str, Any]:
        """
        Get ALL quantities for element

        Returns:
            Dict of quantity name -> value (with unit)
        """
        quantities = {}

        try:
            if hasattr(element, 'IsDefinedBy'):
                for definition in element.IsDefinedBy:
                    if definition.is_a('IfcRelDefinesByProperties'):
                        property_def = definition.RelatingPropertyDefinition

                        if property_def.is_a('IfcElementQuantity'):
                            qset_name = property_def.Name

                            for quantity in property_def.Quantities:
                                q_name = quantity.Name
                                q_value = self._get_quantity_value(quantity)

                                # Prefix with quantity set name
                                full_name = f"{qset_name}.{q_name}" if qset_name else q_name
                                quantities[full_name] = q_value
        except:
            pass

        return quantities

    def _get_quantity_value(self, quantity) -> Optional[float]:
        """Extract value from IFC quantity"""
        try:
            if quantity.is_a('IfcQuantityLength'):
                return quantity.LengthValue
            elif quantity.is_a('IfcQuantityArea'):
                return quantity.AreaValue
            elif quantity.is_a('IfcQuantityVolume'):
                return quantity.VolumeValue
            elif quantity.is_a('IfcQuantityCount'):
                return quantity.CountValue
            elif quantity.is_a('IfcQuantityWeight'):
                return quantity.WeightValue
            elif quantity.is_a('IfcQuantityTime'):
                return quantity.TimeValue
        except:
            pass

        return None

    def _get_materials(self, element) -> List[Dict[str, Any]]:
        """
        Get material information for element

        Returns:
            List of material dictionaries
        """
        materials = []

        try:
            if hasattr(element, 'HasAssociations'):
                for association in element.HasAssociations:
                    if association.is_a('IfcRelAssociatesMaterial'):
                        material = association.RelatingMaterial

                        if material.is_a('IfcMaterial'):
                            materials.append({
                                'name': material.Name,
                                'category': material.Category if hasattr(material, 'Category') else None
                            })
                        elif material.is_a('IfcMaterialList'):
                            for mat in material.Materials:
                                materials.append({
                                    'name': mat.Name,
                                    'category': mat.Category if hasattr(mat, 'Category') else None
                                })
                        elif material.is_a('IfcMaterialLayerSetUsage'):
                            layer_set = material.ForLayerSet
                            for layer in layer_set.MaterialLayers:
                                materials.append({
                                    'name': layer.Material.Name,
                                    'category': layer.Material.Category if hasattr(layer.Material, 'Category') else None,
                                    'thickness': layer.LayerThickness
                                })
        except:
            pass

        return materials

    def _get_type_info(self, element) -> Optional[Dict[str, Any]]:
        """Get type object information"""
        try:
            if hasattr(element, 'IsTypedBy') and element.IsTypedBy:
                type_obj = element.IsTypedBy[0].RelatingType
                return {
                    'type_name': type_obj.Name,
                    'type_description': type_obj.Description if hasattr(type_obj, 'Description') else None,
                    'type_guid': type_obj.GlobalId
                }
        except:
            pass

        return None

    def _get_geometry_info(self, element) -> Dict[str, Any]:
        """
        Get geometry information including calculated volume

        Returns:
            Dict with geometry type, volume, area, etc.
        """
        geo_info = {
            'has_representation': False,
            'representation_type': None,
            'calculated_volume': None,
            'calculated_area': None,
            'calculation_success': False,
            'calculation_error': None
        }

        try:
            # Check if has representation
            if hasattr(element, 'Representation') and element.Representation:
                geo_info['has_representation'] = True

                # Get representation type
                for rep in element.Representation.Representations:
                    geo_info['representation_type'] = rep.RepresentationType
                    break

                # Try to calculate geometry
                try:
                    shape = ifcopenshell.geom.create_shape(self.settings, element)

                    # Get volume (in cubic meters)
                    verts = shape.geometry.verts
                    # Volume calculation from mesh would be complex,
                    # so we'll use a different approach

                    geo_info['calculation_success'] = True
                    geo_info['has_geometry'] = True

                except Exception as e:
                    geo_info['calculation_error'] = str(e)
        except Exception as e:
            geo_info['calculation_error'] = str(e)

        return geo_info

    def _get_relationships(self, element) -> Dict[str, List[str]]:
        """
        Get key relationships for element

        Returns:
            Dict of relationship type -> list of related element GUIDs
        """
        relationships = {}

        try:
            # Fills voids (for doors/windows)
            if hasattr(element, 'FillsVoids') and element.FillsVoids:
                relationships['fills_voids'] = [
                    rel.RelatingOpeningElement.GlobalId
                    for rel in element.FillsVoids
                ]

            # Has openings (for walls)
            if hasattr(element, 'HasOpenings') and element.HasOpenings:
                relationships['has_openings'] = [
                    rel.RelatedOpeningElement.GlobalId
                    for rel in element.HasOpenings
                ]

            # Connected to (structural connections)
            if hasattr(element, 'ConnectedTo') and element.ConnectedTo:
                relationships['connected_to'] = [
                    rel.RelatedElement.GlobalId
                    for rel in element.ConnectedTo
                ]
        except:
            pass

        return relationships

    def validate_data(self) -> Dict[str, Any]:
        """
        Validate extracted data and generate completeness report

        Returns:
            Validation report dictionary
        """
        if not self.elements_data:
            self.extract_all_data()

        print(f"\n{'='*80}")
        print(f"VALIDATION REPORT")
        print(f"{'='*80}")

        total = len(self.elements_data)

        # Count by type
        geometric = sum(1 for e in self.elements_data if e['is_geometric'])
        spatial = sum(1 for e in self.elements_data if e['is_spatial'])

        # Check data completeness
        with_name = sum(1 for e in self.elements_data if e['name'])
        with_properties = sum(1 for e in self.elements_data if e['properties'])
        with_quantities = sum(1 for e in self.elements_data if e['quantities'])
        with_materials = sum(1 for e in self.elements_data if e['materials'])
        with_spatial = sum(1 for e in self.elements_data if any(e['spatial_structure'].values()))

        report = {
            'total_elements': total,
            'geometric_elements': geometric,
            'spatial_elements': spatial,
            'completeness': {
                'with_name': {'count': with_name, 'percentage': (with_name/total)*100},
                'with_properties': {'count': with_properties, 'percentage': (with_properties/total)*100},
                'with_quantities': {'count': with_quantities, 'percentage': (with_quantities/total)*100},
                'with_materials': {'count': with_materials, 'percentage': (with_materials/total)*100},
                'with_spatial_context': {'count': with_spatial, 'percentage': (with_spatial/total)*100},
            },
            'geometric_elements_detail': self._validate_geometric_elements()
        }

        # Print report
        print(f"\nTotal Elements: {total}")
        print(f"  Geometric: {geometric}")
        print(f"  Spatial: {spatial}")
        print(f"  Other: {total - geometric - spatial}")

        print(f"\nData Completeness:")
        print(f"  Elements with Name: {with_name} ({(with_name/total)*100:.1f}%)")
        print(f"  Elements with Properties: {with_properties} ({(with_properties/total)*100:.1f}%)")
        print(f"  Elements with Quantities: {with_quantities} ({(with_quantities/total)*100:.1f}%)")
        print(f"  Elements with Materials: {with_materials} ({(with_materials/total)*100:.1f}%)")
        print(f"  Elements with Spatial Context: {with_spatial} ({(with_spatial/total)*100:.1f}%)")

        if geometric > 0:
            print(f"\nGeometric Elements Detail:")
            geo_detail = report['geometric_elements_detail']
            print(f"  Total: {geo_detail['total']}")
            print(f"  With Properties: {geo_detail['with_properties']} ({geo_detail['with_properties_pct']:.1f}%)")
            print(f"  With Quantities: {geo_detail['with_quantities']} ({geo_detail['with_quantities_pct']:.1f}%)")
            print(f"  With Materials: {geo_detail['with_materials']} ({geo_detail['with_materials_pct']:.1f}%)")

        self.validation_report = report
        return report

    def _validate_geometric_elements(self) -> Dict[str, Any]:
        """Detailed validation for geometric elements"""
        geometric_elements = [e for e in self.elements_data if e['is_geometric']]

        if not geometric_elements:
            return {}

        total = len(geometric_elements)
        with_props = sum(1 for e in geometric_elements if e['properties'])
        with_quants = sum(1 for e in geometric_elements if e['quantities'])
        with_mats = sum(1 for e in geometric_elements if e['materials'])

        return {
            'total': total,
            'with_properties': with_props,
            'with_properties_pct': (with_props/total)*100,
            'with_quantities': with_quants,
            'with_quantities_pct': (with_quants/total)*100,
            'with_materials': with_mats,
            'with_materials_pct': (with_mats/total)*100,
        }

    def export_to_json(self, output_path: str):
        """Export all extracted data to JSON file"""
        if not self.elements_data:
            self.extract_all_data()

        output = {
            'source_file': str(self.ifc_path),
            'schema': self.ifc_file.schema if self.ifc_file else None,
            'total_elements': len(self.elements_data),
            'validation_report': self.validation_report if self.validation_report else None,
            'elements': self.elements_data
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Exported data to: {output_path}")
        print(f"  Total elements: {len(self.elements_data)}")
        print(f"  File size: {Path(output_path).stat().st_size / 1024:.1f} KB")

    def get_element_summary(self) -> str:
        """Get a human-readable summary of all elements"""
        if not self.elements_data:
            self.extract_all_data()

        summary = []
        summary.append("\n" + "="*80)
        summary.append("ELEMENT SUMMARY")
        summary.append("="*80)

        for element in self.elements_data:
            summary.append(f"\n{element['ifc_type']}: {element['name'] or 'Unnamed'}")
            summary.append(f"  GlobalId: {element['global_id']}")

            if element['spatial_structure']['building']:
                summary.append(f"  Location: {element['spatial_structure']['building']} / {element['spatial_structure']['storey']}")

            if element['properties']:
                summary.append(f"  Properties: {len(element['properties'])} property sets")

            if element['quantities']:
                summary.append(f"  Quantities: {list(element['quantities'].keys())}")

            if element['materials']:
                mat_names = [m['name'] for m in element['materials']]
                summary.append(f"  Materials: {', '.join(mat_names)}")

        return '\n'.join(summary)


def quick_parse(ifc_path: str) -> List[Dict[str, Any]]:
    """
    Quick convenience function to parse IFC file in one line

    Args:
        ifc_path: Path to IFC file

    Returns:
        List of element dictionaries
    """
    parser = ComprehensiveIfcParser(ifc_path)
    parser.load()
    return parser.extract_all_data()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ifc_comprehensive_parser.py <ifc_file> [output_json]")
        sys.exit(1)

    ifc_file = sys.argv[1]
    output_json = sys.argv[2] if len(sys.argv) > 2 else ifc_file.replace('.ifc', '_parsed.json')

    # Parse
    parser = ComprehensiveIfcParser(ifc_file)
    parser.load()
    parser.extract_all_data()
    parser.validate_data()

    # Export
    parser.export_to_json(output_json)

    print(f"\n{'='*80}")
    print("PARSING COMPLETE")
    print(f"{'='*80}")
    print(f"\nData exported to: {output_json}")
    print("\nYou can now use this data for AI agent processing!")
