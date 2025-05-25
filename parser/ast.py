# Expression classes
class Expr:
    pass

class LiteralExpr(Expr):
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return str(self.value)

class Identifier(Expr):
    def __init__(self, name):
        self.name = name
    
    def __str__(self):
        return self.name

class BinaryExpr(Expr):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right
    
    def __str__(self):
        return f"({self.left} {self.operator} {self.right})"

class UnaryExpr(Expr):
    def __init__(self, operator, right):
        self.operator = operator
        self.right = right
    
    def __str__(self):
        return f"{self.operator} {self.right}"

class GroupingExpr(Expr):
    def __init__(self, expression):
        self.expression = expression
    
    def __str__(self):
        return f"({self.expression})"

class BetweenExpr(Expr):
    def __init__(self, column, lower, upper):
        self.column = column
        self.lower = lower
        self.upper = upper
    
    def __str__(self):
        return f"{self.column} BETWEEN {self.lower} AND {self.upper}"

class InExpr(Expr):
    def __init__(self, column, values):
        self.column = column
        self.values = values
    
    def __str__(self):
        return f"{self.column} IN ({', '.join(str(v) for v in self.values)})"

class CoordinateExpr(Expr):
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __str__(self):
        return f"({self.x}, {self.y})"

# Data type and column definition
class DataType:
    def __init__(self, type_name, params=None):
        self.type_name = type_name
        self.params = params
    
    def __str__(self):
        if self.params:
            return f"{self.type_name}({', '.join(str(p) for p in self.params)})"
        return self.type_name

class ColumnDef:
    def __init__(self, name, data_type, primary_key=False, index_type=None):
        self.name = name
        self.data_type = data_type
        self.primary_key = primary_key
        self.index_type = index_type
    
    def __str__(self):
        result = f"{self.name} {self.data_type}"
        if self.primary_key:
            result += " PRIMARY KEY"
        if self.index_type:
            result += f" INDEX {self.index_type}"
        return result

# Statement classes
class Stmt:
    pass

class SelectStmt(Stmt):
    def __init__(self, columns, table_name, where=None):
        self.columns = columns
        self.table_name = table_name
        self.where = where
    
    def __str__(self):
        result = f"SELECT {', '.join(str(c) for c in self.columns)} FROM {self.table_name}"
        if self.where:
            result += f" WHERE {self.where}"
        return result

class CreateTableStmt(Stmt):
    def __init__(self, table_name, columns):
        self.table_name = table_name
        self.columns = columns
    
    def __str__(self):
        cols = ', '.join(str(c) for c in self.columns)
        return f"CREATE TABLE {self.table_name} ({cols})"

class DropTableStmt(Stmt):
    def __init__(self, table_name):
        self.table_name = table_name
    
    def __str__(self):
        return f"DROP TABLE {self.table_name}"

class InsertStmt(Stmt):
    def __init__(self, table_name, columns, values):
        self.table_name = table_name
        self.columns = columns
        self.values = values
    
    def __str__(self):
        cols = f"({', '.join(str(c) for c in self.columns)})" if self.columns else ""
        vals = ', '.join(str(v) for v in self.values)
        return f"INSERT INTO {self.table_name}{cols} VALUES ({vals})"

class DeleteStmt(Stmt):
    def __init__(self, table_name, where=None):
        self.table_name = table_name
        self.where = where
    
    def __str__(self):
        result = f"DELETE FROM {self.table_name}"
        if self.where:
            result += f" WHERE {self.where}"
        return result

class CreateIndexStmt(Stmt):
    def __init__(self, index_name, table_name, columns, index_type=None):
        self.index_name = index_name
        self.table_name = table_name
        self.columns = columns
        self.index_type = index_type
    
    def __str__(self):
        type_clause = f" USING {self.index_type}" if self.index_type else ""
        cols = ', '.join(str(c) for c in self.columns)
        return f"CREATE INDEX {self.index_name} ON {self.table_name}{type_clause} ({cols})"

class DropIndexStmt(Stmt):
    def __init__(self, index_name):
        self.index_name = index_name
    
    def __str__(self):
        return f"DROP INDEX {self.index_name}"