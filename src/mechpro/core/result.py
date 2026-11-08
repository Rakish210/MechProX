from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")

@dataclass
class Result(Generic[T]):
    ok: bool
    value: T | None = None
    error: str | None = None

    @staticmethod
    def success(value: T) -> "Result[T]":
        return Result(True, value)

    @staticmethod
    def failure(error: str) -> "Result[T]":
        return Result(False, None, error)
