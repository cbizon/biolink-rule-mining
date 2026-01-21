"""Tests for rule_extractor module."""

import pandas as pd
import pytest
from rule_mining.rule_extractor import extract_rules, rank_rules


@pytest.fixture
def sample_rules_df():
    """Create a sample DataFrame of rules."""
    return pd.DataFrame({
        '3hop_metapath': [
            'Drug|affects|F|Gene|associated|F|Disease',
            'Drug|targets|F|Gene|causes|F|Disease',
            'Drug|binds|F|Protein|linked|F|Disease',
        ],
        '3hop_count': [1000, 500, 200],
        '1hop_count': [100, 100, 100],
        'overlap': [50, 80, 10],
        'Precision': [0.05, 0.16, 0.05],
        'Recall': [0.50, 0.80, 0.10],
        'F1': [0.09, 0.27, 0.07],
        'MCC': [0.10, 0.30, 0.05],
    })


def test_extract_rules_no_filter(sample_rules_df):
    """Test extracting rules without filters."""
    result = extract_rules(sample_rules_df)
    assert len(result) == 3


def test_extract_rules_min_precision(sample_rules_df):
    """Test filtering by minimum precision."""
    result = extract_rules(sample_rules_df, min_precision=0.10)
    assert len(result) == 1
    assert result.iloc[0]['3hop_metapath'] == 'Drug|targets|F|Gene|causes|F|Disease'


def test_extract_rules_min_recall(sample_rules_df):
    """Test filtering by minimum recall."""
    result = extract_rules(sample_rules_df, min_recall=0.50)
    assert len(result) == 2


def test_extract_rules_min_support(sample_rules_df):
    """Test filtering by minimum support."""
    result = extract_rules(sample_rules_df, min_support=50)
    assert len(result) == 2


def test_extract_rules_combined_filters(sample_rules_df):
    """Test combining multiple filters."""
    result = extract_rules(
        sample_rules_df,
        min_precision=0.05,
        min_recall=0.50,
        min_support=50,
    )
    assert len(result) == 2


def test_rank_rules_by_f1(sample_rules_df):
    """Test ranking rules by F1."""
    result = rank_rules(sample_rules_df, sort_by='F1', ascending=False)
    assert result.iloc[0]['F1'] == 0.27  # Highest F1


def test_rank_rules_by_precision(sample_rules_df):
    """Test ranking rules by precision."""
    result = rank_rules(sample_rules_df, sort_by='Precision', ascending=False)
    assert result.iloc[0]['Precision'] == 0.16


def test_rank_rules_invalid_column(sample_rules_df):
    """Test that invalid column raises error."""
    with pytest.raises(ValueError):
        rank_rules(sample_rules_df, sort_by='invalid_column')
