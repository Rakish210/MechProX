from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from .context import AppContext


class Module(Protocol):
    name: str
    title: str
    def create_widget(self, context: AppContext) -> Any: ...

@dataclass
class ModuleSpec:
    name: str
    title: str
    factory: Callable[[AppContext], Any]

class ModuleRegistry:
    def __init__(self) -> None:
        self._modules: list[ModuleSpec] = []

    def register(self, spec: ModuleSpec) -> None:
        if any(m.name == spec.name for m in self._modules):
            raise ValueError(f"Module already registered: {spec.name}")
        self._modules.append(spec)

    def all(self) -> list[ModuleSpec]:
        return list(self._modules)
