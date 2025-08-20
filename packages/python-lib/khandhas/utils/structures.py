from typing import List, Dict, Optional, TypeVar, Generic

T = TypeVar("T")


class Tree(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value: T = value
        self.children: List["Tree[T]"] = []
        self.parent: Optional["Tree[T]"] = None

    def add_child(self, child: "Tree[T]") -> None:
        self.children.append(child)
        child.parent = self

    def __repr__(self) -> str:
        return f"Tree({self.value})"


def build_field_dependency_tree(fields: List[DynamicField]) -> Tree[DynamicField]:
    """
    Build a dependency tree from a list of fields.
    Each field may have a 'depends_on' attribute (list of FieldDependency objects).
    The root is a dummy node 'NoneDep' whose children are fields with no dependencies.
    """
    name_to_node: Dict[str, Tree[DynamicField]] = {}
    for field in fields:
        name_to_node[field.name] = Tree(field)
    root: Tree[DynamicField] = Tree("NoneDep")  # type: ignore
    for field in fields:
        node = name_to_node[field.name]
        depends_on: List[FieldDependency] = getattr(field, "depends_on", [])
        dep_names: List[str] = [dep.field_name for dep in depends_on] if depends_on else []
        if not dep_names:
            root.add_child(node)
        else:
            for dep_name in dep_names:
                parent_node = name_to_node.get(dep_name)
                if parent_node:
                    parent_node.add_child(node)
    return root


def find_node_by_name(node: Tree[DynamicField], name: str) -> Optional[Tree[DynamicField]]:
    if hasattr(node.value, "name") and node.value.name == name:
        return node
    for child in node.children:
        result = find_node_by_name(child, name)
        if result:
            return result
    return None


def get_ready_fields(tree: Tree[DynamicField], state=None) -> List[DynamicField]:
    """
    Given the dependency tree, return a list of fields whose dependencies are all fulfilled and are not yet filled.
    Uses get_missing_dependencies from fields.py for dependency checking.
    If state is not provided, assumes tree traversal only (legacy behavior).
    """
    ready: List[DynamicField] = []

    def is_filled(field: DynamicField) -> bool:
        return getattr(field, "value", None) is not None

    def dfs(node: Tree[DynamicField]):
        if node.value == "NoneDep":
            for child in node.children:
                dfs(child)
            return
        field: DynamicField = node.value
        if is_filled(field):
            for child in node.children:
                dfs(child)
            return
        depends_on = getattr(field, "depends_on", [])
        dep_names = [dep.field_name for dep in depends_on] if depends_on else []

        all_fulfilled = True
        for dep_name in dep_names:
            dep_node = find_node_by_name(tree, dep_name)
            if dep_node is None or not is_filled(dep_node.value):
                all_fulfilled = False
                break
        if all_fulfilled:
            ready.append(field)

        for child in node.children:
            dfs(child)

    dfs(tree)
    return ready
