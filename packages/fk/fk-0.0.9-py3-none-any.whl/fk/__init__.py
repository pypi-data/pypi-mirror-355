"""
F.K. - FactKit: A lightweight Python package for managing and querying simple factual knowledge bases,
enabling quick lookup and retrieval of structured data for AI applications.
"""

from collections.abc import Mapping, MutableMapping
import os
import json
import csv
import pandas as pd
from dol import TextFiles, wrap_kvs
from typing import Union, Dict, Any, Iterable, List, Optional, Callable

# Define package version
__version__ = "0.1.0"

# Expose key components directly
__all__ = [
    "KnowledgeBase",
    "load_from_csv",
    "load_from_json",
    "save_to_csv",
    "save_to_json",
    "create_store",
    "create_mall",
]


class KnowledgeBase(MutableMapping):
    """
    A simple, in-memory knowledge base that uses a pandas DataFrame
    as its underlying storage. It provides a MutableMapping interface
    for easy interaction.
    """

    def __init__(self, data: Optional[Union[pd.DataFrame, Dict, Iterable]] = None):
        if isinstance(data, pd.DataFrame):
            self._data = data
        elif isinstance(data, Mapping):
            self._data = pd.DataFrame([data])
        elif isinstance(data, Iterable) and not isinstance(data, str):
            # Try to convert iterable of mappings to DataFrame
            try:
                self._data = pd.DataFrame(list(data))
            except Exception:
                self._data = pd.DataFrame()  # Initialize empty if conversion fails
                if data:
                    print(
                        f"Warning: Could not convert input data to DataFrame. Initializing empty KB. Input type: {type(data)}"
                    )
        else:
            self._data = pd.DataFrame()

        # Set index to allow key-based access if a 'id' or 'key' column exists
        if 'id' in self._data.columns:
            self._data.set_index('id', inplace=True, drop=False)
        elif 'key' in self._data.columns:
            self._data.set_index('key', inplace=True, drop=False)
        elif not self._data.empty:
            # If no explicit ID column, create a default integer index
            self._data['fk_id'] = range(len(self._data))
            self._data.set_index('fk_id', inplace=True, drop=False)

    def __getitem__(self, key: Any) -> Dict[str, Any]:
        """Retrieve a fact by its primary key (index)."""
        if isinstance(key, int) and 'fk_id' in self._data.columns:
            # Handle integer index if 'fk_id' was created
            if key not in self._data['fk_id'].values:
                raise KeyError(f"Key {key} not found in knowledge base.")
            row = self._data[self._data['fk_id'] == key].iloc[0]
        else:
            try:
                row = self._data.loc[key]
            except KeyError:
                raise KeyError(f"Key {key} not found in knowledge base.")
        return row.to_dict()

    def __setitem__(self, key: Any, value: Dict[str, Any]):
        """Add or update a fact. Key should correspond to the index if set, or a new fact if not."""
        if not isinstance(value, Mapping):
            raise ValueError("Value must be a dictionary-like object.")

        # Ensure the value contains the key if the KB has a dedicated key/id column
        if 'id' in self._data.columns and 'id' not in value:
            value['id'] = key
        elif 'key' in self._data.columns and 'key' not in value:
            value['key'] = key
        elif 'fk_id' in self._data.columns and 'fk_id' not in value:
            value['fk_id'] = key

        new_row = pd.DataFrame([value])

        # If a dedicated index column exists, ensure the new row has it
        if 'id' in self._data.columns and 'id' in new_row.columns:
            new_row.set_index('id', inplace=True, drop=False)
        elif 'key' in self._data.columns and 'key' in new_row.columns:
            new_row.set_index('key', inplace=True, drop=False)
        elif 'fk_id' in self._data.columns and 'fk_id' in new_row.columns:
            new_row.set_index('fk_id', inplace=True, drop=False)
        else:  # Default behavior if no specific ID column
            pass  # pandas will infer/handle index

        # Update existing row or append new row
        if key in self._data.index:
            self._data.loc[key] = new_row.loc[key]
        else:
            self._data = pd.concat([self._data, new_row])
            if 'fk_id' in self._data.columns:  # Re-index if default fk_id was used
                self._data['fk_id'] = range(len(self._data))
                self._data.set_index('fk_id', inplace=True, drop=False)

    def __delitem__(self, key: Any):
        """Delete a fact by its primary key (index)."""
        if isinstance(key, int) and 'fk_id' in self._data.columns:
            # Handle integer index if 'fk_id' was created
            if key not in self._data['fk_id'].values:
                raise KeyError(f"Key {key} not found in knowledge base.")
            self._data = self._data[self._data['fk_id'] != key].reset_index(drop=True)
            # Re-create fk_id if it was present
            if 'fk_id' in self._data.columns:
                self._data['fk_id'] = range(len(self._data))
                self._data.set_index('fk_id', inplace=True, drop=False)
        else:
            try:
                self._data.drop(index=key, inplace=True)
            except KeyError:
                raise KeyError(f"Key {key} not found in knowledge base.")

    def __len__(self) -> int:
        """Return the number of facts in the knowledge base."""
        return len(self._data)

    def __iter__(self) -> Iterable[Any]:
        """Iterate over the primary keys (index) of the facts."""
        return iter(self._data.index)

    def query(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Query the knowledge base using key-value filters.
        Returns a list of matching facts (dictionaries).
        """
        if filters is None:
            return self._data.to_dict(orient='records')

        filtered_df = self._data.copy()
        for col, value in filters.items():
            if col in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[col] == value]
            else:
                # If a filter column doesn't exist, no matches
                return []
        return filtered_df.to_dict(orient='records')

    def to_dataframe(self) -> pd.DataFrame:
        """Return the underlying pandas DataFrame."""
        return self._data.copy()

    def from_dataframe(self, df: pd.DataFrame):
        """Load data from a pandas DataFrame, replacing current knowledge."""
        self._data = df.copy()
        if 'id' in self._data.columns:
            self._data.set_index('id', inplace=True, drop=False)
        elif 'key' in self._data.columns:
            self._data.set_index('key', inplace=True, drop=False)
        elif 'fk_id' in self._data.columns:
            self._data.set_index('fk_id', inplace=True, drop=False)
        else:
            self._data['fk_id'] = range(len(self._data))
            self._data.set_index('fk_id', inplace=True, drop=False)


# --- Facades for Storage ---


def create_store(store_path: str, format: str = 'json') -> MutableMapping:
    """
    Creates a MutableMapping interface for a local directory,
    handling different file formats.

    Args:
        store_path (str): The path to the local directory.
        format (str): The format of the files ('json' or 'csv').
                      For CSV, it expects a single CSV file in the directory
                      which it treats as the entire knowledge base.
    Returns:
        MutableMapping: An object that behaves like a dictionary for file operations.
    """
    if not os.path.isdir(store_path):
        os.makedirs(store_path, exist_ok=True)

    if format == 'json':
        # TextFiles with json serialization/deserialization
        @wrap_kvs(obj_of_data=json.loads, data_of_obj=json.dumps)
        class JsonFiles(TextFiles):
            pass

        return JsonFiles(store_path)
    elif format == 'csv':
        # For CSV, we'll treat the entire directory as a single CSV
        # This is a bit of a hack to fit MutableMapping, as CSV is not
        # naturally a key-value store of individual items.
        # We'll use a single file name 'knowledge.csv'
        csv_filepath = os.path.join(store_path, 'knowledge.csv')

        class CsvFileStore(MutableMapping):
            def __init__(self, filepath):
                self.filepath = filepath
                self._data = self._read_csv()

            def _read_csv(self):
                if os.path.exists(self.filepath) and os.path.getsize(self.filepath) > 0:
                    return pd.read_csv(
                        self.filepath, index_col=0
                    )  # Assume first column is index
                return pd.DataFrame()

            def _write_csv(self):
                self._data.to_csv(self.filepath)

            def __getitem__(self, key):
                if key not in self._data.index:
                    raise KeyError(key)
                return self._data.loc[key].to_dict()

            def __setitem__(self, key, value):
                if not isinstance(value, Mapping):
                    raise ValueError("Value must be a dictionary-like object.")
                new_row = pd.DataFrame([value], index=[key])
                if key in self._data.index:
                    self._data.loc[key] = new_row.loc[key]
                else:
                    self._data = pd.concat([self._data, new_row])
                self._write_csv()

            def __delitem__(self, key):
                if key not in self._data.index:
                    raise KeyError(key)
                self._data.drop(index=key, inplace=True)
                self._write_csv()

            def __len__(self):
                return len(self._data)

            def __iter__(self):
                return iter(self._data.index)

            def items(self):
                return self._data.to_dict(orient='index').items()

        return CsvFileStore(csv_filepath)
    else:
        raise ValueError("Unsupported format. Choose 'json' or 'csv'.")


def create_mall(store_configs: Dict[str, Dict[str, str]]) -> Dict[str, MutableMapping]:
    """
    Creates a 'mall' (dictionary) of stores based on provided configurations.

    Args:
        store_configs (Dict[str, Dict[str, str]]): A dictionary where keys are
            store names and values are dictionaries with 'path' and 'format' keys.
            Example: {'facts': {'path': './data/facts', 'format': 'json'},
                      'metadata': {'path': './data/meta.csv', 'format': 'csv'}}

    Returns:
        Dict[str, MutableMapping]: A dictionary mapping store names to their
                                   respective MutableMapping interfaces.
    """
    mall = {}
    for name, config in store_configs.items():
        path = config.get('path')
        format = config.get('format', 'json')  # Default to json if not specified
        if not path:
            raise ValueError(
                f"Missing 'path' for store '{name}' in mall configuration."
            )

        # If the path points to a file directly, we need to adjust for the CSV store
        # which expects a directory for the dol.TextFiles or our custom CsvFileStore
        if format == 'csv' and not os.path.isdir(path):
            # If path is a file, we treat its parent directory as the store path
            # and name the file 'knowledge.csv'
            store_dir = os.path.dirname(path) or '.'
            filename = os.path.basename(path)
            if filename and filename.endswith('.csv'):
                # Ensure the CSV store specifically targets this file
                mall[name] = _create_csv_single_file_store(path)
            else:
                raise ValueError(
                    f"For 'csv' format, 'path' must be a directory or a specific .csv file path. Got: {path}"
                )
        else:
            mall[name] = create_store(path, format)
    return mall


# Helper for single CSV file store within a mall (special case for specific CSV files)
def _create_csv_single_file_store(filepath: str) -> MutableMapping:
    """
    Internal helper for CSV files when specified as a single file in mall config.
    """

    class SingleCsvFileStore(MutableMapping):
        def __init__(self, filepath):
            self.filepath = filepath
            self._data = self._read_csv()

        def _read_csv(self):
            if os.path.exists(self.filepath) and os.path.getsize(self.filepath) > 0:
                return pd.read_csv(
                    self.filepath, index_col=0
                )  # Assume first column is index
            return pd.DataFrame()

        def _write_csv(self):
            self._data.to_csv(self.filepath)

        def __getitem__(self, key):
            if key not in self._data.index:
                raise KeyError(key)
            return self._data.loc[key].to_dict()

        def __setitem__(self, key, value):
            if not isinstance(value, Mapping):
                raise ValueError("Value must be a dictionary-like object.")
            new_row = pd.DataFrame([value], index=[key])
            if key in self._data.index:
                self._data.loc[key] = new_row.loc[key]
            else:
                self._data = pd.concat([self._data, new_row])
            self._write_csv()

        def __delitem__(self, key):
            if key not in self._data.index:
                raise KeyError(key)
            self._data.drop(index=key, inplace=True)
            self._write_csv()

        def __len__(self):
            return len(self._data)

        def __iter__(self):
            return iter(self._data.index)

        def items(self):
            return self._data.to_dict(orient='index').items()

    return SingleCsvFileStore(filepath)


# --- Convenience Functions for Loading/Saving KnowledgeBase from/to files ---


def load_from_csv(filepath: str, **kwargs) -> KnowledgeBase:
    """
    Loads data from a CSV file into a KnowledgeBase.
    Args:
        filepath (str): Path to the CSV file.
        **kwargs: Additional keyword arguments for pandas.read_csv.
    Returns:
        KnowledgeBase: An initialized KnowledgeBase object.
    """
    try:
        df = pd.read_csv(filepath, **kwargs)
        return KnowledgeBase(df)
    except FileNotFoundError:
        print(f"File not found: {filepath}. Returning empty KnowledgeBase.")
        return KnowledgeBase()
    except Exception as e:
        print(f"Error loading CSV from {filepath}: {e}. Returning empty KnowledgeBase.")
        return KnowledgeBase()


def load_from_json(filepath: str, **kwargs) -> KnowledgeBase:
    """
    Loads data from a JSON file (list of dicts) into a KnowledgeBase.
    Args:
        filepath (str): Path to the JSON file.
        **kwargs: Additional keyword arguments for pandas.read_json.
    Returns:
        KnowledgeBase: An initialized KnowledgeBase object.
    """
    try:
        df = pd.read_json(filepath, **kwargs)
        return KnowledgeBase(df)
    except FileNotFoundError:
        print(f"File not found: {filepath}. Returning empty KnowledgeBase.")
        return KnowledgeBase()
    except Exception as e:
        print(
            f"Error loading JSON from {filepath}: {e}. Returning empty KnowledgeBase."
        )
        return KnowledgeBase()


def save_to_csv(kb: KnowledgeBase, filepath: str, **kwargs):
    """
    Saves the contents of a KnowledgeBase to a CSV file.
    Args:
        kb (KnowledgeBase): The KnowledgeBase object to save.
        filepath (str): Path to the output CSV file.
        **kwargs: Additional keyword arguments for pandas.DataFrame.to_csv.
    """
    kb.to_dataframe().to_csv(filepath, **kwargs)


def save_to_json(kb: KnowledgeBase, filepath: str, **kwargs):
    """
    Saves the contents of a KnowledgeBase to a JSON file (as a list of dicts).
    Args:
        kb (KnowledgeBase): The KnowledgeBase object to save.
        filepath (str): Path to the output JSON file.
        **kwargs: Additional keyword arguments for pandas.DataFrame.to_json.
    """
    kb.to_dataframe().to_json(filepath, orient='records', indent=4, **kwargs)
