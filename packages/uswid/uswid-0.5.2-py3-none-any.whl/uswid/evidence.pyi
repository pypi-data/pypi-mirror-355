from .problem import uSwidProblem as uSwidProblem
from datetime import datetime

class uSwidEvidence:
    date: datetime | None
    device_id: str | None
    def __init__(self, date: datetime | None = None, device_id: str | None = None) -> None: ...
    def problems(self) -> list[uSwidProblem]: ...
