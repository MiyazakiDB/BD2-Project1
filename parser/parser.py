import re

class SQLParser:
    def parse(self, query: str) -> dict:
        query = query.strip()
        if not query.endswith(';'):
            # We dont mind if they forgot the semicolon (maybe throw warning?)
            pass
        else:
            query = query[:-1].strip()

        tokens = query.upper().split()

        if not tokens:
            return None

        command_type = tokens[0]

        try:
            if command_type == "CREATE" and tokens[1] == "TABLE":
                return self._parse_create_table(query)
            elif command_type == "INSERT" and tokens[1] == "INTO":
                return self._parse_insert_into(query)
            elif command_type == "SELECT":
                return self._parse_select(query)
            elif command_type == "DELETE" and tokens[1] == "FROM":
                return self._parse_delete_from(query)
            elif command_type == "DROP" and tokens[1] == "TABLE":
                return self._parse_drop_table(query)
            else:
                print(f"Error: '{command_type}' query no existe.")
                return None
        except IndexError:
            print(f"Error: '{command_type}' query esta incompleta")
            return None
        except Exception as e:
            print(f"Error: '{query}': {e}")
            return None

    def _parse_create_table(self, query):
        match = re.match(r"create\s+table\s+(\w+)\s*\((.+)\)", query, re.IGNORECASE)
        if not match:
            print("Error: CREATE TABLE <nombre> (col1 type [constraints], ...)")
            return None

        table_name = match.group(1)
        columns_str = match.group(2).strip()

        parsed_columns = []
        # NOTE: If we have `ARRAY[VARCHAR(20), INT]` we will need to rework this
        column_definitions = [col.strip() for col in columns_str.split(',')]

        for col_def in column_definitions:
            parts = col_def.split()
            if len(parts) < 2:
                print(f"Error: definicion de columna '{col_def}' malformada")
                return None

            col_name = parts[0]
            col_type = parts[1]
            constraints = parts[2:]

            if "ARRAY[" in col_type and col_type.endswith("]"):
                col_type = "ARRAY"
                # TODO: subtype parsing is pending `ARRAY[FLOAT]` subtype is FLOAT

            parsed_columns.append({'name': col_name, 'type': col_type, 'constraints': constraints})

        return {'command': 'CREATE_TABLE', 'table_name': table_name, 'columns': parsed_columns}

    def _parse_insert_into(self, query):
        match = re.match(r"insert\s+into\s+(\w+)\s+values\s*\((.+)\)", query, re.IGNORECASE)
        if not match:
            # TODO: add parsing for INSERT INTO <nombre> (col1, col2) VALUES (val1, val2)
            print("Error: INSERT INTO <nombre> VALUES (...)")
            return None

        table_name = match.group(1)
        values_str = match.group(2).strip()

        values = [val.strip().strip("'").strip('"') for val in values_str.split(',')]

        return {'command': 'INSERT', 'table_name': table_name, 'values': values}

    def _parse_select(self, query):
        # TODO: make it less simple, it only has `WHERE: col = val`, no boolean operators
        where_clause_parsed = None

        if "WHERE" in query:
            match = re.match(r"select\s+(.+)\s+from\s+(\w+)\s+where\s+(.+)", query, re.IGNORECASE)
            if not match:
                print("Error: SELECT <columnas> FROM <nombre> WHERE col = val")
                return None

            cols_str = match.group(1).strip()
            table_name = match.group(2).strip()
            where_str = match.group(3).strip()

            where_parts = re.match(r"(\w+)\s*=\s*'?([\w\s]+)'?", where_str)
            if not where_parts:
                where_parts = re.match(r"(\w+)\s*=\s*(\d+)", where_str)
                if not where_parts:
                    print("Error: WHERE column = value")
                    return None

            where_clause_parsed = {
                'column': where_parts.group(1).strip(),
                'operator': '=', # NOTE: hardcoded for now
                'value': where_parts.group(2).strip()
            }
        else:
            match = re.match(r"select\s+(.+)\s+from\s+(\w+)", query, re.IGNORECASE)
            if not match:
                print("Error: SELECT <columnas> FROM table")
                return None
            cols_str = match.group(1).strip()
            table_name = match.group(2).strip()

        if cols_str == "*":
            select_columns = ['*']
        else:
            select_columns = [col.strip() for col in cols_str.split(',')]

        return {'command': 'SELECT', 'table_name': table_name, 'select_columns': select_columns, 'where_clause': where_clause_parsed}

    # NOTE: DEPRECATED, will be part of _parse_select
    """
    def _parse_range_select(self, query: str) -> dict:
        match = re.match(r"SELECT \* FROM (\w+) WHERE id\s+BETWEEN\s+(\d+)\s+AND\s+(\d+)", query, re.IGNORECASE)
        if not match:
            raise ValueError("Invalid range SELECT syntax")
        return {
            "action": "range_select",
            "table": match.group(1),
            "from": int(match.group(2)),
            "to": int(match.group(3))
        }

    def _parse_contains(self, query: str) -> dict:
        match = re.match(r"SELECT \* FROM (\w+) WHERE keyword\s+CONTAINS\s+'(.+)'", query, re.IGNORECASE)
        if not match:
            raise ValueError("Invalid CONTAINS syntax")
        return {
            "action": "contains",
            "table": match.group(1),
            "keyword": match.group(2)
        }
    """

    def _parse_delete_from(self, query):
        # NOTE: same as with delete, will need to extend this
        where_clause_parsed = None
        if "WHERE" in query:
            match = re.match(r"delete\s+from\s+(\w+)\s+where\s+(.+)", query, re.IGNORECASE)
            if not match:
                print("Error: DELETE <columnas> FROM <nombre> WHERE <condicion>")
                return None

            table_name = match.group(1).strip()
            where_str = match.group(2).strip()

            where_parts = re.match(r"(\w+)\s*=\s*'?([\w\s]+)'?", where_str, re.IGNORECASE)
            if not where_parts:
                where_parts = re.match(r"(\w+)\s*=\s*(\d+)", where_str, re.IGNORECASE)
                if not where_parts:
                    print("Error: WHERE column = value")
                    return None

            where_clause_parsed = {
                'column': where_parts.group(1).strip(),
                'operator': '=', # NOTE: hardcoded for now
                'value': where_parts.group(2).strip()
            }
        else:
            # TODO: support DELETE <columnas> FROM table (deletes all rows)
            print("Error: DELETE <columnas> FROM <nombre> WHERE <condicion>")
            return None

        return {'command': 'DELETE', 'table_name': table_name, 'where_clause': where_clause_parsed}

    def _parse_drop_table(self, query):
        match = re.match(r"drop\s+table\s+(\w+)", query, re.IGNORECASE)
        if not match:
            print("Error: DROP TABLE <nombre>")
            return None

        table_name = match.group(1)
        return {'command': 'DROP_TABLE', 'table_name': table_name}


class DatabaseManager:
    # This code is being carefully worked on, will be done by the end of the day at max
