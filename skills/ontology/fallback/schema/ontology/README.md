# MIF Ontology Schema

This directory contains the schema definitions for MIF ontology files.

## Files

### ontology.schema.json

JSON Schema (draft 2020-12) for validating ontology YAML files. Key features:

- **Hierarchical namespaces**: Supports cognitive triad hierarchy (semantic/episodic/procedural) with nested children
- **Entity types**: Custom entity definitions with traits and JSON Schema validation
- **Discovery patterns**: Content and file pattern matching for entity suggestions
- **Relationships**: Typed relationships between entities

### ontology.context.jsonld

JSON-LD context for semantic web compatibility. Maps ontology concepts to:

- **Schema.org** for common properties (name, description, version)
- **SKOS** for concept hierarchies
- **OWL** for relationship semantics
- **Custom MIF vocabulary** for memory-specific concepts

## Usage

### Validating an ontology file

```bash
# Using ajv-cli
npx ajv validate -s ontology.schema.json -d ../../ontologies/mif-base.ontology.yaml

# Using Python jsonschema
python -c "
import json, yaml
from jsonschema import validate

with open('ontology.schema.json') as f:
    schema = json.load(f)
with open('../../ontologies/mif-base.ontology.yaml') as f:
    data = yaml.safe_load(f)
validate(data, schema)
print('Valid!')
"
```

### Converting to JSON-LD

```bash
python ../../scripts/yaml2jsonld.py ../../ontologies/mif-base.ontology.yaml
```

## Schema Evolution

- **v1.0** (current): Cognitive triad hierarchy with nested namespaces

When updating the schema:
1. Increment version in `$id`
2. Update CHANGELOG.md
3. Regenerate JSON-LD files from YAML sources
