from enum import Enum


class LeadStage(str, Enum):
    ENQUIRED = "enquired"
    ENGAGED = "engaged"
    CONTACTED = "contacted"
    IN_PROGRESS = "in_progress"
    QUALIFIED = "qualified"
    APPLICATION = "application"
    DEPOSIT = "deposit"
    COMPLETE = "complete"
    LOST = "lost"

class RoomType(str, Enum):
    NON_ENSUITE = "non_ensuite"
    ENSUITE = "ensuite"
    SHARED = "shared"
    STUDIO = "studio"
    APARTMENT = "apartment"

    def __str__(self) -> str:
        return self.value
    
class LevelOfStudy(str, Enum):
    UG = "UG"
    PG = "PG"
    NON_STUDENT = "Non Student"
    PHD = "PhD"

    def __str__(self) -> str:
        return self.value
    
class Currency(str, Enum):
    GBP = "GBP"
    EUR = "EUR"
    USD = "USD"
    INR = "INR"
    AUD = "AUD"
    PLN = "PLN"
    CAD = "CAD"
    AED = "AED"
    CHF = "CHF"
    DKK = "DKK"

    def __str__(self) -> str:
        return self.value
    
