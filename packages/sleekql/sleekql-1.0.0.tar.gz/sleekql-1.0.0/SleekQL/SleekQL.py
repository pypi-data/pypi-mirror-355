import sqlite3
from typing import Optional, List, Any


class SleekQL:
    """
    A class to simplify the use of SQLite3 in Python.
    """

    def __init__(self, database: str) -> None:
        """
        Initialize the SleekQL object and connect to the SQLite3 database.

        Args:
            database (str): Name or path to the SQLite database file.
        """
        self.database = database
        self.db = sqlite3.connect(database=database)
        self.cursor = self.db.cursor()

    def close_connection(self) -> None:
        """
        Close the connection to the database.
        """
        self.db.close()

    def create_table(self, table_name: str, columns: List[str], datatypes_constraints: List[str]) -> None:
        """
        Create a table in the database.

        Args:
            table_name (str): Name of the table.
            columns (List[str]): List of column names.
            datatypes_constraints (List[str]): List of datatypes and constraints for each column.

        Raises:
            ValueError: If the number of columns and datatypes_constraints do not match.
        """
        if len(columns) != len(datatypes_constraints):
            raise ValueError(
                "Lengths of columns and datatypes_constraints must match!")

        temp = []
        for col, dtc in zip(columns, datatypes_constraints):
            temp.append(f"{col} {dtc}")
        cdc = ", ".join(temp)

        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({cdc});"
        self.cursor.execute(query)
        self.db.commit()

    def insert(self, table_name: str, columns: List[str], values: List[Any]) -> None:
        """
        Insert data into the table.

        Args:
            table_name (str): Name of the table.
            columns (List[str]): List of column names.
            values (List[Any]): List of values corresponding to the columns.

        Raises:
            ValueError: If the number of columns and values do not match.
        """
        if len(columns) != len(values):
            raise ValueError("Lengths of columns and values must match!")

        columns_str = ", ".join(columns)
        placeholder = ", ".join(["?"] * len(values))

        query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholder})"
        self.cursor.execute(query, values)
        self.db.commit()

    def select(
        self,
        table_name: str,
        columns: List[str],
        where: Optional[str] = None,
        having: Optional[str] = None,
        order_by: Optional[str] = None,
        group_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[dict]:
        """
        Retrieve data from the table.

        Args:
            table_name (str): Name of the table.
            columns (List[str]): List of columns to retrieve.
            where (Optional[str]): WHERE condition.
            having (Optional[str]): HAVING condition.
            order_by (Optional[str]): ORDER BY clause.
            group_by (Optional[str]): GROUP BY clause.
            limit (Optional[int]): LIMIT number of results.
            offset (Optional[int]): OFFSET for pagination.

        Returns:
            List[dict]: List of rows as dictionaries (column_name: value).
        """
        columns_str = ", ".join(columns)
        query = f"SELECT {columns_str} FROM {table_name}"

        if where:
            query += f" WHERE {where}"
        if group_by:
            query += f" GROUP BY {group_by}"
        if having:
            query += f" HAVING {having}"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit is not None:
            query += f" LIMIT {limit}"
        if offset is not None:
            query += f" OFFSET {offset}"

        result = self.cursor.execute(query).fetchall()
        column_names = [desc[0] for desc in self.cursor.description]
        dict_result = [dict(zip(column_names, row)) for row in result]
        return dict_result

    def drop_table(self, table_name: str) -> None:
        """
        Drop the table if it exists.

        Args:
            table_name (str): Name of the table to drop.
        """
        query = f"DROP TABLE IF EXISTS {table_name}"
        self.cursor.execute(query)
        self.db.commit()

    def delete(self, table_name: str, where: Optional[str] = None) -> None:
        """
        Delete data from the table.

        Args:
            table_name (str): Name of the table.
            where (Optional[str]): WHERE condition for deleting specific rows.
        """
        query = f"DELETE FROM {table_name}"
        if where is not None:
            query += f" WHERE {where}"
        self.cursor.execute(query)
        self.db.commit()

    def update(self, table_name: str, columns_values: List[str], where: Optional[str] = None) -> None:
        """
        Update data in the table.

        Args:
            table_name (str): Name of the table.
            columns_values (List[str]): List of column assignments like ["name = 'John'", "age = 30"].
            where (Optional[str]): WHERE condition for updating specific rows.
        """

        columns_str = ", ".join(columns_values)
        query = f"UPDATE {table_name} SET {columns_str}"
        if where is not None:
            query += f" WHERE {where}"
        self.cursor.execute(query)
        self.db.commit()

    def raw_sql(self, query: str) -> List[tuple]:
        """
        Execute raw SQL queries directly.

        Args:
            query (str): The SQL query string.

        Returns:
            List[tuple]: Fetched results from the query.
        """
        self.cursor.execute(query)
        self.db.commit()
        return self.cursor.fetchall()
