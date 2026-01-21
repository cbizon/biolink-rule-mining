# Biolink Rule Mining

Mine association rules from biolink metapath statistics.

## Overview

This package analyzes metapath statistics from [metapath-counts](https://github.com/cbizon/metapath-counts) to discover association rules that predict relationships in biolink knowledge graphs.

**Rule format:**
```
3-hop metapath => 1-hop relationship
```

**Example:**
```
Drug -> Gene -> Disease => Drug treats Disease
```

## Installation

```bash
git clone https://github.com/cbizon/biolink-rule-mining.git
cd biolink-rule-mining
uv venv
uv pip install -e .
```

## Prerequisites

You need output from `metapath-counts`:

```bash
# Run metapath-counts first to generate grouped_by_1hop/
cd /path/to/metapath-counts
./run_analysis.sh
```

This creates the `grouped_by_1hop/` directory with TSV files containing metapath statistics.

## Quick Start

### Mine Top Rules

```bash
uv run python scripts/mine_rules.py \
    --input /path/to/metapath-counts/grouped_by_1hop \
    --output top_rules.tsv \
    --top 100 \
    --sort-by F1
```

### Apply Thresholds

```bash
uv run python scripts/mine_rules.py \
    --input /path/to/metapath-counts/grouped_by_1hop \
    --output filtered_rules.tsv \
    --min-precision 0.1 \
    --min-recall 0.05 \
    --min-support 10
```

### Summary by 1-Hop Metapath

```bash
uv run python scripts/mine_rules.py \
    --input /path/to/metapath-counts/grouped_by_1hop \
    --output summary.tsv \
    --summary
```

## Library Usage

```python
from rule_mining.rule_ranker import get_top_rules, summarize_by_onehop
from pathlib import Path

# Get top 100 rules
rules = get_top_rules(
    Path("/path/to/grouped_by_1hop"),
    n=100,
    sort_by='F1',
    min_precision=0.1,
)

# Summarize by 1-hop metapath
summary = summarize_by_onehop(Path("/path/to/grouped_by_1hop"))
```

## Output Format

### Rules Output

| Column | Description |
|--------|-------------|
| 3hop_metapath | The 3-hop path pattern |
| 3hop_count | Number of 3-hop path instances |
| 1hop_metapath | The predicted 1-hop relationship |
| overlap | Paths matching both patterns |
| Precision | overlap / 3hop_count |
| Recall | overlap / 1hop_count |
| F1 | Harmonic mean of precision and recall |
| MCC | Matthews correlation coefficient |
| 1hop_target | The 1-hop metapath file this came from |

### Summary Output

| Column | Description |
|--------|-------------|
| 1hop_metapath | The 1-hop relationship |
| total_rules | Number of 3-hop rules for this 1-hop |
| mean_precision | Average precision across rules |
| mean_recall | Average recall across rules |
| mean_f1 | Average F1 across rules |
| max_f1 | Best F1 score |
| rules_with_f1_gt_0.5 | Count of rules with F1 > 0.5 |

## Metrics

- **Precision**: What fraction of 3-hop predictions are correct?
- **Recall**: What fraction of true 1-hop edges are captured?
- **F1**: Balance between precision and recall
- **MCC**: Matthews correlation coefficient (handles class imbalance)
- **Support**: Number of overlapping instances

## Testing

```bash
uv run pytest
```

## License

MIT License - see LICENSE file.

## Related Projects

- [metapath-counts](https://github.com/cbizon/metapath-counts) - Generate metapath statistics
- [pathfilter](https://github.com/cbizon/pathfilter) - Path filtering and evaluation
