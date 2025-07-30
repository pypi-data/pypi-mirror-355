# Immersive Projects CG Pipeline Schema Suite

A JSON Schema designed to ensure consistent data structure across production pipelines.

## 🌟 Features

* **Core shot schema** – validates every scene or sub-scene with detailed metadata
* **Project schema** – wraps all shots for whole-show validation and global settings
* **Enum packs** – single source of truth for techniques, risk flags, screen zones, and more
* **Taxonomy packs** – human-friendly categorization for UI components
* **LLM I/O schema** – guarantees safe, auditable AI edits
* **Comprehensive examples** – real-world usage patterns and edge cases
* **Automated testing** – full validation suite with edge case coverage
* **ESM/CommonJS Support** – dual module format support for modern Node.js environments

## 📦 Installation

```bash
# npm
npm install immerschema@1.3.0

# pip
pip install immerschema==1.3.0
```

## 📦 Project Structure

```
immerschema/
├── schemas/                    # Core JSON Schema files
│   ├── enum/                  # Enumeration schemas
│   ├── ext/                   # Extension schemas
│   ├── io/                    # Input/Output schemas
│   └── taxonomy/              # Taxonomy definitions
├── examples/                   # Comprehensive examples
├── test/                      # Test files and validation
└── scripts/
    └── test_runner.js         # Automated test runner
```

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
npm install

# Or install AJV globally for command-line validation
npm run install-global-ajv
```

### Basic Validation

```bash
# Validate a shot against core schema
ajv validate -s schemas/core.schema.json -d examples/simple_shot.json

# Validate whole project
ajv validate -s schemas/project.schema.json -d examples/simple_project.json

# Run all automated tests
npm test
```

## 🧪 Testing & Validation

### Automated Test Suite

Run the comprehensive test suite:

```bash
npm test
```

This validates:
- All example files against their schemas
- Edge cases and boundary conditions
- Invalid input detection
- Enum value validation
- Required field enforcement

### Manual Testing

```bash
# Test individual files
ajv validate -s schemas/core.schema.json -d test/edge_cases.json

# Test with verbose output
ajv validate -s schemas/project.schema.json -d examples/comprehensive_project.json --verbose
```


```bash
# Install dependencies
npm install

# Run tests during development
npm test

# Validate specific examples
npm run validate-shot examples/ai_generated_shot.json
npm run validate-project examples/comprehensive_project.json
```

## 📄 License

MIT License - see LICENSE file for details.

---
