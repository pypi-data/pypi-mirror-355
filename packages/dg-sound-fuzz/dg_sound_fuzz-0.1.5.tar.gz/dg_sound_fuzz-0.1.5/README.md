
A Python package for fuzzy string matching and name scoring using sound-based algorithms.

## Features

- Sound-based string matching
- Configurable matching rules
- Singleton engine pattern for efficient resource usage
- Easy-to-use API for name matching score calculation

## Installation

```bash
pip install dg-sound-fuzz
```

## Usage

```python
from dg_sound_fuzz import get_score

# Get matching score between two strings
score = get_score("John Doe", "Jon Doe")
print(score)  # Returns a float between 0 and 100
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.