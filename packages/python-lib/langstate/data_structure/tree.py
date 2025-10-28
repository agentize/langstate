from __future__ import annotations
from dataclasses import dataclass, field
from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")

@dataclass(slots=True)
class TreeNode(Generic[T]):
    """Pure data-structure representation of a tree node."""
    value: Optional[T] = None
    children: List["TreeNode[T]"] = field(default_factory=list)

    def add_child(self, child: "TreeNode[T]") -> None:
        """Attach a child node."""
        self.children.append(child)

    def walk(self) -> List["TreeNode[T]"]:
        """Return a flat list of all nodes in depth-first order."""
        result = [self]
        for c in self.children:
            result.extend(c.walk())
        return result