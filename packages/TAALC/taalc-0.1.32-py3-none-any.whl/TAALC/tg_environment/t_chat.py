from epure import epure
from .telegram_entity import TelegramEntity

@epure()
class TChat(TelegramEntity):    
    shifted_id: int