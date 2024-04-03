from enum import Enum

class LoanStatus(Enum):
    IN_PROGRESS = "in-progress"
    APPROVED = "approved"
    NOT_APPROVED = "not approved"