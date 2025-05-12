import re
import json
import os

class SQLParser:
    def __init__(self):
        self.command_parts = []
        self.pos = 0

    def parse(self, query: str) -> dict:
        self.command_parts = []
        self.pos = 0

        query = query.strip()
        if not query.endswith(';'):
            # NOTE: We dont mind if they forgot the semicolon (maybe throw warning?)
            pass
        else:
            query = query[:-1].strip()

        create_table_from_file_match = re.match(r"CREATE\s+TABLE\s+(\w+)\s+FROM\s+FILE\s+'([^']*)'(?:\s+USING\s+INDEX\s+(\w+)\s*\(([\w\"]+)\))?", query, re.IGNORECASE)
        if create_table_from_file_match:
            table_name = create_table_from_file_match.group(1)
            file_path = create_table_from_file_match.group(2)
            index_type = create_table_from_file_match.group(3)
            index_column = create_table_from_file_match.group(4)
            if index_column:
                index_column = index_column.strip('"')
            return {'command': 'CREATE_TABLE_FROM_FILE', 'table_name': table_name, 'file_path': file_path, 'index_info': {'type': index_type, 'column': index_column} if index_type else None}

        command_parts = query.split(maxsplit=2)

        if not command_parts:
            return None

        command_keyword_1 = command_parts[0].upper()
        command_keyword_2 = ""

        if len(command_parts) > 1:
            command_keyword_2 = command_parts[1].upper()

        full_query_for_parsers = query

        try:
            if command_keyword_1 == "CREATE" and command_keyword_2 == "TABLE":
                return self._parse_create_table(full_query_for_parsers)
            elif command_keyword_1 == "INSERT" and command_keyword_2 == "INTO":
                return self._parse_insert_into(full_query_for_parsers)
            elif command_keyword_1 == "SELECT":
                return self._parse_select(full_query_for_parsers)
            elif command_keyword_1 == "DELETE" and command_keyword_2 == "FROM":
                return self._parse_delete_from(full_query_for_parsers)
            elif command_keyword_1 == "DROP" and command_keyword_2 == "TABLE":
                return self._parse_drop_table(full_query_for_parsers)
            else:
                print(f"Error: '{command_keyword_1} {command_keyword_2}' query no existe o esta malformada.")
                return None
        except IndexError:
            print(f"Error: '{command_keyword_1} {command_keyword_2}' query esta incompleta.")
            return None
        except Exception as e:
            print(f"Error procesando query '{query}': {e}")
            return None

    def _parse_create_table(self, query):
        match = re.match(r"CREATE\s+TABLE\s+(\w+)\s*\((.+)\)", query, re.IGNORECASE)
        if not match:
            print("Error: CREATE TABLE <nombre> (col1 type [constraints], ...)")
            return None

        table_name = match.group(1)
        columns_str = match.group(2).strip()
        parsed_columns = []

        raw_column_definitions = columns_str.split(',')

        current_col_def_parts = []
        for part in raw_column_definitions:
            current_col_def_parts.append(part)
            temp_def = "".join(current_col_def_parts)
            if ")" not in temp_def or temp_def.count("(") == temp_def.count(")"):
                col_def_str = "".join(current_col_def_parts).strip()
                current_col_def_parts = []

                parts = col_def_str.split()
                if len(parts) < 2:
                    print(f"Error: definicion de columna '{col_def_str}' malformada.")
                    return None

            col_name = parts[0]
            col_type_str = parts[1].upper()
            constraints = []
            index_info = None
            type_details = {}

            type_match_varchar = re.match(r"VARCHAR\((\d+)\)", col_type_str, re.IGNORECASE)
            type_match_array = re.match(r"ARRAY\[([^\]]+)\]", col_type_str, re.IGNORECASE)

            if type_match_varchar:
                col_type = "VARCHAR"
                type_details = {'size': int(type_match_varchar.group(1))}
            elif type_match_array:
                col_type = "ARRAY"
                type_details = {'subtype': type_match_array.group(1).upper()}
            else:
                col_type = col_type_str

            remaining_parts = parts[2:]
            i = 0
            while i < len(remaining_parts):
                part = remaining_parts[i].upper()
                if part == "PRIMARY" and i + 1 < len(remaining_parts) and remaining_parts[i+1].upper() == "KEY":
                    constraints.append("PRIMARY KEY")
                    i += 1
                elif part == "INDEX":
                    constraints.append("INDEX")
                    if i + 1 < len(remaining_parts):
                        index_info = {'type': remaining_parts[i+1]}
                        i += 1
                else:
                    constraints.append(part)
                i += 1

            parsed_columns.append({
                'name': col_name,
                'type': col_type,
                'type_details': type_details,
                'constraints': constraints,
                'index_info': index_info
            })

        return {'command': 'CREATE_TABLE', 'table_name': table_name, 'columns': parsed_columns}

    def _parse_insert_into(self, query):
        match_with_cols = re.match(r"INSERT\s+INTO\s+(\w+)\s*\(([^)]+)\)\s*VALUES\s*\((.+)\)", query, re.IGNORECASE)
        if match_with_cols:
            table_name = match_with_cols.group(1)
            cols_str = match_with_cols.group(2).strip()
            values_str = match_with_cols.group(3).strip()
            target_columns = [col.strip() for col in cols_str.split(',')]
            values = [val.strip().strip("'").strip('"') for val in values_str.split(',')]
            return {'command': 'INSERT', 'table_name': table_name, 'columns': target_columns, 'values': values}

        match_no_cols = re.match(r"INSERT\s+INTO\s+(\w+)\s+VALUES\s*\((.+)\)", query, re.IGNORECASE)
        if match_no_cols:
            table_name = match_no_cols.group(1)
            values_str = match_no_cols.group(2).strip()
            values = [val.strip().strip("'").strip('"') for val in values_str.split(',')]
            return {'command': 'INSERT', 'table_name': table_name, 'columns': None, 'values': values}

        print("Error: INSERT INTO <nombre> [(columnas)] VALUES (...)")
        return None

    def _tokenize_where_clause(self, text: str):
        if not text:
            return []

        token_specification = [
            ('STRING', r"'[^']*'|\"[^\"]*\""),
            ('NUMBER', r'\b\d+(?:\.\d+)?\b'),
            ('BETWEEN', r'\bBETWEEN\b'),
            ('AND', r'\bAND\b'),
            ('OR', r'\bOR\b'),
            ('OPERATOR', r'!=|>=|<=|=|>|<'),
            ('IDENTIFIER', r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
            ('LPAREN', r'\('),
            ('RPAREN', r'\)'),
            ('WHITESPACE', r'\s+'),
            ('MISMATCH', r'.')
        ]

        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
        tokens = []

        for mo in re.finditer(tok_regex, text, re.IGNORECASE):
            kind = mo.lastgroup
            value = mo.group()
            if kind == 'WHITESPACE':
                continue
            elif kind == 'MISMATCH':
                print(f"Error: '{value}' no reconocido.")
                return None

            if kind in ['BETWEEN', 'AND', 'OR']:
                value = value.upper()
            tokens.append({'kind': kind, 'value': value})
        return tokens

    def _peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _consume(self, expected_kind=None, expected_value=None):
        if self.pos >= len(self.tokens):
            expected_str = ""
            if expected_kind:
                expected_str += expected_kind
            if expected_value:
                expected_str += f" ('{expected_value}')"
            print(f"Error: se esperaba {expected_str if expected_str else 'mas tokens'}.")

        token = self.tokens[self.pos]
        if expected_kind and token['kind'] != expected_kind:
            print(f"Error: se esperaba {expected_kind} pero se encontro {token['kind']} ('{token['value']}').")
            return None
        if expected_value and token['value'].upper() != expected_value.upper():
            print(f"Error: se esperaba '{expected_value}' pero se encontro '{token['value']}'.")
            return None
        self.pos += 1
        return token

    def _parse_value(self):
        token = self._peek()
        if not token:
            print("Error: se esperaba un valor, pero no hay mas tokens.")
            return None
        if token['kind'] in ['STRING', 'NUMBER']:
            return self._consume(token['kind'])
        elif token['kind'] == 'IDENTIFIER':
            return self._consume('IDENTIFIER')
        else:
            print(f"Error: se esperaba un valor (STRING, NUMBER) pero se encontro {token['kind']} ('{token['value']}').")
            return None

    def _parse_condition(self):
        column_token = self._consume('IDENTIFIER')
        next_token = self._peek()
        if not next_token:
            print(f"Error: fin inesperado despues de la columna '{column_token['value']}', se esperaba un operador.")
            return None

        if next_token['kind'] == 'OPERATOR':
            op_token = self._consume('OPERATOR')
            value_node = self._parse_value()
            return {'type': 'condition', 'column': column_token['value'], 'operator': op_token['value'], 'value': value_node['value'].strip("'\"")}
        elif next_token['kind'] == 'BETWEEN':
            self._consume('BETWEEN')
            value1_node = self._parse_value()
            self._consume('AND')
            value2_node = self._parse_value()
            return {'type': 'condition', 'column': column_token['value'], 'operator': 'BETWEEN', 'value': [value1_node['value'].strip("'\""), value2_node['value'].strip("'\"")]}
        else:
            print(f"Error: se esperaba OPERATOR o BETWEEN despues de la columna '{column_token['value']}', pero se encontro {next_token['kind']} ('{next_token['value']}').")
            return None

    def _parse_factor(self):
        next_token = self._peek()
        if not next_token:
            print("Error: fin inesperado de la clausula, se esperaba un factor.")
            return None
        if next_token['kind'] == 'LPAREN':
            self._consume('LPAREN')
            node = self._parse_expression()
            self._consume('RPAREN')
            return node
        else:
            return self._parse_condition()

    def _parse_term(self):
        node = self._parse_factor()
        while self._peek() and self._peek()['kind'] == 'AND':
            op_token = self._consume('AND')
            right_node = self._parse_factor()
            node = {'type': 'logical', 'op': op_token['value'], 'left': node, 'right': right_node}
        return node

    def _parse_expression(self):
        node = self._parse_term()
        while self._peek() and self._peek()['kind'] == 'OR':
            op_token = self._consume('OR')
            right_node = self._parse_term()
            node = {'type': 'logical', 'op': op_token['value'], 'left': node, 'right': right_node}
        return node

    def _parse_where_clause(self, where_str: str):
        if not where_str or where_str.isspace():
            return None

        self.tokens = self._tokenize_where_clause(where_str)
        if self.tokens is None:
            return None
        if not self.tokens:
            return None

        self.pos = 0

        expr_tree = self._parse_expression()

        if self.pos < len(self.tokens):
            print(f"Error: tokens extraños al final de la clausula WHERE: {self.tokens[self.pos:]}.")
            return None

        return expr_tree

    def _parse_select(self, query):
        where_clause_tree = None

        match_where_split = re.match(r"(SELECT\s+.+?\s+FROM\s+\w+)(?:\s+WHERE\s+(.+))?", query, re.IGNORECASE)
        if not match_where_split:
            print("Error: SELECT <columnas> FROM <nombre> [WHERE <condicion>]")
            return None

        select_from_part = match_where_split.group(1)
        where_str_part = match_where_split.group(2)

        match_select_from = re.match(r"SELECT\s+(.+?)\s+FROM\s+(\w+)", select_from_part, re.IGNORECASE)
        if not match_select_from:
            print("Error: parte SELECT ... FROM malformada.")
            return None

        cols_str = match_select_from.group(1).strip()
        table_name = match_select_from.group(2).strip()

        if where_str_part:
            where_clause_tree = self._parse_where_clause(where_str_part)

        select_columns = ['*'] if cols_str == "*" else [col.strip() for col in cols_str.split(',')]

        return {'command': 'SELECT', 'table_name': table_name, 'select_columns': select_columns, 'where_clause': where_clause_tree}

    def _parse_delete_from(self, query):
        where_clause_tree = None

        match_where_split = re.match(r"(DELETE\s+FROM\s+\w+)(?:\s+WHERE\s+(.+))?", query, re.IGNORECASE)
        if not match_where_split:
            raise SyntaxError("Error: DELETE FROM <nombre> [WHERE <condicion>]")

        delete_from_part = match_where_split.group(1)
        where_str_part = match_where_split.group(2)

        match_delete_from = re.match(r"DELETE\s+FROM\s+(\w+)", delete_from_part, re.IGNORECASE)
        if not match_delete_from:
            raise SyntaxError("Error: parte DELETE FROM malformada.")

        table_name = match_delete_from.group(1).strip()

        if where_str_part:
            where_clause_tree = self._parse_where_clause(where_str_part)
        else:
            print("Warning: DELETE sin clausula WHERE eliminara todas las filas.")
            pass

        return {'command': 'DELETE', 'table_name': table_name, 'where_clause': where_clause_tree}

    def _parse_drop_table(self, query):
        match = re.match(r"DROP\s+TABLE\s+(\w+)", query, re.IGNORECASE)
        if not match:
            print("Error: DROP TABLE <nombre>")
            return None

        table_name = match.group(1)
        return {'command': 'DROP_TABLE', 'table_name': table_name}


class DatabaseManager:
    def __init__(self, db_directory="db_data"):
        self._tables = {}
        self._parser = SQLParser()
        self.db_directory = db_directory
        self._ensure_db_directory()
        self._load_all_tables_from_disk()

    def _ensure_db_directory(self):
        if not os.path.exists(self.db_directory):
            try:
                os.makedirs(self.db_directory)
            except OSError as e:
                print(f"Error creando directorio '{self.db_directory}': {e}")
                raise

    def _get_table_filepath(self, table_name):
        return os.path.join(self.db_directory, f"{table_name.lower()}.json")

    def _save_table_to_disk(self, table_name):
        if table_name not in self._tables:
            return
        filepath = self._get_table_filepath(table_name)
        try:
            with open(filepath, 'w') as f:
                json.dump(self._tables[table_name], f, indent=4)
        except IOError as e:
            print(f"Error guardando tabla '{table_name}' a '{filepath}': {e}")

    def _load_table_from_disk(self, table_name_from_file):
        filepath = self._get_table_filepath(table_name_from_file)

        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    self._tables[table_name_from_file] = json.load(f)
                return True
            except (IOError, json.JSONDecodeError) as e:
                print(f"Error cargando tabla '{table_name_from_file}' desde '{filepath}': {e}")
        return False

    def _load_all_tables_from_disk(self):
        if not os.path.exists(self.db_directory):
            return
        for filename in os.listdir(self.db_directory):
            if filename.endswith(".json"):
                table_name = os.path.splitext(filename)[0]
                self._load_table_from_disk(table_name)

    def _delete_table_file(self, table_name):
        filepath = self._get_table_filepath(table_name)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError as e:
                print(f"Error eliminando archivo '{filepath}': {e}")

    def _get_col_def(self, table_schema, col_name_to_find):
        return next((cd for cd in table_schema if cd['name'].lower() == col_name_to_find.lower()), None)

    def _cast_value_for_comparison(self, value_str, target_schema_type):
        target_type_upper = target_schema_type.upper()
        if value_str is None:
            return None
        try:
            if target_type_upper == 'INT':
                return int(value_str)
            if target_type_upper == 'FLOAT':
                return float(value_str)
            # NOTE: Add DATE, ARRAY, etc. casting here if needed for direct comparison
        except (ValueError, TypeError):
            pass
        return value_str

    def _evaluate_expression_tree(self, row: dict, node: dict, table_schema: list):
        if node is None:
            return True

        node_type = node.get('type')

        if node_type == 'logical':
            left_result = self._evaluate_expression_tree(row, node['left'], table_schema)
            op = node['op'].upper()
            if op == 'AND':
                return left_result and self._evaluate_expression_tree(row, node['right'], table_schema)
            elif op == 'OR':
                return left_result or self._evaluate_expression_tree(row, node['right'], table_schema)

        elif node_type == 'condition':
            col_name_from_cond = node['column']
            operator = node['operator']
            condition_val_parsed = node['value']

            schema_col_def = self._get_col_def(table_schema, col_name_from_cond)
            if not schema_col_def:
                print(f"Error: columna '{col_name_from_cond}' no encontrada en schema.")
                return False

            row_val = row.get(schema_col_def['name'])

            casted_condition_val = None
            if operator == 'BETWEEN':
                try:
                    val1_casted = self._cast_value_for_comparison(condition_val_parsed[0], schema_col_def['type'])
                    val2_casted = self._cast_value_for_comparison(condition_val_parsed[1], schema_col_def['type'])
                    casted_condition_val = [val1_casted, val2_casted]
                except (IndexError, TypeError):
                    return False
            else:
                casted_condition_val = self._cast_value_for_comparison(condition_val_parsed, schema_col_def['type'])

            if row_val is None and casted_condition_val is not None:
                 if operator == '=' and str(casted_condition_val).upper() == 'NULL':
                     return True
                 if operator == '!=' and str(casted_condition_val).upper() == 'NULL':
                     return False
                 return False

            try:
                if operator == '=':
                    return row_val == casted_condition_val
                if operator == '!=':
                    return row_val != casted_condition_val
                if operator == '>':
                    return row_val > casted_condition_val
                if operator == '<':
                    return row_val < casted_condition_val
                if operator == '>=':
                    return row_val >= casted_condition_val
                if operator == '<=':
                    return row_val <= casted_condition_val
                if operator == 'BETWEEN':
                    if row_val is None or casted_condition_val is None or not isinstance(casted_condition_val, list) or len(casted_condition_val) != 2:
                        return False
                    lower_bound, upper_bound = casted_condition_val
                    if lower_bound is None or upper_bound is None:
                        return False
                    return lower_bound <= row_val <= upper_bound
            except TypeError:
                return False
            return False

        print(f"Error: nodo de expresion desconocido o malformado: {node}")
        return False

    def execute_query(self, query_string):
        parsed_command = self._parser.parse(query_string)

        if not parsed_command:
            return "Error: no se pudo procesar la consulta (comando nulo)."

        command = parsed_command.get('command')
        raw_table_name = parsed_command.get('table_name')

        table_name_key = raw_table_name.lower() if raw_table_name else None

        if command == 'CREATE_TABLE':
            if table_name_key in self._tables:
                return f"Error: tabla '{raw_table_name}' (o '{table_name_key}') ya existe."

            columns = parsed_command.get('columns')
            self._tables[table_name_key] = {'columns': columns, 'rows': [], 'original_name': raw_table_name}
            self._save_table_to_disk(table_name_key)
            return f"tabla '{raw_table_name}' creada exitosamente."

        elif command == 'CREATE_TABLE_FROM_FILE':
            if table_name_key in self._tables:
                return f"Error: tabla '{raw_table_name}' (o '{table_name_key}') ya existe."

            file_path = parsed_command.get('file_path')
            index_info = parsed_command.get('index_info')
            # TODO: implementar carga de datos desde '{file_path}' para la tabla '{raw_table_name}'
            #       usar informacion de indice: {index_info}

            # Placeholder schema
            self._tables[table_name_key] = {'columns': [{'name': 'placeholder', 'type': 'TEXT', 'type_details': {}, 'constraints':[], 'index_info': None, 'original_name': raw_table_name}], 'rows': []}
            self._save_table_to_disk(table_name_key)
            return f"tabla '{raw_table_name}' creada (desde archivo '{file_path}', carga de datos pendiente)."

        elif command == 'DROP_TABLE':
            if table_name_key not in self._tables:
                return f"Error: tabla '{raw_table_name}' (o '{table_name_key}') no existe."
            del self._tables[table_name_key]
            self._delete_table_file(table_name_key)
            return f"tabla '{raw_table_name}' eliminada exitosamente."

        if table_name_key not in self._tables:
            if self._load_table_from_disk(table_name_key):
                print(f"Warning: tabla '{table_name_key}' cargada desde disco bajo demanda.")
            else:
                return f"Error: tabla '{raw_table_name}' (o '{table_name_key}') no existe."

        table_data = self._tables[table_name_key]
        table_schema = table_data['columns']

        if command == 'INSERT':
            values_to_insert = parsed_command.get('values')
            target_columns_names = parsed_command.get('columns') 
            row_data = {}

            if target_columns_names:
                if len(target_columns_names) != len(values_to_insert):
                    return f"Error: discrepancia columnas/valores ({len(target_columns_names)} vs {len(values_to_insert)})."

                temp_row_data = {}
                for i, col_name_req in enumerate(target_columns_names):
                    col_def = self._get_col_def(table_schema, col_name_req)
                    if not col_def:
                        return f"Error: columna '{col_name_req}' no existe."

                    val_str = values_to_insert[i]
                    casted_val = self._cast_value_for_comparison(val_str, col_def['type'])
                    # TODO: Add more robust validation against col_def constraints (VARCHAR size, etc.)
                    temp_row_data[col_def['name']] = casted_val

                for schema_col in table_schema:
                    row_data[schema_col['name']] = temp_row_data.get(schema_col['name'])

            else:
                if len(values_to_insert) != len(table_schema):
                    return f"Error: tabla tiene {len(table_schema)} columnas, se dieron {len(values_to_insert)} valores."
                for i, col_def in enumerate(table_schema):
                    val_str = values_to_insert[i]
                    casted_val = self._cast_value_for_comparison(val_str, col_def['type'])
                    row_data[col_def['name']] = casted_val

            pk_col_def = next((col for col in table_schema if "PRIMARY KEY" in [c.upper() for c in col.get('constraints', [])]), None)
            if pk_col_def:
                pk_name = pk_col_def['name']
                pk_value = row_data.get(pk_name)
                if pk_value is not None and any(r.get(pk_name) == pk_value for r in table_data['rows']):
                    return f"Error: PRIMARY KEY constraint violada para '{pk_name}' = '{pk_value}'."

            table_data['rows'].append(row_data)
            self._save_table_to_disk(table_name_key)
            return "1 fila insertada."

        elif command == 'SELECT':
            select_columns_names = parsed_command.get('select_columns')
            where_clause_tree = parsed_command.get('where_clause')
            result_rows = []

            for row in table_data['rows']:
                if self._evaluate_expression_tree(row, where_clause_tree, table_schema):
                    if select_columns_names == ['*']:
                        result_rows.append(row.copy())
                    else:
                        projected_row = {}
                        for col_name_req in select_columns_names:
                            original_col_def = self._get_col_def(table_schema, col_name_req)
                            if original_col_def and original_col_def['name'] in row:
                                projected_row[original_col_def['name']] = row[original_col_def['name']]
                            else:
                                return f"Error: columna '{col_name_req}' no encontrada en tabla."
                        result_rows.append(projected_row)
            return result_rows

        elif command == 'DELETE':
            where_clause_tree = parsed_command.get('where_clause')

            if where_clause_tree is None and query_string.upper().strip().endswith(f"DELETE FROM {raw_table_name.upper()}"):
                 print(f"Warning: todas las filas de la tabla '{raw_table_name}' seran eliminadas.")
            elif where_clause_tree is None:
                 return "Error: DELETE requiere una clausula WHERE o ser una eliminacion total explicita."

            rows_to_keep = []
            deleted_count = 0
            for row in table_data['rows']:
                if self._evaluate_expression_tree(row, where_clause_tree, table_schema):
                    deleted_count += 1
                else:
                    rows_to_keep.append(row)

            if deleted_count > 0 or where_clause_tree is None:
                table_data['rows'] = rows_to_keep
                self._save_table_to_disk(table_name_key)
            return f"{deleted_count} fila(s) eliminada(s)."

        return f"Error: comando '{command}' no reconocido o aun no implementado."
