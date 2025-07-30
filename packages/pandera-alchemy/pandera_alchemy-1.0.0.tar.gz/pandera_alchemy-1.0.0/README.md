# Pandera Alchemy

<img src="./images/pandera_alchemy.png" alt="pandera_alchemy logo" width="700" height="500">

The `pandera_alchemy` package bridges Pandera and SQLAlchemy, allowing users to define the structure of a database table using Pandera DataFrameModels or DataFrameSchemas and validate that the table has the expected structure with SQLAlchemy.

## Motivation

In modern data pipelines, ensuring that the structure of database tables matches the expected schema is crucial for maintaining data integrity and consistency. The `pandera_alchemy` package provides a seamless way to define and validate these structures, leveraging the power of Pandera for schema definitions and SQLAlchemy for database interactions.

## Installation

To add the `pandera_alchemy` as a dependency to a project, add it to the project's `pyproject.toml` file:


Install the dependencies:
    ```sh
    poetry install
    ```

## Usage

See the notebook `demo.ipynb` for a full example of how to use the `pandera_alchemy` package.

### Validating a Table

To validate a table, use the `Table` class. Below is an example of how to validate a table:


```python
import pandera as pa
import pandera_alchemy
import sqlalchemy

class ExampleSchema(pa.DataFrameModel):
    col1: str
    col2: int


example_table = pandera_alchemy.Table(
    name="example_table",
    table_schema=ExampleSchema,
    db_schema="public",
)

engine = sqlalchemy.create_engine(...)
example_table.validate(engine)
```


### Supported Constraints
The `pandera_alchemy` current checks the following conditions when validating a table:

1. The table exists in the database in the specified schema
2. The types for all columns in the Pandera schema loosely match the types for the columns in the database.  We support the following database-agnostic types: [Boolean, DateTime, Float, Integer, String, Timedelta, Date, NoneType].
   - We do not distinguish between different implementations of the same logical type.  For example, all implementations of Integer (Int8, Int16, UINT32, etc.) are just handled as Integer.
3. Optionally, you can verify that a column's "nullable" status matches between Pandera and SQLAlchemy.  This is skipped by default.  To enable run `table.validate(engine, check_nullable=True)`

# Tests

Tests can be run with pytest:

```sh
poetry run pytest
```