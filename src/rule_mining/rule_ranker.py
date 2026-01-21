"""
Rank and score association rules across multiple 1-hop relationships.

Provides utilities for:
- Aggregating rules across all 1-hop metapaths
- Computing global rankings
- Identifying top rules by various metrics
"""

import pandas as pd
from pathlib import Path
from .rule_extractor import load_grouped_results, extract_rules, rank_rules


def aggregate_all_rules(
    grouped_dir: Path,
    min_precision: float = 0.0,
    min_recall: float = 0.0,
    min_f1: float = 0.0,
    min_support: int = 0,
) -> pd.DataFrame:
    """
    Load and aggregate rules from all grouped result files.

    Args:
        grouped_dir: Path to grouped_by_1hop directory
        min_precision: Minimum precision threshold
        min_recall: Minimum recall threshold
        min_f1: Minimum F1 threshold
        min_support: Minimum support (overlap count)

    Returns:
        DataFrame with all rules, including '1hop_metapath' column
    """
    all_rules = []

    for onehop_name, df in load_grouped_results(grouped_dir):
        filtered = extract_rules(
            df,
            min_precision=min_precision,
            min_recall=min_recall,
            min_f1=min_f1,
            min_support=min_support,
        )

        if len(filtered) > 0:
            filtered = filtered.copy()
            filtered['1hop_target'] = onehop_name
            all_rules.append(filtered)

    if not all_rules:
        return pd.DataFrame()

    return pd.concat(all_rules, ignore_index=True)


def get_top_rules(
    grouped_dir: Path,
    n: int = 100,
    sort_by: str = 'F1',
    min_precision: float = 0.0,
    min_recall: float = 0.0,
    min_f1: float = 0.0,
    min_support: int = 0,
) -> pd.DataFrame:
    """
    Get the top N rules across all 1-hop relationships.

    Args:
        grouped_dir: Path to grouped_by_1hop directory
        n: Number of top rules to return
        sort_by: Metric to sort by
        min_precision: Minimum precision threshold
        min_recall: Minimum recall threshold
        min_f1: Minimum F1 threshold
        min_support: Minimum support

    Returns:
        DataFrame with top N rules
    """
    all_rules = aggregate_all_rules(
        grouped_dir,
        min_precision=min_precision,
        min_recall=min_recall,
        min_f1=min_f1,
        min_support=min_support,
    )

    if len(all_rules) == 0:
        return all_rules

    ranked = rank_rules(all_rules, sort_by=sort_by, ascending=False)
    return ranked.head(n)


def summarize_by_onehop(grouped_dir: Path) -> pd.DataFrame:
    """
    Summarize rule statistics for each 1-hop metapath.

    Args:
        grouped_dir: Path to grouped_by_1hop directory

    Returns:
        DataFrame with summary statistics per 1-hop metapath
    """
    summaries = []

    for onehop_name, df in load_grouped_results(grouped_dir):
        summary = {
            '1hop_metapath': onehop_name,
            'total_rules': len(df),
            'mean_precision': df['Precision'].mean() if 'Precision' in df.columns else None,
            'mean_recall': df['Recall'].mean() if 'Recall' in df.columns else None,
            'mean_f1': df['F1'].mean() if 'F1' in df.columns else None,
            'max_f1': df['F1'].max() if 'F1' in df.columns else None,
            'rules_with_f1_gt_0.5': (df['F1'] > 0.5).sum() if 'F1' in df.columns else None,
        }
        summaries.append(summary)

    return pd.DataFrame(summaries)
