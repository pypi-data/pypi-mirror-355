# Natan Logical Engine (NLE)

![Natan Logical Engine](docs/NLE.png)

## Overview

Natan Logical Engine (NLE) is a simple natural language parser designed to interpret player commands in text-based games or interactive fiction. It processes input strings, removes stop words, resolves pronouns based on context, and extracts structured commands (verb and object) from user input.

## Features

- **Stop Word Removal:** Ignores common words that do not affect command meaning.
- **Pronoun Resolution:** Substitutes pronouns with the last referenced object for contextual understanding.
- **Syntactic Analysis:** Identifies verbs and objects from the input and returns structured commands.
- **Logging:** Provides detailed debug and info logs for development and debugging.

## Usage

Example usage in Python:

```python
from parser import NLEParser

config = {
    "language": "en-us",
}
vocabulary = {
    "pronouns": {"he", "she", "it", "this", "that"},
    "verbs": {"take", "look", "use"},
    "objects": {"key", "door", "box"},
}
stop_words = {"the", "a", "an", "of", "in", "on", "at", "to"}

parser = NLEParser(config, vocabulary, stop_words)

parsed_command = parser.parse("take the key")
print(parsed_command)  # Output: {'verb': 'take', 'object': 'key'}
```
