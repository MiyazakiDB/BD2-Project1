import math
from typing import List, Tuple, Optional

MAX_CHILDREN = 4  # TODO check if we will keep it there

class Rectangle:
    def __init__(self, x1, y1, x2=None, y2=None):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x1 if x2 is None else x2
        self.y2 = y1 if y2 is None else y2

    def contains_point(self, x, y):
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def intersects(self, other: 'Rectangle'):
        return not (self.x2 < other.x1 or self.x1 > other.x2 or
                    self.y2 < other.y1 or self.y1 > other.y2)

    def expand_to_include(self, other: 'Rectangle'):
        self.x1 = min(self.x1, other.x1)
        self.y1 = min(self.y1, other.y1)
        self.x2 = max(self.x2, other.x2)
        self.y2 = max(self.y2, other.y2)

class Circle:
    def __init__(self, x, y, r):
        self.x, self.y, self.r = x, y, r

    def contains_point(self, px, py):
        return math.hypot(self.x - px, self.y - py) <= self.r

    def intersects_rect(self, rect: Rectangle):
        nearest_x = max(rect.x1, min(self.x, rect.x2))
        nearest_y = max(rect.y1, min(self.y, rect.y2))
        return self.contains_point(nearest_x, nearest_y)

class RTreeNode:
    def __init__(self, leaf=False):
        self.leaf = leaf
        self.entries = []

    def is_full(self):
        return len(self.entries) >= MAX_CHILDREN

class RTree:
    def __init__(self, data_file="data.bin"):
        self.root = RTreeNode(leaf=True)
        self.data_file = data_file
        self.records = {}
        self.load_data()

    def load_data(self):
        with open(self.data_file, "rb") as f:
            for line in f:
                record = line.decode("utf-8").strip()
                if not record:
                    continue
                parts = record.split(",")
                if len(parts) < 7:
                    continue  # TODO skip malformed, maybe we modify this
                record_id = int(parts[0])
                x, y = float(parts[5]), float(parts[6])
                self.records[record_id] = record
                self.insert(x, y, record_id)

    def insert(self, x, y, record_id):
        mbr = Rectangle(x, y)
        new_root = self._insert(self.root, mbr, record_id)
        if new_root:
            self.root = new_root

    def _insert(self, node: RTreeNode, rect: Rectangle, record_id: int) -> Optional[RTreeNode]:
        if node.leaf:
            node.entries.append((rect, record_id))
        else:
            best = min(node.entries, key=lambda c: self._enlargement(c[0], rect))
            child = best[1]
            result = self._insert(child, rect, record_id)
            if result:
                # child was split, so we need to insert both parts
                node.entries.remove(best)
                for new_rect, new_node in result:
                    node.entries.append((new_rect, new_node))
            else:
                best[0].expand_to_include(rect)

        if node.is_full():
            return self._split(node)
        return None

    def _split(self, node: RTreeNode) -> List[Tuple[Rectangle, RTreeNode]]:
        entries = node.entries
        half = len(entries) // 2
        left_entries = entries[:half]
        right_entries = entries[half:]

        left = RTreeNode(leaf=node.leaf)
        right = RTreeNode(leaf=node.leaf)
        left.entries = left_entries
        right.entries = right_entries

        return [
            (self._calculate_mbr(left), left),
            (self._calculate_mbr(right), right)
        ]

    def _enlargement(self, r1: Rectangle, r2: Rectangle) -> float:
        original_area = (r1.x2 - r1.x1) * (r1.y2 - r1.y1)
        combined = Rectangle(r1.x1, r1.y1, r1.x2, r1.y2)
        combined.expand_to_include(r2)
        new_area = (combined.x2 - combined.x1) * (combined.y2 - combined.y1)
        return new_area - original_area

    def _calculate_mbr(self, node: RTreeNode) -> Rectangle:
        rects = [r for r, _ in node.entries]
        x1 = min(r.x1 for r in rects)
        y1 = min(r.y1 for r in rects)
        x2 = max(r.x2 for r in rects)
        y2 = max(r.y2 for r in rects)
        return Rectangle(x1, y1, x2, y2)

    def search_rect(self, x1, y1, x2, y2) -> List[str]:
        return self._search_rect(self.root, Rectangle(x1, y1, x2, y2))

    def search_circle(self, cx, cy, radius) -> List[str]:
        return self._search_circle(self.root, Circle(cx, cy, radius))

    def _search_rect(self, node: RTreeNode, query: Rectangle) -> List[str]:
        results = []
        for entry in node.entries:
            if node.leaf:
                rect, record_id = entry
                if query.contains_point(rect.x1, rect.y1):
                    results.append(self.records[record_id])
            else:
                rect, child = entry
                if rect.intersects(query):
                    results.extend(self._search_rect(child, query))
        return results

    def _search_circle(self, node: RTreeNode, query: Circle) -> List[str]:
        results = []
        for entry in node.entries:
            if node.leaf:
                rect, record_id = entry
                if query.contains_point(rect.x1, rect.y1):
                    results.append(self.records[record_id])
            else:
                rect, child = entry
                if query.intersects_rect(rect):
                    results.extend(self._search_circle(child, query))
        return results

    def delete(self, record_id):
        rect = self._find_rect(self.root, record_id)
        if rect:
            orphaned = []
            self._delete(self.root, rect, record_id, orphaned)
            if not self.root.entries and not self.root.leaf:
                self.root = orphaned.pop() if orphaned else RTreeNode(leaf=True)
            for orphan in orphaned:
                for entry in orphan.entries:
                    if orphan.leaf:
                        self._insert(self.root, entry[0], entry[1])
                    else:
                        self._reinsert_subtree(entry[1])
            if record_id in self.records:
                del self.records[record_id]

    def _find_rect(self, node: RTreeNode, record_id: int) -> Optional[Rectangle]:
        for entry in node.entries:
            if node.leaf:
                rect, rid = entry
                if rid == record_id:
                    return rect
            else:
                rect, child = entry
                if (res := self._find_rect(child, record_id)):
                    return res
        return None

    def _delete(self, node: RTreeNode, rect: Rectangle, record_id: int, orphaned: list) -> bool:
        for i, entry in enumerate(node.entries):
            if node.leaf:
                r, rid = entry
                if rid == record_id:
                    node.entries.pop(i)
                    return True
            else:
                r, child = entry
                if r.intersects(rect):
                    deleted = self._delete(child, rect, record_id, orphaned)
                    if deleted:
                        if not child.entries:
                            node.entries.pop(i)
                        else:
                            new_mbr = self._calculate_mbr(child)
                            node.entries[i] = (new_mbr, child)
                        if not child.entries:
                            orphaned.append(child)
                        return True
        return False

    def _reinsert_subtree(self, node: RTreeNode):
        if node.leaf:
            for rect, record_id in node.entries:
                self._insert(self.root, rect, record_id)
        else:
            for _, child in node.entries:
                self._reinsert_subtree(child)
