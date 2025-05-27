import os
import math
import pickle
from typing import List, Tuple, Optional, Any, cast

DEFAULT_MAX_CHILDREN = 4
MIN_FILL_FACTOR = 0.4

class Box:
    def __init__(self, x1: float, y1: float, z1: float,
                 x2: Optional[float] = None, y2: Optional[float] = None, z2: Optional[float] = None):
        self.x1 = float(x1)
        self.y1 = float(y1)
        self.z1 = float(z1)
        self.x2 = float(x1) if x2 is None else float(x2)
        self.y2 = float(y1) if y2 is None else float(y2)
        self.z2 = float(z1) if z2 is None else float(z2)
        if self.x1 > self.x2:
            self.x1, self.x2 = self.x2, self.x1
        if self.y1 > self.y2:
            self.y1, self.y2 = self.y2, self.y1
        if self.z1 > self.z2:
            self.z1, self.z2 = self.z2, self.z1

    @property
    def volume(self) -> float:
        vol = (self.x2 - self.x1) * (self.y2 - self.y1) * (self.z2 - self.z1)
        return max(0.0, vol)

    def intersects(self, other: 'Box') -> bool:
        return not (self.x2 < other.x1 or self.x1 > other.x2 or
                    self.y2 < other.y1 or self.y1 > other.y2 or
                    self.z2 < other.z1 or self.z1 > other.z2)

    def expand_to_include(self, other: 'Box'):
        self.x1 = min(self.x1, other.x1)
        self.y1 = min(self.y1, other.y1)
        self.z1 = min(self.z1, other.z1)
        self.x2 = max(self.x2, other.x2)
        self.y2 = max(self.y2, other.y2)
        self.z2 = max(self.z2, other.z2)

    @classmethod
    def union_mbr(cls, box1: 'Box', box2: 'Box') -> 'Box':
        return Box(min(box1.x1, box2.x1), min(box1.y1, box2.y1), min(box1.z1, box2.z1),
                   max(box1.x2, box2.x2), max(box1.y2, box2.y2), max(box1.z2, box2.z2))

    def __eq__(self, other):
        if not isinstance(other, Box):
            return NotImplemented
        return (self.x1 == other.x1 and self.y1 == other.y1 and
                self.z1 == other.z1 and self.x2 == other.x2 and
                self.y2 == other.y2 and self.z2 == other.z2)

    def __hash__(self):
        return hash((self.x1, self.y1, self.z1, self.x2, self.y2, self.z2))

    def __repr__(self) -> str:
        return f"Box({self.x1:.2f},{self.y1:.2f},{self.z1:.2f} -> {self.x2:.2f},{self.y2:.2f},{self.z2:.2f})"

class Sphere:
    def __init__(self, x: float, y: float, z:float, r: float):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.r = float(r)
        self.r_sq = r * r

    def contains_point(self, px: float, py: float, pz: float) -> bool:
        return (self.x - px)**2 + (self.y - py)**2 + (self.z - pz)**2 <= self.r_sq

    def intersects_box(self, box: Box) -> bool:
        closest_x = max(box.x1, min(self.x, box.x2))
        closest_y = max(box.y1, min(self.y, box.y2))
        closest_z = max(box.z1, min(self.z, box.z2))
        return self.contains_point(closest_x, closest_y, closest_z)

    def __repr__(self) -> str:
        return f"Sphere(center=({self.x:.2f},{self.y:.2f},{self.z:.2f}), r={self.r:.2f})"

class RTreeNode:
    def __init__(self, leaf: bool = False, parent: Optional['RTreeNode'] = None, level: int = 0):
        self.leaf = leaf
        self.parent = parent
        self.level = level
        self.entries: List[Tuple[Box, Any]] = []

    def is_overfull(self, max_children: int) -> bool:
        return len(self.entries) > max_children

    def add_entry(self, mbr: Box, item: Any):
        self.entries.append((mbr, item))

    def remove_entry_by_item(self, item_to_remove: Any) -> bool:
        idx_to_remove = -1
        for i, (_, item) in enumerate(self.entries):
            if item == item_to_remove:
                idx_to_remove = i
                break
        if idx_to_remove != -1:
            del self.entries[idx_to_remove]
            return True
        return False

    def remove_entry_by_mbr_and_item(self, mbr_to_remove: Box, item_to_remove: Any) -> bool:
        idx_to_remove = -1
        for i, (mbr, item) in enumerate(self.entries):
            if item == item_to_remove and mbr == mbr_to_remove:
                idx_to_remove = i
                break
        if idx_to_remove != -1:
            del self.entries[idx_to_remove]
            return True
        return False

class RTreeFile:
    def __init__(self, data_file="rtree_data.jsonl", index_file="rtree.idx", max_children: int = DEFAULT_MAX_CHILDREN):
        self.data_file = data_file
        self.index_file = index_file
        self.max_children = max(2, max_children)
        self.min_fill = max(1, math.ceil(self.max_children * MIN_FILL_FACTOR))
        self.root: RTreeNode = RTreeNode(leaf=True, level=0)
        self._load_index()
        if not os.path.exists(self.data_file):
            with open(self.data_file, "w", encoding="utf-8") as f:
                pass

    def _save_index(self):
        try:
            with open(self.index_file, "wb") as f:
                pickle.dump((self.max_children, self.root), f)
        except Exception as e:
            print(f"Error al guardar el indice R-Tree en '{self.index_file}': {e}")

    def _load_index(self):
        if os.path.exists(self.index_file) and os.path.getsize(self.index_file) > 0:
            try:
                with open(self.index_file, "rb") as f:
                    persisted_max_children, persisted_root = pickle.load(f)
                self.max_children = persisted_max_children
                self.min_fill = max(1, math.ceil(self.max_children * MIN_FILL_FACTOR))
                self.root = persisted_root
                self._recalculate_levels_from_root()
            except Exception as e:
                print(f"Error al cargar el indice R-Tree '{self.index_file}': {e}")
                self.root = RTreeNode(leaf=True, level=0)
        else:
            self.root = RTreeNode(leaf=True, level=0)

    def _update_tree_metadata(self, node: RTreeNode, parent: Optional[RTreeNode], level: int):
        node.parent = parent
        node.level = level
        if not node.leaf:
            for _, child_node_item in node.entries:
                child_node = cast(RTreeNode, child_node_item)
                self._update_tree_metadata(child_node, node, level + 1)

    def _get_tree_height(self) -> int:
        if not self.root:
            return -1
        return self.root.level

    def _choose_node_for_insertion(self, current_node: RTreeNode, entry_mbr: Box, target_parent_level: int) -> RTreeNode:
        if current_node.level == target_parent_level:
            return current_node

        if current_node.leaf and target_parent_level > 0:
            raise Exception(f"No se encontro padre en el nivel {target_parent_level} cuando ya esta en la hoja (nivel 0)")

        min_enlargement = float('inf')
        min_volume_tie = float('inf')
        best_next_node: Optional[RTreeNode] = None

        for child_mbr, child_node_item in current_node.entries:
            child_node = cast(RTreeNode, child_node_item)
            current_volume = child_mbr.volume

            expanded_mbr_candidate = Box.union_mbr(child_mbr, entry_mbr)
            enlargement = expanded_mbr_candidate.volume - current_volume

            if enlargement < min_enlargement:
                min_enlargement = enlargement
                min_volume_tie = current_volume
                best_next_node = child_node
            elif enlargement == min_enlargement and current_volume < min_volume_tie:
                min_volume_tie = current_volume
                best_next_node = child_node

        if best_next_node is None:
            if not current_node.entries:
                if current_node == self.root and self.root.leaf and target_parent_level == 0:
                    return self.root
                raise ValueError(f"Nodo interno {id(current_node)} (nivel {current_node.level}) genera error en _choose_node_for_insertion")
            best_next_node = cast(RTreeNode, current_node.entries[0][1])

        return self._choose_node_for_insertion(best_next_node, entry_mbr, target_parent_level)

    def _calculate_mbr_for_node(self, node: RTreeNode) -> Optional[Box]:
        if not node.entries:
            return None
        current_mbr_tuple = node.entries[0]
        overall_mbr = Box(current_mbr_tuple[0].x1, current_mbr_tuple[0].y1, current_mbr_tuple[0].z1,
                          current_mbr_tuple[0].x2, current_mbr_tuple[0].y2, current_mbr_tuple[0].z2)
        for mbr, _ in node.entries[1:]:
            overall_mbr.expand_to_include(mbr)
        return overall_mbr

    def _choose_subtree(self, current_node: RTreeNode, entry_mbr: Box, target_level_of_child: int) -> RTreeNode:
        if current_node.level == target_level_of_child:
            return current_node
        if current_node.leaf:
            return current_node

        min_enlargement = float('inf')
        min_volume_tie = float('inf')
        best_next_node: Optional[RTreeNode] = None
        for child_mbr, child_node_item in current_node.entries:
            child_node = cast(RTreeNode, child_node_item)
            current_volume = child_mbr.volume
            expanded_mbr_candidate = Box.union_mbr(child_mbr, entry_mbr)
            enlargement = expanded_mbr_candidate.volume - current_volume
            if enlargement < min_enlargement:
                min_enlargement = enlargement
                min_volume_tie = current_volume
                best_next_node = child_node
            elif enlargement == min_enlargement and current_volume < min_volume_tie:
                min_volume_tie = current_volume
                best_next_node = child_node

        if best_next_node is None:
            if not current_node.entries:
                raise Exception(f"Nodo interno {id(current_node)} a nivel {current_node.level} no tiene hijos")
            best_next_node = cast(RTreeNode, current_node.entries[0][1])

        return self._choose_subtree(best_next_node, entry_mbr, target_level_of_child)

    def _execute_insert(self, entry_mbr: Box, item_to_insert: Any, item_is_a_node_flag: bool, known_item_level_if_node: Optional[int] = None):
        target_parent_node_level: int
        if not item_is_a_node_flag:
            target_parent_node_level = 0
        else:
            if known_item_level_if_node is None:
                raise ValueError("known_item_level_if_node no fue recibido (obligatorio si item_is_a_node_flag)")
            target_parent_node_level = known_item_level_if_node + 1

        chosen_parent_node = self._choose_node_for_insertion(self.root, entry_mbr, target_parent_node_level)
        chosen_parent_node.add_entry(entry_mbr, item_to_insert)

        if item_is_a_node_flag:
            node_inserted = cast(RTreeNode, item_to_insert)
            node_inserted.parent = chosen_parent_node
            if node_inserted.level != chosen_parent_node.level - 1:
                pass

        if chosen_parent_node.is_overfull(self.max_children):
            self._handle_overflow(chosen_parent_node, None)
        else:
            self._adjust_tree(chosen_parent_node)

    def insert(self, item_box: Box, data_position: int):
        self._execute_insert(item_box, data_position, False)
        self._save_index()

    def _handle_overflow(self, node1_modified: RTreeNode, node2_new_sibling: Optional[RTreeNode]):
        if node2_new_sibling is None:
            node1_prime, node2_prime = self._quadratic_split(node1_modified)
            return self._handle_overflow(node1_prime, node2_prime)

        parent = node1_modified.parent

        mbr_node1 = self._calculate_mbr_for_node(node1_modified)
        mbr_node2 = self._calculate_mbr_for_node(node2_new_sibling)

        if parent is None:
            new_root = RTreeNode(leaf=False, level=node1_modified.level + 1)
            if mbr_node1:
                new_root.add_entry(mbr_node1, node1_modified)
            if mbr_node2:
                new_root.add_entry(mbr_node2, node2_new_sibling)
            node1_modified.parent = new_root
            node2_new_sibling.parent = new_root
            self.root = new_root
            return

        updated_in_parent = False
        for i, (p_mbr, p_child) in enumerate(parent.entries):
            if p_child == node1_modified:
                if mbr_node1:
                    parent.entries[i] = (mbr_node1, node1_modified)
                else:
                    del parent.entries[i]
                updated_in_parent = True
                break
        if not updated_in_parent:
            print(f"Error: Nodo {id(node1_modified)} no encontrado en padre {id(parent)} durante handle_overflow")

        if mbr_node2:
            parent.add_entry(mbr_node2, node2_new_sibling)
        node2_new_sibling.parent = parent

        if parent.is_overfull(self.max_children):
            self._handle_overflow(parent, None)
        else:
            self._adjust_tree(parent)

    def _quadratic_split(self, node_to_split: RTreeNode) -> Tuple[RTreeNode, RTreeNode]:
        all_entries = list(node_to_split.entries)

        best_pair_indices = (0, 1)
        max_dead_space = -float('inf')
        if len(all_entries) <=1:
            return node_to_split, RTreeNode(leaf=node_to_split.leaf, parent=node_to_split.parent, level=node_to_split.level)

        for i in range(len(all_entries)):
            for j in range(i + 1, len(all_entries)):
                e1_mbr, _ = all_entries[i]
                e2_mbr, _ = all_entries[j]
                combined_mbr = Box.union_mbr(e1_mbr, e2_mbr)
                dead_space = combined_mbr.volume - e1_mbr.volume - e2_mbr.volume
                if dead_space > max_dead_space:
                    max_dead_space = dead_space
                    best_pair_indices = (i, j)

        idx1, idx2 = best_pair_indices

        group1_node = node_to_split
        group1_node.entries = []

        group2_node = RTreeNode(leaf=node_to_split.leaf, parent=node_to_split.parent, level=node_to_split.level)

        seed1_entry = all_entries.pop(max(idx1, idx2))
        seed2_entry = all_entries.pop(min(idx1, idx2))

        group1_node.add_entry(seed1_entry[0], seed1_entry[1])
        group2_node.add_entry(seed2_entry[0], seed2_entry[1])

        while all_entries:
            if len(group1_node.entries) + len(all_entries) == self.min_fill:
                for entry in all_entries:
                    group1_node.add_entry(entry[0], entry[1])
                all_entries.clear()
                break
            if len(group2_node.entries) + len(all_entries) == self.min_fill:
                for entry in all_entries:
                    group2_node.add_entry(entry[0], entry[1])
                all_entries.clear()
                break

            best_entry_idx = -1
            max_pref_diff = -float('inf')
            sel_cost1, sel_cost2 = 0.0, 0.0

            mbr_g1 = self._calculate_mbr_for_node(group1_node)
            mbr_g2 = self._calculate_mbr_for_node(group2_node)

            for i, (entry_mbr, _) in enumerate(all_entries):
                vol_g1 = mbr_g1.volume if mbr_g1 else 0.0
                vol_g2 = mbr_g2.volume if mbr_g2 else 0.0
                cost1 = (Box.union_mbr(mbr_g1, entry_mbr).volume - vol_g1) if mbr_g1 else entry_mbr.volume
                cost2 = (Box.union_mbr(mbr_g2, entry_mbr).volume - vol_g2) if mbr_g2 else entry_mbr.volume

                preference_diff = abs(cost1 - cost2)
                if preference_diff > max_pref_diff:
                    max_pref_diff = preference_diff
                    best_entry_idx = i
                    sel_cost1, sel_cost2 = cost1, cost2

            chosen_entry_tuple = all_entries.pop(best_entry_idx)

            if sel_cost1 < sel_cost2:
                group1_node.add_entry(chosen_entry_tuple[0], chosen_entry_tuple[1])
            elif sel_cost2 < sel_cost1:
                group2_node.add_entry(chosen_entry_tuple[0], chosen_entry_tuple[1])
            else:
                vol_g1_curr = self._calculate_mbr_for_node(group1_node).volume if group1_node.entries else 0
                vol_g2_curr = self._calculate_mbr_for_node(group2_node).volume if group2_node.entries else 0
                if vol_g1_curr < vol_g2_curr:
                    group1_node.add_entry(chosen_entry_tuple[0], chosen_entry_tuple[1])
                elif vol_g2_curr < vol_g1_curr:
                    group2_node.add_entry(chosen_entry_tuple[0], chosen_entry_tuple[1])
                else:
                    if len(group1_node.entries) <= len(group2_node.entries):
                        group1_node.add_entry(chosen_entry_tuple[0], chosen_entry_tuple[1])
                    else:
                        group2_node.add_entry(chosen_entry_tuple[0], chosen_entry_tuple[1])

        if not group1_node.leaf:
            for _, child_item in group1_node.entries:
                cast(RTreeNode, child_item).parent = group1_node
        if not group2_node.leaf:
            for _, child_item in group2_node.entries:
                cast(RTreeNode, child_item).parent = group2_node

        return group1_node, group2_node

    def _adjust_tree(self, node: RTreeNode):
        current = node
        while current is not None:
            if current.parent:
                parent = current.parent
                new_mbr_for_current = self._calculate_mbr_for_node(current)
                updated_in_parent = False
                for i, (p_mbr, p_child) in enumerate(parent.entries):
                    if p_child == current:
                        if new_mbr_for_current and p_mbr != new_mbr_for_current:
                            parent.entries[i] = (new_mbr_for_current, current)
                        elif not new_mbr_for_current:
                            del parent.entries[i]
                        break

            current = current.parent

    def _search_recursive(self, node: RTreeNode, query_shape: Any, results: List[int]):
        for mbr, item_or_child_node in node.entries:
            shape_intersects_mbr = False
            if isinstance(query_shape, Box):
                shape_intersects_mbr = query_shape.intersects(mbr)
            elif isinstance(query_shape, Sphere):
                shape_intersects_mbr = query_shape.intersects_box(mbr)
            else:
                raise TypeError(f"Query shape no soportado: {type(query_shape)}")

            if shape_intersects_mbr:
                if node.leaf:
                    results.append(cast(int, item_or_child_node))
                else:
                    self._search_recursive(cast(RTreeNode, item_or_child_node), query_shape, results)

    def search_box(self, query_box: Box) -> List[int]:
        results = []
        if self.root and self.root.entries:
            self._search_recursive(self.root, query_box, results)
        return list(set(results))

    def search_sphere(self, query_sphere: Sphere) -> List[int]:
        results = []
        if self.root and self.root.entries:
            self._search_recursive(self.root, query_sphere, results)
        return list(set(results))

    def delete(self, item_box_to_delete: Box, data_position_to_delete: int) -> bool:
        leaf_node = self._find_leaf_for_item(self.root, item_box_to_delete, data_position_to_delete)
        if leaf_node:
            removed = leaf_node.remove_entry_by_mbr_and_item(item_box_to_delete, data_position_to_delete)
            if removed:
                self._condense_tree(leaf_node)
                self._save_index()
                return True
        return False

    def _find_leaf_for_item(self, node: RTreeNode, item_box: Box, data_position: int) -> Optional[RTreeNode]:
        if node.leaf:
            for mbr, pos in node.entries:
                if pos == data_position and mbr == item_box:
                    return node
            return None
        else:
            for mbr, child_node_item in node.entries:
                child_node = cast(RTreeNode, child_node_item)
                if mbr.intersects(item_box):
                    found_node = self._find_leaf_for_item(child_node, item_box, data_position)
                    if found_node:
                        return found_node
            return None

    def _reinsert_node_entry(self, node_mbr: Box, node_to_reinsert: RTreeNode):
        self._execute_insert(node_mbr, node_to_reinsert, True, node_to_reinsert.level)

    def _condense_tree(self, leaf_node: RTreeNode):
        Q_eliminated_nodes: List[RTreeNode] = []
        current_N = leaf_node

        while current_N != self.root:
            P = current_N.parent
            if P is None:
                break

            if len(current_N.entries) < self.min_fill:
                P.remove_entry_by_item(current_N)
                Q_eliminated_nodes.append(current_N)
            else:
                mbr_N_actual = self._calculate_mbr_for_node(current_N)
                updated_in_parent = False
                for i, (p_mbr, p_child) in enumerate(P.entries):
                    if p_child == current_N:
                        if mbr_N_actual and p_mbr != mbr_N_actual:
                            P.entries[i] = (mbr_N_actual, current_N)
                        elif not mbr_N_actual and P.entries:
                            del P.entries[i]
                        updated_in_parent = True
                        break
            current_N = P

        if Q_eliminated_nodes:
            original_save_fn = self._save_index
            self._save_index = lambda: None

            for eliminated_node in sorted(Q_eliminated_nodes, key=lambda n: n.level, reverse=True):
                for entry_mbr, entry_item in eliminated_node.entries:
                    if eliminated_node.leaf:
                        self._execute_insert(entry_mbr, cast(int, entry_item), 0)
                    else:
                        child_node_to_reinsert = cast(RTreeNode, entry_item)
                        self._reinsert_node_entry(entry_mbr, child_node_to_reinsert)

            self._save_index = original_save_fn

        if self.root and not self.root.leaf and len(self.root.entries) == 1:
            old_root = self.root
            self.root = cast(RTreeNode, old_root.entries[0][1])
            self.root.parent = None
            self._update_tree_metadata(self.root, None, self.root.level)
            if self.root.leaf:
                self.root.level = 0
            self._recalculate_levels_from_root()

    def _recalculate_levels_from_root(self, node: Optional[RTreeNode] = None, parent: Optional[RTreeNode] = None, current_height_assignment: Optional[int] = None):
        if node is None:
            node = self.root
            if not node:
                return
            h = 0
            temp_node = node
            if not temp_node.leaf:
                h = 1
                while temp_node.entries and not cast(RTreeNode, temp_node.entries[0][1]).leaf:
                    temp_node = cast(RTreeNode, temp_node.entries[0][1])
                    h += 1
            current_height_assignment = h

        if not node:
            return

        node.parent = parent
        node.level = current_height_assignment

        if not node.leaf:
            for _, child_item in node.entries:
                child_node = cast(RTreeNode, child_item)
                self._recalculate_levels_and_parents_from_root(child_node, node, current_height_assignment - 1)

    def _set_levels_recursive(self, node: RTreeNode, current_level_from_root_as_height: int):
        if not node:
            return
        node.level = current_level_from_root_as_height
        if not node.leaf:
            for _, child_node_item in node.entries:
                self._set_levels_recursive(cast(RTreeNode, child_node_item), current_level_from_root_as_height - 1)

    def _reinsert_node_entry(self, node_mbr: Box, node_to_reinsert: RTreeNode):
        self._execute_insert(node_mbr, node_to_reinsert, True, node_to_reinsert.level)

    def _collect_leaf_entries_for_reinsertion(self, node:RTreeNode, reinsert_list: List[Tuple[Box, int]]):
        if node.leaf:
            reinsert_list.extend(cast(List[Tuple[Box, int]], node.entries))
        else:
            for _, child_node_item in node.entries:
                self._collect_leaf_entries_for_reinsertion(cast(RTreeNode, child_node_item), reinsert_list)

    def update(self, old_item_box: Box, old_data_pos: int, new_item_box: Box, new_data_pos: int) -> bool:
        deleted = self.delete(old_item_box, old_data_pos)
        if deleted:
            self.insert(new_item_box, new_data_pos)
            return True
        else:
            self.insert(new_item_box, new_data_pos)
            return False

    def compact_data_file(self, pos_map: dict):
        print("Actualizando posiciones en R-Tree debido a la compactacion del archivo de datos...")
        updated_count = 0
        q: List[RTreeNode] = [self.root]
        visited_nodes_ids = set()
        while q:
            curr_node = q.pop(0)
            if id(curr_node) in visited_nodes_ids:
                continue
            visited_nodes_ids.add(id(curr_node))
            if curr_node.leaf:
                for i in range(len(curr_node.entries)):
                    mbr, old_pos = curr_node.entries[i]
                    if old_pos in pos_map:
                        new_pos = pos_map[old_pos]
                        if old_pos != new_pos:
                            curr_node.entries[i] = (mbr, new_pos)
                            updated_count += 1
            else:
                for _, child_node_item in curr_node.entries:
                    q.append(cast(RTreeNode, child_node_item))
        if updated_count > 0:
            print(f"Se actualizaron {updated_count} posiciones de datos en el R-Tree.")
            self._save_index()
        else:
            print("No se requirieron actualizaciones de posicion en el R-Tree.")

    def print_tree(self, node: Optional[RTreeNode] = None, level_print_depth: int = 0):
        if node is None:
            node = self.root
            print(f"R-Tree 3D (Max Hijos: {self.max_children}, Min Llenado: {self.min_fill}, Altura Nodos Raiz: {node.level})")

        indent = "  " * level_print_depth
        node_type = "Leaf" if node.leaf else "Internal"
        parent_id_str = str(id(node.parent)) if node.parent else "None"
        node_mbr_str = str(self._calculate_mbr_for_node(node)) if node.entries else 'EmptyNode'
        print(f"{indent}{node_type} Node (ID: {id(node)}, Level: {node.level}, ParentID: {parent_id_str}) MBR: {node_mbr_str} Entries: {len(node.entries)}")

        for i, (mbr, item) in enumerate(node.entries):
            if node.leaf:
                print(f"{indent}  Entry {i}: MBR={mbr}, DataPos={item}")
            else:
                child_node = cast(RTreeNode, item)
                print(f"{indent}  Entry {i}: ChildMBR={mbr}, ChildNodeID={id(child_node)} (Level: {child_node.level})")
                self.print_tree(child_node, level_print_depth + 1)
