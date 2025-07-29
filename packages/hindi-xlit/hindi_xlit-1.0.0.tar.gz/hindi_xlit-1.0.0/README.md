# Hindi Transliteration Library

A Python library for transliterating English text to Hindi using AI4Bharat's model. This library provides a simple interface for converting English words to their Hindi (Devanagari) equivalents.

## Features

- Simple and intuitive API
- Supports both single word and batch transliteration
- Returns multiple transliteration candidates
- CPU-only implementation (no GPU required)
- Interactive command-line interface

## Installation

```bash
pip install hindi-xlit
```

## Usage

### Basic Usage

```python
from hindi_xlit import HindiTransliterator

# Initialize the transliterator
transliterator = HindiTransliterator()

# Transliterate a single word
word = "namaste"
candidates = transliterator.transliterate(word)
print(f"Transliteration candidates for '{word}':")
for i, candidate in enumerate(candidates, 1):
    print(f"{i}. {candidate}")

# Transliterate multiple words
words = ["hello", "world"]
results = transliterator.transliterate_batch(words)
for word, candidates in zip(words, results):
    print(f"\nTransliteration candidates for '{word}':")
    for i, candidate in enumerate(candidates, 1):
        print(f"{i}. {candidate}")
```

### Command Line Interface

The library provides an interactive command-line interface:

```bash
hindi-xlit
```

Available commands:
- Type a word to transliterate
- Type multiple words separated by spaces for batch transliteration
- Type `topk N` to change the number of candidates (default: 5)
- Type `help` to show help
- Type `quit` or `exit` to exit

## API Reference

### HindiTransliterator

The main class for Hindi transliteration.

#### Methods

- `transliterate(word: str, topk: int = 5) -> List[str]`
  - Transliterates a single word to Hindi
  - Returns a list of top-k transliteration candidates

- `transliterate_batch(words: List[str], topk: int = 5) -> List[List[str]]`
  - Transliterates multiple words to Hindi
  - Returns a list of lists, where each inner list contains top-k transliteration candidates for the corresponding word

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

This library uses the transliteration model from [AI4Bharat](https://github.com/AI4Bharat/IndicXlit).
