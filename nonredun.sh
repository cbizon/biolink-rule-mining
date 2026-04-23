uv run python scripts/prepare_graph.py \
      --input ../translator_kg/March_19 \
      --output ../translator_kg/March_19_filtered_nonredundant \
      --filter-predicates biolink:subclass_of \
      --no-redundant \
      --max-degree-per-type 10000 
