"""
    Parse url "https://www.unicode.org/Public/UNIDATA/Blocks.txt"
    Get mapping symbol <-> block
    Fast search for block by symbol
    Some hand rules how to aggregate blocks to detect cyrillic issues
"""
import os
import json
import bisect
from collections import Counter
from functools import lru_cache
from pathlib import Path
import requests
from .singleton import SingletonClass
from .config import Config, CharacterConflictError


class ConfigurationError(Exception):
    """Exception raised for errors in configuration file."""


class UnicodeBlockParser(SingletonClass):
    """Parser that identifies and aggregates Unicode block information from text strings."""

    fn_cache_dataset = fn_template = Path(__file__).parent / "cache/unicode_block.json"
    config_path = Path(__file__).parent / "config.json"
    UNICODE_BLOCKS_URL = "https://www.unicode.org/Public/UNIDATA/Blocks.txt"

    def __init__(self):
        """Initialize UnicodeBlockParser by loading cached Unicode block data and configuration."""
        if not os.path.exists(self.fn_cache_dataset):
            self.read_dataset_from_web()
        self.read_dataset_local()
        self._load_config()

    def read_dataset_from_web(self):
        """
        Download Unicode block data from the Unicode Consortium and cache locally.

        Notes
        -----
        Fetches Unicode block ranges from "https://www.unicode.org/Public/UNIDATA/Blocks.txt"
        and saves the data in JSON format for local use.
        """
        response = requests.get(self.UNICODE_BLOCKS_URL, timeout=10)
        response.raise_for_status()
        text = response.text
        data = []
        for line in text.splitlines():
            line_no_comment = line.split('#')[0]
            if line_no_comment:
                row = line_no_comment.replace('..', ';').split(';')
                row[2] = row[2].strip()
                left = int(row[0], 16)
                right = int(row[1], 16)
                data.append({"block": row[2], "l": left, "r": right})
        with open(self.fn_cache_dataset, "w", encoding="utf-8") as file:
            json.dump(data, file)

    def read_dataset_local(self):
        """
        Loads Unicode block data from the local cache file into memory.

        Notes
        -----
        This method populates `data`, `blocks`, and `r_ind` attributes with
        Unicode block names, block ranges, and range endpoints respectively.
        """
        with open(self.fn_cache_dataset, "r", encoding="utf-8") as file:
            self.data = json.load(file)
        self.blocks = [line['block'] for line in self.data]
        self.r_ind = [line['r'] for line in self.data]

    def _load_config(self):
        """Load configuration from config.json."""
        try:
            self.config = Config.load(self.config_path)
        except (FileNotFoundError, ValueError, json.JSONDecodeError, CharacterConflictError) as e:
            raise ConfigurationError(f"Failed to load configuration: {e}") from e

    @property
    def preferred_blocks(self):
        """Returns the list of preferred Unicode blocks from configuration."""
        return self.config.preferred_blocks

    @property
    def filtered_blocks(self):
        """Returns the list of filtered Unicode blocks from configuration."""
        return self.config.filtered_blocks

    @lru_cache(maxsize=5000)
    def get_single_block(self, s: str) -> str:
        """
        Determines the Unicode block name for a single character.

        Parameters
        ----------
        s : str
            A single character string.

        Returns
        -------
        str
            The name of the Unicode block to which the character belongs.

        Raises
        ------
        AssertionError
            If input `s` is not a single character.

        Examples
        --------
        >>> parser = UnicodeBlockParser()
        >>> parser.get_single_block('A')
        'Basic Latin'
        """
        assert len(s) == 1, "Input must be a single character."

        # Check custom character mappings first
        if s in self.config.character_mapping:
            return self.config.character_mapping[s]

        # Fall back to Unicode block detection
        unicode_val = ord(s)
        index = bisect.bisect_left(self.r_ind, unicode_val)

        return self.blocks[index]

    def get_stats(self, s: str) -> dict:
        """
        Aggregates Unicode block statistics for each character in a string.

        Parameters
        ----------
        s : str
            The input string to analyze.

        Returns
        -------
        dict
            A dictionary where keys are Unicode block names and values are dictionaries
            containing the number of characters (`n`) and symbols present (`symbols`).

        Examples
        --------
        >>> parser = UnicodeBlockParser()
        >>> parser.get_stats("Hello, Привет")
        {'Basic Latin': {'n': 7, 'symbols': 'Helo,'},
         'Cyrillic (Russian)': {'n': 6, 'symbols': 'Привет'}}
        """
        symbol_counts = Counter(s)
        stats = {}

        for char, count in symbol_counts.items():
            block = self.get_single_block(char)
            if block in stats:
                stats[block]['n'] += count
                stats[block]['symbols'].add(char)
            else:
                stats[block] = {"n": count, "symbols": set(char)}

        for block in list(stats.keys()):
            stats[block]['symbols'] = ''.join(sorted(stats[block]['symbols'], key=lambda x: -symbol_counts[x]))

        return stats

    def get_single_lang(self, s: str) -> str:
        """
        Identifies the primary language or Unicode block of the input string.

        Parameters
        ----------
        s : str
            Input string.

        Returns
        -------
        str
            The primary language or Unicode block based on the most common block in `s`.

        Examples
        --------
        >>> parser = UnicodeBlockParser()
        >>> parser.get_single_lang("Привет, мир!")
        'Cyrillic (Russian)'
        """
        if not s:
            return "unk"

        stats = self.get_stats(s)
        primary_block = max(stats.items(), key=lambda x: x[1]['n'])[0]
        return self.config.block_to_lang(primary_block)

    def get_all_lang(self, s: str) -> str:
        """
        Lists all languages or Unicode blocks represented in the input string.

        Parameters
        ----------
        s : str
            Input string.

        Returns
        -------
        str
            Comma-separated string of all detected languages or Unicode blocks.

        Examples
        --------
        >>> parser = UnicodeBlockParser()
        >>> parser.get_all_lang("Hello, Привет")
        'Basic Latin,Cyrillic (Russian)'
        """
        if not s:
            return "unk"

        stats = self.get_stats(s)
        all_blocks = ','.join([self.config.block_to_lang(block) for block, _ in sorted(stats.items(), key=lambda x: -x[1]['n'])])
        return all_blocks

    def get_lang(self, s: str, return_main_lang: bool = True) -> str:
        """
        Determines the primary or all languages in the input string based on Unicode blocks.

        Parameters
        ----------
        s : str
            Input string to analyze.
        return_main_lang : bool, optional
            If True (default), returns the primary language or block. If False, returns all.

        Returns
        -------
        str
            Primary language if `return_main_lang` is True, otherwise all languages or blocks.

        Examples
        --------
        >>> parser = UnicodeBlockParser()
        >>> parser.get_lang("Hello, Привет", return_main_lang=True)
        'Basic Latin'
        >>> parser.get_lang("Hello, Привет", return_main_lang=False)
        'Basic Latin,Cyrillic (Russian)'
        """
        return self.get_single_lang(s) if return_main_lang else self.get_all_lang(s)
