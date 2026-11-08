from enum import StrEnum


class InformationOrigin(StrEnum):
    USER_INPUT = "user_input"
    DRAWING_IMPORT = "drawing_import"
    ENGINEERING_ASSUMPTION = "engineering_assumption"
    CALCULATED = "calculated"
    APPROVED_DESIGN = "approved_design"


class ValidationStatus(StrEnum):
    NOT_CHECKED = "not_checked"
    VALID = "valid"
    INVALID = "invalid"
    REQUIRES_REVIEW = "requires_review"


class SourceKind(StrEnum):
    MANUAL = "manual"
    DWG = "dwg"
    DXF = "dxf"
    REVIT = "revit"
    IFC = "ifc"
    PDF = "pdf"
    PRODUCT_CATALOGUE = "product_catalogue"
    PUBLIC_WORKS_CATALOGUE = "public_works_catalogue"
    STANDARD = "standard"
    CALCULATION = "calculation"
    OTHER = "other"


class GeometryFormat(StrEnum):
    DWG = "dwg"
    DXF = "dxf"
    RVT = "rvt"
    IFC = "ifc"
    PDF = "pdf"
    OTHER = "other"


class RevisionState(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"


class ApprovalDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED_FOR_REVISION = "returned_for_revision"


class ConnectorDomain(StrEnum):
    FLUID = "fluid"
    AIR = "air"
    ELECTRICAL = "electrical"
    CONTROL = "control"
    STRUCTURAL = "structural"
    DATA = "data"
    SPATIAL = "spatial"
    GENERIC = "generic"


class ConnectorDirection(StrEnum):
    INLET = "inlet"
    OUTLET = "outlet"
    BIDIRECTIONAL = "bidirectional"
    UNSPECIFIED = "unspecified"


class ConnectionKind(StrEnum):
    PHYSICAL = "physical"
    FLOW = "flow"
    CONTROL = "control"
    LOGICAL = "logical"
    SPATIAL = "spatial"
    OTHER = "other"


class ConnectionDirection(StrEnum):
    BIDIRECTIONAL = "bidirectional"
    A_TO_B = "a_to_b"
    B_TO_A = "b_to_a"


class CalculationState(StrEnum):
    PREPARED = "prepared"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CalculationPurpose(StrEnum):
    ENGINEERING = "engineering"
    DEMONSTRATION = "demonstration"


class ValidationSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
