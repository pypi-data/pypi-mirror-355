from .entity import uSwidEntity as uSwidEntity
from .vex_document import uSwidVexDocument as uSwidVexDocument
from .vex_product import uSwidVexProduct as uSwidVexProduct
from enum import Enum

class uSwidVexStatementStatus(Enum):
    UNKNOWN = 'unknown'
    NOT_AFFECTED = 'not_affected'
    AFFECTED = 'affected'
    FIXED = 'fixed'
    UNDER_INVESTIGATION = 'under_investigation'
    @classmethod
    def from_string(cls, status: str) -> uSwidVexStatementStatus: ...

class uSwidVexStatementJustification(Enum):
    UNKNOWN = 'unknown'
    COMPONENT_NOT_PRESENT = 'component_not_present'
    VULNERABLE_CODE_NOT_PRESENT = 'vulnerable_code_not_present'
    VULNERABLE_CODE_NOT_IN_EXECUTE_PATH = 'vulnerable_code_not_in_execute_path'
    VULNERABLE_CODE_CANNOT_BE_CONTROLLED_BY_ADVERSARY = 'vulnerable_code_cannot_be_controlled_by_adversary'
    INLINE_MITIGATIONS_ALREADY_EXIST = 'inline_mitigations_already_exist'
    @classmethod
    def from_string(cls, status: str) -> uSwidVexStatementJustification: ...

class uSwidVexStatement:
    vulnerability_name: str | None
    status: uSwidVexStatementStatus | None
    justification: uSwidVexStatementJustification | None
    impact_statement: str | None
    products: list[uSwidVexProduct]
    def __init__(self) -> None: ...
    @property
    def trusted_entity(self) -> uSwidEntity | None: ...
