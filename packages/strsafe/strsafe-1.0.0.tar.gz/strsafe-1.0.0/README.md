# StrSafe

Transliterate Unicode strings to 'safe' ASCII strings suitable for filenames, identifiers, and other contexts where only basic ASCII characters would be 'safe' or allowed.

## Installation

### uv

```shell
uv add strsafe
```

### pip

```shell
pip install strsafe
```

### Requirements

- Python 3.10+
- [unidecode](https://pypi.org/project/Unidecode/)

## Quick Start

```python
from strsafe import StrSafe

# Basic usage
safe = StrSafe("Héllo Wörld! 🌍")
print(safe)  # "hello_world"
print(safe.original)  # "Héllo Wörld! 🌍"

# Custom configuration
safe = StrSafe(
    "Café & Restaurant",
    case="upper",
    replacement_char="-",
    allow_hyphen=True,
    max_length=10
)
print(safe)  # "CAFE-RESTA"
```

## API Reference

### StrSafe Class

#### Constructor

```python
StrSafe(
    text: str,
    *,
    case: Literal["lower", "upper", "unchanged"] = "lower",
    replacement_char: str = "_",
    allow_underscore: bool = True,
    allow_hyphen: bool = False,
    allow_period: bool = False,
    collapse_replacement: bool = True,
    strip_replacement: Literal["both", "start", "end", "neither"] = "both",
    max_length: int | None = 64,
)
```

#### Properties

- `original: str` - The original input string
- `safe: str` - The processed ASCII string
- `is_truncated: bool` - Whether the result was truncated
- `is_empty: bool` - Whether the safe string is empty

#### Methods

- `startswith(prefix: str) -> bool` - Check if safe string starts with prefix
- `endswith(suffix: str) -> bool` - Check if safe string ends with suffix

#### String Methods

- `str(safe)` - Get the safe string
- `len(safe)` - Get length of safe string
- `bool(safe)` - Check if safe string is non-empty
- `safe == other` - Compare with another StrSafe or string
- `hash(safe)` - Get hash of safe string

## Processing Pipeline

The library processes strings through these steps:

1. Transliterate to ASCII with [unidecode](https://pypi.org/project/Unidecode/).
2. Apply case transformation ('lower', 'upper', or 'unchanged').
3. Replace or remove disallowed characters.
4. Collapse consecutive replacement characters.
5. Strip replacement characters from start/end.
6. Truncate to `max_length`.

## Error Handling

```python
# Invalid replacement character
StrSafe("test", replacement_char="ab")  # ValueError: replacement_char must be a single character or empty string

# Invalid max_length
StrSafe("test", max_length=-1)  # ValueError: max_length must be non-negative or None
```

## License

MIT License - see LICENSE file for details.
