# SleekQL
**SleekQL** is a light **SQLite3** wrapper for Python, designed to execute simple operations more quickly.<br>

![Python](https://img.shields.io/pypi/pyversions/simplehook) ![License](https://img.shields.io/badge/license-AGPL--3.0-3b3b3b?style=flat)

## 🔧 Features
- Create a database
- Delete from database
- Drop database
- Fetch data from database
- insert and update
- Execute raw SQL

## 🚀 Usage
### Import and setup
```python
from SleekQL import SleekQL

# Initialize with database name or path
db = SleekQL("database.db")
```
### Functions
```python
# Close connection to database
db.close_connection()

# Create table
db.create_table(
  table_name="Table1",
  columns=["Column1", "Column2"],
  datatypes_constraints=["INTEGER PRIMARY KEY", "TEXT"]
)

# Insert data
db.insert(table_name="Table1", columns=["Column1", "Column2"], values=[100, "Data"])

# Fetch data and return list[dict]
db.select(table_name="Table1", columns=["*"])

# Update data
db.update(table_name="Table1", columns_values=["Column1 = 101", "Column2 = 'DATA'"])

# Delete data
db.delete(table_name="Table1", where="Column1 = 101")

# Drop table
db.drop_table(table_name="Table1")
```
### Use raw SQL
```python
# returns List[tuple] if needed
db.raw_sql(query="SELECT * FROM Table1")
```
## 📦 Installation

```bash
pip install sleekql
```
