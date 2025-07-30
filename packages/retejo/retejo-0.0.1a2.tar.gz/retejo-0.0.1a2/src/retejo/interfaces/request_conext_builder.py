from abc import abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from retejo.interfaces.method import Method
from retejo.types import File


@dataclass(frozen=True, slots=True)
class RequestContext:
    body: Mapping[str, Any] | None = None
    files: Mapping[str, File] | None = None
    headers: Mapping[str, Any] | None = None
    query_params: Mapping[str, Any] | None = None
    url_vars: Mapping[str, Any] | None = None


@runtime_checkable
class RequestContextBuilder(Protocol):
    @abstractmethod
    def build(self, method: Method[Any]) -> RequestContext:
        raise NotImplementedError
