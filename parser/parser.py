import re
import json
import sys
import os
import csv

class SQLParser:
    def __init__(self):
        pass

    def parse(self, query: str) -> dict:
        self.tokens = []
        self.pos = 0

        query = query.strip()
        if query.endswith(';'):
            query = query[:-1].strip()

        create_table_from_file_match = re.match(r"CREATE\s+TABLE\s+(\w+)\s+FROM\s+FILE\s+'([^']*)'(?:\s+USING\s+INDEX\s+(\w+)\s*\(([\w\"]+)\))?", query, re.IGNORECASE)
        if create_table_from_file_match:
            table_name = create_table_from_file_match.group(1)
            file_path = create_table_from_file_match.group(2)
            index_type = create_table_from_file_match.group(3)
            index_column = create_table_from_file_match.group(4)
            if index_column:
                index_column = index_column.strip('"')
            return {
                'command': 'CREATE_TABLE_FROM_FILE',
                'table_name': table_name,
                'file_path': file_path,
                'index_info': {'type': index_type, 'column': index_column} if index_type else None
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
        match = re.match(r"CREATE\s+TABLE\s+(\w+)\s*\((.+)\)", query, re.IGNORECASE | re.DOTALL)
        if not match:
            raise SyntaxError("CREATE TABLE <nombre> (col1 type [constraints] [INDEX <tipo>], ...)")

        table_name = match.group(1)
        columns_str = match.group(2).strip()

        definitions_str_list = re.split(r',(?![^\[]*\])(?![^\(]*\))', columns_str)

        parsed_columns = []
        for col_def_str in definitions_str_list:
            col_def_str = col_def_str.strip()
            if not col_def_str:
                continue

            main_parts_match = re.match(r"(\w+)\s+([\w\[\]\(\)]+)\s*(.*)", col_def_str, re.IGNORECASE)
            if not main_parts_match:
                raise SyntaxError(f"Definicion de columna malformada: '{col_def_str}'")

            col_name, col_type_raw, rest_of_def = main_parts_match.groups()

            col_type_upper = col_type_raw.upper()
            type_details = {}
            if col_type_upper.startswith("VARCHAR"):
                col_type = "VARCHAR"
                size_match = re.search(r"\((\d+)\)", col_type_upper)
                if size_match:
                    type_details['size'] = int(size_match.group(1))
            elif col_type_upper.startswith("ARRAY"):
                col_type = "ARRAY"
                subtype_match = re.search(r"\[([^\]]+)\]", col_type_upper)
                if subtype_match:
                    type_details['subtype'] = subtype_match.group(1)
            else:
                col_type = col_type_upper

            constraints = []
            index_info = None

            if "PRIMARY KEY" in rest_of_def.upper():
                constraints.append("PRIMARY KEY")

            other_keywords = re.findall(r"NOT NULL|UNIQUE|INDEX\s+\w+", rest_of_def, re.IGNORECASE)
            for keyword in other_keywords:
                kw_upper = keyword.upper()
                if kw_upper.startswith("INDEX"):
                    index_info = {'type': kw_upper.split()[1]}
                else:
                    if kw_upper not in constraints:
                        constraints.append(kw_upper)

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

class QueryOptimizer:
    def create_plan(self, table_metadata, where_clause_tree):
        available_indexes = table_metadata.get('indexes', {})

        if not where_clause_tree:
            return {'type': 'FULL_TABLE_SCAN'}

        conditions = self._flatten_conditions(where_clause_tree)

        for condition in conditions:
            if condition['operator'] == '=':
                column = condition['column']
                if column in available_indexes:
                    index_info = available_indexes[column]
                    return {
                        'type': 'INDEX_SCAN',
                        'index_column': column,
                        'index_type': index_info['type'],
                        'search_key': condition['value'],
                        'filter_after': where_clause_tree
                    }

        return {
            'type': 'FULL_TABLE_SCAN',
            'filter': where_clause_tree
        }

    def _flatten_conditions(self, node):
        if not node:
            return []

        if node['type'] == 'logical':
            return self._flatten_conditions(node['left']) + self._flatten_conditions(node['right'])
        elif node['type'] == 'condition':
            return [node]
        return []

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
indices_dir = os.path.join(project_root, 'indices')

if indices_dir not in sys.path:
    sys.path.insert(0, indices_dir)

from avl_file import AVLFile
from bplus_tree import BPlusTreeFile
from extendible_hash import DynamicHashFile
from isam import ISAMFile
from rtree import RTreeFile, Box

class DatabaseManager:
    def __init__(self, db_directory="db_data"):
        self.db_directory = db_directory
        self.metadata_file = os.path.join(db_directory, "db_metadata.json")
        self.tables_metadata = {}
        self.active_indexes = {}
        self._ensure_db_directory()
        self._load_metadata()

    def _ensure_db_directory(self):
        os.makedirs(self.db_directory, exist_ok=True)

    def _load_metadata(self):
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r', encoding="utf-8") as f:
                self.tables_metadata = json.load(f)
            print("Metadatos cargados")
        else:
            print("No se encontraron metadatos, se creara uno nuevo")

    def _save_metadata(self):
        with open(self.metadata_file, 'w', encoding="utf-8") as f:
            json.dump(self.tables_metadata, f, indent=4)
        print("Metadatos guardados")

    def _get_index_instance(self, table_name, index_info):
        table_name_key = table_name.lower()
        index_col = index_info['column']
        index_key = f"{table_name_key}_{index_col}"

        if index_key in self.active_indexes:
            return self.active_indexes[index_key]

        index_type = index_info['type'].lower()
        data_file_path = os.path.join(self.db_directory, f"{table_name_key}.jsonl")
        index_file_path = os.path.join(self.db_directory, f"{index_key}.idx")

        instance = None
        if index_type == 'btree':
            instance = BPlusTreeFile(data_file=data_file_path, index_file=index_file_path)
        elif index_type == 'hash':
            instance = DynamicHashFile(data_file=data_file_path, index_file=index_file_path)
        elif index_type == 'avl':
             instance = AVLFile(data_file=data_file_path, index_file=index_file_path)
        elif index_type == 'rtree':
             instance = RTreeFile(data_file=data_file_path, index_file=index_file_path)
        elif index_type == 'isam':
             meta_file_path = os.path.join(self.db_directory, f"{index_key}_meta.pkl")
             instance = ISAMFile(data_file=data_file_path, index_file=index_file_path, meta_file=meta_file_path)

        if instance:
            self.active_indexes[index_key] = instance
        return instance

    def execute_query(self, query):
        parser = SQLParser()
        parsed_command = parser.parse(query)

        if not parsed_command:
            return "Error: consulta invalida"

        command = parsed_command.get('command')
        table_name = parsed_command.get('table_name')

        if command == 'CREATE_TABLE':
            return self.create_table(parsed_command)

        if command == 'CREATE_TABLE_FROM_FILE':
            return self.create_table_from_file(parsed_command)

        if command == 'INSERT':
            return self.insert_into(parsed_command)

        if command == 'SELECT':
            return self.select_from(parsed_command)

        if command == 'DELETE':
            return self.delete_from(parsed_command)

        if command == 'DROP_TABLE':
             return self.drop_table(table_name)

        return f"Comando '{command}' no reconocido o no implementado"

    def create_table(self, command_data):
        table_name = command_data['table_name']
        table_name_key = table_name.lower()
        if table_name_key in self.tables_metadata:
            return f"Error: la tabla '{table_name}' ya existe"

        self.tables_metadata[table_name_key] = {
            'original_name': table_name,
            'columns': command_data['columns'],
            'indexes': {}
        }

        for col in command_data['columns']:
            if col.get('index_info'):
                index_type = col['index_info'].get('type')
                if index_type:
                    self.tables_metadata[table_name_key]['indexes'][col['name']] = {
                        'type': index_type.lower(),
                        'column': col['name']
                    }

        self._save_metadata()
        return f"Tabla '{table_name}' creada exitosamente"

    def create_table_from_file(self, command_data):
        table_name = command_data['table_name']
        table_name_key = table_name.lower()
        file_path = command_data['file_path']
        index_info_raw = command_data.get('index_info')

        if table_name_key in self.tables_metadata:
            return f"Error: la tabla '{table_name}' ya existe"

        if not os.path.exists(file_path):
            return f"Error: archivo no encontrado en '{file_path}'"

        try:
            with open(file_path, 'r', newline='', encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader, None)
                if not header:
                    return f"Error: archivo CSV '{file_path}' esta vacio o no tiene cabecera"
                records = [dict(zip(header, row)) for row in reader]
        except Exception as e:
            return f"Error leyendo el archivo CSV '{file_path}': {e}"

        inferred_columns = [{'name': h.strip(), 'type': 'TEXT', 'type_details': {}, 'constraints':[], 'index_info': None} for h in header]

        self.tables_metadata[table_name_key] = {'original_name': table_name, 'columns': inferred_columns, 'indexes': {}}

        if index_info_raw and index_info_raw.get('column'):
            index_col = index_info_raw['column']
            index_type = index_info_raw['type'].lower()

            if index_col not in header:
                del self.tables_metadata[table_name_key]
                return f"Error: la columna de indice '{index_col}' no se encuentra en la cabecera del CSV"

            for col_meta in self.tables_metadata[table_name_key]['columns']:
                if col_meta['name'] == index_col:
                    col_meta['index_info'] = {'type': index_type}
                    break
            self.tables_metadata[table_name_key]['indexes'][index_col] = {'type': index_type, 'column': index_col}

            index_instance = self._get_index_instance(table_name, {'type': index_type, 'column': index_col})

            if index_type == 'isam' and isinstance(index_instance, ISAMFile):
                try:
                    sorted_records_tuples = sorted([(rec.get(index_col), rec) for rec in records], key=lambda x: x[0])
                    index_instance.bulk_load(sorted_records_tuples)
                    self._save_metadata()
                    return f"Tabla '{table_name}' creada desde '{file_path}' con {len(records)} filas usando ISAM Bulk Load"
                except Exception as e:
                    self.drop_table(table_name)
                    return f"Error durante el bulk load de ISAM: {e}"
            else:
                for record in records:
                    key = record.get(index_col)
                    if key is not None:
                        pos = index_instance._append_to_data_file(record)
                        index_instance.insert(key, pos)
                self._save_metadata()
                return f"Tabla '{table_name}' creada desde '{file_path}' con {len(records)} filas y indice '{index_type}'"
        else:
            data_file_path = os.path.join(self.db_directory, f"{table_name_key}.jsonl")
            with open(data_file_path, "w", encoding="utf-8") as f:
                for record in records:
                    f.write(json.dumps(record) + "\n")
            self._save_metadata()
            return f"Tabla '{table_name}' creada desde '{file_path}' con {len(records)} filas (sin indice)"

    def insert_into(self, command_data):
        table_name = command_data['table_name']
        table_name_key = table_name.lower()

        if table_name_key not in self.tables_metadata:
            return f"Error: la tabla '{table_name}' no existe"

        meta = self.tables_metadata[table_name_key]
        values = command_data['values']
        row_dict = {}
        for i, col_def in enumerate(meta['columns']):
            row_dict[col_def['name']] = values[i]

        if not meta['indexes']:
            data_file_path = os.path.join(self.db_directory, f"{table_name_key}.jsonl")
            with open(data_file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row_dict) + "\n")
        else:
            data_file_path = os.path.join(self.db_directory, f"{table_name_key}.jsonl")
            pos = 0
            with open(data_file_path, "a", encoding="utf-8") as f:
                pos = f.tell()
                f.write(json.dumps(row_dict) + "\n")

            for index_col, index_info in meta['indexes'].items():
                index_instance = self._get_index_instance(table_name, index_info)
                if not index_instance:
                    continue

                key = row_dict.get(index_col)
                if key is None:
                    continue

                if isinstance(index_instance, RTreeFile):
                    try:
                        coords = [float(c) for c in key.split(',')]
                        item_box = Box(coords[0], coords[1], coords[2], coords[3], coords[4], coords[5])
                        index_instance.insert(item_box, pos)
                    except (ValueError, IndexError):
                        return f"Error: valor para R-Tree en columna '{index_col}' no es valido"
                else:
                    index_instance.insert(key, pos)

        return "1 fila insertada"

    def select_from(self, command_data):
        table_name = command_data['table_name']
        table_name_key = table_name.lower()

        if table_name_key not in self.tables_metadata:
            return f"Error: la tabla '{table_name}' no existe"

        meta = self.tables_metadata[table_name_key]
        where_clause = command_data.get('where_clause')

        if not where_clause:
            data_file_path = os.path.join(self.db_directory, f"{table_name_key}.jsonl")
            if not os.path.exists(data_file_path):
                return []

            results = []
            with open(data_file_path, 'r', encoding="utf-8") as f:
                for line in f:
                    results.append(json.loads(line))
            return results

        if where_clause['type'] == 'condition':
            col_to_search = where_clause['column']
            if col_to_search in meta['indexes']:
                index_info = meta['indexes'][col_to_search]
                index_instance = self._get_index_instance(table_name, index_info)

                search_key = where_clause['value']
                record = index_instance.search(search_key)

                return [record] if record else []

        return "Error: busqueda compleja sin optimizador no implementada, se requiere un full-scan"

    def delete_from(self, command_data):
        table_name = command_data['table_name']
        table_name_key = table_name.lower()
        if table_name_key not in self.tables_metadata:
            return f"Error: la tabla '{table_name}' no existe"
        meta = self.tables_metadata[table_name_key]
        where_clause = command_data.get('where_clause')

        if where_clause and where_clause['type'] == 'condition':
            col_to_delete = where_clause['column']
            if col_to_delete in meta['indexes']:
                index_info = meta['indexes'][col_to_delete]
                index_instance = self._get_index_instance(table_name, index_info)
                delete_key = where_clause['value']

                if isinstance(index_instance, RTreeFile):
                    return "DELETE en R-Tree necesita impl mas especifica (encontrar MBR y posicion)"

                deleted = index_instance.delete(delete_key)
                if deleted:
                    return f"1 fila eliminada del indice, se recomienda compactar la tabla '{table_name}'"
                else:
                    return "No se encontro la fila para eliminar"

        return "Error: DELETE solo soportado con condicion simple en columna indexada"

    def drop_table(self, table_name):
        table_name_key = table_name.lower()
        if table_name_key not in self.tables_metadata:
            return f"Error: la tabla '{table_name}' no existe"

        meta = self.tables_metadata[table_name_key]

        for index_col in meta['indexes']:
            index_file_path = os.path.join(self.db_directory, f"{table_name_key}_{index_col}.idx")
            if os.path.exists(index_file_path):
                os.remove(index_file_path)
            if meta['indexes'][index_col]['type'] == 'isam':
                meta_file_path = os.path.join(self.db_directory, f"{table_name_key}_{index_col}_meta.pkl")
                if os.path.exists(meta_file_path):
                    os.remove(meta_file_path)

        data_file_path = os.path.join(self.db_directory, f"{table_name_key}.jsonl")
        if os.path.exists(data_file_path):
            os.remove(data_file_path)

        del self.tables_metadata[table_name_key]
        del self.active_indexes[f"{table_name_key}_{index_col}"]
        self._save_metadata()

        return f"Tabla '{table_name}' eliminada"
