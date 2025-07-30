from enum import Enum

class BillingType(str, Enum):
    PPU_BASED_ON_SESSION = "ppu_based_on_sessions"
    PPU_BASED_ON_CONSUMPTION = "ppu_based_on_consumption"

class Channel(str, Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    CALL = "call"
    WIDGET = "widget"

