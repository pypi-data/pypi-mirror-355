# TODOs for future implementations:
# - Support more complex filtering queries (e.g., multiple conditions)
# - Add delete_record(s) method
# - Add update_record method
# - Allow for DB path reconfiguration after initialization
# - Accept DbSetting instance and extract data_db_path from it

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Union
from auth_db_neonix.dto.user_settings_dto import DbSetting


class DataRetriever:
    _instance = None
    _db_path: str = None

    def __new__(cls, db_source: Union[str, Path, DbSetting] = None):
        """
        Initialize the singleton instance with the database path or a DbSetting instance.
        Must be provided the first time the class is used.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            if db_source is None:
                raise ValueError("You must provide a database path or DbSetting instance on first initialization.")
            if isinstance(db_source, DbSetting):
                cls._db_path = str(db_source.data_db_path)
            else:
                cls._db_path = str(db_source)
            cls._ensure_directory()
        return cls._instance

    @classmethod
    def instance(cls):
        """
        Returns the singleton instance. Raises if not yet initialized.
        """
        if cls._instance is not None:
            return cls._instance
        raise RuntimeError("DataRetriever has not been initialized yet!")

    @classmethod
    def _ensure_directory(cls):
        """
        Ensures the directory for the DB path exists.
        """
        Path(cls._db_path).parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _connect(cls):
        """
        Opens a new connection to the SQLite database.
        """
        return sqlite3.connect(cls._db_path)

    @staticmethod
    def create_table_from_csv(table_name: str, csv_path: str):
        """
        Creates a table in the database from a CSV file.
        """
        try:
            conn = DataRetriever._connect()
            df = pd.read_csv(csv_path)
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            conn.close()
        except Exception as e:
            print(f"[create_table_from_csv] Error: {e}")

    @staticmethod
    def insert_data(table_name: str, data: pd.DataFrame):
        """
        Inserts data into the specified table.
        """
        try:
            conn = DataRetriever._connect()
            data.to_sql(table_name, conn, if_exists='append', index=False)
            conn.close()
        except Exception as e:
            print(f"[insert_data] Error: {e}")

    @staticmethod
    def fetch_data(table_name: str) -> Union[pd.DataFrame, None]:
        """
        Fetches all data from the specified table.
        """
        try:
            conn = DataRetriever._connect()
            df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
            conn.close()
            return df
        except Exception as e:
            print(f"[fetch_data] Error: {e}")
            return None

    @staticmethod
    def fetch_data_from_prop(table_name: str, prop_name: str, prop_val) -> Union[pd.DataFrame, None]:
        """
        Fetches data from the specified table based on a property value.
        """
        try:
            conn = DataRetriever._connect()
            df = pd.read_sql(f"SELECT * FROM {table_name} WHERE {prop_name}=?", conn, params=(prop_val,))
            conn.close()
            return df
        except Exception as e:
            print(f"[fetch_data_from_prop] Error: {e}")
            return None

    @staticmethod
    def create_dedicated_table(table_name: str, df: pd.DataFrame):
        """
        Creates or replaces a table with the provided DataFrame.
        """
        try:
            conn = DataRetriever._connect()
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            conn.close()
        except Exception as e:
            print(f"[create_dedicated_table] Error: {e}")
