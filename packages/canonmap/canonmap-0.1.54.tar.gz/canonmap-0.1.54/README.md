# CanonMap

A powerful Python library for intelligent entity matching and data canonicalization. CanonMap uses advanced techniques to identify, match, and standardize entities across your datasets.

## Key Features

- **Multi-strategy Entity Matching**: Combines multiple matching strategies for robust entity identification:
  - Semantic matching (45%): Uses transformer embeddings for understanding meaning
  - Fuzzy matching (35%): Handles typos and variations
  - Initial matching (10%): Matches abbreviations and initials
  - Keyword matching (5%): Matches individual words
  - Phonetic matching (5%): Sound-based matching using Double Metaphone

- **Smart Scoring System**: Sophisticated scoring with bonus points for:
  - High semantic + fuzzy score combinations (+10 points)
  - Perfect initial matches (+10 points)
  - Perfect phonetic matches (+5 points)
  - Penalties for mismatched high fuzzy/low semantic scores (-15 points)

- **Intelligent Entity Extraction**:
  - Automatic entity detection using spaCy NER
  - Smart handling of name fields and patterns
  - Configurable uniqueness ratios and length thresholds
  - Support for both manual field selection and automatic extraction

- **Data Processing**:
  - CSV file processing with schema inference
  - Metadata generation and management
  - Entity normalization and standardization
  - Support for custom field mapping

## Installation

```bash
pip install canonmap
```

## Dependencies

- Python 3.8 or higher
- spaCy and its English language model (automatically downloaded on first use)

## Quick Start

```python
from canonmap import CanonMap

# Initialize the library
canon = CanonMap()

# Generate artifacts from a CSV file
artifacts = canon.generate_artifacts(
    csv_path="path/to/your/data.csv",
    output_path="output",  # Optional: directory to save artifacts
    name="my_data",        # Base name for output files
    entity_fields=["name", "email"],  # Optional: specify entity fields
    use_other_fields_as_metadata=True,  # Include other columns as metadata
    num_rows=None,  # Optional: limit number of rows to process
    embed=True  # Whether to compute and save embeddings
)

# The artifacts dictionary contains:
# - metadata: List of entity objects with their metadata
# - schema: Nested dictionary of data types and formats
# - paths: Dictionary of paths to saved artifacts
# - embeddings: Optional numpy array of entity embeddings

# Match entities against your data
matches = canon.match_entity(
    entity_term="John Smith",
    metadata_path=artifacts["paths"]["metadata"],
    schema_path=artifacts["paths"]["schema"],
    embedding_path=artifacts["paths"]["embeddings"],  # Required for semantic search
    top_k=5,  # Maximum number of results to return
    threshold=80.0,  # Minimum score threshold (default: 0)
    field_filter=["name", "contact_name"],  # Optional: restrict matching to specific fields
    use_semantic_search=True,  # Enable semantic search (default: False)
    weights=None  # Optional: customize matching strategy weights
)

# Process results
for match in matches:
    print(f"Entity: {match['entity']}")
    print(f"Score: {match['score']}")
    print(f"Passes: {match['passes']}")  # Number of matching strategies that passed
    print(f"Metadata: {match['metadata']}")
    print("---")
```

## Advanced Usage

### Custom Matching Weights

```python
# Customize the matching strategy weights
custom_weights = {
    'semantic': 0.50,  # Increase semantic matching importance
    'fuzzy': 0.30,     # Decrease fuzzy matching
    'initial': 0.10,   # Keep initial matching
    'keyword': 0.05,   # Keep keyword matching
    'phonetic': 0.05   # Keep phonetic matching
}

matches = canon.match_entity(
    entity_term="John Smith",
    metadata_path="metadata.pkl",
    schema_path="schema.pkl",
    embedding_path="embeddings.npz",  # Required for semantic search
    weights=custom_weights
)
```

### Field-Specific Matching

```python
# Restrict matching to specific fields
matches = canon.match_entity(
    entity_term="John Smith",
    metadata_path="metadata.pkl",
    schema_path="schema.pkl",
    embedding_path="embeddings.npz",
    field_filter=["customer_name", "contact_name"],
    use_semantic_search=True
)
```

## Features in Detail

### Entity Extraction
- Automatic detection of entity fields
- Support for custom entity field selection
- Intelligent handling of name patterns
- Configurable uniqueness thresholds
- Length-based filtering
- spaCy NER integration for complex text

### Matching Process
1. Semantic pruning (if enabled)
2. Multi-strategy scoring
3. Weighted combination of scores
4. Bonus/penalty application
5. Result ranking and filtering

### Data Processing
- Schema inference
- Data type detection
- Date format recognition
- Metadata generation
- Entity normalization
- Custom field mapping

## Requirements

- Python 3.8+
- See setup.py for full list of dependencies

## License

MIT License 