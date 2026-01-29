"""Generate redundant edges by inferring ancestor predicates and qualifier combinations."""

from itertools import product
from typing import Iterator
import bmt


class RedundantEdgeGenerator:
    """Generate redundant edges from original edges."""

    def __init__(self):
        self.toolkit = bmt.Toolkit()

    def get_predicate_ancestors(self, predicate: str) -> list[str]:
        """Get ancestor predicates from biolink model."""
        # Remove biolink: prefix if present for bmt lookup
        pred_name = predicate.replace("biolink:", "").replace("_", " ")

        ancestors = []
        try:
            # Get ancestors includes the element itself, so skip the first one
            all_ancestors = self.toolkit.get_ancestors(pred_name)
            if all_ancestors and len(all_ancestors) > 1:
                # Skip first element (the predicate itself)
                for ancestor in all_ancestors[1:]:
                    # Format with biolink: prefix and underscores
                    formatted = f"biolink:{ancestor.replace(' ', '_')}"
                    ancestors.append(formatted)
        except Exception:
            # If predicate not found, return empty list
            pass

        return ancestors

    def get_qualifier_ancestors(self, qualifier_value: str) -> list[str]:
        """Get ancestor values for a qualifier from biolink model.

        Handles both regular elements and enum values (e.g., direction/aspect qualifiers).
        """
        # Remove any prefix for lookup
        qual_name = qualifier_value.split(":")[-1] if ":" in qualifier_value else qualifier_value

        ancestors = [qual_name]  # Start with original

        # Check qualifier enums for is_a relationships
        for enum_name in ['DirectionQualifierEnum', 'GeneOrGeneProductOrChemicalEntityAspectEnum']:
            try:
                enum_def = self.toolkit.get_element(enum_name)
                if enum_def and hasattr(enum_def, 'permissible_values'):
                    if qual_name in enum_def.permissible_values:
                        # Walk up the is_a chain for this enum value
                        current = enum_def.permissible_values[qual_name]
                        while current and hasattr(current, 'is_a') and current.is_a:
                            parent = current.is_a
                            if parent not in ancestors:
                                ancestors.append(parent)
                            # Get the parent's definition to continue walking
                            if parent in enum_def.permissible_values:
                                current = enum_def.permissible_values[parent]
                            else:
                                break
                        return ancestors
            except Exception:
                pass

        # If not found in enums, try regular element hierarchy
        try:
            # Convert underscores to spaces for element lookup
            element_name = qual_name.replace("_", " ")
            all_ancestors = self.toolkit.get_ancestors(element_name)
            if all_ancestors:
                ancestors = [a.replace(" ", "_") for a in all_ancestors]
        except Exception:
            pass

        return ancestors

    def encode_qualifiers_in_predicate(self, predicate: str, direction: str | None, aspect: str | None) -> str:
        """Encode qualifiers into predicate name as predicate_direction_aspect."""
        parts = [predicate]

        if direction:
            # Remove namespace prefix if present
            direction_val = direction.split(":")[-1] if ":" in direction else direction
            parts.append(direction_val)

        if aspect:
            # Remove namespace prefix if present
            aspect_val = aspect.split(":")[-1] if ":" in aspect else aspect
            parts.append(aspect_val)

        return "_".join(parts)

    def create_edge_variant(
        self,
        original_edge: dict,
        predicate: str,
        direction: str | None = None,
        aspect: str | None = None,
    ) -> dict:
        """Create an edge variant with encoded predicate and no qualifier fields."""
        edge = original_edge.copy()

        # Encode qualifiers into predicate name
        edge["predicate"] = self.encode_qualifiers_in_predicate(predicate, direction, aspect)

        # Remove qualifier fields
        if "qualifiers" in edge:
            del edge["qualifiers"]
        if "object_direction_qualifier" in edge:
            del edge["object_direction_qualifier"]
        if "object_aspect_qualifier" in edge:
            del edge["object_aspect_qualifier"]
        if "qualified_predicate" in edge:
            del edge["qualified_predicate"]

        return edge

    def generate_redundant_edges(self, edge: dict) -> Iterator[dict]:
        """Generate all redundant edges from an original edge.

        For edges with qualifiers:
        1. Original edge with qualifiers encoded in predicate
        2. All permutations of qualifier ancestors encoded in predicate
        3. Original predicate with no qualifiers
        4. Ancestor predicates with no qualifiers

        For edges without qualifiers:
        1. Original edge as-is
        2. Ancestor predicates with no qualifiers
        """
        original_predicate = edge["predicate"]

        # Extract qualifiers from edge
        # Qualifiers might be in a "qualifiers" dict or as separate fields
        direction = None
        aspect = None

        if "qualifiers" in edge:
            # Parse qualifiers - could be dict or list
            qualifiers = edge["qualifiers"]
            if isinstance(qualifiers, dict):
                direction = qualifiers.get("object_direction_qualifier")
                aspect = qualifiers.get("object_aspect_qualifier")
            # If list, we'd need different parsing - skip for now

        # Also check for direct fields
        if "object_direction_qualifier" in edge:
            direction = edge["object_direction_qualifier"]
        if "object_aspect_qualifier" in edge:
            aspect = edge["object_aspect_qualifier"]

        has_qualifiers = direction is not None or aspect is not None

        if has_qualifiers:
            # Get qualifier ancestors
            direction_values = [None]  # Always include None (no qualifier)
            aspect_values = [None]

            if direction:
                direction_ancestors = self.get_qualifier_ancestors(direction)
                direction_values.extend(direction_ancestors)

            if aspect:
                aspect_ancestors = self.get_qualifier_ancestors(aspect)
                aspect_values.extend(aspect_ancestors)

            # Generate all permutations with original predicate
            for dir_val, asp_val in product(direction_values, aspect_values):
                # Skip the (None, None) case - we'll handle that separately
                if dir_val is None and asp_val is None:
                    continue
                yield self.create_edge_variant(edge, original_predicate, dir_val, asp_val)

            # Original predicate with no qualifiers
            yield self.create_edge_variant(edge, original_predicate, None, None)
        else:
            # No qualifiers - yield original edge as-is
            yield edge.copy()

        # Generate ancestor predicate versions (always without qualifiers)
        ancestor_predicates = self.get_predicate_ancestors(original_predicate)
        for ancestor_pred in ancestor_predicates:
            yield self.create_edge_variant(edge, ancestor_pred, None, None)
