from __future__ import annotations
from jaclang import *
import typing
from enum import Enum, auto
if typing.TYPE_CHECKING:
    from jivas.agent.core.graph_node import GraphNode
else:
    GraphNode, = jac_import('jivas.agent.core.graph_node', items={'GraphNode': None})

class Collection(GraphNode, Node):
    name: str = field('')
    data: dict = field(gen=lambda: {})

    def get_name(self) -> str:
        return self.name

    def set_name(self, name: str) -> None:
        self.name = name

    def get_data_item(self, label: str) -> any:
        return self.data.get(label, None)

    def set_data_item(self, label: str, value: any) -> None:
        self.data[label] = value

    def delete(self) -> list:
        return self.spawn(_purge_collection()).removed

class _purge_collection(Walker):
    removed: list = field(gen=lambda: JacList([]))

    class __specs__(Obj):
        private: static[bool] = True

    @with_entry
    def on_collection(self, here: Collection) -> None:
        if not self.visit(here.refs()):
            self.removed.append(here)
            Jac.destroy(here)

    @with_entry
    def on_collection_node(self, here: Node) -> None:
        self.visit(here.refs())
        self.removed.append(here)
        Jac.destroy(here)