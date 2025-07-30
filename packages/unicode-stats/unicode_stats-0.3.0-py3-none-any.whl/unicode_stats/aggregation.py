"""
Module aggregated unicode block
use inverted index to aggregate unicode block statistics
"""
import json
import logging
from typing import List, Dict, Union
from pathlib import Path
from collections import Counter
import fire
from pandas import DataFrame
from unicode_stats import unicode_block_parser


class ExceptionFileInput(Exception):
    """Exception raised for errors in the input JSON file."""


class AggregatedUnicodeBlockParser:
    """
    A parser that aggregates Unicode block statistics from JSONL data files.

    Parameters
    ----------
    columns : str, list of str, or None, optional
        Specify columns to process in each JSON object.
        If None (default), all columns are processed.
    convert_non_str_to_str : bool, optional
        If True, non-string values are converted to strings. Default is False.
    max_lines : int, optional
        Maximum number of lines to read from the input file. Default is 10000.

    Examples
    --------
    >>> parser = AggregatedUnicodeBlockParser(columns="qwen")
    >>> df = parser.get_stats("3model_cp.jsonl")
    >>> print(df)
    > |    | block   | column   |    n |   rate | symbols   |   n_symbols | rows   | example_first   | example_last   |
    > |---:|:--------|:---------|-----:|-------:|:----------|------------:|:-------|:----------------|:---------------|
    > |  0 | Cyril   | qwen     | 2161 |  0.777 | оеаи      |       57234 | [0, 1  | Чтобы           | Для р          |
    > |  1 | Basic   | qwen     | 2778 |  1     | оеаи      |       57234 | [0, 1  | Чтобы           | Для р          |
    """

    def __init__(self,
                 columns: Union[str, List[str], None] = None,
                 convert_non_str_to_str: bool = False,
                 max_lines: int = 10000
                 ):
        self.columns = [columns] if isinstance(columns, str) else columns
        self.convert_non_str_to_str = convert_non_str_to_str
        self.max_lines = max_lines
        self.n_total = 0

    def create_inv_index(self, list_of_dicts: List[Dict]) -> Dict[str, Dict[str, Dict[str, object]]]:
        """
        Creates an inverted index for Unicode blocks found in the dataset.

        Parameters
        ----------
        list_of_dicts : list of dict
            List of dictionaries representing JSON data, each containing one row.

        Returns
        -------
        dict
            Nested dictionary structure with block statistics organized by column and Unicode block.

        Notes
        -----
        This method iterates through each row and column, grouping character data by Unicode block.
        Counts are maintained for symbols and occurrences within the column.

        Example of output
        -----
             {
                'Cyrillic (Russian)': {
                    'qwen': (
                        {0},
                        Counter({
                            ' ': 140, 'е': 38, 'и': 31, 'о': 27, 'т': 20, 'а': 19, 'м': 19, 'н': 18,
                            'л': 18, 'р': 17, '\n': 17, 'в': 15, 'с': 13, ',': 11, 'я': 11, 'n': 11,
                            'i': 11, 'ы': 10, '(': 10, ')': 10
                        }),
                        1
                    )
                },
                'Basic Latin': {
                    'qwen': (
                        {0},
                        Counter({
                            ' ': 140, 'e': 38, 'i': 31, 'o': 27, 't': 20, 'a': 19, 'm': 19, 'n': 18,
                            'l': 18, 'r': 17, '\n': 17, 's': 15, ',': 13, 'y': 11, 'd': 11, '(': 10,
                            ')': 10, 'p': 9
                        }),
                        1
                    )
                }
            }

        """
        inv_dict = {}
        self.n_total = len(list_of_dicts)

        for row_num, dct in enumerate(list_of_dicts):
            columns_list = self.columns if self.columns else dct.keys()
            for column in columns_list:
                value = dct.get(column)

                if not isinstance(value, str):
                    if self.convert_non_str_to_str:
                        value = str(value)
                    else:
                        continue

                if not value:
                    continue

                all_symbol_counter = Counter(value)
                block_stat_dict = unicode_block_parser.get_stats(value)

                for block_name, statistics in block_stat_dict.items():
                    symbol_counter = Counter({k: v
                                              for k, v in all_symbol_counter.items()
                                              if k in statistics['symbols']
                                              }
                                             )

                    if block_name not in inv_dict:
                        inv_dict[block_name] = {}

                    if column not in inv_dict[block_name]:
                        inv_dict[block_name][column] = [{row_num}, symbol_counter, 1]
                    else:
                        stats_before = inv_dict[block_name][column]
                        stats_before[0].add(row_num)
                        stats_before[1].update(symbol_counter)
                        stats_before[2] += 1
        return inv_dict

    def create_aggregated_statistics(self, inv_dict: Dict, list_of_dicts: List[Dict]) -> Dict:
        """
        Aggregates statistics from the inverted index to generate Unicode block summaries.

        Parameters
        ----------
        inv_dict : dict
            Inverted index dictionary with Unicode block statistics.
        list_of_dicts : list of dict
            Original JSON data for extracting example text.

        Returns
        -------
        dict
            Aggregated statistics for Unicode blocks and columns, including symbol counts and sample rows.
        """
        stats_dict = {}
        for block_name, dct in inv_dict.items():
            for column_name, (row_set, symbols_counter, n) in dct.items():
                symbols = "".join([char for char, _ in symbols_counter.most_common()])
                n_symbols = sum(symbols_counter.values())
                rows_list_str = json.dumps(list(row_set))

                example_first = list_of_dicts[next(iter(row_set))][column_name]
                example_last = None if len(row_set) == 1 else list_of_dicts[list(row_set)[-1]][column_name]

                stats_dict[(block_name, column_name)] = {
                    "n": n,
                    "rate": n / self.n_total,
                    "symbols": symbols,
                    "n_symbols": n_symbols,
                    "rows": rows_list_str,
                    "example_first": example_first,
                    "example_last": example_last,
                }
        return stats_dict

    def get_aggregated_statistics_df(self, list_of_dicts: List[Dict]) -> DataFrame:
        """
        Generates a DataFrame with aggregated Unicode block statistics.

        Parameters
        ----------
        list_of_dicts : list of dict
            List of dictionaries for Unicode block parsing.

        Returns
        -------
        pandas.DataFrame
            Aggregated statistics DataFrame with Unicode block and column data.
        """
        inv_dict = self.create_inv_index(list_of_dicts)
        stats_dict = self.create_aggregated_statistics(inv_dict, list_of_dicts)
        df_result = DataFrame(stats_dict).T
        df_result.reset_index(names=["block", "column"], inplace=True)
        return df_result

    def read_jsonl(self, fn: str) -> List[Dict]:
        """
        Reads a JSONL (JSON Lines) file and returns a list of dictionaries.

        Parameters
        ----------
        fn : str
            The filename of the JSONL file.

        Returns
        -------
        list of dict
            Parsed JSON data as a list of dictionaries.

        Raises
        ------
        ExceptionFileInput
            If there is an error reading or parsing the file.
        """
        data = []
        try:
            with open(fn, 'r', encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if line:
                        data.append(json.loads(line))
                    if len(data) >= self.max_lines:
                        break
            return data
        except (FileNotFoundError, IOError) as e:
            logging.error("File error in %s: %s", fn, e)
            raise ExceptionFileInput(f"Error reading file {fn}: {e}") from e
        except json.JSONDecodeError as e:
            logging.error("JSON parsing error in %s: %s", fn, e)
            raise ExceptionFileInput(f"Error parsing JSON in {fn}: {e}") from e

    def get_stats(self, fn_input: str) -> DataFrame:
        """
        Reads a JSONL file and returns aggregated Unicode statistics as a DataFrame.

        Parameters
        ----------
        fn_input : str
            Filename of the JSONL file to process.

        Returns
        -------
        pandas.DataFrame
            Aggregated statistics DataFrame with Unicode block and column data.
        """
        list_of_dicts = self.read_jsonl(fn_input)
        return self.get_aggregated_statistics_df(list_of_dicts)


def main_fire(fn_input: str, fn_output: str = 'auto', columns: Union[str, List[str], None] = None,
              convert_non_str_to_str: bool = False, max_lines: int = 10000):
    """
    Runs the AggregatedUnicodeBlockParser and saves the output to a CSV file.

    Parameters
    ----------
    fn_input : str
        Path to the input JSONL file.
    fn_output : str
        Path to the output CSV file. (Auto to fn_output = fn_input - '.jsonl' + '.png')
    columns : str, list of str, or None, optional
        Columns to include. None (default) includes all columns.
    convert_non_str_to_str : bool, optional
        Whether to convert non-string values to strings. Default is False.
    max_lines : int, optional
        Maximum number of lines to read from the input file. Default is 10000.
    """
    if fn_output == 'auto':
        fn_output = Path(fn_input).name[:-len(".jsonl")] + '.csv'

    parser = AggregatedUnicodeBlockParser(columns=columns,
                                          convert_non_str_to_str=convert_non_str_to_str,
                                          max_lines=max_lines)
    df = parser.get_stats(fn_input)
    df.to_csv(fn_output, index=False)
    print(f"Aggregated statistics saved to {fn_output}")


def main_bash_entry_point():
    """ There are a bug inside fire NAME COULD'T BE main """
    fire.Fire(main_fire)


if __name__ == "__main__":
    main_bash_entry_point()
