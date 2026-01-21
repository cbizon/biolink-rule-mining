"""
Extract association rules from metapath statistics.

Rules are of the form:
    3-hop metapath => 1-hop relationship

For example:
    Drug -> Gene -> Disease (3-hop) => Drug treats Disease (1-hop)

The strength of a rule is measured by metrics like precision, recall, and F1.
"""

import pandas as pd
from pathlib import Path
from typing import Iterator


def load_grouped_results(grouped_dir: Path) -> Iterator[tuple[str, pd.DataFrame]]:
    """
    Load all grouped metapath results from a directory.

    Args:
        grouped_dir: Path to directory containing grouped TSV files
                    (e.g., grouped_by_1hop/ from metapath-counts)

    Yields:
        Tuples of (1hop_metapath_name, DataFrame with 3hop rules)
    """
    grouped_path = Path(grouped_dir)

    for tsv_file in sorted(grouped_path.glob("*.tsv")):
        # Filename is the 1-hop metapath (e.g., Drug_treats_F_Disease.tsv)
        onehop_name = tsv_file.stem

        df = pd.read_csv(tsv_file, sep='\t')
        yield onehop_name, df


def extract_rules(
    df: pd.DataFrame,
    min_precision: float = 0.0,
    min_recall: float = 0.0,
    min_f1: float = 0.0,
    min_support: int = 0,
) -> pd.DataFrame:
    """
    Extract rules from a grouped metapath DataFrame.

    Args:
        df: DataFrame with columns including:
            - 3hop_metapath: The 3-hop path pattern
            - 3hop_count: Number of 3-hop paths
            - overlap: Paths that match the 1-hop relationship
            - Precision, Recall, F1, MCC, etc.
        min_precision: Minimum precision threshold
        min_recall: Minimum recall threshold
        min_f1: Minimum F1 threshold
        min_support: Minimum overlap count (support)

    Returns:
        Filtered DataFrame of rules meeting thresholds
    """
    filtered = df.copy()

    if 'Precision' in filtered.columns:
        filtered = filtered[filtered['Precision'] >= min_precision]

    if 'Recall' in filtered.columns:
        filtered = filtered[filtered['Recall'] >= min_recall]

    if 'F1' in filtered.columns:
        filtered = filtered[filtered['F1'] >= min_f1]

    if 'overlap' in filtered.columns:
        filtered = filtered[filtered['overlap'] >= min_support]

    return filtered


def rank_rules(
    df: pd.DataFrame,
    sort_by: str = 'F1',
    ascending: bool = False
) -> pd.DataFrame:
    """
    Rank rules by a specified metric.

    Args:
        df: DataFrame of rules
        sort_by: Column to sort by (e.g., 'F1', 'Precision', 'MCC')
        ascending: Sort order

    Returns:
        Sorted DataFrame
    """
    if sort_by not in df.columns:
        raise ValueError(f"Column '{sort_by}' not found. Available: {list(df.columns)}")

    return df.sort_values(sort_by, ascending=ascending).reset_index(drop=True)
