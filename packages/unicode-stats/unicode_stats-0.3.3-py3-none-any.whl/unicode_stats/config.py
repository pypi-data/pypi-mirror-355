"""
Configuration module
    at config.json specified
{"character_mappings": {str: str}
"block_rules": {
    "preferred_blocks": List[str],
    "filtered_blocks": List[str]
    },
"block_to_lang_mapping": {str: str)
}
"""
from dataclasses import dataclass
from typing import Dict, List
import json
from pathlib import Path


class CharacterConflictError(Exception):
    """Exception raised when characters appear in multiple character sets."""


@dataclass
class Config:
    """Configuration class for Unicode stats."""
    character_mappings: Dict[str, str]
    preferred_blocks: List[str]
    filtered_blocks: List[str]
    block_to_lang_mapping: Dict[str, str]
    _replace_character_mapping: Dict[str, str] = None

    def __post_init__(self):
        """Build character mapping and validate after initialization."""
        self._build_character_mapping()
        self._validate()

    def _build_character_mapping(self):
        """
        Build the character-to-block mapping dictionary from configuration.

        Raises
        ------
        CharacterConflictError
            If any character appears in multiple character sets.
        """
        self._replace_character_mapping = {}

        for block_name, characters in self.character_mappings.items():
            for char in characters:
                if char in self._replace_character_mapping:
                    existing_block = self._replace_character_mapping[char]
                    raise CharacterConflictError(
                        f"Character '{char}' appears in both '{existing_block}' and '{block_name}'"
                    )
                self._replace_character_mapping[char] = block_name

    def _validate(self):
        """Validate configuration data."""
        if not isinstance(self.character_mappings, dict):
            raise ValueError("character_mappings must be a dictionary")

        if not isinstance(self.preferred_blocks, list):
            raise ValueError("preferred_blocks must be a list")

        if not isinstance(self.filtered_blocks, list):
            raise ValueError("filtered_blocks must be a list")

        if len(self.preferred_blocks) == 0:
            raise ValueError("preferred_blocks cannot be empty")

        if len(self.filtered_blocks) == 0:
            raise ValueError("filtered_blocks cannot be empty")

        # Check for overlaps between preferred and filtered blocks
        overlap = set(self.preferred_blocks) & set(self.filtered_blocks)
        if overlap:
            raise ValueError(f"Blocks cannot be both preferred and filtered: {overlap}")

    @property
    def character_mapping(self) -> Dict[str, str]:
        """Get the character-to-block mapping dictionary."""
        return self._replace_character_mapping

    def block_to_lang(self, block: str) -> str:
        """Convert block name to language code using configuration mapping."""
        return self.block_to_lang_mapping.get(block, block)

    @classmethod
    def load(cls, config_path: Path) -> 'Config':
        """Load configuration from JSON file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract data with validation - no .get() fallbacks
        try:
            character_mappings = data["character_mappings"]
            block_rules = data["block_rules"]
            preferred_blocks = block_rules["preferred_blocks"]
            filtered_blocks = block_rules["filtered_blocks"]
            block_to_lang_mapping = data["block_to_lang_mapping"]
        except KeyError as e:
            raise ValueError(f"Missing required config key: {e}") from e

        return cls(
            character_mappings=character_mappings,
            preferred_blocks=preferred_blocks,
            filtered_blocks=filtered_blocks,
            block_to_lang_mapping=block_to_lang_mapping
        )
