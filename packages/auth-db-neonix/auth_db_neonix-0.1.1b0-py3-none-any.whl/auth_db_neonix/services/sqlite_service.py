import sqlite3
import os
from pathlib import Path
from typing import List, Tuple, Any, Union
from auth_db_neonix.dto.user_settings_dto import DbSetting


# region TODOs for future implementations:
# TODO - Add method: push_objects(obj_list, tab_schema, insert_query, unique_key?)
# TODO - Add method: update_records(table_name, updates_dict, conditions_dict)
# TODO - Add method: retrieve_by_values(col_name, table_name, values_list)
# TODO - Add method: exists_check(col_name, table_name, values_list)
# TODO - Add method: delete_records(table_name, conditions_dict)
# TODO - Add option to switch DB path dynamically (reinitialize safely)
# TODO - Accept DbSetting instance and extract item_db_path from it
# endregion


class SQLiteManager:
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
                cls._db_path = str(db_source.item_db_path)
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
        raise RuntimeError("SQLiteManager has not been initialized yet!")

    @classmethod
    def _ensure_directory(cls):
        """
        Ensures the directory for the DB path exists.
        """
        os.makedirs(os.path.dirname(cls._db_path), exist_ok=True)

    @classmethod
    def _connect(cls):
        """
        Opens a new connection to the SQLite database.
        """
        return sqlite3.connect(cls._db_path)

    # ===== Database Operations =====

    @staticmethod
    def try_table_creation(tab_schema: str):
        """
        Attempts to create a table using the provided SQL schema.

        :param tab_schema: SQL CREATE TABLE schema.
        """
        conn = SQLiteManager._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(tab_schema)
            conn.commit()
        except sqlite3.Error as e:
            print(f"[try_table_creation] Database error: {e}")
            conn.rollback()
        finally:
            conn.close()

    @staticmethod
    def retrieve_all(tab_name: str) -> List[tuple]:
        """
        Retrieves all records from the given table.

        :param tab_name: Name of the table.
        :return: List of tuples representing rows.
        """
        conn = SQLiteManager._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {tab_name}")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[retrieve_all] Database error: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def retrieve_last(tab_name: str, prop_name: str = 'id') -> Union[tuple, None]:
        """
        Retrieves the last record ordered by a given column (default 'id').

        :param tab_name: Name of the table.
        :param prop_name: Column to order by.
        :return: The last row as a tuple or None if empty.
        """
        conn = SQLiteManager._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT {prop_name} FROM {tab_name} ORDER BY {prop_name} DESC LIMIT 1")
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"[retrieve_last] Database error: {e}")
            return None
        finally:
            conn.close()
