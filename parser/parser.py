import re
import json
import os
import csv
import datetime

class SQLParser:
    def __init__(self):
        pass

    def parse(self, query: str) -> dict:
        self.tokens = []
        self.pos = 0

        query = query.strip()
        if query.endswith(';'):
            query = query[:-1].strip()

        create_table_from_file_match = re.match(r"CREATE\s+TABLE\s+(\w+)\s+FROM\s+FILE\s+'([^']*)'(?:\s+USING\s+INDEX\s+(\w+)\s*\(([\w\"]+)\))?(?:\s+WITH\s+ENCODING\s+'([^']*)')?", query, re.IGNORECASE)
        if create_table_from_file_match:
            table_name = create_table_from_file_match.group(1)
            file_path = create_table_from_file_match.group(2)
            index_type = create_table_from_file_match.group(3)
            index_column = create_table_from_file_match.group(4)
            encoding = create_table_from_file_match.group(5)
            if index_column:
                index_column = index_column.strip('"')
            return {
                'command': 'CREATE_TABLE_FROM_FILE',
                'table_name': table_name,
                'file_path': file_path,
                'index_info': {'type': index_type, 'column': index_column} if index_type else None,
                'encoding': encoding
            }

        command_parts = query.split(maxsplit=2)
        if not command_parts:
            return None

        command_keyword_1 = command_parts[0].upper()
        command_keyword_2 = command_parts[1].upper() if len(command_parts) > 1 else ""
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
        except SyntaxError as se:
            print(f"Error de sintaxis: {se}")
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
            raise SyntaxError("CREATE TABLE <nombre> (col1 type [constraints], ...)")

        table_name = match.group(1)
        columns_str = match.group(2).strip()
        parsed_columns = []

        balance = 0
        current_col_start = 0
        definitions_str_list = []
        for i, char in enumerate(columns_str):
            if char == '(':
                balance += 1
            elif char == ')':
                balance -= 1
            elif char == ',' and balance == 0:
                definitions_str_list.append(columns_str[current_col_start:i].strip())
                current_col_start = i + 1
        definitions_str_list.append(columns_str[current_col_start:].strip())

        for col_def_str in definitions_str_list:
            if not col_def_str:
                continue

            parts = col_def_str.split()
            if len(parts) < 2:
                raise SyntaxError(f"Definicion de columna '{col_def_str}' malformada")

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
                        index_info = {'type': None}
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

        return {
            'command': 'CREATE_TABLE',
            'table_name': table_name,
            'columns': parsed_columns
        }

    def _parse_insert_into(self, query):
        match_with_cols = re.match(r"INSERT\s+INTO\s+(\w+)\s*\(([^)]+)\)\s*VALUES\s*\((.+)\)", query, re.IGNORECASE)
        if match_with_cols:
            table_name, cols_str, values_str = match_with_cols.group()
            target_columns = [col.strip() for col in cols_str.split(',')]
            values = [val.strip().strip("'").strip('"') for val in values_str.split(',')]
            return {
                'command': 'INSERT',
                'table_name': table_name,
                'columns': target_columns,
                'values': values
            }

        match_no_cols = re.match(r"INSERT\s+INTO\s+(\w+)\s+VALUES\s*\((.+)\)", query, re.IGNORECASE)
        if match_no_cols:
            table_name, values_str = match_no_cols.group()
            values = [val.strip().strip("'").strip('"') for val in values_str.split(',')]
            return {
                'command': 'INSERT',
                'table_name': table_name,
                'columns': None,
                'values': values
            }

        raise SyntaxError("INSERT INTO <nombre> [(columnas)] VALUES (...)")

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
                raise SyntaxError(f"Caracter inesperado en clausula WHERE: '{value}'")
            if kind in ['BETWEEN', 'AND', 'OR']:
                value = value.upper()
            tokens.append({'kind': kind, 'value': value})
        return tokens

    def _peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _consume(self, expected_kind=None, expected_value=None):
        if self.pos >= len(self.tokens):
            expected_str = f"{expected_kind or ''}{f' ({expected_value})' if expected_value else ''}"
            raise SyntaxError(f"Fin inesperado. Se esperaba {expected_str or 'mas tokens'}")

        token = self.tokens[self.pos]
        if expected_kind and token['kind'] != expected_kind:
            raise SyntaxError(f"Se esperaba {expected_kind} pero se encontro {token['kind']} ('{token['value']}')")
        if expected_value and token['value'].upper() != expected_value.upper():
            raise SyntaxError(f"Se esperaba '{expected_value}' pero se encontro '{token['value']}'")
        self.pos += 1
        return token

    def _parse_value(self):
        token = self._peek()
        if not token:
            raise SyntaxError("Se esperaba un valor")
        if token['kind'] in ['STRING', 'NUMBER']:
            return self._consume(token['kind'])
        elif token['kind'] == 'IDENTIFIER':
            return self._consume('IDENTIFIER')
        else:
            raise SyntaxError(f"Se esperaba un valor (STRING, NUMBER) pero se encontro {token['kind']}")

    def _parse_condition(self):
        column_token = self._consume('IDENTIFIER')
        next_token = self._peek()
        if not next_token:
            raise SyntaxError(f"Fin inesperado despues de '{column_token['value']}'")

        if next_token['kind'] == 'OPERATOR':
            op_token = self._consume('OPERATOR')
            value_node = self._parse_value()
            return {
                'type': 'condition',
                'column': column_token['value'],
                'operator': op_token['value'],
                'value': value_node['value'].strip("'\"")
            }
        elif next_token['kind'] == 'BETWEEN':
            self._consume('BETWEEN')
            value1_node = self._parse_value()
            self._consume('AND')
            value2_node = self._parse_value()
            return {
                'type': 'condition',
                'column': column_token['value'],
                'operator': 'BETWEEN',
                'value': [value1_node['value'].strip("'\""), value2_node['value'].strip("'\"")]
            }
        else:
            raise SyntaxError(f"Se esperaba OPERATOR o BETWEEN despues de '{column_token['value']}', pero se encontro {next_token['kind']}")

    def _parse_factor(self):
        next_token = self._peek()
        if not next_token:
            raise SyntaxError("Se esperaba un factor")
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
        if not self.tokens:
            return None
        self.pos = 0
        expr_tree = self._parse_expression()
        if self.pos < len(self.tokens):
            raise SyntaxError(f"Tokens extraños al final de WHERE: {self.tokens[self.pos:]}")
        return expr_tree

    def _parse_select(self, query):
        where_clause_tree = None
        match_where_split = re.match(r"(SELECT\s+.+?\s+FROM\s+\w+)(?:\s+WHERE\s+(.+))?", query, re.IGNORECASE)
        if not match_where_split:
            raise SyntaxError("SELECT <columnas> FROM <nombre> [WHERE <condicion>]")

        select_from_part = match_where_split.group(1)
        where_str_part = match_where_split.group(2)

        match_select_from = re.match(r"SELECT\s+(.+?)\s+FROM\s+(\w+)", select_from_part, re.IGNORECASE)
        if not match_select_from:
            raise SyntaxError("Parte SELECT ... FROM malformada")

        cols_str = match_select_from.group(1).strip()
        table_name = match_select_from.group(2).strip()

        if where_str_part:
            where_clause_tree = self._parse_where_clause(where_str_part)

        select_columns = ['*'] if cols_str == "*" else [col.strip() for col in cols_str.split(',')]
        return {
            'command': 'SELECT',
            'table_name': table_name,
            'select_columns': select_columns,
            'where_clause': where_clause_tree
        }

    def _parse_delete_from(self, query):
        where_clause_tree = None
        match_where_split = re.match(r"(DELETE\s+FROM\s+\w+)(?:\s+WHERE\s+(.+))?", query, re.IGNORECASE)
        if not match_where_split:
            raise SyntaxError("DELETE FROM <nombre> [WHERE <condicion>]")

        delete_from_part = match_where_split.group(1)
        where_str_part = match_where_split.group(2)

        match_delete_from = re.match(r"DELETE\s+FROM\s+(\w+)", delete_from_part, re.IGNORECASE)
        if not match_delete_from:
            raise SyntaxError("Parte DELETE FROM malformada")

        table_name = match_delete_from.group(1).strip()

        if where_str_part:
            where_clause_tree = self._parse_where_clause(where_str_part)
        else:
            pass

        return {
            'command': 'DELETE',
            'table_name': table_name,
            'where_clause': where_clause_tree
        }

    def _parse_drop_table(self, query):
        match = re.match(r"DROP\s+TABLE\s+(\w+)", query, re.IGNORECASE)
        if not match:
            raise SyntaxError("DROP TABLE <nombre>")
        return {'command': 'DROP_TABLE', 'table_name': match.group(1)}


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
                raise OSError(f"Error creando directorio '{self.db_directory}': {e}")

    def _get_table_filepath(self, table_name_key: str):
        return os.path.join(self.db_directory, f"{table_name_key}.json")

    def _save_table_to_disk(self, table_name_key: str):
        if table_name_key not in self._tables:
            return
        filepath = self._get_table_filepath(table_name_key)
        try:
            table_data_to_save = {
                'columns': self._tables[table_name_key]['columns'],
                'rows': self._tables[table_name_key]['rows'],
                'original_name': self._tables[table_name_key].get('original_name', table_name_key.capitalize())
            }
            with open(filepath, 'w') as f:
                json.dump(table_data_to_save, f, indent=4)
        except (IOError, TypeError) as e:
            print(f"Error guardando tabla '{table_name_key}' a '{filepath}': {e}")

    def _load_table_from_disk(self, table_name_key: str):
        filepath = self._get_table_filepath(table_name_key)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    loaded_data = json.load(f)
                    self._tables[table_name_key] = {
                        'columns': loaded_data.get('columns', []),
                        'rows': loaded_data.get('rows', []),
                        'original_name': loaded_data.get('original_name', table_name_key.capitalize())
                    }
                return True
            except (IOError, json.JSONDecodeError) as e:
                print(f"Error cargando tabla '{table_name_key}' desde '{filepath}': {e}")
        return False

    def _load_all_tables_from_disk(self):
        if not os.path.exists(self.db_directory):
            return
        print(f"Cargando tablas desde '{self.db_directory}'...")
        count = 0
        for filename in os.listdir(self.db_directory):
            if filename.endswith(".json"):
                table_name_key = os.path.splitext(filename)[0]
                if self._load_table_from_disk(table_name_key):
                    count += 1
        print(f"Carga completada. {count} tablas cargadas.")

    def _delete_table_file(self, table_name_key: str):
        filepath = self._get_table_filepath(table_name_key)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError as e:
                print(f"Error eliminando archivo '{filepath}': {e}")

    def _get_col_def(self, table_schema: list, col_name_to_find: str):
        return next((cd for cd in table_schema if cd['name'].lower() == col_name_to_find.lower()), None)

    def _cast_value_for_comparison(self, value_str, target_schema_type: str):
        target_type_upper = target_schema_type.upper() if target_schema_type else "TEXT"
        if value_str is None:
            return None

        if target_type_upper == 'ARRAY' and isinstance(value_str, str) and value_str.startswith('[') and value_str.endswith(']'):
            try:
                return json.loads(value_str)
            except json.JSONDecodeError:
                pass
        try:
            if target_type_upper == 'INT':
                return int(value_str)
            if target_type_upper == 'FLOAT':
                return float(value_str)
            if target_type_upper == 'DATE':
                return datetime.strptime(value_str, '%Y-%m-%d').date() # NOTE: we may change this format as we go
        except (ValueError, TypeError):
            pass
        return value_str

    def _evaluate_expression_tree(self, row: dict, node: dict, table_schema: list) -> bool:
        if node is None:
            return True

        node_type = node.get('type')

        if node_type == 'logical':
            left_result = self._evaluate_expression_tree(row, node['left'], table_schema)
            op = node['op'].upper()
            if op == 'AND':
                return left_result and self._evaluate_expression_tree(row, node['right'], table_schema)
            if op == 'OR':
                return left_result or self._evaluate_expression_tree(row, node['right'], table_schema)

        elif node_type == 'condition':
            col_name_from_cond = node['column']
            operator = node['operator']
            condition_val_parsed = node['value']

            schema_col_def = self._get_col_def(table_schema, col_name_from_cond)
            if not schema_col_def:
                raise ValueError(f"Columna '{col_name_from_cond}' no encontrada en schema")

            row_val = row.get(schema_col_def['name'])
            casted_condition_val = None

            try:
                if operator == 'BETWEEN':
                    if not isinstance(condition_val_parsed, list) or len(condition_val_parsed) != 2:
                        return False
                    val1_casted = self._cast_value_for_comparison(condition_val_parsed[0], schema_col_def['type'])
                    val2_casted = self._cast_value_for_comparison(condition_val_parsed[1], schema_col_def['type'])
                    if val1_casted is None or val2_casted is None:
                        return False
                    casted_condition_val = [val1_casted, val2_casted]
                else:
                    casted_condition_val = self._cast_value_for_comparison(condition_val_parsed, schema_col_def['type'])
            except Exception as cast_err:
                raise ValueError(f"Error during value casting: {cast_err}")

            is_null_check = isinstance(casted_condition_val, str) and casted_condition_val.upper() == 'NULL'
            if row_val is None:
                if operator == '=' and is_null_check:
                    return True
                if operator == '!=' and is_null_check:
                    return False
                return False

            if is_null_check:
                return operator == '!='

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
                    if not isinstance(casted_condition_val, list):
                        return False
                    lower, upper = casted_condition_val
                    return lower <= row_val <= upper
            except TypeError:
                return False
            except Exception as comp_err:
                raise RuntimeError(f"Error inesperado durante comparacion: {comp_err}")

        raise ValueError(f"Nodo de expresion desconocido: {node}")

    def execute_query(self, query):
        try:
            parsed_command = self._parser.parse(query)
            if not parsed_command:
                return "Error: no se pudo procesar la consulta (comando nulo)"

            command = parsed_command.get('command')
            raw_table_name = parsed_command.get('table_name')
            table_name_key = raw_table_name.lower() if raw_table_name else None

            if command == 'CREATE_TABLE':
                if table_name_key in self._tables:
                    return f"Error: tabla '{raw_table_name}' ya existe"
                columns = parsed_command.get('columns')
                self._tables[table_name_key] = {'columns': columns, 'rows': [], 'original_name': raw_table_name}
                self._save_table_to_disk(table_name_key)
                return f"tabla '{raw_table_name}' creada exitosamente"

            elif command == 'CREATE_TABLE_FROM_FILE':
                if table_name_key in self._tables:
                    return f"Error: tabla '{raw_table_name}' ya existe"
                file_path = parsed_command.get('file_path')
                index_info = parsed_command.get('index_info')
                encoding = parsed_command.get('encoding', 'utf-8')

                if not os.path.exists(file_path):
                    return f"Error: archivo no encontrado en '{file_path}'"

                rows_data = []
                inferred_columns = []
                
                # Try with specified encoding or attempt to detect it
                encodings_to_try = [encoding] if encoding else ['utf-8', 'latin1', 'cp1252', 'ISO-8859-1']
                success = False
                
                for enc in encodings_to_try:
                    try:
                        with open(file_path, 'r', newline='', encoding=enc) as csvfile:
                            # Detect dialect for better CSV parsing
                            sample = csvfile.read(4096)
                            csvfile.seek(0)
                            try:
                                dialect = csv.Sniffer().sniff(sample)
                            except:
                                dialect = csv.excel  # Default to Excel dialect if detection fails
                            
                            reader = csv.reader(csvfile, dialect=dialect)
                            header = next(reader, None)
                            if not header:
                                continue  # Try next encoding if file appears empty

                            inferred_columns = [{'name': h.strip(), 'type': 'TEXT', 'type_details': {}, 'constraints':[], 'index_info': None} for h in header]

                            for row in reader:
                                if len(row) == len(inferred_columns):
                                    row_dict = {inferred_columns[i]['name']: val for i, val in enumerate(row)}
                                    rows_data.append(row_dict)
                                else:
                                    print(f"Warning: fila ignorada en '{file_path}' por numero incorrecto de columnas: {row}")
                        
                        success = True
                        break  # Successfully processed file with this encoding
                        
                    except UnicodeDecodeError:
                        # Try next encoding
                        continue
                    except Exception as e:
                        return f"error procesando archivo '{file_path}' con encoding '{enc}': {e}"

                if not success:
                    return f"Error: No se pudo procesar el archivo '{file_path}' con ningún encoding. Intente especificar un encoding válido."

                self._tables[table_name_key] = {'columns': inferred_columns, 'rows': rows_data, 'original_name': raw_table_name}
                self._save_table_to_disk(table_name_key)
                return f"tabla '{raw_table_name}' creada desde '{file_path}' con {len(rows_data)} filas"

            elif command == 'DROP_TABLE':
                if table_name_key not in self._tables:
                    return f"Error: tabla '{raw_table_name}' no existe"
                del self._tables[table_name_key]
                self._delete_table_file(table_name_key)
                return f"tabla '{raw_table_name}' eliminada exitosamente"

            if table_name_key not in self._tables:
                return f"Error: tabla '{raw_table_name}' no existe"

            table_data = self._tables[table_name_key]
            table_schema = table_data['columns']

            if command == 'INSERT':
                values_to_insert = parsed_command.get('values')
                target_columns_names = parsed_command.get('columns')
                row_data = {}

                if target_columns_names:
                    if len(target_columns_names) != len(values_to_insert):
                        return f"Error: discrepancia columnas/valores ({len(target_columns_names)} vs {len(values_to_insert)})"
                    temp_row_data = {}
                    for i, col_name_req in enumerate(target_columns_names):
                        col_def = self._get_col_def(table_schema, col_name_req)
                        if not col_def:
                            return f"Error: columna '{col_name_req}' no existe"
                        val_str = values_to_insert[i]
                        casted_val = self._cast_value_for_comparison(val_str, col_def['type'])

                        if col_def['type'].upper() == 'VARCHAR' and 'size' in col_def.get('type_details', {}):
                            if isinstance(casted_val, str) and len(casted_val) > col_def['type_details']['size']:
                                return f"Error: valor para columna '{col_def['name']}' excede el tamaño maximo de VARCHAR({col_def['type_details']['size']})"
                        temp_row_data[col_def['name']] = casted_val
                    for schema_col in table_schema:
                        row_data[schema_col['name']] = temp_row_data.get(schema_col['name'])
                else:
                    if len(values_to_insert) != len(table_schema):
                        return f"Error: tabla tiene {len(table_schema)} columnas, se dieron {len(values_to_insert)} valores"
                    for i, col_def in enumerate(table_schema):
                        val_str = values_to_insert[i]
                        casted_val = self._cast_value_for_comparison(val_str, col_def['type'])
                        if col_def['type'].upper() == 'VARCHAR' and 'size' in col_def.get('type_details', {}):
                            if isinstance(casted_val, str) and len(casted_val) > col_def['type_details']['size']:
                                return f"Error: valor para columna '{col_def['name']}' excede el tamaño maximo de VARCHAR({col_def['type_details']['size']})"
                        row_data[col_def['name']] = casted_val

                pk_col_def = next((col for col in table_schema if "PRIMARY KEY" in [c.upper() for c in col.get('constraints', [])]), None)
                if pk_col_def:
                    pk_name = pk_col_def['name']
                    pk_value = row_data.get(pk_name)
                    if pk_value is not None and any(r.get(pk_name) == pk_value for r in table_data['rows']):
                        return f"Error: PRIMARY KEY constraint violada para '{pk_name}' = '{pk_value}'"

                table_data['rows'].append(row_data)
                self._save_table_to_disk(table_name_key)
                return "1 fila insertada"

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
                                    return f"Error: columna '{col_name_req}' no encontrada"
                            result_rows.append(projected_row)
                return result_rows

            elif command == 'DELETE':
                where_clause_tree = parsed_command.get('where_clause')
                rows_to_keep = []
                deleted_count = 0
                for row in table_data['rows']:
                    if self._evaluate_expression_tree(row, where_clause_tree, table_schema):
                        deleted_count += 1
                    else:
                        rows_to_keep.append(row)

                if deleted_count > 0:
                    table_data['rows'] = rows_to_keep
                    self._save_table_to_disk(table_name_key)
                return f"{deleted_count} fila(s) eliminada(s)"

            else:
                return f"Error: comando '{command}' no reconocido o aun no implementado"

        except SyntaxError as se:
            return f"Error de Sintaxis: {se}"
        except FileNotFoundError as fnf:
            return f"Error de Archivo: {fnf}"
        except KeyError as ke:
            return f"Error de Clave/Columna: {ke}"
        except ValueError as ve:
            return f"Error de Valor/Tipo: {ve}"
        except Exception as e:
            return f"Error inesperado durante la ejecucion: {e}"
