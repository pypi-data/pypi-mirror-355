from .entity import uSwidEntity as uSwidEntity
from .vex_statement import uSwidVexStatement as uSwidVexStatement
from datetime import datetime
from typing import Any

class uSwidVexDocument:
    id: str | None
    author: str | None
    date: datetime | None
    version: str | None
    trusted_entity: uSwidEntity | None
    def __init__(self, data: dict[str, Any] | None = None) -> None: ...
    @property
    def statements(self) -> list[uSwidVexStatement]: ...
    def add_statement(self, statement: uSwidVexStatement) -> None: ...
    def load(self, data: dict[str, Any]) -> None: ...
