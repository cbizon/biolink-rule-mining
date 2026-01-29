#!/usr/bin/env python3
"""CLI script to prepare graphs for metapath analysis.

Filters and augments knowledge graphs by:
1. Filtering out specified predicates (default: subclass_of)
2. Removing orphaned nodes
3. Generating redundant edges (ancestor predicates and qualifier combinations)
"""

import argparse
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from prepare import prepare_graph


def main():
    parser = argparse.ArgumentParser(
        description="Prepare knowledge graph by filtering and augmenting edges",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Input directory containing nodes.jsonl and edges.jsonl",
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output directory for filtered/augmented graph",
    )

    parser.add_argument(
        "--filter-predicates",
        nargs="*",
        default=["biolink:subclass_of"],
        help="Predicates to filter out (default: biolink:subclass_of)",
    )

    args = parser.parse_args()

    try:
        prepare_graph(
            input_dir=args.input,
            output_dir=args.output,
            filter_predicates=args.filter_predicates,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
