from sqlalchemy import Table, MetaData, select, text, column, and_, or_
from sqlalchemy.sql.expression import ColumnClause
from typing import Dict, Any, List

class QueryParser:
    """
    Parses a JSON-defined query and builds a safe SQLAlchemy query object.
    """

    OPERATORS = {
        "=": lambda c, v: c == v,
        "!=": lambda c, v: c != v,
        ">": lambda c, v: c > v,
        "<": lambda c, v: c < v,
        ">=": lambda c, v: c >= v,
        "<=": lambda c, v: c <= v,
        "in": lambda c, v: c.in_(v),
        "like": lambda c, v: c.like(v),
    }

    def __init__(self, account_uuid: str, custom_table_name: str):
        if not custom_table_name.startswith("custom_"):
            raise ValueError("QueryParser only works with tables prefixed with 'custom_'.")
        self.account_uuid = account_uuid
        self.table_name = custom_table_name
        self.metadata = MetaData()
        self.table = Table(custom_table_name, self.metadata, autoload_with=None) # Placeholder

    def _get_column(self, column_name: str) -> ColumnClause:
        """Returns a column object from the table."""
        return column(column_name)

    def _build_where_clause(self, conditions: Dict[str, Any]):
        """Recursively builds a WHERE clause from a dictionary."""
        # Expects a single key: "and" or "or"
        if len(conditions) != 1:
            raise ValueError("WHERE clause must have a single 'and' or 'or' root.")
        
        op, clauses = list(conditions.items())[0]
        op = op.lower()

        if op not in ("and", "or"):
            raise ValueError(f"Unsupported logical operator: {op}")

        if not isinstance(clauses, list):
            raise ValueError("Logical operator must be followed by a list of conditions.")

        parts = []
        for clause in clauses:
            if "and" in clause or "or" in clause:
                parts.append(self._build_where_clause(clause))
            else:
                # Simple "column op value" clause
                if len(clause) != 1:
                    raise ValueError(f"Invalid condition format: {clause}")
                
                col_name, condition = list(clause.items())[0]
                col = self._get_column(col_name)

                if not isinstance(condition, dict) or len(condition) != 1:
                    raise ValueError(f"Invalid operator/value format: {condition}")

                op_str, value = list(condition.items())[0]
                op_func = self.OPERATORS.get(op_str.lower())

                if not op_func:
                    raise ValueError(f"Unsupported operator: {op_str}")
                
                parts.append(op_func(col, value))
        
        return and_(*parts) if op == "and" else or_(*parts)

    def parse_select(self, query_def: Dict[str, Any]):
        """Parses a SELECT query definition."""
        if "select" not in query_def:
            raise ValueError("Missing 'select' key in query definition.")

        columns_to_select = [self._get_column(c) for c in query_def["select"]]
        if not columns_to_select:
            # Default to selecting all columns if none are specified
            columns_to_select = [text("*")]

        stmt = select(*columns_to_select).select_from(self.table)

        if "where" in query_def:
            stmt = stmt.where(self._build_where_clause(query_def["where"]))

        if "limit" in query_def:
            stmt = stmt.limit(int(query_def["limit"]))
        
        if "offset" in query_def:
            stmt = stmt.offset(int(query_def["offset"]))

        return stmt

    def parse_upsert(self, query_def: Dict[str, Any]):
        """
        Parses an UPSERT query definition for PostgreSQL.
        Example: { "upsert": [{"id": 1, "name": "A"}], "on_conflict": {"keys": ["id"], "update": ["name"]} }
        """
        from sqlalchemy.dialects.postgresql import insert

        if "upsert" not in query_def or not isinstance(query_def["upsert"], list):
            raise ValueError("Missing or invalid 'upsert' data in query definition.")
        
        values = query_def["upsert"]
        stmt = insert(self.table).values(values)

        if "on_conflict" in query_def:
            conflict_def = query_def["on_conflict"]
            index_elements = conflict_def.get("keys")
            update_columns = conflict_def.get("update")

            if not index_elements or not update_columns:
                raise ValueError("'on_conflict' requires 'keys' and 'update' lists.")

            update_dict = {col: getattr(stmt.excluded, col) for col in update_columns}
            stmt = stmt.on_conflict_do_update(
                index_elements=index_elements,
                set_=update_dict,
            )
        
        return stmt

    def parse_delete(self, query_def: Dict[str, Any]):
        """
        Parses a DELETE query definition.
        Example: { "delete": true, "where": { ... } }
        """
        from sqlalchemy import delete

        if "where" not in query_def:
            raise ValueError("DELETE statements require a 'where' clause for safety.")

        stmt = delete(self.table)
        stmt = stmt.where(self._build_where_clause(query_def["where"]))
        return stmt