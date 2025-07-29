from epure import epure
from ..tg_environment.t_user import TUser
from ..finance.currency import Currency
from ..tg_environment.t_message import TMessage
from .offer_state import OfferState
from .offer_type import OfferType
from uuid import UUID, uuid4
from datetime import datetime
from ..tg_environment.telegram_entity import TelegramEntity

# @epure()
class TOffer:
    from_user: TUser
    to_user: TUser
    offer_type: str
    offer_state: str
    subject: TelegramEntity
    currency: Currency
    price: float
    datetime: datetime
    duration: int
    offer_message: TMessage
    bidding_id: UUID

    def __init__(self,    
            from_user: TUser,
            to_user: TUser,
            offer_type: str,
            offer_state: str,
            subject: TMessage,
            currency: Currency,
            price: float,            
            offer_message: TMessage,
            duration: int=None,
            bidding_id: UUID=None
            ):
        self.from_user = from_user
        self.to_user = to_user
        self.offer_type = offer_type
        self.offer_state = offer_state
        self.subject = subject
        self.currency = currency
        self.price = price
        self.offer_message = offer_message
        self.duration = duration
        self.bidding_id = bidding_id
        self.datetime = datetime.now()

        if not self.bidding_id:
            self.bidding_id = uuid4()