import logging
from typing import Dict, Any, List

from sqlalchemy import (
    Table,
    MetaData,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    JSON,
    Float,
)
from sqlalchemy.exc import SQLAlchemyError

from leodb.core.connection_manager import connection_manager
from leodb.encryption.types import EncryptedString

logger = logging.getLogger(__name__)

class CustomTableService:
    """
    Service for managing custom tables within an account's schema.
    """

    # A mapping from string type names to SQLAlchemy type classes.
    SUPPORTED_TYPES = {
        "integer": Integer,
        "string": String,
        "text": String,  # Often used for longer text
        "boolean": Boolean,
        "datetime": DateTime,
        "json": JSON,
        "float": Float,
    }

    async def create_custom_table(
        self, account_uuid: str, table_name: str, schema: Dict[str, Any]
    ) -> str:
        """
        Creates a new custom table in the specified account's database.

        :param account_uuid: The UUID of the account.
        :param table_name: The desired name for the table.
        :param schema: A dictionary defining the table structure.
            Example:
            {
              "columns": [
                { "name": "id", "type": "integer", "primary_key": True },
                { "name": "customer_name", "type": "string", "length": 255 },
                { "name": "order_details", "type": "json" },
                { "name": "api_key", "type": "string", "encrypted": True }
              ]
            }
        :return: The final name of the created table.
        :raises ValueError: If the schema is invalid or table name is problematic.
        :raises RuntimeError: If the table could not be created.
        """
        if not table_name.startswith("custom_"):
            table_name = f"custom_{table_name}"

        if not schema or "columns" not in schema:
            raise ValueError("Invalid schema: 'columns' key is missing.")

        metadata = MetaData()
        columns = []
        for col_def in schema["columns"]:
            col_name = col_def.get("name")
            col_type_str = col_def.get("type")
            if not col_name or not col_type_str:
                raise ValueError(f"Column definition is missing 'name' or 'type': {col_def}")

            col_type_class = self.SUPPORTED_TYPES.get(col_type_str.lower())
            if not col_type_class:
                raise ValueError(f"Unsupported column type: {col_type_str}")

            is_encrypted = col_def.get("encrypted", False)
            if is_encrypted:
                if col_type_class is not String:
                    raise ValueError("Encryption is only supported for 'string' type.")
                col_type_instance = EncryptedString(col_def.get("length"))
            else:
                # Handle types with optional length
                if col_type_class is String and "length" in col_def:
                    col_type_instance = col_type_class(col_def["length"])
                else:
                    col_type_instance = col_type_class()
            
            is_pk = col_def.get("primary_key", False)
            columns.append(Column(col_name, col_type_instance, primary_key=is_pk))

        if not any(c.primary_key for c in columns):
            raise ValueError("At least one column must be a primary key.")

        try:
            engine = await connection_manager.get_engine(account_uuid)
            async with engine.begin() as conn:
                # The schema name for the account is derived from the connection string
                # or engine configuration, so we don't specify it here.
                table = Table(table_name, metadata, *columns)
                await conn.run_sync(metadata.create_all)
            
            logger.info(f"Successfully created table '{table_name}' for account {account_uuid}.")
            return table_name
        except SQLAlchemyError as e:
            logger.error(f"Failed to create table '{table_name}' for account {account_uuid}: {e}")
            raise RuntimeError(f"Could not create table '{table_name}'.") from e

    async def delete_custom_table(self, account_uuid: str, table_name: str):
        """
        Deletes a custom table from the account's database.
        For security, only tables prefixed with 'custom_' can be deleted.
        """
        if not table_name.startswith("custom_"):
            raise ValueError("For security, only tables prefixed with 'custom_' can be deleted.")

        try:
            engine = await connection_manager.get_engine(account_uuid)
            metadata = MetaData()
            table = Table(table_name, metadata)
            async with engine.begin() as conn:
                await conn.run_sync(table.drop)
            logger.info(f"Successfully deleted table '{table_name}' for account {account_uuid}.")
        except SQLAlchemyError as e:
            logger.error(f"Failed to delete table '{table_name}' for account {account_uuid}: {e}")
            raise RuntimeError(f"Could not delete table '{table_name}'.") from e

    async def list_custom_tables(self, account_uuid: str) -> List[str]:
        """
        Lists all custom tables in the account's database.
        """
        from sqlalchemy import inspect

        try:
            engine = await connection_manager.get_engine(account_uuid)
            inspector = inspect(engine)
            # Note: get_table_names() is a sync function, run it in a thread
            all_tables = await inspector.get_table_names()
            custom_tables = [name for name in all_tables if name.startswith("custom_")]
            return custom_tables
        except SQLAlchemyError as e:
            logger.error(f"Failed to list tables for account {account_uuid}: {e}")
            raise RuntimeError("Could not list tables.") from e

    async def execute_query(self, account_uuid: str, query_def: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a JSON-defined query on a custom table.
        """
        # Identify the target table from the query definition
        op_map = {"select": "from", "upsert": "table", "delete": "table"}
        table_name = None
        operation = None

        for op, key in op_map.items():
            if op in query_def:
                table_name = query_def.get(key)
                operation = op
                break
        
        if not table_name:
             # Fallback for select which uses 'from'
            if 'from' in query_def:
                table_name = query_def['from']
                operation = 'select'
            else:
                raise ValueError("Could not determine table name from query definition.")

        if not table_name.startswith("custom_"):
            raise ValueError("Queries can only be executed on tables prefixed with 'custom_'.")

        from .query_parser import QueryParser
        parser = QueryParser(account_uuid, table_name)

        if operation == "select":
            stmt = parser.parse_select(query_def)
        elif operation == "upsert":
            stmt = parser.parse_upsert(query_def)
        elif operation == "delete":
            stmt = parser.parse_delete(query_def)
        else:
            raise ValueError(f"Unsupported operation type in query: {list(query_def.keys())}")

        session = await connection_manager.get_session(account_uuid)
        try:
            result = await session.execute(stmt)
            if operation == "select":
                return {"data": [dict(row) for row in result.mappings()]}
            else:
                await session.commit()
                return {"status": "success", "rows_affected": result.rowcount}
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Query failed on table '{table_name}' for account {account_uuid}: {e}")
            raise RuntimeError("Query execution failed.") from e
        finally:
            await session.close()