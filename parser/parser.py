import re

# TODO check which fields we will have to add to the parser

class SQLParser:
    def parse(self, query: str) -> dict:
        query = query.strip().rstrip(";")
        query_upper = query.upper()

        if query_upper.startswith("INSERT INTO"):
            return self._parse_insert(query)
        elif query_upper.startswith("SELECT"):
            if "BETWEEN" in query_upper:
                return self._parse_range_select(query)
            elif "CONTAINS" in query_upper:
                return self._parse_contains(query)
            else:
                return self._parse_select(query)
        elif query_upper.startswith("DELETE FROM"):
            return self._parse_delete(query)
        else:
            raise ValueError("Unsupported query")

    def _parse_insert(self, query: str) -> dict:
        match = re.match(r"INSERT INTO (\w+) VALUES \((.+)\)", query, re.IGNORECASE)
        if not match:
            raise ValueError("Invalid INSERT syntax")
        table = match.group(1)
        values = [self._parse_value(v.strip()) for v in self._split_values(match.group(2))]
        return {
            "action": "insert",
            "table": table,
            "values": values
        }

    def _parse_select(self, query: str) -> dict:
        match = re.match(r"SELECT \* FROM (\w+) WHERE id\s*=\s*(\d+)", query, re.IGNORECASE)
        if not match:
            raise ValueError("Invalid SELECT syntax")
        return {
            "action": "select",
            "table": match.group(1),
            "value": int(match.group(2))
        }

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

    def _parse_delete(self, query: str) -> dict:
        match = re.match(r"DELETE FROM (\w+) WHERE id\s*=\s*(\d+)", query, re.IGNORECASE)
        if not match:
            raise ValueError("Invalid DELETE syntax")
        return {
            "action": "delete",
            "table": match.group(1),
            "id": int(match.group(2))
        }

    def _parse_value(self, val: str):
        if val.startswith("'") and val.endswith("'"):
            return val[1:-1]
        elif "." in val:
            return float(val)
        else:
            try:
                return int(val)
            except ValueError:
                return val

    def _split_values(self, values_str: str):
        return re.findall(r"'[^']*'|[^,]+", values_str)
