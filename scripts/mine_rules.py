#!/usr/bin/env python3
"""
Mine association rules from metapath-counts output.

Usage:
    uv run python scripts/mine_rules.py \
        --input /path/to/grouped_by_1hop \
        --output top_rules.tsv \
        --top 100 \
        --sort-by F1 \
        --min-precision 0.1 \
        --min-support 10
"""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from rule_mining.rule_ranker import get_top_rules, summarize_by_onehop, aggregate_all_rules


def main():
    parser = argparse.ArgumentParser(
        description='Mine association rules from metapath statistics'
    )
    parser.add_argument('--input', required=True,
                        help='Path to grouped_by_1hop directory from metapath-counts')
    parser.add_argument('--output', required=True,
                        help='Output TSV file for rules')
    parser.add_argument('--top', type=int, default=None,
                        help='Return only top N rules (default: all)')
    parser.add_argument('--sort-by', default='F1',
                        choices=['F1', 'Precision', 'Recall', 'MCC', 'overlap'],
                        help='Metric to sort by (default: F1)')
    parser.add_argument('--min-precision', type=float, default=0.0,
                        help='Minimum precision threshold (default: 0.0)')
    parser.add_argument('--min-recall', type=float, default=0.0,
                        help='Minimum recall threshold (default: 0.0)')
    parser.add_argument('--min-f1', type=float, default=0.0,
                        help='Minimum F1 threshold (default: 0.0)')
    parser.add_argument('--min-support', type=int, default=0,
                        help='Minimum support/overlap count (default: 0)')
    parser.add_argument('--summary', action='store_true',
                        help='Output summary by 1-hop metapath instead of rules')

    args = parser.parse_args()

    input_dir = Path(args.input)
    if not input_dir.exists():
        print(f"ERROR: Input directory not found: {input_dir}")
        sys.exit(1)

    print("=" * 80)
    print("MINING ASSOCIATION RULES")
    print("=" * 80)
    print(f"\nInput: {input_dir}")
    print(f"Output: {args.output}")
    print(f"\nFilters:")
    print(f"  Min precision: {args.min_precision}")
    print(f"  Min recall: {args.min_recall}")
    print(f"  Min F1: {args.min_f1}")
    print(f"  Min support: {args.min_support}")

    if args.summary:
        print("\nGenerating summary by 1-hop metapath...")
        df = summarize_by_onehop(input_dir)
        print(f"Found {len(df)} 1-hop metapaths")
    elif args.top:
        print(f"\nExtracting top {args.top} rules by {args.sort_by}...")
        df = get_top_rules(
            input_dir,
            n=args.top,
            sort_by=args.sort_by,
            min_precision=args.min_precision,
            min_recall=args.min_recall,
            min_f1=args.min_f1,
            min_support=args.min_support,
        )
        print(f"Found {len(df)} rules")
    else:
        print(f"\nExtracting all rules, sorted by {args.sort_by}...")
        df = aggregate_all_rules(
            input_dir,
            min_precision=args.min_precision,
            min_recall=args.min_recall,
            min_f1=args.min_f1,
            min_support=args.min_support,
        )
        if len(df) > 0:
            df = df.sort_values(args.sort_by, ascending=False).reset_index(drop=True)
        print(f"Found {len(df)} rules")

    # Save output
    df.to_csv(args.output, sep='\t', index=False)
    print(f"\nSaved to: {args.output}")

    # Print preview
    if len(df) > 0:
        print(f"\nTop 5 results:")
        print(df.head().to_string())

    print("\n" + "=" * 80)
    print("COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
