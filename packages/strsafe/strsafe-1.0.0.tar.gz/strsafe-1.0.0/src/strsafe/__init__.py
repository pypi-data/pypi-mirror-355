import re
from enum import Enum
from typing import Literal

from unidecode import unidecode


class CaseMode(Enum):
    """Case transformation modes."""

    LOWER = "lower"
    UPPER = "upper"
    UNCHANGED = "unchanged"


class StripMode(Enum):
    """Replacement character stripping modes."""

    BOTH = "both"
    START = "start"
    END = "end"
    NEITHER = "neither"


class StrSafe:
    """
    Transliterate Unicode strings to 'safe' ASCII strings suitable for
    filenames, identifiers, and other contexts where only basic ASCII characters
    would be 'safe' or allowed.

    Args:
        text: The original string to be modified
        case: Case transformation mode - 'lower', 'upper', or 'unchanged'
        replacement_char: Character used to replace disallowed characters
        allow_underscore: Whether to allow underscore characters
        allow_hyphen: Whether to allow hyphen characters
        allow_period: Whether to allow period characters
        collapse_replacement: Whether to collapse consecutive replacement chars
        strip_replacement: Where to strip replacement chars from result
        max_length: Maximum length of result string (None for no limit)

    Example:
        ```python
        >>> safe = StrSafe("Héllo Wörld!", case="lower", replacement_char="-")
        >>> str(safe)
        'hello-world'
        >>> safe.original
        'Héllo Wörld!'
        >>> StrSafe("Very long string", max_length=5)
        StrSafe(original='Very long string', safe='very_')
        ```
    """

    def __init__(
        self,
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
    ) -> None:
        """Initialize StrSafe with the given text and options."""
        self._original_string = text
        self._case = CaseMode(case)
        self._replacement_char = replacement_char
        self._allow_underscore = allow_underscore
        self._allow_hyphen = allow_hyphen
        self._allow_period = allow_period
        self._collapse_replacement = collapse_replacement
        self._strip_mode = StripMode(strip_replacement)
        self._max_length = max_length

        # Validate replacement character
        if len(replacement_char) > 1:
            raise ValueError("replacement_char must be a single character or empty string")

        # Validate max_length
        if max_length is not None and max_length < 0:
            raise ValueError("max_length must be non-negative or None")

        # Process the string
        self._safe_string = self._process_string(text)

    def _process_string(self, text: str) -> str:
        """Process the input string according to configuration."""
        # Step 1: Transliterate to ASCII
        ascii_text = unidecode(text)

        # Step 2: Apply case transformation
        if self._case == CaseMode.LOWER:
            ascii_text = ascii_text.lower()
        elif self._case == CaseMode.UPPER:
            ascii_text = ascii_text.upper()

        # Step 3: Build allowed character pattern
        allowed_chars = "a-zA-Z0-9"
        if self._allow_underscore:
            allowed_chars += "_"
        if self._allow_hyphen:
            allowed_chars += r"\-"
        if self._allow_period:
            allowed_chars += r"\."

        # Step 4: Replace disallowed characters
        result = re.sub(f"[^{allowed_chars}]", self._replacement_char, ascii_text)

        if self._replacement_char:
            # Step 5: Collapse consecutive replacement characters
            if self._collapse_replacement:
                result = re.sub(re.escape(self._replacement_char) + "{2,}", self._replacement_char, result)

            # Step 6: Strip replacement characters
            if self._strip_mode == StripMode.BOTH:
                result = result.strip(self._replacement_char)
            elif self._strip_mode == StripMode.START:
                result = result.lstrip(self._replacement_char)
            elif self._strip_mode == StripMode.END:
                result = result.rstrip(self._replacement_char)

        # Step 7: Check if truncation will occur and truncate
        if self._max_length is not None:
            pre_truncate_length = len(result)
            self._is_truncated = pre_truncate_length > self._max_length
            result = result[: self._max_length]
        else:
            self._is_truncated = False

        return result

    def __str__(self) -> str:
        """Return the 'safe' ASCII string."""
        return self._safe_string

    def __repr__(self) -> str:
        """Return a detailed string representation."""
        return f"StrSafe(original={self._original_string!r}, safe={self._safe_string!r})"

    def __eq__(self, other: object) -> bool:
        """Check equality with another StrSafe instance or string."""
        if isinstance(other, StrSafe):
            return self._safe_string == other._safe_string
        if isinstance(other, str):
            return self._safe_string == other
        return NotImplemented

    def __hash__(self) -> int:
        """Return hash of the safe string."""
        return hash(self._safe_string)

    def __len__(self) -> int:
        """Return length of the safe string."""
        return len(self._safe_string)

    def __bool__(self) -> bool:
        """Return True if safe string is non-empty."""
        return bool(self._safe_string)

    @property
    def original(self) -> str:
        """The original input string."""
        return self._original_string

    @property
    def safe(self) -> str:
        """The processed ASCII-safe string."""
        return self._safe_string

    @property
    def is_empty(self) -> bool:
        """Whether the safe string is empty."""
        return len(self._safe_string) == 0

    @property
    def is_truncated(self) -> bool:
        """Whether the result was truncated due to max_length."""
        return self._is_truncated

    def startswith(self, prefix: str) -> bool:
        """Check if safe string starts with prefix."""
        return self._safe_string.startswith(prefix)

    def endswith(self, suffix: str) -> bool:
        """Check if safe string ends with suffix."""
        return self._safe_string.endswith(suffix)
